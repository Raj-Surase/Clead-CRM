from typing import Dict, Any, List, Optional
import logging
import os
from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import delete, and_
from .file_processor import FileProcessor
from .data_cleaner import DataCleaner
from .lead_crud import LeadCRUD
from lead_backend.app.models.schemas import LeadCreate
from lead_backend.app.models.file_upload import FileUpload
from lead_backend.app.models.lead import Lead
import time
from datetime import datetime
import redis
import json
from config.settings import settings

logger = logging.getLogger(__name__)

redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)

class LeadProcessingService:
    """Comprehensive lead processing service that orchestrates all operations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.file_processor = FileProcessor()
        self.data_cleaner = DataCleaner()
        self.lead_crud = LeadCRUD(db)
    
    def process_file_upload(self, file_path: str, original_filename: str, 
                          user_id: str, **parser_kwargs) -> Dict[str, Any]:
        """Process uploaded file and create leads for a specific user"""
        start_time = time.time()
        
        file_upload = FileUpload(
            filename=file_path.split('/')[-1],
            original_filename=original_filename,
            file_path=file_path,
            file_size=0,
            file_type=file_path.split('.')[-1].lower(),
            user_id=user_id
        )
        
        try:
            file_upload.file_size = os.path.getsize(file_path)
            
            self.db.add(file_upload)
            self.db.commit()
            self.db.refresh(file_upload)
            
            logger.info(f"Starting file processing for: {original_filename} by user: {user_id}")
            processing_result = self.file_processor.process_file(file_path, **parser_kwargs)
            
            if not processing_result['success']:
                raise HTTPException(status_code=400, detail=f"File processing failed: {'; '.join(processing_result['errors'])}")
            
            raw_data = processing_result['data']
            
            cleaned_data, cleaning_stats = self.data_cleaner.clean_batch_data(raw_data)
            
            created_leads = []
            failed_leads = []
            
            for i, lead_data in enumerate(cleaned_data):
                try:
                    lead_data['user_id'] = user_id
                    lead_data['source_file_name'] = original_filename
                    lead_data['file_upload_id'] = file_upload.id
                    
                    existing_lead = None
                    if lead_data.get('email'):
                        existing_lead = self.lead_crud.get_by_email(lead_data['email'], user_id)
                    
                    if existing_lead:
                        failed_leads.append(f"Row {i+1}: Lead with email already exists")
                        continue
                    
                    lead_create = LeadCreate(**lead_data)
                    new_lead = self.lead_crud.create(
                        lead_create,
                        source_file_name=original_filename,
                        source_file_row=lead_data.get('source_file_row'),
                        file_upload_id=file_upload.id
                    )
                    created_leads.append(new_lead)
                
                except Exception as e:
                    failed_leads.append(f"Row {i+1}: {str(e)}")
                    logger.error(f"Error processing lead {i+1}: {str(e)}")
            
            self.db.commit()
            
            logger.info(f"File processing completed. Created: {len(created_leads)}, Failed: {len(failed_leads)}")
            
            # Invalidate cache
            redis_client.delete(f"file_history:{user_id}")
            
            return {
                'success': True,
                'file_upload_id': file_upload.id,
                'stats': {
                    'created_leads': len(created_leads),
                    'failed_leads': len(failed_leads),
                    'cleaning_warnings': cleaning_stats.get('warnings', [])
                },
                'created_leads': [lead.id for lead in created_leads],
                'failed_leads': failed_leads
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"File processing failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"File processing failed: {str(e)}")
    
    def delete_file_upload(self, file_id: int, user_id: str) -> Dict[str, Any]:
        """Delete a file upload and its associated leads for a specific user"""
        file_upload = self.db.query(FileUpload).filter(and_(FileUpload.id == file_id, FileUpload.user_id == user_id)).first()
        
        if not file_upload:
            raise HTTPException(status_code=404, detail="File upload not found or not authorized")
        
        try:
            deleted_leads_count = self.db.query(Lead).filter(
                and_(
                    (Lead.source_file_name == file_upload.original_filename) |
                    (Lead.file_upload_id == file_id),
                    Lead.user_id == user_id
                )
            ).delete()
            
            if os.path.exists(file_upload.file_path):
                os.remove(file_upload.file_path)
            
            self.db.delete(file_upload)
            self.db.commit()
            
            logger.info(f"Deleted file upload {file_id} and {deleted_leads_count} associated leads for user {user_id}")
            
            # Invalidate cache
            redis_client.delete(f"file_history:{user_id}")
            
            return {
                "message": "File and associated leads deleted successfully",
                "file_id": file_id,
                "deleted_leads_count": deleted_leads_count
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting file upload {file_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}")
    
    def get_file_upload_history(self, limit: int = 50, offset: int = 0, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get file upload history for a specific user"""
        cache_key = f"file_history:{user_id}:{limit}:{offset}"
        cached_result = redis_client.get(cache_key)
        
        if cached_result:
            return json.loads(cached_result)
        
        try:
            query = self.db.query(FileUpload)
            if user_id:
                query = query.filter(FileUpload.user_id == user_id)
            
            file_uploads = (
                query
                .order_by(FileUpload.created_at.desc())
                .offset(offset)
                .limit(limit)
                .all()
            )
            result = [
                {
                    'id': upload.id,
                    'filename': upload.filename,
                    'original_filename': upload.original_filename,
                    'file_type': upload.file_type,
                    'file_size': upload.file_size,
                    'mime_type': upload.mime_type,
                    'created_at': upload.created_at.isoformat(),
                    'updated_at': upload.updated_at.isoformat() if upload.updated_at else None,
                    'user_id': upload.user_id
                }
                for upload in file_uploads
            ]
            
            redis_client.setex(cache_key, settings.REDIS_CACHE_TTL, json.dumps(result))
            
            return result
        except Exception as e:
            logger.error(f"Error fetching file upload history: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to fetch file upload history: {str(e)}")