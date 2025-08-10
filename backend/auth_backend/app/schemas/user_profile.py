"""
User profile schemas for request/response validation
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, validator


class UserProfileCreate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    timezone: str = "UTC"

    @validator('first_name', 'last_name')
    def validate_names(cls, v):
        if v is not None and len(v.strip()) == 0:
            return None
        return v.strip() if v else None

    @validator('phone')
    def validate_phone(cls, v):
        if v is not None:
            # Remove all non-digit characters for validation
            digits_only = ''.join(filter(str.isdigit, v))
            if len(digits_only) < 10:
                raise ValueError('Phone number must contain at least 10 digits')
        return v
    
    @validator('timezone')
    def validate_timezone(cls, v):
        valid_timezones = [
            "UTC", "America/New_York", "America/Los_Angeles", "America/Chicago",
            "Europe/London", "Europe/Paris", "Europe/Berlin", "Asia/Tokyo",
            "Asia/Shanghai", "Asia/Kolkata", "Australia/Sydney"
        ]
        if v not in valid_timezones:
            raise ValueError(f'Invalid timezone. Must be one of: {", ".join(valid_timezones)}')
        return v

    @validator('timezone')
    def validate_timezone(cls, v):
        # List of common timezones - in production, you might want to use pytz
        valid_timezones = [
            "UTC", "America/New_York", "America/Los_Angeles", "America/Chicago",
            "Europe/London", "Europe/Paris", "Europe/Berlin", "Asia/Tokyo",
            "Asia/Shanghai", "Asia/Kolkata", "Australia/Sydney"
        ]
        if v not in valid_timezones:
            raise ValueError(f'Invalid timezone. Must be one of: {", ".join(valid_timezones)}')
        return v


class UserProfileUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    timezone: Optional[str] = None

    @validator('first_name', 'last_name')
    def validate_names(cls, v):
        if v is not None and len(v.strip()) == 0:
            return None
        return v.strip() if v else None

    @validator('phone')
    def validate_phone(cls, v):
        if v is not None:
            # Remove all non-digit characters for validation
            digits_only = ''.join(filter(str.isdigit, v))
            if len(digits_only) < 10:
                raise ValueError('Phone number must contain at least 10 digits')
        return v

    @validator('timezone')
    def validate_timezone(cls, v):
        if v is not None:
            valid_timezones = [
                "UTC", "America/New_York", "America/Los_Angeles", "America/Chicago",
                "Europe/London", "Europe/Paris", "Europe/Berlin", "Asia/Tokyo",
                "Asia/Shanghai", "Asia/Kolkata", "Australia/Sydney"
            ]
            if v not in valid_timezones:
                raise ValueError(f'Invalid timezone. Must be one of: {", ".join(valid_timezones)}')
        return v


class UserProfileResponse(BaseModel):
    id: str
    user_id: str
    first_name: Optional[str]
    last_name: Optional[str]
    phone: Optional[str]
    profile_picture_url: Optional[str]
    timezone: str
    created_at: datetime
    updated_at: datetime
    full_name: Optional[str]

    class Config:
        from_attributes = True

