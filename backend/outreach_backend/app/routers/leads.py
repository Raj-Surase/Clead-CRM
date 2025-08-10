from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any

from outreach_backend.app.database import get_db, get_lead_parser_db
from outreach_backend.app.schemas import Lead, LeadGroupingRequest, LeadGroupingResponse
from outreach_backend.app.services.lead_service import lead_service

router = APIRouter()

@router.get("/user/{user_id}/statistics-overview")
async def get_lead_statistics(
    user_id: str,
    lead_parser_db: Session = Depends(get_lead_parser_db),
    outreach_db: Session = Depends(get_db)
):
    """Get overall lead statistics for a user"""
    return lead_service.get_lead_statistics(user_id, lead_parser_db, outreach_db)

@router.get("/user/{user_id}/leads", response_model=List[Lead])
async def get_leads(
    user_id: str,
    skip: int = 0,
    limit: int = 100,
    industry: Optional[str] = None,
    lead_status: Optional[str] = None,
    lead_source: Optional[str] = None,
    priority: Optional[str] = None,
    country: Optional[str] = None,
    state: Optional[str] = None,
    city: Optional[str] = None,
    company: Optional[str] = None,
    job_title: Optional[str] = None,
    email_valid: Optional[bool] = None,
    phone_valid: Optional[bool] = None,
    min_lead_score: Optional[int] = None,
    max_lead_score: Optional[int] = None,
    min_data_completeness: Optional[int] = None,
    has_social_profiles: Optional[bool] = None,
    contacted: Optional[bool] = None,
    lead_parser_db: Session = Depends(get_lead_parser_db)
):
    """Get leads with optional filtering for a user"""
    # Build filters dictionary
    filters = {}
    if industry:
        filters["industry"] = industry
    if lead_status:
        filters["lead_status"] = lead_status
    if lead_source:
        filters["lead_source"] = lead_source
    if priority:
        filters["priority"] = priority
    if country:
        filters["country"] = country
    if state:
        filters["state"] = state
    if city:
        filters["city"] = city
    if company:
        filters["company"] = company
    if job_title:
        filters["job_title"] = job_title
    if email_valid is not None:
        filters["email_valid"] = email_valid
    if phone_valid is not None:
        filters["phone_valid"] = phone_valid
    if min_lead_score is not None:
        filters["min_lead_score"] = min_lead_score
    if max_lead_score is not None:
        filters["max_lead_score"] = max_lead_score
    if min_data_completeness is not None:
        filters["min_data_completeness"] = min_data_completeness
    if has_social_profiles is not None:
        filters["has_social_profiles"] = has_social_profiles
    if contacted is not None:
        filters["contacted"] = contacted
    
    return lead_service.get_leads(
        user_id=user_id,
        skip=skip,
        limit=limit,
        filters=filters,
        lead_parser_db=lead_parser_db
    )

@router.get("/user/{user_id}/leads/{lead_id}", response_model=Lead)
async def get_lead(
    user_id: str,
    lead_id: int,
    lead_parser_db: Session = Depends(get_lead_parser_db)
):
    """Get a specific lead by ID for a user"""
    lead = lead_service.get_lead(user_id, lead_id, lead_parser_db)
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found or not authorized for user"
        )
    return lead

@router.get("/user/{user_id}/search")
async def search_leads(
    user_id: str,
    search_term: str = Query(..., description="Search term to look for in lead data"),
    search_fields: Optional[List[str]] = Query(None, description="Fields to search in"),
    lead_parser_db: Session = Depends(get_lead_parser_db)
):
    """Search leads by term in specified fields for a user"""
    leads = lead_service.search_leads(
        user_id=user_id,
        search_term=search_term,
        search_fields=search_fields,
        lead_parser_db=lead_parser_db
    )
    
    return {
        "search_term": search_term,
        "search_fields": search_fields,
        "leads": leads,
        "count": len(leads)
    }

@router.post("/user/{user_id}/group", response_model=LeadGroupingResponse)
async def group_leads(
    user_id: str,
    request: LeadGroupingRequest,
    lead_parser_db: Session = Depends(get_lead_parser_db),
    outreach_db: Session = Depends(get_db)
):
    """Group leads based on specified criteria for a user"""
    if request.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User ID in request does not match authenticated user"
        )
    
    valid_group_by_options = [
        "industry", "status", "source", "location", 
        "platform", "engagement"
    ]
    
    if request.group_by not in valid_group_by_options:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid group_by option. Must be one of: {', '.join(valid_group_by_options)}"
        )
    
    try:
        return lead_service.group_leads(request, lead_parser_db, outreach_db)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/user/{user_id}/group/industry")
async def group_leads_by_industry(
    user_id: str,
    industry: Optional[str] = None,
    lead_status: Optional[str] = None,
    lead_source: Optional[str] = None,
    country: Optional[str] = None,
    lead_parser_db: Session = Depends(get_lead_parser_db)
):
    """Group leads by industry with optional filters for a user"""
    filters = {}
    if industry:
        filters["industry"] = industry
    if lead_status:
        filters["lead_status"] = lead_status
    if lead_source:
        filters["lead_source"] = lead_source
    if country:
        filters["country"] = country
    
    return lead_service.group_leads_by_industry(user_id, filters, lead_parser_db)

@router.get("/user/{user_id}/group/status")
async def group_leads_by_status(
    user_id: str,
    industry: Optional[str] = None,
    lead_source: Optional[str] = None,
    country: Optional[str] = None,
    lead_parser_db: Session = Depends(get_lead_parser_db)
):
    """Group leads by status with optional filters for a user"""
    filters = {}
    if industry:
        filters["industry"] = industry
    if lead_source:
        filters["lead_source"] = lead_source
    if country:
        filters["country"] = country
    
    return lead_service.group_leads_by_status(user_id, filters, lead_parser_db)

@router.get("/user/{user_id}/group/source")
async def group_leads_by_source(
    user_id: str,
    industry: Optional[str] = None,
    lead_status: Optional[str] = None,
    country: Optional[str] = None,
    lead_parser_db: Session = Depends(get_lead_parser_db)
):
    """Group leads by source with optional filters for a user"""
    filters = {}
    if industry:
        filters["industry"] = industry
    if lead_status:
        filters["lead_status"] = lead_status
    if country:
        filters["country"] = country
    
    return lead_service.group_leads_by_source(user_id, filters, lead_parser_db)

@router.get("/user/{user_id}/group/location")
async def group_leads_by_location(
    user_id: str,
    industry: Optional[str] = None,
    lead_status: Optional[str] = None,
    lead_source: Optional[str] = None,
    lead_parser_db: Session = Depends(get_lead_parser_db)
):
    """Group leads by location with optional filters for a user"""
    filters = {}
    if industry:
        filters["industry"] = industry
    if lead_status:
        filters["lead_status"] = lead_status
    if lead_source:
        filters["lead_source"] = lead_source
    
    return lead_service.group_leads_by_location(user_id, filters, lead_parser_db)

@router.get("/user/{user_id}/group/platform")
async def group_leads_by_platform_connectivity(
    user_id: str,
    industry: Optional[str] = None,
    lead_status: Optional[str] = None,
    country: Optional[str] = None,
    lead_parser_db: Session = Depends(get_lead_parser_db),
    outreach_db: Session = Depends(get_db)
):
    """Group leads by platform connectivity with optional filters for a user"""
    filters = {}
    if industry:
        filters["industry"] = industry
    if lead_status:
        filters["lead_status"] = lead_status
    if country:
        filters["country"] = country
    
    return lead_service.group_leads_by_platform_connectivity(user_id, filters, lead_parser_db, outreach_db)

@router.get("/user/{user_id}/group/engagement")
async def group_leads_by_engagement(
    user_id: str,
    industry: Optional[str] = None,
    lead_status: Optional[str] = None,
    country: Optional[str] = None,
    lead_parser_db: Session = Depends(get_lead_parser_db),
    outreach_db: Session = Depends(get_db)
):
    """Group leads by engagement level with optional filters for a user"""
    filters = {}
    if industry:
        filters["industry"] = industry
    if lead_status:
        filters["lead_status"] = lead_status
    if country:
        filters["country"] = country
    
    return lead_service.group_leads_by_engagement(user_id, filters, lead_parser_db, outreach_db)

@router.get("/user/{user_id}/filters/options")
async def get_filter_options(
    user_id: str,
    lead_parser_db: Session = Depends(get_lead_parser_db)
):
    """Get available filter options for leads for a user"""
    from sqlalchemy import distinct
    from outreach_backend.app.models import Lead
    
    # Get unique values for filter fields for user
    industries = [row[0] for row in lead_parser_db.query(distinct(Lead.industry)).filter(
        Lead.industry.isnot(None), Lead.user_id == user_id).all()]
    statuses = [row[0] for row in lead_parser_db.query(distinct(Lead.lead_status)).filter(
        Lead.lead_status.isnot(None), Lead.user_id == user_id).all()]
    sources = [row[0] for row in lead_parser_db.query(distinct(Lead.lead_source)).filter(
        Lead.lead_source.isnot(None), Lead.user_id == user_id).all()]
    priorities = [row[0] for row in lead_parser_db.query(distinct(Lead.priority)).filter(
        Lead.priority.isnot(None), Lead.user_id == user_id).all()]
    countries = [row[0] for row in lead_parser_db.query(distinct(Lead.country)).filter(
        Lead.country.isnot(None), Lead.user_id == user_id).all()]
    
    return {
        "industries": sorted(industries),
        "statuses": sorted(statuses),
        "sources": sorted(sources),
        "priorities": sorted(priorities),
        "countries": sorted(countries),
        "group_by_options": [
            "industry", "status", "source", "location", 
            "platform", "engagement"
        ]
    }

@router.get("/user/{user_id}/leads/{lead_id}/outreach-history")
async def get_lead_outreach_history(
    user_id: str,
    lead_id: int,
    lead_parser_db: Session = Depends(get_lead_parser_db),
    outreach_db: Session = Depends(get_db)
):
    """Get outreach history for a specific lead for a user"""
    # Verify lead exists and belongs to user
    lead = lead_service.get_lead(user_id, lead_id, lead_parser_db)
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found or not authorized for user"
        )
    
    from outreach_backend.app.models import OutreachMessage, Conversation
    
    # Get messages sent to this lead for user
    messages = outreach_db.query(OutreachMessage).filter(
        OutreachMessage.lead_id == lead_id,
        OutreachMessage.user_id == user_id
    ).order_by(OutreachMessage.sent_at.desc()).all()
    
    # Get conversations for this lead for user
    conversations = outreach_db.query(Conversation).filter(
        Conversation.lead_id == lead_id,
        Conversation.user_id == user_id
    ).all()
    
    return {
        "lead_id": lead_id,
        "lead": lead,
        "messages": messages,
        "conversations": conversations,
        "total_messages": len(messages),
        "total_conversations": len(conversations)
    }