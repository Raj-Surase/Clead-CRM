"""
User profile routes
"""
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, status
from sqlalchemy.orm import Session
import redis
from config.settings import settings

from auth_backend.database.connection import get_db
from auth_backend.app.schemas.user_profile import UserProfileUpdate, UserProfileResponse
from auth_backend.app.schemas.company_profile import CompanyProfileUpdate, CompanyProfileResponse
from auth_backend.app.services.user_service import UserService
from auth_backend.app.utils.security import get_current_verified_user
from auth_backend.app.models.user import User

redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)

router = APIRouter(tags=["User Profile"])

def rate_limit_check(user_id: str) -> bool:
    """Check and enforce rate limiting using Redis"""
    key = f"rate_limit:user:{user_id}"
    current = redis_client.get(key)
    
    if current is None:
        redis_client.setex(key, settings.REDIS_RATE_LIMIT_WINDOW, 1)
        return True
    
    if int(current) >= settings.REDIS_MAX_REQUESTS:
        return False
        
    redis_client.incr(key)
    return True

@router.get("/profile", response_model=UserProfileResponse)
async def get_user_profile(
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Get user profile"""
    if not rate_limit_check(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many profile requests"
        )
    user_service = UserService(db)
    profile = user_service.get_user_profile(current_user)
    if not profile:
        from auth_backend.app.models.user_profile import UserProfile
        empty_profile = UserProfile(user_id=current_user.id)
        return UserProfileResponse.from_orm(empty_profile)
    return profile

@router.put("/profile", response_model=UserProfileResponse)
async def update_user_profile(
    profile_data: UserProfileUpdate,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Update user profile"""
    if not rate_limit_check(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many profile update requests"
        )
    user_service = UserService(db)
    return user_service.create_or_update_user_profile(current_user, profile_data)

@router.get("/company", response_model=CompanyProfileResponse)
async def get_company_profile(
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Get company profile"""
    if not rate_limit_check(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many company profile requests"
        )
    user_service = UserService(db)
    profile = user_service.get_company_profile(current_user)
    if not profile:
        from auth_backend.app.models.company_profile import CompanyProfile
        empty_profile = CompanyProfile(user_id=current_user.id)
        return CompanyProfileResponse.from_orm(empty_profile)
    return profile

@router.put("/company", response_model=CompanyProfileResponse)
async def update_company_profile(
    profile_data: CompanyProfileUpdate,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Update company profile"""
    if not rate_limit_check(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many company profile update requests"
        )
    user_service = UserService(db)
    return user_service.create_or_update_company_profile(current_user, profile_data)

@router.post("/profile/avatar")
async def upload_profile_picture(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Upload profile picture"""
    if not rate_limit_check(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many profile picture upload requests"
        )
    user_service = UserService(db)
    return user_service.upload_profile_picture(current_user, file)

@router.delete("/profile/avatar")
async def remove_profile_picture(
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Remove profile picture"""
    if not rate_limit_check(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many profile picture removal requests"
        )
    user_service = UserService(db)
    return user_service.remove_profile_picture(current_user)

@router.delete("/account")
async def delete_account(
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Delete user account"""
    if not rate_limit_check(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many account deletion requests"
        )
    user_service = UserService(db)
    return user_service.delete_user_account(current_user)