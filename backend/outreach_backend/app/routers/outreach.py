from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from sqlalchemy import String, func, or_
from pydantic import BaseModel

from outreach_backend.app.database import get_db, get_lead_parser_db
from outreach_backend.app.schemas import (
    SendMessageRequest, SendMessageResponse, OutreachMessage,
    OutreachMessageCreate, OutreachMessageUpdate, BulkMessageGroup
)
from outreach_backend.app.services.message_service import message_service
from outreach_backend.app.models import OutreachCampaign, OutreachMessage as OutreachMessageModel, OutreachPlatform
from outreach_backend.app.models import BulkMessageGroup as BulkMessageGroupModel

router = APIRouter()

class PaginatedMessagesResponse(BaseModel):
    results: List[OutreachMessage]
    per_page: int
    total_pages: int

@router.post("/user/{user_id}/send-message", response_model=SendMessageResponse)
async def send_message(
    user_id: str,
    request: SendMessageRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    lead_parser_db: Session = Depends(get_lead_parser_db)
):
    """Send messages to multiple leads via specified platform for a user"""
    # Validate request
    if not request.lead_ids and not request.campaign_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either lead_ids or campaign_id must be provided"
        )
    
    if not request.message_content.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message content cannot be empty"
        )
    
    if request.campaign_id:
        campaign = db.query(OutreachCampaign).filter(
            OutreachCampaign.id == request.campaign_id,
            OutreachCampaign.user_id == user_id
        ).first()
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found or not authorized for user"
            )
    
    # Create bulk message group
    bulk_group = BulkMessageGroupModel(
        user_id=user_id,
        platform_id=request.platform_id,
        campaign_id=request.campaign_id,
        total_leads=len(request.lead_ids) if request.lead_ids else 0,
        subject=request.subject,
        success_count=0,
        failed_count=0
    )
    db.add(bulk_group)
    db.commit()
    db.refresh(bulk_group)
    
    # Update request with bulk_group_id
    request.bulk_group_id = bulk_group.id
    
    # Send messages
    result = await message_service.send_bulk_messages(
        request,
        db,
        lead_parser_db
    )
    
    # Update bulk group stats
    bulk_group.success_count = result.get("success_count", 0)
    bulk_group.failed_count = result.get("failed_count", 0)
    db.commit()
    
    if not result.get("success", True):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "Failed to send messages")
        )
    
    return SendMessageResponse(**result)

@router.post("/user/{user_id}/resend-failed-messages/{bulk_group_id}", response_model=SendMessageResponse)
async def resend_failed_messages(
    user_id: str,
    bulk_group_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    lead_parser_db: Session = Depends(get_lead_parser_db)
):
    """Resend failed messages for a specific bulk message group for a user"""
    bulk_group = db.query(BulkMessageGroupModel).filter(
        BulkMessageGroupModel.id == bulk_group_id,
        BulkMessageGroupModel.user_id == user_id
    ).first()
    if not bulk_group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bulk message group not found or not authorized for user"
        )
    
    # Get failed messages
    failed_messages = db.query(OutreachMessageModel).filter(
        OutreachMessageModel.bulk_group_id == bulk_group_id,
        OutreachMessageModel.status == 'failed',
        OutreachMessageModel.user_id == user_id
    ).all()
    
    if not failed_messages:
        return SendMessageResponse(
            success_count=0,
            failed_count=0,
            messages=[],
            errors=["No failed messages to resend"]
        )
    
    # Create new bulk group for resend
    new_bulk_group = BulkMessageGroupModel(
        user_id=user_id,
        platform_id=bulk_group.platform_id,
        campaign_id=bulk_group.campaign_id,
        total_leads=len(failed_messages),
        subject=bulk_group.subject,
        is_resend=True,
        parent_group_id=bulk_group_id,
        success_count=0,
        failed_count=0
    )
    db.add(new_bulk_group)
    db.commit()
    db.refresh(new_bulk_group)
    
    # Resend messages
    result = await message_service.send_bulk_messages(
        SendMessageRequest(
            lead_ids=[msg.lead_id for msg in failed_messages],
            platform_id=bulk_group.platform_id,
            message_content=failed_messages[0].message_content,
            subject=bulk_group.subject,
            campaign_id=bulk_group.campaign_id,
            bulk_group_id=new_bulk_group.id,
            user_id=user_id
        ),
        db,
        lead_parser_db
    )
    
    # Update new bulk group stats
    new_bulk_group.success_count = result.get("success_count", 0)
    new_bulk_group.failed_count = result.get("failed_count", 0)
    db.commit()
    
    return SendMessageResponse(**result)

@router.get("/user/{user_id}/messages", response_model=PaginatedMessagesResponse)
async def get_messages(
    user_id: str,
    skip: int = 0,
    limit: int = 10,
    platform_id: int = None,
    lead_id: int = None,
    status: str = None,
    search: str = None,
    bulk_group_id: int = None,
    db: Session = Depends(get_db)
):
    """Get paginated outreach messages with optional filtering for a user"""
    query = db.query(OutreachMessageModel).filter(OutreachMessageModel.user_id == user_id)
    
    # Apply filters
    if platform_id:
        query = query.filter(OutreachMessageModel.platform_id == platform_id)
    
    if lead_id:
        query = query.filter(OutreachMessageModel.lead_id == lead_id)
    
    if status:
        query = query.filter(OutreachMessageModel.status == status)
    
    if bulk_group_id:
        query = query.filter(OutreachMessageModel.bulk_group_id == bulk_group_id)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                OutreachMessageModel.message_content.ilike(search_term),
                OutreachMessageModel.lead_id.cast(String).ilike(search_term)
            )
        )
    
    # Ensure only valid statuses are returned
    valid_statuses = ['sent', 'failed', 'delivered', 'read']
    query = query.filter(OutreachMessageModel.status.in_(valid_statuses))
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    messages = query.order_by(OutreachMessageModel.sent_at.desc()).offset(skip).limit(limit).all()
    
    return PaginatedMessagesResponse(
        results=messages,
        total=total,
        per_page=limit,
        total_pages=max(1, (total + limit - 1) // limit)
    )

@router.get("/user/{user_id}/bulk-message-groups", response_model=List[BulkMessageGroup])
async def get_bulk_message_groups(
    user_id: str,
    platform_id: int = None,
    campaign_id: int = None,
    db: Session = Depends(get_db)
):
    """Get bulk message groups with optional filtering for a user"""
    query = db.query(BulkMessageGroupModel).filter(BulkMessageGroupModel.user_id == user_id)
    
    if platform_id:
        query = query.filter(BulkMessageGroupModel.platform_id == platform_id)
    
    if campaign_id:
        query = query.filter(BulkMessageGroupModel.campaign_id == campaign_id)
    
    return query.all()

@router.get("/user/{user_id}/messages/{message_id}", response_model=OutreachMessage)
async def get_message(
    user_id: str,
    message_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific outreach message for a user"""
    message = db.query(OutreachMessageModel).filter(
        OutreachMessageModel.id == message_id,
        OutreachMessageModel.user_id == user_id
    ).first()
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found or not authorized for user"
        )
    return message

@router.put("/user/{user_id}/messages/{message_id}", response_model=OutreachMessage)
async def update_message(
    user_id: str,
    message_id: int,
    message_update: OutreachMessageUpdate,
    db: Session = Depends(get_db)
):
    """Update an outreach message for a user"""
    message = db.query(OutreachMessageModel).filter(
        OutreachMessageModel.id == message_id,
        OutreachMessageModel.user_id == user_id
    ).first()
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found or not authorized for user"
        )
    
    update_data = message_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(message, field, value)
    
    db.commit()
    db.refresh(message)
    return message

@router.delete("/user/{user_id}/messages/{message_id}")
async def delete_message(
    user_id: str,
    message_id: int,
    db: Session = Depends(get_db)
):
    """Delete an outreach message for a user"""
    message = db.query(OutreachMessageModel).filter(
        OutreachMessageModel.id == message_id,
        OutreachMessageModel.user_id == user_id
    ).first()
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found or not authorized for user"
        )
    
    db.delete(message)
    db.commit()
    return {"message": "Message deleted successfully"}

@router.delete("/user/{user_id}/bulk-messages/{bulk_group_id}")
async def delete_bulk_messages(
    user_id: str,
    bulk_group_id: int,
    db: Session = Depends(get_db)
):
    """Delete all messages associated with a bulk message group for a user"""
    bulk_group = db.query(BulkMessageGroupModel).filter(
        BulkMessageGroupModel.id == bulk_group_id,
        BulkMessageGroupModel.user_id == user_id
    ).first()
    if not bulk_group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bulk message group not found or not authorized for user"
        )
    
    # Delete all messages with this bulk_group_id
    deleted_count = db.query(OutreachMessageModel).filter(
        OutreachMessageModel.bulk_group_id == bulk_group_id,
        OutreachMessageModel.user_id == user_id
    ).delete()
    
    db.commit()
    
    return {
        "message": f"Successfully deleted {deleted_count} messages from bulk group {bulk_group_id}"
    }

@router.post("/user/{user_id}/validate-leads")
async def validate_leads_for_platform(
    user_id: str,
    lead_ids: List[int],
    platform_id: int,
    db: Session = Depends(get_db),
    lead_parser_db: Session = Depends(get_lead_parser_db)
):
    """Validate leads for a specific platform for a user"""
    from outreach_backend.app.models import Lead, OutreachPlatform
    
    platform = db.query(OutreachPlatform).filter(
        OutreachPlatform.id == platform_id,
        OutreachPlatform.user_id == user_id
    ).first()
    if not platform:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Platform not found or not authorized for user"
        )
    
    leads = lead_parser_db.query(Lead).filter(
        Lead.id.in_(lead_ids),
        Lead.user_id == user_id
    ).all()
    
    validation_results = []
    for lead in leads:
        is_valid = await message_service.validate_lead_for_platform(lead, platform, db)
        validation_results.append({
            "lead_id": lead.id,
            "is_valid": is_valid,
            "platform_name": platform.name
        })
    
    return {
        "platform_id": platform_id,
        "platform_name": platform.name,
        "total_leads": len(leads),
        "valid_leads": sum(1 for r in validation_results if r["is_valid"]),
        "invalid_leads": sum(1 for r in validation_results if not r["is_valid"]),
        "results": validation_results
    }

@router.get("/user/{user_id}/invalid-leads/{platform_id}")
async def get_invalid_leads(
    user_id: str,
    platform_id: int,
    db: Session = Depends(get_db)
):
    """Get list of invalid lead IDs for a platform for a user"""
    invalid_lead_ids = message_service.get_invalid_leads_for_platform(user_id, platform_id, db)
    return {
        "platform_id": platform_id,
        "invalid_lead_ids": invalid_lead_ids,
        "count": len(invalid_lead_ids)
    }

@router.get("/user/{user_id}/message-stats")
async def get_message_statistics(
    user_id: str,
    platform_id: int = None,
    bulk_group_id: int = None,
    db: Session = Depends(get_db)
):
    """Get message sending statistics for a user"""
    from sqlalchemy import func
    from outreach_backend.app.schemas import MessageStatus
    
    query = db.query(OutreachMessageModel).filter(OutreachMessageModel.user_id == user_id)
    
    if platform_id:
        query = query.filter(OutreachMessageModel.platform_id == platform_id)
    
    if bulk_group_id:
        query = query.filter(OutreachMessageModel.bulk_group_id == bulk_group_id)
    
    status_counts = query.with_entities(
        OutreachMessageModel.status,
        func.count(OutreachMessageModel.id)
    ).group_by(OutreachMessageModel.status).all()
    
    total_messages = query.count()
    
    stats = {
        "total_messages": total_messages,
        "status_breakdown": {status: count for status, count in status_counts},
        "success_rate": 0
    }
    
    sent_count = next((count for status, count in status_counts if status == MessageStatus.SENT), 0)
    if total_messages > 0:
        stats["success_rate"] = (sent_count / total_messages) * 100
    
    return stats