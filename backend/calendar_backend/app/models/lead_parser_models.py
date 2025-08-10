"""
Lead Parser Models - Mirror of the existing lead parser database schema
These models represent the existing lead parser database tables for integration purposes
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey
from sqlalchemy.sql import func
from calendar_backend.app.database.connection import LeadParserBase

class FileUpload(LeadParserBase):
    """
    Mirror of the file_uploads table from lead parser module
    """
    __tablename__ = "file_uploads"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    file_type = Column(String(50), nullable=False)
    mime_type = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    user_id = Column(String(36), nullable=False, index=True)  # UUID string format

class Lead(LeadParserBase):
    """
    Mirror of the leads table from lead parser module
    """
    __tablename__ = "leads"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(36), nullable=False, index=True)  # UUID string format
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    full_name = Column(String(200), nullable=True, index=True)
    company = Column(String(200), nullable=True, index=True)
    job_title = Column(String(150), nullable=True)
    industry = Column(String(100), nullable=True)
    email = Column(String(255), nullable=True, index=True)
    phone = Column(String(50), nullable=True)
    mobile = Column(String(50), nullable=True)
    website = Column(String(500), nullable=True)
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    linkedin_url = Column(String(500), nullable=True)
    facebook_url = Column(String(500), nullable=True)
    instagram_url = Column(String(500), nullable=True)
    twitter_url = Column(String(500), nullable=True)
    youtube_url = Column(String(500), nullable=True)
    tiktok_url = Column(String(500), nullable=True)
    additional_data = Column(JSON, nullable=True)
    notes = Column(Text, nullable=True)
    tags = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    source_file_name = Column(String(255), nullable=True)
    source_file_row = Column(Integer, nullable=True)
    file_upload_id = Column(Integer, ForeignKey('file_uploads.id'), nullable=True)
    
    def __repr__(self):
        return f"<Lead(id={self.id}, full_name='{self.full_name}', company='{self.company}', email='{self.email}', user_id='{self.user_id}')>"
    
    @property
    def contact_methods(self):
        """Get available contact methods for this lead"""
        methods = []
        if self.email:
            methods.append("email")
        if self.phone:
            methods.append("phone")
        if self.mobile:
            methods.append("mobile")
        if self.linkedin_url:
            methods.append("linkedin")
        if self.facebook_url:
            methods.append("facebook")
        if self.instagram_url:
            methods.append("instagram")
        return methods
    
    @property
    def primary_contact_method(self):
        """Get the primary contact method based on availability"""
        if self.email:
            return "email"
        elif self.phone:
            return "phone"
        elif self.mobile:
            return "mobile"
        elif self.linkedin_url:
            return "linkedin"
        else:
            return None
    
    @property
    def display_name(self):
        """Get display name for the lead"""
        if self.full_name:
            return self.full_name
        elif self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.email:
            return self.email.split('@')[0]
        else:
            return f"Lead #{self.id}"
    
    @property
    def company_display(self):
        """Get company display name"""
        return self.company or "Unknown Company"
    
    def to_dict(self):
        """Convert lead to dictionary for API responses"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "full_name": self.full_name,
            "display_name": self.display_name,
            "company": self.company,
            "company_display": self.company_display,
            "job_title": self.job_title,
            "industry": self.industry,
            "email": self.email,
            "phone": self.phone,
            "mobile": self.mobile,
            "website": self.website,
            "city": self.city,
            "state": self.state,
            "country": self.country,
            "linkedin_url": self.linkedin_url,
            "facebook_url": self.facebook_url,
            "instagram_url": self.instagram_url,
            "twitter_url": self.twitter_url,
            "additional_data": self.additional_data,
            "notes": self.notes,
            "tags": self.tags,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "source_file_name": self.source_file_name,
            "source_file_row": self.source_file_row
        }