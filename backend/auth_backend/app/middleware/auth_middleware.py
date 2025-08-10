"""
Authentication middleware for request processing
"""
import logging
from typing import Optional
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.orm import Session

from auth_backend.database.connection import SessionLocal
from auth_backend.app.utils.security import verify_token
from auth_backend.app.models.user import User

logger = logging.getLogger(__name__)


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Authentication middleware for processing requests
    """
    
    def __init__(self, app):
        super().__init__(app)
        
        # Public endpoints that don't require authentication
        self.public_endpoints = {
            "/auth/register",
            "/auth/login",
            "/auth/google",
            "/auth/google/url",
            "/auth/forgot-password",
            "/auth/reset-password",
            "/auth/verify-email",
            "/auth/refresh",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health",
            "/"
        }
        
        # Endpoints that require verified email
        self.verified_required_endpoints = {
            "/auth/onboarding/personal",
            "/auth/onboarding/company",
            "/auth/onboarding/complete"
        }

    def get_db(self) -> Session:
        """Get database session"""
        return SessionLocal()

    def extract_token_from_header(self, request: Request) -> Optional[str]:
        """Extract JWT token from Authorization header"""
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return None
        
        try:
            scheme, token = auth_header.split(" ", 1)
            if scheme.lower() != "bearer":
                return None
            return token
        except ValueError:
            return None

    def is_public_endpoint(self, path: str) -> bool:
        """Check if endpoint is public"""
        return path in self.public_endpoints

    def requires_verified_email(self, path: str) -> bool:
        """Check if endpoint requires verified email"""
        return path in self.verified_required_endpoints

    async def dispatch(self, request: Request, call_next):
        """Process the request with authentication checks"""
        path = request.url.path
        
        # Skip authentication for public endpoints
        if self.is_public_endpoint(path):
            response = await call_next(request)
            return response
        
        # Extract token from header
        token = self.extract_token_from_header(request)
        if not token:
            return JSONResponse(
                status_code=401,
                content={"detail": "Authentication required"}
            )
        
        # Verify token
        payload = verify_token(token, "access")
        if not payload:
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid or expired token"}
            )
        
        user_id = payload.get("sub")
        if not user_id:
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid token payload"}
            )
        
        # Get user from database
        db = self.get_db()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return JSONResponse(
                    status_code=401,
                    content={"detail": "User not found"}
                )
            
            if not user.is_active:
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Account is deactivated"}
                )
            
            # Check email verification for specific endpoints
            if self.requires_verified_email(path) and not user.is_verified:
                return JSONResponse(
                    status_code=403,
                    content={"detail": "Email verification required"}
                )
            
            # Add user to request state for use in endpoints
            request.state.current_user = user
            
        except Exception as e:
            logger.error(f"Database error in auth middleware: {str(e)}")
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error"}
            )
        finally:
            db.close()
        
        # Process the request
        response = await call_next(request)
        return response

