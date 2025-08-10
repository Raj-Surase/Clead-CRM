"""
Authentication schemas package
"""
from .auth import (
    UserRegister, UserLogin, UserResponse, TokenResponse,
    PasswordReset, PasswordResetConfirm, EmailVerification
)
from .user_profile import UserProfileCreate, UserProfileUpdate, UserProfileResponse
from .company_profile import CompanyProfileCreate, CompanyProfileUpdate, CompanyProfileResponse
from .onboarding import OnboardingStatus, OnboardingPersonal, OnboardingCompany

__all__ = [
    "UserRegister", "UserLogin", "UserResponse", "TokenResponse",
    "PasswordReset", "PasswordResetConfirm", "EmailVerification",
    "UserProfileCreate", "UserProfileUpdate", "UserProfileResponse",
    "CompanyProfileCreate", "CompanyProfileUpdate", "CompanyProfileResponse",
    "OnboardingStatus", "OnboardingPersonal", "OnboardingCompany"
]

