"""
Onboarding routes
"""
from fastapi import HTTPException
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
import redis
from config.settings import settings

from auth_backend.database.connection import get_db
from auth_backend.app.schemas.onboarding import OnboardingStatus, OnboardingPersonal, OnboardingCompany
from auth_backend.app.schemas.user_profile import UserProfileResponse
from auth_backend.app.schemas.company_profile import CompanyProfileResponse
from auth_backend.app.services.user_service import UserService
from auth_backend.app.utils.security import get_current_verified_user
from auth_backend.app.models.user import User

redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)

router = APIRouter(tags=["Onboarding"])

def rate_limit_check(user_id: str) -> bool:
    """Check and enforce rate limiting using Redis"""
    key = f"rate_limit:onboarding:{user_id}"
    current = redis_client.get(key)
    
    if current is None:
        redis_client.setex(key, settings.REDIS_RATE_LIMIT_WINDOW, 1)
        return True
    
    if int(current) >= settings.REDIS_MAX_REQUESTS:
        return False
        
    redis_client.incr(key)
    return True

@router.get("/status", response_model=OnboardingStatus)
async def get_onboarding_status(
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Get onboarding completion status"""
    if not rate_limit_check(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many onboarding status requests"
        )
    user_service = UserService(db)
    return user_service.get_onboarding_status(current_user)

@router.put("/personal", response_model=UserProfileResponse)
async def update_personal_info(
    personal_data: OnboardingPersonal,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Update personal information during onboarding"""
    if not rate_limit_check(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many personal info update requests"
        )
    user_service = UserService(db)
    return user_service.update_personal_info(current_user, personal_data)

@router.put("/company", response_model=CompanyProfileResponse)
async def update_company_info(
    company_data: OnboardingCompany,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Update company information during onboarding"""
    if not rate_limit_check(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many company info update requests"
        )
    user_service = UserService(db)
    return user_service.update_company_info(current_user, company_data)

@router.post("/complete")
async def complete_onboarding(
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Mark onboarding as complete"""
    if not rate_limit_check(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many onboarding completion requests"
        )
    user_service = UserService(db)
    return user_service.complete_onboarding(current_user)