from fastapi import APIRouter, Depends, HTTPException, Query, status, BackgroundTasks
from sqlalchemy import text
from sqlalchemy.orm import Session
from typing import List, Optional

from outreach_backend.app.database import get_db, get_lead_parser_db, get_calendar_db
from outreach_backend.app.services.integration_service import integration_service
from outreach_backend.app.schemas import Event

router = APIRouter()

@router.post("/user/{user_id}/sync-lead-contact-status/{lead_id}")
async def sync_lead_contact_status(
    user_id: str,
    lead_id: int,
    platform_name: str,
    outreach_db: Session = Depends(get_db),
    lead_parser_db: Session = Depends(get_lead_parser_db)
):
    """Sync contact status for a lead back to lead parser database for a user"""
    success = integration_service.sync_lead_contact_status(
        lead_id, platform_name, user_id, outreach_db, lead_parser_db
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to sync lead contact status or not authorized for user"
        )
    
    return {"message": "Lead contact status synced successfully"}

@router.post("/user/{user_id}/create-follow-up-event")
async def create_follow_up_event(
    user_id: str,
    lead_id: int,
    outreach_message_id: int,
    follow_up_days: int = 3,
    calendar_db: Session = Depends(get_calendar_db),
    lead_parser_db: Session = Depends(get_lead_parser_db),
    outreach_db: Session = Depends(get_db)
):
    """Create a follow-up event in the calendar system for a user"""
    event = integration_service.create_follow_up_event(
        lead_id, outreach_message_id, follow_up_days, user_id,
        calendar_db, lead_parser_db, outreach_db
    )
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create follow-up event or not authorized for user"
        )
    
    return {
        "message": "Follow-up event created successfully",
        "event_id": event.id,
        "event": event
    }

@router.get("/user/{user_id}/leads-with-upcoming-events")
async def get_leads_with_upcoming_events(
    user_id: str,
    days_ahead: int = 7,
    calendar_db: Session = Depends(get_calendar_db),
    lead_parser_db: Session = Depends(get_lead_parser_db)
):
    """Get leads that have upcoming events for a user"""
    results = integration_service.get_leads_with_upcoming_events(
        user_id, days_ahead, calendar_db, lead_parser_db
    )
    
    return {
        "days_ahead": days_ahead,
        "leads_with_events": results,
        "count": len(results)
    }

@router.get("/user/{user_id}/leads-for-outreach-based-on-events")
async def get_leads_for_outreach_based_on_events(
    user_id: str,
    event_types: Optional[List[str]] = Query(None),
    days_before_event: int = 1,
    calendar_db: Session = Depends(get_calendar_db),
    lead_parser_db: Session = Depends(get_lead_parser_db),
    outreach_db: Session = Depends(get_db)
):
    """Get leads for outreach based on upcoming events for a user"""
    results = integration_service.get_leads_for_outreach_based_on_events(
        user_id, event_types, days_before_event, calendar_db, lead_parser_db, outreach_db
    )
    return {
        "event_types": event_types,
        "days_before_event": days_before_event,
        "leads_for_outreach": results,
        "count": len(results),
        "should_contact_count": len([r for r in results if r["should_contact"]])
    }

@router.post("/user/{user_id}/sync-conversation-to-calendar/{conversation_id}")
async def sync_conversation_to_calendar(
    user_id: str,
    conversation_id: int,
    create_follow_up: bool = True,
    outreach_db: Session = Depends(get_db),
    calendar_db: Session = Depends(get_calendar_db),
    lead_parser_db: Session = Depends(get_lead_parser_db)
):
    """Create calendar events based on conversation activity for a user"""
    event = integration_service.sync_conversation_to_calendar(
        conversation_id, create_follow_up, user_id, outreach_db, calendar_db, lead_parser_db
    )
    
    if not event:
        return {"message": "No event created (no follow-up needed or conversation not found)"}
    
    return {
        "message": "Conversation synced to calendar successfully",
        "event_id": event.id,
        "event": event
    }

@router.get("/user/{user_id}/lead-engagement-score/{lead_id}")
async def get_lead_engagement_score(
    user_id: str,
    lead_id: int,
    outreach_db: Session = Depends(get_db),
    calendar_db: Session = Depends(get_calendar_db)
):
    """Calculate engagement score for a lead for a user"""
    score_data = integration_service.get_lead_engagement_score(
        lead_id, user_id, outreach_db, calendar_db
    )
    
    return score_data

@router.post("/user/{user_id}/bulk-sync")
async def bulk_sync_lead_data(
    user_id: str,
    background_tasks: BackgroundTasks,
    lead_ids: Optional[List[int]] = None,
    outreach_db: Session = Depends(get_db),
    lead_parser_db: Session = Depends(get_lead_parser_db),
    calendar_db: Session = Depends(get_calendar_db)
):
    """Bulk sync data between outreach system and other modules for a user"""
    # Run sync in background for large datasets
    if not lead_ids or len(lead_ids) > 100:
        background_tasks.add_task(
            integration_service.bulk_sync_lead_data,
            lead_ids, user_id, outreach_db, lead_parser_db, calendar_db
        )
        return {"message": "Bulk sync started in background"}
    
    # Run sync immediately for small datasets
    results = integration_service.bulk_sync_lead_data(
        lead_ids, user_id, outreach_db, lead_parser_db, calendar_db
    )
    
    return results

@router.get("/user/{user_id}/integration-health")
async def check_integration_health(
    user_id: str,
    outreach_db: Session = Depends(get_db),
    lead_parser_db: Session = Depends(get_lead_parser_db),
    calendar_db: Session = Depends(get_calendar_db)
):
    """Check the health of integrations with other modules for a user"""
    health_status = {
        "outreach_db": "healthy",
        "lead_parser_db": "healthy",
        "calendar_db": "healthy",
        "integration_status": "healthy"
    }
    
    try:
        # Test outreach database
        outreach_db.execute(text("SELECT 1"))
    except Exception as e:
        health_status["outreach_db"] = f"error: {str(e)}"
        health_status["integration_status"] = "degraded"
    
    try:
        # Test lead parser database
        lead_parser_db.execute(text("SELECT 1"))
    except Exception as e:
        health_status["lead_parser_db"] = f"error: {str(e)}"
        health_status["integration_status"] = "degraded"
    
    try:
        # Test calendar database
        calendar_db.execute(text("SELECT 1"))
    except Exception as e:
        health_status["calendar_db"] = f"error: {str(e)}"
        health_status["integration_status"] = "degraded"
    
    return health_status

@router.get("/user/{user_id}/integration-statistics")
async def get_integration_statistics(
    user_id: str,
    outreach_db: Session = Depends(get_db),
    # lead_parser_db: Session = Depends(get_lead_parser_db),
    # calendar_db: Session = Depends(get_calendar_db)
):
    """Get statistics about data integration for a user"""
    from outreach_backend.app.models import Lead, Event, OutreachMessage, Conversation
    
    try:
        # Count records in each database for user
        # total_leads = lead_parser_db.query(Lead).filter(Lead.user_id == user_id).count()
        # total_events = calendar_db.query(Event).filter(Event.user_id == user_id).count()
        total_messages = outreach_db.query(OutreachMessage).filter(OutreachMessage.user_id == user_id).count()
        total_conversations = outreach_db.query(Conversation).filter(Conversation.user_id == user_id).count()
        
        # Count leads with events
        # leads_with_events = calendar_db.query(Event.lead_id).filter(
        #     Event.lead_id.isnot(None),
        #     Event.user_id == user_id
        # ).distinct().count()
        
        # Count leads with outreach activity
        leads_with_messages = outreach_db.query(OutreachMessage.lead_id).filter(
            OutreachMessage.user_id == user_id
        ).distinct().count()

        average_messages_per_lead = (
            total_messages / leads_with_messages if leads_with_messages > 0 else 0
        )
        
        return {
            # "total_leads": total_leads,
            # "total_events": total_events,
            "total_messages": total_messages,
            "total_conversations": total_conversations,
            "average_messages_per_lead": average_messages_per_lead
            # "leads_with_events": leads_with_events,
            # "leads_with_messages": leads_with_messages,
            # "integration_coverage": {
            #     "leads_with_events_percentage": (leads_with_events / total_leads * 100) if total_leads > 0 else 0,
            #     "leads_with_messages_percentage": (leads_with_messages / total_leads * 100) if total_leads > 0 else 0
            # }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting integration statistics: {str(e)}"
        )