"""
Authentication routes package
"""
from .auth import router as auth_router
from .user import router as user_router
from .onboarding import router as onboarding_router

__all__ = ["auth_router", "user_router", "onboarding_router"]

