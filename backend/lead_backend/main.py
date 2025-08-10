from fastapi import APIRouter, Depends, FastAPI, HTTPException, UploadFile, File, Query, BackgroundTasks, Request
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import os
import shutil
import uuid
from datetime import datetime
import redis
import json

from lead_backend.app.database.connection import get_db, create_tables
from lead_backend.app.services.lead_processing_service import LeadProcessingService
from lead_backend.app.services.lead_crud import LeadCRUD
from lead_backend.app.services.statistics_service import StatisticsService
from lead_backend.app.models.schemas import (
    LeadResponse, LeadCreate, LeadUpdate, LeadListResponse, 
    FileUploadResponse, FileDeleteResponse, LeadGroupingRequest, LeadGroupingResponse
)
from config.settings import settings

# Redis connection
redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Lead parsing and data cleaning module for outreach teams",
    docs_url="/docs",
    redoc_url="/redoc",
    redirect_slashes=False
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "uploads")
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

router = APIRouter()

def rate_limit_check(user_id: str) -> bool:
    """Check and enforce rate limiting using Redis"""
    key = f"rate_limit:{user_id}"
    current = redis_client.get(key)
    
    if current is None:
        redis_client.setex(key, settings.REDIS_RATE_LIMIT_WINDOW, 1)
        return True
    
    if int(current) >= settings.REDIS_MAX_REQUESTS:
        return False
        
    redis_client.incr(key)
    return True

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}

@router.post("/files/upload", response_model=Dict[str, Any])
async def upload_file(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    sheet_name: Optional[str] = Query(None, description="Sheet name for Excel files"),
    encoding: Optional[str] = Query("utf-8", description="File encoding for CSV/JSON files"),
    delimiter: Optional[str] = Query(",", description="Delimiter for CSV files"),
    db: Session = Depends(get_db)
):
    """Upload and process a file containing lead data"""
    
    user = request.state.current_user
    if not user:
        raise HTTPException(status_code=401, detail="User not authenticated")
    user_id = user.id
    
    if not rate_limit_check(user_id):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    file_extension = file.filename.split('.')[-1].lower()
    if file_extension not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file type. Allowed: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )
    
    if file.size and file.size > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400, 
            detail=f"File too large. Maximum size: {settings.MAX_FILE_SIZE} bytes"
        )
    
    unique_filename = f"{uuid.uuid4()}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        processing_service = LeadProcessingService(db)
        
        parser_kwargs = {}
        if file_extension in ['xlsx', 'xls'] and sheet_name:
            parser_kwargs['sheet_name'] = sheet_name
        elif file_extension == 'csv':
            parser_kwargs['encoding'] = encoding
            parser_kwargs['delimiter'] = delimiter
        elif file_extension == 'json':
            parser_kwargs['encoding'] = encoding
        
        result = processing_service.process_file_upload(
            file_path, 
            unique_filename, 
            user_id,
            **parser_kwargs
        )
        
        # Invalidate cache for file upload history
        redis_client.delete(f"file_history:{user_id}")
        
        return result
        
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"File processing failed: {str(e)}")

@router.delete("/files/{user_id}/{file_id}", response_model=FileDeleteResponse)
async def delete_file(
    user_id: str,
    file_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Delete a file upload and its associated leads"""
    user = request.state.current_user
    if not user or user.id != user_id:
        raise HTTPException(status_code=401, detail="User not authorized")
    
    if not rate_limit_check(user_id):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    
    processing_service = LeadProcessingService(db)
    result = processing_service.delete_file_upload(file_id, user_id=user_id)
    
    # Invalidate cache
    redis_client.delete(f"file_history:{user_id}")
    redis_client.delete(f"leads:{user_id}")
    
    return FileDeleteResponse(**result)

@router.get("/files/{user_id}/history", response_model=List[FileUploadResponse])
async def get_file_upload_history(
    user_id: str,
    request: Request,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Get file upload history for a specific user"""
    user = request.state.current_user
    if not user or user.id != user_id:
        raise HTTPException(status_code=401, detail="User not authorized")
    
    if not rate_limit_check(user_id):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    
    cache_key = f"file_history:{user_id}:{limit}:{offset}"
    cached_result = redis_client.get(cache_key)
    
    if cached_result:
        return json.loads(cached_result)
    
    processing_service = LeadProcessingService(db)
    history = processing_service.get_file_upload_history(limit, offset, user_id=user_id)
    
    result = [FileUploadResponse(**item) for item in history]
    redis_client.setex(cache_key, settings.REDIS_CACHE_TTL, json.dumps(jsonable_encoder(result)))
    
    return result

@router.get("/{user_id}", response_model=LeadListResponse)
async def get_leads(
    user_id: str,
    request: Request,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    search: Optional[str] = None,
    company: Optional[str] = None,
    industry: Optional[str] = None,
    city: Optional[str] = None,
    country: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get leads with optional filtering and pagination for a specific user"""
    user = request.state.current_user
    if not user or user.id != user_id:
        raise HTTPException(status_code=401, detail="User not authorized")
    
    if not rate_limit_check(user_id):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    
    cache_key = f"leads:{user_id}:{page}:{per_page}:{search}:{company}:{industry}:{city}:{country}"
    cached_result = redis_client.get(cache_key)
    
    if cached_result:
        return LeadListResponse.parse_raw(cached_result)
    
    lead_crud = LeadCRUD(db)
    
    filters = {'user_id': user_id}
    if search:
        filters['search'] = search
    if company:
        filters['company'] = company
    if industry:
        filters['industry'] = industry
    if city:
        filters['city'] = city
    if country:
        filters['country'] = country
    
    skip = (page - 1) * per_page
    
    leads = lead_crud.get_multiple(skip=skip, limit=per_page, filters=filters)
    total = lead_crud.count(filters=filters)
    total_pages = (total + per_page - 1) // per_page
    
    response = LeadListResponse(
        leads=[LeadResponse.from_orm(lead) for lead in leads],
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages
    )
    
    redis_client.setex(cache_key, settings.REDIS_CACHE_TTL, response.json())
    
    return response

@router.get("/{user_id}/{lead_id}", response_model=LeadResponse)
async def get_lead(
    user_id: str,
    lead_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Get a specific lead by ID for a specific user"""
    user = request.state.current_user
    if not user or user.id != user_id:
        raise HTTPException(status_code=401, detail="User not authorized")
    
    if not rate_limit_check(user_id):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    
    cache_key = f"lead:{user_id}:{lead_id}"
    cached_result = redis_client.get(cache_key)
    
    if cached_result:
        return LeadResponse.parse_raw(cached_result)
    
    lead_crud = LeadCRUD(db)
    lead = lead_crud.get(lead_id, user_id=user_id)
    
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found or not authorized")
    
    response = LeadResponse.from_orm(lead)
    redis_client.setex(cache_key, settings.REDIS_CACHE_TTL, response.json())
    
    return response

@router.post("/", response_model=LeadResponse)
async def create_lead(
    lead_data: LeadCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    """Create a new lead with user_id in body"""
    user = request.state.current_user
    if not user or user.id != lead_data.user_id:
        raise HTTPException(status_code=401, detail="User not authorized")
    
    if not rate_limit_check(lead_data.user_id):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    
    lead_crud = LeadCRUD(db)
    
    if lead_data.email:
        existing_lead = lead_crud.get_by_email(lead_data.email, user_id=lead_data.user_id)
        if existing_lead:
            raise HTTPException(status_code=400, detail="Lead with this email already exists for this user")
    
    lead = lead_crud.create(lead_data)
    
    # Invalidate cache for leads
    redis_client.delete(f"leads:{lead_data.user_id}")
    
    return LeadResponse.from_orm(lead)

@router.put("/{lead_id}", response_model=LeadResponse)
async def update_lead(
    lead_id: int,
    lead_data: LeadUpdate,
    request: Request,
    db: Session = Depends(get_db)
):
    """Update an existing lead with user_id in body"""
    user = request.state.current_user
    if not user or user.id != lead_data.user_id:
        raise HTTPException(status_code=401, detail="User not authorized")
    
    if not rate_limit_check(lead_data.user_id):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    
    lead_crud = LeadCRUD(db)
    lead = lead_crud.update(lead_id, lead_data, user_id=lead_data.user_id)
    
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found or not authorized")
    
    # Invalidate cache
    redis_client.delete(f"lead:{lead_data.user_id}:{lead_id}")
    redis_client.delete(f"leads:{lead_data.user_id}")
    
    return LeadResponse.from_orm(lead)

@router.delete("/{user_id}/{lead_id}")
async def delete_lead(
    user_id: str,
    lead_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Delete a lead for a specific user"""
    user = request.state.current_user
    if not user or user.id != user_id:
        raise HTTPException(status_code=401, detail="User not authorized")
    
    if not rate_limit_check(user_id):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    
    lead_crud = LeadCRUD(db)
    success = lead_crud.delete(lead_id, user_id=user_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Lead not found or not authorized")
    
    # Invalidate cache
    redis_client.delete(f"lead:{user_id}:{lead_id}")
    redis_client.delete(f"leads:{user_id}")
    
    return {"message": "Lead deleted successfully"}

@router.get("/user/{user_id}/statistics-overview")
async def get_lead_statistics(
    user_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """Get overall lead statistics for a user"""
    user = request.state.current_user
    if not user or user.id != user_id:
        raise HTTPException(status_code=401, detail="User not authorized")
    
    if not rate_limit_check(user_id):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    
    cache_key = f"stats:{user_id}"
    cached_result = redis_client.get(cache_key)
    
    if cached_result:
        return json.loads(cached_result)
    
    statistics_service = StatisticsService()
    result = statistics_service.get_lead_statistics(user_id, db)
    
    redis_client.setex(cache_key, settings.REDIS_CACHE_TTL, json.dumps(result))
    
    return result

@router.get("/user/{user_id}/group/location")
async def group_leads_by_location(
    user_id: str,
    request: Request,
    industry: Optional[str] = None,
    company: Optional[str] = None,
    country: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Group leads by location with optional filters for a user"""
    user = request.state.current_user
    if not user or user.id != user_id:
        raise HTTPException(status_code=401, detail="User not authorized")
    
    if not rate_limit_check(user_id):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    
    cache_key = f"location_groups:{user_id}:{industry}:{company}:{country}"
    cached_result = redis_client.get(cache_key)
    
    if cached_result:
        return json.loads(cached_result)
    
    filters = {}
    if industry:
        filters["industry"] = industry
    if company:
        filters["company"] = company
    if country:
        filters["country"] = country
    
    statistics_service = StatisticsService()
    result = statistics_service.group_leads_by_location(user_id, filters, db)
    
    redis_client.setex(cache_key, settings.REDIS_CACHE_TTL, json.dumps(result))
    
    return result

@router.get("/user/{user_id}/group/engagement")
async def group_leads_by_engagement(
    user_id: str,
    request: Request,
    industry: Optional[str] = None,
    company: Optional[str] = None,
    country: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Group leads by engagement level with optional filters for a user"""
    user = request.state.current_user
    if not user or user.id != user_id:
        raise HTTPException(status_code=401, detail="User not authorized")
    
    if not rate_limit_check(user_id):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    
    cache_key = f"engagement_groups:{user_id}:{industry}:{company}:{country}"
    cached_result = redis_client.get(cache_key)
    
    if cached_result:
        return json.loads(cached_result)
    
    filters = {}
    if industry:
        filters["industry"] = industry
    if company:
        filters["company"] = company
    if country:
        filters["country"] = country
    
    statistics_service = StatisticsService()
    result = statistics_service.group_leads_by_engagement(user_id, filters, db)
    
    redis_client.setex(cache_key, settings.REDIS_CACHE_TTL, json.dumps(result))
    
    return result

app.include_router(router)