"""
Company profile schemas for request/response validation
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, validator, HttpUrl


class CompanyProfileCreate(BaseModel):
    company_name: Optional[str] = None
    company_size: Optional[str] = None
    industry: Optional[str] = None
    website: Optional[str] = None
    description: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None

    @validator('company_size')
    def validate_company_size(cls, v):
        if v is not None:
            valid_sizes = [
                "1-10", "11-50", "51-200", "201-500", 
                "501-1000", "1001-5000", "5000+"
            ]
            if v not in valid_sizes:
                raise ValueError(f'Invalid company size. Must be one of: {", ".join(valid_sizes)}')
        return v

    @validator('industry')
    def validate_industry(cls, v):
        if v is not None:
            valid_industries = [
                "Technology", "Healthcare", "Finance", "Education", "Retail",
                "Manufacturing", "Real Estate", "Consulting", "Marketing",
                "Legal", "Non-profit", "Government", "Entertainment",
                "Transportation", "Energy", "Agriculture", "Other"
            ]
            if v not in valid_industries:
                raise ValueError(f'Invalid industry. Must be one of: {", ".join(valid_industries)}')
        return v

    @validator('website')
    def validate_website(cls, v):
        if v is not None and v.strip():
            # Add protocol if missing
            if not v.startswith(('http://', 'https://')):
                v = f'https://{v}'
            # Basic URL validation
            try:
                HttpUrl(v)
            except:
                raise ValueError('Invalid website URL format')
        return v

    @validator('postal_code')
    def validate_postal_code(cls, v):
        if v is not None:
            # Basic postal code validation (alphanumeric, spaces, hyphens)
            import re
            if not re.match(r'^[A-Za-z0-9\s\-]+$', v):
                raise ValueError('Invalid postal code format')
        return v


class CompanyProfileUpdate(BaseModel):
    company_name: Optional[str] = None
    company_size: Optional[str] = None
    industry: Optional[str] = None
    website: Optional[str] = None
    description: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None

    @validator('company_size')
    def validate_company_size(cls, v):
        if v is not None:
            valid_sizes = [
                "1-10", "11-50", "51-200", "201-500", 
                "501-1000", "1001-5000", "5000+"
            ]
            if v not in valid_sizes:
                raise ValueError(f'Invalid company size. Must be one of: {", ".join(valid_sizes)}')
        return v

    @validator('industry')
    def validate_industry(cls, v):
        if v is not None:
            valid_industries = [
                "Technology", "Healthcare", "Finance", "Education", "Retail",
                "Manufacturing", "Real Estate", "Consulting", "Marketing",
                "Legal", "Non-profit", "Government", "Entertainment",
                "Transportation", "Energy", "Agriculture", "Other"
            ]
            if v not in valid_industries:
                raise ValueError(f'Invalid industry. Must be one of: {", ".join(valid_industries)}')
        return v

    @validator('website')
    def validate_website(cls, v):
        if v is not None and v.strip():
            # Add protocol if missing
            if not v.startswith(('http://', 'https://')):
                v = f'https://{v}'
            # Basic URL validation
            try:
                HttpUrl(v)
            except:
                raise ValueError('Invalid website URL format')
        return v

    @validator('postal_code')
    def validate_postal_code(cls, v):
        if v is not None:
            # Basic postal code validation (alphanumeric, spaces, hyphens)
            import re
            if not re.match(r'^[A-Za-z0-9\s\-]+$', v):
                raise ValueError('Invalid postal code format')
        return v


class CompanyProfileResponse(BaseModel):
    id: str
    user_id: str
    company_name: Optional[str]
    company_size: Optional[str]
    industry: Optional[str]
    website: Optional[str]
    description: Optional[str]
    address: Optional[str]
    city: Optional[str]
    state: Optional[str]
    country: Optional[str]
    postal_code: Optional[str]
    created_at: datetime
    updated_at: datetime
    full_address: str
    is_complete: bool

    class Config:
        from_attributes = True

