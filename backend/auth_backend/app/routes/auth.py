"""
Authentication routes
"""
import json
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
import redis
from config.settings import settings

from auth_backend.database.connection import get_db
from auth_backend.app.schemas.auth import (
    UserRegister, UserLogin, TokenResponse, RefreshTokenRequest,
    PasswordReset, PasswordResetConfirm, EmailVerification,
    GoogleAuthRequest, ChangePasswordRequest, UserResponse
)
from auth_backend.app.services.auth_service import AuthService
from auth_backend.app.services.google_auth_service import GoogleAuthService
from auth_backend.app.utils.security import get_current_user, get_current_verified_user
from auth_backend.app.models.user import User

redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)

router = APIRouter(tags=["Authentication"])

def rate_limit_check(identifier: str) -> bool:
    """Check and enforce rate limiting using Redis"""
    key = f"rate_limit:auth:{identifier}"
    
    # Use Redis pipeline for atomic operations
    with redis_client.pipeline() as pipe:
        pipe.get(key)
        pipe.incr(key)
        pipe.expire(key, settings.REDIS_RATE_LIMIT_WINDOW)
        current, _, _ = pipe.execute()
    
    if current is None:
        return True
    
    if int(current) >= settings.REDIS_MAX_REQUESTS:
        return False
    
    return True

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegister,
    db: Session = Depends(get_db)
):
    """Register a new user"""
    if not rate_limit_check(user_data.email):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many registration attempts"
        )
    auth_service = AuthService(db)
    return auth_service.register_user(user_data)

@router.post("/login", response_model=TokenResponse)
async def login(
    login_data: UserLogin,
    db: Session = Depends(get_db)
):
    """Login user with email and password"""
    if not rate_limit_check(login_data.email):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts"
        )
    auth_service = AuthService(db)
    return auth_service.login_user(login_data)

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """Refresh access token"""
    if not rate_limit_check("refresh"):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many token refresh attempts"
        )
    auth_service = AuthService(db)
    return auth_service.refresh_access_token(refresh_data.refresh_token)

@router.post("/logout")
async def logout(
    refresh_data: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """Logout user"""
    if not rate_limit_check("logout"):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many logout attempts"
        )
    auth_service = AuthService(db)
    return auth_service.logout_user(refresh_data.refresh_token)

@router.get("/verify-email")
async def verify_email(
    token: str = Query(..., description="Email verification token"),
    db: Session = Depends(get_db)
):
    """Verify user email"""
    if not rate_limit_check(f"verify_email:{token[:10]}"):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many email verification attempts"
        )
    auth_service = AuthService(db)
    return auth_service.verify_email(token)

@router.post("/forgot-password")
async def forgot_password(
    reset_data: PasswordReset,
    db: Session = Depends(get_db)
):
    """Request password reset"""
    if not rate_limit_check(reset_data.email):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many password reset attempts"
        )
    auth_service = AuthService(db)
    return auth_service.request_password_reset(reset_data.email)

@router.post("/reset-password")
async def reset_password(
    reset_data: PasswordResetConfirm,
    db: Session = Depends(get_db)
):
    """Reset password with token"""
    if not rate_limit_check(f"reset_password:{reset_data.token[:10]}"):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many password reset attempts"
        )
    auth_service = AuthService(db)
    return auth_service.reset_password(reset_data.token, reset_data.new_password)

@router.post("/change-password")
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Change user password"""
    if not rate_limit_check(f"change_password:{current_user.id}"):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many password change attempts"
        )
    auth_service = AuthService(db)
    return auth_service.change_password(
        current_user, 
        password_data.current_password, 
        password_data.new_password
    )

@router.get("/me")
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Get current user information"""
    if not rate_limit_check(f"user_info:{current_user.id}"):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many user info requests"
        )
    cache_key = f"user:{current_user.id}"
    cached_user = redis_client.get(cache_key)
    
    if cached_user:
        return UserResponse.parse_obj(json.loads(cached_user))
        
    user_response = UserResponse(
        id=current_user.id,
        email=current_user.email,
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
        created_at=current_user.created_at,
        last_login=current_user.last_login,
        full_name=current_user.full_name,
        is_onboarding_complete=current_user.is_onboarding_complete
    )
    
    redis_client.setex(
        cache_key,
        settings.REDIS_CACHE_TTL,
        json.dumps(user_response.dict())
    )
    
    return user_response