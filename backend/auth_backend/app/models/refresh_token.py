"""
Refresh token model for session management
"""
import uuid
from datetime import datetime, timedelta
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.orm import relationship
from auth_backend.database.connection import Base


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(
        CHAR(36), 
        primary_key=True, 
        default=lambda: str(uuid.uuid4()),
        unique=True,
        nullable=False
    )
    user_id = Column(CHAR(36), ForeignKey("users.id"), nullable=False)
    token = Column(Text, nullable=False, unique=True)
    expires_at = Column(DateTime, nullable=False)
    is_revoked = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="refresh_tokens")

    def __repr__(self):
        return f"<RefreshToken(id={self.id}, user_id={self.user_id}, expires_at={self.expires_at})>"

    @property
    def is_expired(self):
        """Check if token is expired"""
        return datetime.utcnow() > self.expires_at

    @property
    def is_valid(self):
        """Check if token is valid (not expired and not revoked)"""
        return not self.is_expired and not self.is_revoked

    def revoke(self):
        """Revoke the token"""
        self.is_revoked = True

    @classmethod
    def create_token(cls, user_id: str, token: str, expires_in_days: int = 30):
        """Create a new refresh token"""
        expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
        return cls(
            user_id=user_id,
            token=token,
            expires_at=expires_at
        )

