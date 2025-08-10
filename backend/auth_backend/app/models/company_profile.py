"""
Company profile model for business information
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Text
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.orm import relationship
from auth_backend.database.connection import Base


class CompanyProfile(Base):
    __tablename__ = "company_profiles"

    id = Column(
        CHAR(36), 
        primary_key=True, 
        default=lambda: str(uuid.uuid4()),
        unique=True,
        nullable=False
    )
    user_id = Column(CHAR(36), ForeignKey("users.id"), nullable=False, unique=True)
    company_name = Column(String(255), nullable=True)
    company_size = Column(String(50), nullable=True)  # e.g., "1-10", "11-50", "51-200", etc.
    industry = Column(String(100), nullable=True)
    website = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    
    # Address information
    address = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="company_profile")

    def __repr__(self):
        return f"<CompanyProfile(id={self.id}, user_id={self.user_id}, company={self.company_name})>"

    @property
    def full_address(self):
        """Get formatted full address"""
        address_parts = [
            self.address,
            self.city,
            self.state,
            self.postal_code,
            self.country
        ]
        return ", ".join([part for part in address_parts if part])

    @property
    def is_complete(self):
        """Check if company profile has minimum required information"""
        return (
            self.company_name is not None and
            self.industry is not None and
            self.company_size is not None
        )

