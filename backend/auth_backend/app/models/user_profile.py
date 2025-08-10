"""
User profile model for personal information
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.orm import relationship
from auth_backend.database.connection import Base
from sqlalchemy.dialects.mysql import CHAR, ENUM

class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(
        CHAR(36), 
        primary_key=True, 
        default=lambda: str(uuid.uuid4()),
        unique=True,
        nullable=False
    )
    user_id = Column(CHAR(36), ForeignKey("users.id"), nullable=False, unique=True)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=True)
    profile_picture_url = Column(Text, nullable=True)
    timezone = Column(
        ENUM(
            'UTC',
            'America/New_York',
            'America/Los_Angeles',
            'America/Chicago',
            'Europe/London',
            'Europe/Paris',
            'Europe/Berlin',
            'Asia/Tokyo',
            'Asia/Shanghai',
            'Asia/Kolkata',
            'Australia/Sydney'
        ),
        nullable=False,
        default='UTC'
    )
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="profile")

    def __repr__(self):
        return f"<UserProfile(id={self.id}, user_id={self.user_id}, name={self.first_name} {self.last_name})>"

    @property
    def full_name(self):
        """Get user's full name"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        return None

