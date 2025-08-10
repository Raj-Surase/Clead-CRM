"""
User service for profile and onboarding management
"""
import os
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status, UploadFile
from datetime import datetime
import redis
import json
from config.settings import settings

from auth_backend.app.models.user import User
from auth_backend.app.models.user_profile import UserProfile
from auth_backend.app.models.company_profile import CompanyProfile
from auth_backend.app.schemas.user_profile import UserProfileCreate, UserProfileUpdate, UserProfileResponse
from auth_backend.app.schemas.company_profile import CompanyProfileCreate, CompanyProfileUpdate, CompanyProfileResponse
from auth_backend.app.schemas.onboarding import OnboardingStatus, OnboardingPersonal, OnboardingCompany

redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)

class UserService:
    def __init__(self, db: Session):
        self.db = db

    def get_user_profile(self, user: User) -> Optional[UserProfileResponse]:
        """Get user profile"""
        cache_key = f"user_profile:{user.id}"
        cached_profile = redis_client.get(cache_key)
        
        if cached_profile:
            return UserProfileResponse.parse_obj(json.loads(cached_profile))
        
        if not user.profile:
            return None
        
        profile = UserProfileResponse.from_orm(user.profile)
        redis_client.setex(
            cache_key,
            settings.REDIS_CACHE_TTL,
            profile.json()
        )
        return profile

    def create_or_update_user_profile(self, user: User, profile_data: UserProfileUpdate) -> UserProfileResponse:
        """Create or update user profile"""
        if user.profile:
            # Update existing profile
            for field, value in profile_data.dict(exclude_unset=True).items():
                setattr(user.profile, field, value)
            user.profile.updated_at = datetime.utcnow()
        else:
            # Create new profile
            profile_dict = profile_data.dict(exclude_unset=True)
            user.profile = UserProfile(user_id=user.id, **profile_dict)
            self.db.add(user.profile)

        self.db.commit()
        self.db.refresh(user.profile)
        
        # Update cache
        profile = UserProfileResponse.from_orm(user.profile)
        redis_client.setex(
            f"user_profile:{user.id}",
            settings.REDIS_CACHE_TTL,
            profile.json()
        )
        redis_client.delete(f"onboarding_status:{user.id}")
        
        return profile

    def get_company_profile(self, user: User) -> Optional[CompanyProfileResponse]:
        """Get company profile"""
        cache_key = f"company_profile:{user.id}"
        cached_profile = redis_client.get(cache_key)
        
        if cached_profile:
            return CompanyProfileResponse.parse_obj(json.loads(cached_profile))
        
        if not user.company_profile:
            return None
        
        profile = CompanyProfileResponse.from_orm(user.company_profile)
        redis_client.setex(
            cache_key,
            settings.REDIS_CACHE_TTL,
            profile.json()
        )
        return profile

    def create_or_update_company_profile(self, user: User, profile_data: CompanyProfileUpdate) -> CompanyProfileResponse:
        """Create or update company profile"""
        if user.company_profile:
            # Update existing profile
            for field, value in profile_data.dict(exclude_unset=True).items():
                setattr(user.company_profile, field, value)
            user.company_profile.updated_at = datetime.utcnow()
        else:
            # Create new profile
            profile_dict = profile_data.dict(exclude_unset=True)
            user.company_profile = CompanyProfile(user_id=user.id, **profile_dict)
            self.db.add(user.company_profile)

        self.db.commit()
        self.db.refresh(user.company_profile)
        
        # Update cache
        profile = CompanyProfileResponse.from_orm(user.company_profile)
        redis_client.setex(
            f"company_profile:{user.id}",
            settings.REDIS_CACHE_TTL,
            profile.json()
        )
        redis_client.delete(f"onboarding_status:{user.id}")
        
        return profile

    def get_onboarding_status(self, user: User) -> OnboardingStatus:
        """Get user onboarding status"""
        cache_key = f"onboarding_status:{user.id}"
        cached_status = redis_client.get(cache_key)
        
        if cached_status:
            return OnboardingStatus.parse_obj(json.loads(cached_status))
        
        steps_completed = {
            "email_verified": user.is_verified,
            "personal_info": False,
            "company_info": False
        }

        # Check personal info completion
        if user.profile and user.profile.first_name and user.profile.last_name:
            steps_completed["personal_info"] = True

        # Check company info completion
        if (user.company_profile and 
            user.company_profile.company_name and 
            user.company_profile.industry and 
            user.company_profile.company_size):
            steps_completed["company_info"] = True

        # Determine next step
        next_step = None
        if not steps_completed["email_verified"]:
            next_step = "verify_email"
        elif not steps_completed["personal_info"]:
            next_step = "personal_info"
        elif not steps_completed["company_info"]:
            next_step = "company_info"

        is_complete = all(steps_completed.values())

        status = OnboardingStatus(
            is_complete=is_complete,
            steps_completed=steps_completed,
            next_step=next_step
        )
        
        redis_client.setex(
            cache_key,
            settings.REDIS_CACHE_TTL,
            status.json()
        )
        
        return status

    def update_personal_info(self, user: User, personal_data: OnboardingPersonal) -> UserProfileResponse:
        """Update personal information during onboarding"""
        profile_data = UserProfileUpdate(
            first_name=personal_data.first_name,
            last_name=personal_data.last_name,
            phone=personal_data.phone,
            timezone=personal_data.timezone
        )
        return self.create_or_update_user_profile(user, profile_data)

    def update_company_info(self, user: User, company_data: OnboardingCompany) -> CompanyProfileResponse:
        """Update company information during onboarding"""
        profile_data = CompanyProfileUpdate(
            company_name=company_data.company_name,
            company_size=company_data.company_size,
            industry=company_data.industry,
            website=company_data.website,
            description=company_data.description,
            address=company_data.address,
            city=company_data.city,
            state=company_data.state,
            country=company_data.country,
            postal_code=company_data.postal_code
        )
        return self.create_or_update_company_profile(user, profile_data)

    def complete_onboarding(self, user: User) -> dict:
        """Mark onboarding as complete"""
        onboarding_status = self.get_onboarding_status(user)
        
        if not onboarding_status.is_complete:
            missing_steps = [
                step for step, completed in onboarding_status.steps_completed.items() 
                if not completed
            ]
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot complete onboarding. Missing steps: {', '.join(missing_steps)}"
            )

        # Update cache
        redis_client.delete(f"onboarding_status:{user.id}")
        
        return {
            "message": "Onboarding completed successfully",
            "onboarding_status": onboarding_status
        }

    def upload_profile_picture(self, user: User, file: UploadFile) -> dict:
        """Upload user profile picture"""
        # Validate file type
        allowed_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file type. Only JPEG, PNG, GIF, and WebP are allowed."
            )

        # Validate file size (5MB limit)
        max_size = 5 * 1024 * 1024  # 5MB
        if file.size and file.size > max_size:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File too large. Maximum size is 5MB."
            )

        try:
            # Create uploads directory if it doesn't exist
            upload_dir = os.path.join(os.getcwd(), "uploads", "profile_pictures")
            os.makedirs(upload_dir, exist_ok=True)

            # Generate unique filename
            import uuid
            file_extension = file.filename.split(".")[-1] if file.filename else "jpg"
            filename = f"{user.id}_{uuid.uuid4().hex}.{file_extension}"
            file_path = os.path.join(upload_dir, filename)

            # Save file
            with open(file_path, "wb") as buffer:
                content = file.file.read()
                buffer.write(content)

            # Update user profile with file URL
            if not user.profile:
                user.profile = UserProfile(user_id=user.id)
                self.db.add(user.profile)

            user.profile.profile_picture_url = f"/uploads/profile_pictures/{filename}"
            user.profile.updated_at = datetime.utcnow()
            self.db.commit()

            # Update cache
            redis_client.delete(f"user_profile:{user.id}")
            
            return {
                "message": "Profile picture uploaded successfully",
                "profile_picture_url": user.profile.profile_picture_url
            }

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload file: {str(e)}"
            )

    def remove_profile_picture(self, user: User) -> dict:
        """Remove user profile picture"""
        if not user.profile or not user.profile.profile_picture_url:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No profile picture found"
            )

        # Remove file from filesystem
        try:
            if user.profile.profile_picture_url.startswith("/uploads/"):
                file_path = os.path.join(os.getcwd(), user.profile.profile_picture_url.lstrip("/"))
                if os.path.exists(file_path):
                    os.remove(file_path)
        except Exception:
            pass

        # Update database
        user.profile.profile_picture_url = None
        user.profile.updated_at = datetime.utcnow()
        self.db.commit()

        # Update cache
        redis_client.delete(f"user_profile:{user.id}")
        
        return {"message": "Profile picture removed successfully"}

    def delete_user_account(self, user: User) -> dict:
        """Delete user account and all associated data"""
        try:
            # Remove profile picture file if exists
            if user.profile and user.profile.profile_picture_url:
                try:
                    if user.profile.profile_picture_url.startswith("/uploads/"):
                        file_path = os.path.join(os.getcwd(), user.profile.profile_picture_url.lstrip("/"))
                        if os.path.exists(file_path):
                            os.remove(file_path)
                except Exception:
                    pass

            # Delete user (cascading will delete related records)
            self.db.delete(user)
            self.db.commit()

            # Clear cache
            redis_client.delete(f"user:{user.id}")
            redis_client.delete(f"user_email:{user.email}")
            redis_client.delete(f"user_profile:{user.id}")
            redis_client.delete(f"company_profile:{user.id}")
            redis_client.delete(f"onboarding_status:{user.id}")

            return {"message": "Account deleted successfully"}

        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete account: {str(e)}"
            )