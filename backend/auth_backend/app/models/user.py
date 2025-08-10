"""
User model for authentication system
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Text
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.orm import relationship
from auth_backend.database.connection import Base


class User(Base):
    __tablename__ = "users"

    id = Column(
        CHAR(36), 
        primary_key=True, 
        default=lambda: str(uuid.uuid4()),
        unique=True,
        nullable=False
    )
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=True)  # Nullable for OAuth users
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    google_id = Column(String(255), unique=True, nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login = Column(DateTime, nullable=True)

    # Relationships
    profile = relationship("UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    company_profile = relationship("CompanyProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>"

    @property
    def full_name(self):
        """Get user's full name from profile"""
        if self.profile:
            return f"{self.profile.first_name} {self.profile.last_name}".strip()
        return self.email.split("@")[0]

    @property
    def is_onboarding_complete(self):
        """Check if user has completed onboarding"""
        return (
            self.profile is not None and
            self.profile.first_name is not None and
            self.profile.last_name is not None and
            self.company_profile is not None and
            self.company_profile.company_name is not None
        )

