from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any, List
from datetime import datetime

class LeadBase(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    full_name: Optional[str] = None
    company: Optional[str] = None
    job_title: Optional[str] = None
    industry: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    website: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    linkedin_url: Optional[str] = None
    facebook_url: Optional[str] = None
    instagram_url: Optional[str] = None
    twitter_url: Optional[str] = None
    youtube_url: Optional[str] = None
    tiktok_url: Optional[str] = None
    additional_data: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None
    tags: Optional[str] = None

class LeadCreate(LeadBase):
    user_id: str  # Required for POST

class LeadUpdate(LeadBase):
    user_id: str  # Required for PUT

class LeadResponse(LeadBase):
    id: int
    user_id: str
    created_at: datetime
    updated_at: datetime
    source_file_name: Optional[str]
    source_file_row: Optional[int]

    class Config:
        from_attributes = True

class LeadListResponse(BaseModel):
    leads: List[LeadResponse]
    total: int
    page: int
    per_page: int
    total_pages: int

class FileUploadResponse(BaseModel):
    id: int
    user_id: str
    filename: str
    original_filename: str
    file_size: int
    file_type: str
    mime_type: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class FileDeleteResponse(BaseModel):
    message: str
    file_id: int

class LeadGroupingRequest(BaseModel):
    user_id: str
    group_by: str
    filters: Optional[Dict[str, Any]] = None

class LeadGroupingResponse(BaseModel):
    groups: Dict[str, Any]
    total_leads: int
    group_type: str