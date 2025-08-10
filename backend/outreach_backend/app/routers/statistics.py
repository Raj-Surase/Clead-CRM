from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict
from pydantic import BaseModel
from outreach_backend.app.database import get_db, get_lead_parser_db, get_calendar_db
from outreach_backend.app.models import CampaignLead, OutreachMessage, OutreachCampaign, Lead, Event
from outreach_backend.app.schemas import MessageStatus

router = APIRouter()

class MessageStat(BaseModel):
    name: str
    value: int
    status: str

class EngagementData(BaseModel):
    lead_id: int
    engagement_score: int
    messages_sent: int
    responses: int

class OverallStatisticsResponse(BaseModel):
    statistics: Dict[str, float]
    messageStats: List[MessageStat]
    engagementData: List[EngagementData]

@router.get("/user/{user_id}/overall", response_model=OverallStatisticsResponse)
async def get_overall_statistics(user_id: str, db: Session = Depends(get_db), lead_parser_db: Session = Depends(get_lead_parser_db), calendar_db: Session = Depends(get_calendar_db)):
    """Calculate overall statistics for a user"""
    # Calculate total counts
    total_messages = db.query(OutreachMessage).filter(OutreachMessage.user_id == user_id).count()
    total_campaigns = db.query(OutreachCampaign).filter(OutreachCampaign.user_id == user_id).count()
    # Count distinct leads with sent or replied messages to represent "active interactions"
    active_interactions = db.query(OutreachMessage.lead_id).filter(OutreachMessage.user_id == user_id).distinct().count()

    # Calculate leads with events percentage
    total_leads = lead_parser_db.query(Lead).filter(Lead.user_id == user_id).count()
    leads_with_events = calendar_db.query(Event.lead_id).filter(Event.user_id == user_id, Event.lead_id.isnot(None)).distinct().count()
    leads_with_events_percentage = (leads_with_events / total_leads * 100) if total_leads > 0 else 0.0

    # Calculate response rate (based on messages with status "replied")
    replied_messages = db.query(OutreachMessage).filter(
        OutreachMessage.user_id == user_id,
        OutreachMessage.status == MessageStatus.REPLIED
    ).count()
    response_rate = (replied_messages / total_messages * 100) if total_messages > 0 else 0.0

    # Calculate conversion rate (based on leads with status "converted")
    converted_leads = db.query(CampaignLead).join(
        Lead, CampaignLead.lead_id == Lead.id
    ).filter(
        CampaignLead.status == "converted",
        Lead.user_id == user_id
    ).count()
    conversion_rate = (converted_leads / total_leads * 100) if total_leads > 0 else 0.0

    # Message statistics by status
    message_stats_query = db.query(
        OutreachMessage.status,
        func.count(OutreachMessage.id).label("count")
    ).filter(OutreachMessage.user_id == user_id).group_by(OutreachMessage.status).all()
    
    message_stats = [
        MessageStat(
            name=status.capitalize(),
            value=count,
            status=status
        ) for status, count in message_stats_query
    ]

    # Ensure all expected statuses are included
    expected_statuses = {
        "sent": "Sent",
        "delivered": "Delivered",
        "read": "Opened",  # Map "read" to "Opened" for response
        "replied": "Replied",
        "failed": "Failed"
    }
    for status, name in expected_statuses.items():
        if status == "read":
            # Map "read" status to "Opened" in response
            read_count = next((stat.value for stat in message_stats if stat.status == "read"), 0)
            if not any(stat.status == "opened" for stat in message_stats):
                message_stats.append(MessageStat(name="Opened", value=read_count, status="opened"))
        elif not any(stat.status == status for stat in message_stats):
            message_stats.append(MessageStat(name=name, value=0, status=status))

    # Engagement data for a sample of leads
    engagement_data = []
    sample_leads = lead_parser_db.query(Lead).filter(Lead.user_id == user_id).limit(5).all()  # Sample up to 5 leads
    for lead in sample_leads:
        messages_sent = db.query(OutreachMessage).filter(
            OutreachMessage.lead_id == lead.id,
            OutreachMessage.user_id == user_id,
            OutreachMessage.status != MessageStatus.FAILED
        ).count()
        
        responses = db.query(OutreachMessage).filter(
            OutreachMessage.lead_id == lead.id,
            OutreachMessage.user_id == user_id,
            OutreachMessage.status == MessageStatus.REPLIED
        ).count()
        
        # Calculate engagement score (example: based on messages sent and responses)
        engagement_score = min(100, (messages_sent * 10 + responses * 20))
        
        engagement_data.append(EngagementData(
            lead_id=lead.id,
            engagement_score=engagement_score,
            messages_sent=messages_sent,
            responses=responses
        ))

    # Construct response
    response = OverallStatisticsResponse(
        statistics={
            "total_messages": total_messages,
            "total_campaigns": total_campaigns,
            "active_interactions": active_interactions,
            "leads_with_events_percentage": round(leads_with_events_percentage, 1),
            "response_rate": round(response_rate, 1),
            "conversion_rate": round(conversion_rate, 1)
        },
        messageStats=message_stats,
        engagementData=engagement_data
    )

    return response