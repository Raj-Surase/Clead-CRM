from sqlalchemy import JSON, Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from lead_backend.app.database.connection import Base
from datetime import datetime
from typing import Optional

class Lead(Base):
    __tablename__ = "leads"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # User association
    user_id = Column(String(36), nullable=False, index=True)  # UUID string format
    
    # Basic information
    first_name = Column(String(100), nullable=True, index=True)
    last_name = Column(String(100), nullable=True, index=True)
    full_name = Column(String(200), nullable=True, index=True)
    company = Column(String(200), nullable=True, index=True)
    job_title = Column(String(200), nullable=True)
    industry = Column(String(100), nullable=True)
    
    # Contact information
    email = Column(String(255), nullable=True, index=True)
    phone = Column(String(50), nullable=True)
    mobile = Column(String(50), nullable=True)
    website = Column(String(500), nullable=True)
    
    # Address information
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    
    # Social media profiles
    linkedin_url = Column(String(500), nullable=True)
    facebook_url = Column(String(500), nullable=True)
    instagram_url = Column(String(500), nullable=True)
    twitter_url = Column(String(500), nullable=True)
    youtube_url = Column(String(500), nullable=True)
    tiktok_url = Column(String(500), nullable=True)
    
    # Additional data
    additional_data = Column(JSON, nullable=True)
    
    # Notes and comments
    notes = Column(Text, nullable=True)
    tags = Column(String(500), nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # File tracking
    source_file_name = Column(String(255), nullable=True)
    source_file_row = Column(Integer, nullable=True)
    file_upload_id = Column(Integer, ForeignKey('file_uploads.id'), nullable=True)
    
    def __repr__(self):
        return f"<Lead(id={self.id}, name='{self.full_name}', email='{self.email}', user_id='{self.user_id}')>"