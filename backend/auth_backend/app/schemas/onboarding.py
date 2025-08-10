"""
Onboarding schemas for request/response validation
"""
from typing import Optional
from pydantic import BaseModel


class OnboardingStatus(BaseModel):
    is_complete: bool
    steps_completed: dict
    next_step: Optional[str]


class OnboardingPersonal(BaseModel):
    first_name: str
    last_name: str
    phone: Optional[str] = None
    timezone: str = "UTC"


class OnboardingCompany(BaseModel):
    company_name: str
    company_size: str
    industry: str
    website: Optional[str] = None
    description: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None

