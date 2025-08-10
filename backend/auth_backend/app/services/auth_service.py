"""
Authentication service for handling user authentication logic
"""
from datetime import datetime, timedelta
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import redis
import json
from config.settings import settings

from auth_backend.app.models.user import User
from auth_backend.app.models.user_profile import UserProfile
from auth_backend.app.models.company_profile import CompanyProfile
from auth_backend.app.models.refresh_token import RefreshToken
from auth_backend.app.schemas.auth import UserRegister, UserLogin, TokenResponse, UserResponse
from auth_backend.app.utils.security import (
    hash_password, verify_password, create_access_token, create_refresh_token,
    verify_token, create_verification_token, create_password_reset_token,
    verify_verification_token, generate_secure_token, ACCESS_TOKEN_EXPIRE_MINUTES
)
from auth_backend.app.utils.email import send_verification_email, send_password_reset_email

redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)

class AuthService:
    def __init__(self, db: Session):
        self.db = db

    def register_user(self, user_data: UserRegister) -> dict:
        """Register a new user"""
        # Check cache first
        cache_key = f"user_email:{user_data.email}"
        if redis_client.get(cache_key):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        # Check database
        existing_user = self.db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            redis_client.setex(cache_key, settings.REDIS_CACHE_TTL, "exists")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        # Create new user
        hashed_password = hash_password(user_data.password)
        user = User(
            email=user_data.email,
            password_hash=hashed_password,
            is_active=True,
            is_verified=False
        )
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

        # Create empty user profile
        user_profile = UserProfile(user_id=user.id)
        self.db.add(user_profile)

        # Create empty company profile
        company_profile = CompanyProfile(user_id=user.id)
        self.db.add(company_profile)

        self.db.commit()

        # Cache user existence
        redis_client.setex(cache_key, settings.REDIS_CACHE_TTL, "exists")

        # Send verification email
        verification_token = create_verification_token(user.email)
        send_verification_email(user.email, verification_token)

        return {
            "message": "User registered successfully. Please check your email to verify your account.",
            "user_id": user.id
        }

    def login_user(self, login_data: UserLogin) -> TokenResponse:
        """Authenticate user and return tokens"""
        # Rate limiting
        rate_limit_key = f"rate_limit:login:{login_data.email}"
        current = redis_client.get(rate_limit_key)
        
        if current and int(current) >= settings.REDIS_MAX_REQUESTS:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many login attempts"
            )
        
        redis_client.incr(rate_limit_key)
        redis_client.expire(rate_limit_key, settings.REDIS_RATE_LIMIT_WINDOW)

        # Check Redis cache for user credentials
        cache_key = f"user_credentials:{login_data.email}"
        cached_credentials = redis_client.get(cache_key)
        
        if cached_credentials:
            cached_data = json.loads(cached_credentials)
            user_id = cached_data.get("id")
            stored_password_hash = cached_data.get("password_hash")
            is_active = cached_data.get("is_active")
            
            if not is_active:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Account is deactivated"
                )
            
            if not verify_password(login_data.password, stored_password_hash):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Incorrect email or password"
                )
            
            user = self.db.query(User).filter(User.id == user_id).first()
        else:
            # Query database if not in cache
            user = self.db.query(User).filter(User.email == login_data.email).first()
            
            if not user or not verify_password(login_data.password, user.password_hash):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Incorrect email or password"
                )

            if not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Account is deactivated"
                )
            
            # Cache credentials
            redis_client.setex(
                cache_key,
                settings.REDIS_CACHE_TTL,
                json.dumps({
                    "id": user.id,
                    "password_hash": user.password_hash,
                    "is_active": user.is_active
                })
            )

        # Update last login
        user.last_login = datetime.utcnow()
        # self.db.commit()

        # Create tokens
        access_token = create_access_token(data={"sub": user.id})
        refresh_token_str = create_refresh_token(data={"sub": user.id})

        # Store refresh token in database
        refresh_token = RefreshToken.create_token(user.id, refresh_token_str)
        self.db.add(refresh_token)
        self.db.commit()

        # Cache user response
        user_response = UserResponse(
            id=user.id,
            email=user.email,
            is_active=user.is_active,
            is_verified=user.is_verified,
            created_at=user.created_at,
            last_login=user.last_login,
            full_name=user.full_name,
            is_onboarding_complete=user.is_onboarding_complete
        )
        
        redis_client.setex(
            f"user:{user.id}",
            settings.REDIS_CACHE_TTL,
            json.dumps(user_response.dict(), default=str)
        )
        redis_client.setex(
            f"user_email:{user.email}",
            settings.REDIS_CACHE_TTL,
            "exists"
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token_str,
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=user_response
        )

    def refresh_access_token(self, refresh_token: str) -> TokenResponse:
        """Refresh access token using refresh token"""
        # Rate limiting
        rate_limit_key = f"rate_limit:refresh_token"
        current = redis_client.get(rate_limit_key)
        
        if current and int(current) >= settings.REDIS_MAX_REQUESTS:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many token refresh attempts"
            )
        
        redis_client.incr(rate_limit_key)
        redis_client.expire(rate_limit_key, settings.REDIS_RATE_LIMIT_WINDOW)

        # Verify refresh token
        payload = verify_token(refresh_token, "refresh")
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )

        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )

        # Check cache first
        cache_key = f"user:{user_id}"
        cached_user = redis_client.get(cache_key)
        
        if cached_user:
            user_response = UserResponse.parse_obj(json.loads(cached_user))
            user = self.db.query(User).filter(User.id == user_id).first()
            if user and not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found or inactive"
                )
        else:
            # Check database
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user or not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found or inactive"
                )
            
            user_response = UserResponse(
                id=user.id,
                email=user.email,
                is_active=user.is_active,
                is_verified=user.is_verified,
                created_at=user.created_at,
                last_login=user.last_login,
                full_name=user.full_name,
                is_onboarding_complete=user.is_onboarding_complete
            )
            redis_client.setex(
                cache_key,
                settings.REDIS_CACHE_TTL,
                json.dumps(user_response.dict(), default=str)
            )

        # Check refresh token in database
        db_refresh_token = self.db.query(RefreshToken).filter(
            RefreshToken.token == refresh_token,
            RefreshToken.user_id == user_id
        ).first()

        if not db_refresh_token or not db_refresh_token.is_valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token"
            )

        # Create new access token
        access_token = create_access_token(data={"sub": user_id})

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=user_response
        )

    def logout_user(self, refresh_token: str) -> dict:
        """Logout user by revoking refresh token"""
        # Find and revoke refresh token
        db_refresh_token = self.db.query(RefreshToken).filter(
            RefreshToken.token == refresh_token
        ).first()

        if db_refresh_token:
            db_refresh_token.revoke()
            self.db.commit()

        return {"message": "Logged out successfully"}

    def verify_email(self, token: str) -> dict:
        """Verify user email with token"""
        email = verify_verification_token(token, "email_verification")
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired verification token"
            )

        user = self.db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        if user.is_verified:
            return {"message": "Email already verified"}

        user.is_verified = True
        self.db.commit()

        # Invalidate user cache
        redis_client.delete(f"user:{user.id}")
        redis_client.delete(f"user_email:{email}")

        return {"message": "Email verified successfully"}

    def request_password_reset(self, email: str) -> dict:
        """Request password reset"""
        # Rate limiting
        rate_limit_key = f"rate_limit:password_reset:{email}"
        current = redis_client.get(rate_limit_key)
        
        if current and int(current) >= settings.REDIS_MAX_REQUESTS:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many password reset attempts"
            )
        
        redis_client.incr(rate_limit_key)
        redis_client.expire(rate_limit_key, settings.REDIS_RATE_LIMIT_WINDOW)

        user = self.db.query(User).filter(User.email == email).first()
        if not user:
            return {"message": "If the email exists, a password reset link has been sent"}

        # Create password reset token
        reset_token = create_password_reset_token(email)
        send_password_reset_email(email, reset_token)

        return {"message": "If the email exists, a password reset link has been sent"}

    def reset_password(self, token: str, new_password: str) -> dict:
        """Reset password with token"""
        email = verify_verification_token(token, "password_reset")
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token"
            )

        user = self.db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Update password
        user.password_hash = hash_password(new_password)
        self.db.commit()

        # Revoke all refresh tokens and clear cache
        self.db.query(RefreshToken).filter(RefreshToken.user_id == user.id).update(
            {"is_revoked": True}
        )
        self.db.commit()
        redis_client.delete(f"user:{user.id}")
        redis_client.delete(f"user_email:{email}")

        return {"message": "Password reset successfully"}

    def change_password(self, user: User, current_password: str, new_password: str) -> dict:
        """Change user password"""
        if not verify_password(current_password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )

        # Update password
        user.password_hash = hash_password(new_password)
        self.db.commit()

        # Revoke all refresh tokens and clear cache
        self.db.query(RefreshToken).filter(RefreshToken.user_id == user.id).update(
            {"is_revoked": True}
        )
        self.db.commit()
        redis_client.delete(f"user:{user.id}")
        redis_client.delete(f"user_email:{user.email}")

        return {"message": "Password changed successfully"}