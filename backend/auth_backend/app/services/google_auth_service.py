"""
Google OAuth authentication service
"""
import os
import requests
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import datetime

from auth_backend.app.models.user import User
from auth_backend.app.models.user_profile import UserProfile
from auth_backend.app.models.company_profile import CompanyProfile
from auth_backend.app.models.refresh_token import RefreshToken
from auth_backend.app.schemas.auth import TokenResponse, UserResponse
from auth_backend.app.utils.security import (
    create_access_token, create_refresh_token, ACCESS_TOKEN_EXPIRE_MINUTES
)

# Google OAuth configuration
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:3000/auth/google/callback")


class GoogleAuthService:
    def __init__(self, db: Session):
        self.db = db

    def get_google_auth_url(self, state: Optional[str] = None) -> str:
        """Generate Google OAuth authorization URL"""
        if not GOOGLE_CLIENT_ID:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Google OAuth not configured"
            )

        base_url = "https://accounts.google.com/o/oauth2/auth"
        params = {
            "client_id": GOOGLE_CLIENT_ID,
            "redirect_uri": GOOGLE_REDIRECT_URI,
            "scope": "openid email profile",
            "response_type": "code",
            "access_type": "offline",
            "prompt": "consent"
        }
        
        if state:
            params["state"] = state

        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{base_url}?{query_string}"

    def exchange_code_for_token(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        """Exchange authorization code for access token"""
        if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Google OAuth not configured"
            )

        token_url = "https://oauth2.googleapis.com/token"
        data = {
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri
        }

        try:
            response = requests.post(token_url, data=data)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to exchange code for token: {str(e)}"
            )

    def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """Get user information from Google"""
        user_info_url = "https://www.googleapis.com/oauth2/v2/userinfo"
        headers = {"Authorization": f"Bearer {access_token}"}

        try:
            response = requests.get(user_info_url, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to get user info: {str(e)}"
            )

    def authenticate_with_google(self, code: str, redirect_uri: str) -> TokenResponse:
        """Authenticate user with Google OAuth"""
        # Exchange code for token
        token_data = self.exchange_code_for_token(code, redirect_uri)
        access_token = token_data.get("access_token")
        
        if not access_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to get access token from Google"
            )

        # Get user info from Google
        user_info = self.get_user_info(access_token)
        google_id = user_info.get("id")
        email = user_info.get("email")
        name = user_info.get("name", "")
        picture = user_info.get("picture")

        if not google_id or not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to get user information from Google"
            )

        # Check if user exists by Google ID
        user = self.db.query(User).filter(User.google_id == google_id).first()
        
        if not user:
            # Check if user exists by email
            user = self.db.query(User).filter(User.email == email).first()
            
            if user:
                # Link Google account to existing user
                user.google_id = google_id
                user.is_verified = True  # Google accounts are pre-verified
            else:
                # Create new user
                user = User(
                    email=email,
                    google_id=google_id,
                    is_active=True,
                    is_verified=True,  # Google accounts are pre-verified
                    password_hash=None  # No password for OAuth users
                )
                self.db.add(user)
                self.db.flush()  # Get user ID

                # Create user profile with Google info
                name_parts = name.split(" ", 1) if name else ["", ""]
                first_name = name_parts[0] if name_parts[0] else None
                last_name = name_parts[1] if len(name_parts) > 1 and name_parts[1] else None

                user_profile = UserProfile(
                    user_id=user.id,
                    first_name=first_name,
                    last_name=last_name,
                    profile_picture_url=picture
                )
                self.db.add(user_profile)

                # Create empty company profile
                company_profile = CompanyProfile(user_id=user.id)
                self.db.add(company_profile)

        # Update last login
        user.last_login = datetime.utcnow()
        self.db.commit()
        self.db.refresh(user)

        # Create JWT tokens
        jwt_access_token = create_access_token(data={"sub": user.id})
        refresh_token_str = create_refresh_token(data={"sub": user.id})

        # Store refresh token in database
        refresh_token = RefreshToken.create_token(user.id, refresh_token_str)
        self.db.add(refresh_token)
        self.db.commit()

        # Create user response
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

        return TokenResponse(
            access_token=jwt_access_token,
            refresh_token=refresh_token_str,
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=user_response
        )

    def unlink_google_account(self, user: User) -> dict:
        """Unlink Google account from user"""
        if not user.google_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No Google account linked"
            )

        if not user.password_hash:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot unlink Google account without setting a password first"
            )

        user.google_id = None
        self.db.commit()

        return {"message": "Google account unlinked successfully"}

