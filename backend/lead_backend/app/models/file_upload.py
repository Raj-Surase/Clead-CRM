from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func
from lead_backend.app.database.connection import Base
from datetime import datetime

class FileUpload(Base):
    __tablename__ = "file_uploads"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # User association
    user_id = Column(String(36), nullable=False, index=True)  # UUID string format
    
    # File information
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    file_type = Column(String(50), nullable=False)
    mime_type = Column(String(100), nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<FileUpload(id={self.id}, filename='{self.filename}', user_id='{self.user_id}')>"