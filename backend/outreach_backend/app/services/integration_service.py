from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime, timedelta
import redis
import json
from config.settings import settings

from outreach_backend.app.models import Lead, Event, OutreachMessage, Conversation
from outreach_backend.app.services.conversation_service import conversation_service
from outreach_backend.app.services.message_service import message_service

redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)

class IntegrationService:
    def __init__(self):
        pass
    
    def sync_lead_contact_status(
        self, 
        lead_id: int, 
        platform_name: str,
        outreach_db: Session,
        lead_parser_db: Session
    ) -> bool:
        """Sync contact status back to lead parser database"""
        cache_key = f"lead_contact_status:{lead_id}"
        try:
            # Update contact status
            lead = lead_parser_db.query(Lead).filter(Lead.id == lead_id).first()
            if not lead:
                return False
            
            if platform_name == "Email":
                lead.contacted_via_email = True
            elif platform_name == "Facebook":
                lead.contacted_via_facebook = True
            elif platform_name == "Instagram":
                lead.contacted_via_instagram = True
            elif platform_name == "LinkedIn":
                lead.contacted_via_linkedin = True
            elif platform_name in ["WhatsApp", "SMS"]:
                lead.contacted_via_phone = True
            
            lead.last_contact_date = datetime.utcnow()
            
            lead_parser_db.commit()
            
            # Invalidate cache
            redis_client.delete(cache_key)
            return True
            
        except Exception as e:
            print(f"Error syncing lead contact status: {e}")
            return False
    
    def create_follow_up_event(
        self,
        lead_id: int,
        outreach_message_id: int,
        follow_up_days: int = 3,
        calendar_db: Session = None,
        lead_parser_db: Session = None,
        outreach_db: Session = None
    ) -> Optional[Event]:
        """Create a follow-up event in the calendar system"""
        try:
            # Get lead and message
            lead = lead_parser_db.query(Lead).filter(Lead.id == lead_id).first()
            if not lead:
                return None
            
            message = outreach_db.query(OutreachMessage).filter(
                OutreachMessage.id == outreach_message_id
            ).first()
            if not message:
                return None
            
            # Calculate follow-up date
            follow_up_date = datetime.utcnow() + timedelta(days=follow_up_days)
            
            # Create event
            event = Event(
                title=f"Follow up with {lead.full_name or lead.first_name} {lead.last_name or ''}".strip(),
                description=f"Follow up on outreach message sent via {message.platform.name}\n\nOriginal message: {message.message_content[:200]}...",
                start_datetime=follow_up_date,
                end_datetime=follow_up_date + timedelta(hours=1),
                all_day=False,
                event_type="follow_up",
                status="scheduled",
                priority="medium",
                lead_id=lead.id,
                lead_name=lead.full_name,
                lead_email=lead.email,
                lead_phone=lead.phone or lead.mobile,
                lead_company=lead.company,
                notes=f"Follow up on outreach message ID: {outreach_message_id}",
                reminder_minutes=60,
                email_reminders=True
            )
            
            calendar_db.add(event)
            calendar_db.commit()
            calendar_db.refresh(event)
            
            # Invalidate cache
            redis_client.delete(f"leads_with_upcoming_events:{lead_id}")
            
            return event
            
        except Exception as e:
            print(f"Error creating follow-up event: {e}")
            return None
    
    def get_leads_with_upcoming_events(
        self,
        days_ahead: int = 7,
        calendar_db: Session = None,
        lead_parser_db: Session = None
    ) -> List[Dict[str, Any]]:
        """Get leads that have upcoming events"""
        cache_key = f"leads_with_upcoming_events:{days_ahead}"
        cached_data = redis_client.get(cache_key)
        
        if cached_data:
            return json.loads(cached_data)
            
        try:
            upcoming_date = datetime.utcnow() + timedelta(days=days_ahead)
            events = calendar_db.query(Event).filter(
                and_(
                    Event.start_datetime >= datetime.utcnow(),
                    Event.start_datetime <= upcoming_date,
                    Event.lead_id.isnot(None)
                )
            ).all()
            
            lead_ids = [event.lead_id for event in events if event.lead_id]
            leads = lead_parser_db.query(Lead).filter(Lead.id.in_(lead_ids)).all()
            
            lead_dict = {lead.id: lead for lead in leads}
            results = []
            
            for event in events:
                if event.lead_id in lead_dict:
                    results.append({
                        "lead": lead_dict[event.lead_id].__dict__,
                        "event": event.__dict__,
                        "days_until_event": (event.start_datetime - datetime.utcnow()).days
                    })
            
            # Cache results
            redis_client.setex(
                cache_key,
                settings.REDIS_CACHE_TTL,
                json.dumps(results, default=str)
            )
            
            return results
            
        except Exception as e:
            print(f"Error getting leads with upcoming events: {e}")
            return []
    
    def get_leads_for_outreach_based_on_events(
        self,
        event_types: List[str] = None,
        days_before_event: int = 1,
        calendar_db: Session = None,
        lead_parser_db: Session = None,
        outreach_db: Session = None
    ) -> List[Dict[str, Any]]:
        """Get leads that should be contacted based on upcoming events"""
        cache_key = f"leads_for_outreach:{':'.join(event_types or [])}:{days_before_event}"
        cached_data = redis_client.get(cache_key)
        
        if cached_data:
            return json.loads(cached_data)
            
        try:
            if not event_types:
                event_types = ["meeting", "call", "demo", "presentation"]
            
            start_date = datetime.utcnow() + timedelta(days=days_before_event)
            end_date = start_date + timedelta(days=1)
            
            events = calendar_db.query(Event).filter(
                and_(
                    Event.start_datetime >= start_date,
                    Event.start_datetime <= end_date,
                    Event.event_type.in_(event_types),
                    Event.lead_id.isnot(None)
                )
            ).all()
            
            lead_ids = [event.lead_id for event in events if event.lead_id]
            leads = lead_parser_db.query(Lead).filter(Lead.id.in_(lead_ids)).all()
            
            lead_dict = {lead.id: lead for lead in leads}
            results = []
            
            for event in events:
                if event.lead_id in lead_dict:
                    lead = lead_dict[event.lead_id]
                    recent_messages = outreach_db.query(OutreachMessage).filter(
                        and_(
                            OutreachMessage.lead_id == lead.id,
                            OutreachMessage.sent_at >= datetime.utcnow() - timedelta(days=7)
                        )
                    ).count()
                    
                    results.append({
                        "lead": lead.__dict__,
                        "event": event.__dict__,
                        "recent_contact_count": recent_messages,
                        "should_contact": recent_messages == 0,
                        "suggested_message": f"Hi {lead.first_name}, just wanted to confirm our {event.event_type} scheduled for {event.start_datetime.strftime('%B %d at %I:%M %p')}. Looking forward to speaking with you!"
                    })
            
            # Cache results
            redis_client.setex(
                cache_key,
                settings.REDIS_CACHE_TTL,
                json.dumps(results, default=str)
            )
            
            return results
            
        except Exception as e:
            print(f"Error getting leads for outreach based on events: {e}")
            return []
    
    def sync_conversation_to_calendar(
        self,
        conversation_id: int,
        create_follow_up: bool = True,
        outreach_db: Session = None,
        calendar_db: Session = None,
        lead_parser_db: Session = None
    ) -> Optional[Event]:
        """Create calendar events based on conversation activity"""
        try:
            conversation = outreach_db.query(Conversation).filter(
                Conversation.id == conversation_id
            ).first()
            if not conversation:
                return None
            
            lead = lead_parser_db.query(Lead).filter(Lead.id == conversation.lead_id).first()
            if not lead:
                return None
            
            summary = conversation_service.get_conversation_summary(conversation_id, outreach_db)
            
            if create_follow_up and summary["incoming_messages"] > 0:
                follow_up_date = datetime.utcnow() + timedelta(days=2)
                
                event = Event(
                    title=f"Follow up conversation with {lead.full_name or lead.first_name} {lead.last_name or ''}".strip(),
                    description=f"Continue conversation on {conversation.platform.name}\n\nConversation summary:\n- Total messages: {summary['total_messages']}\n- Lead responses: {summary['incoming_messages']}\n- Response rate: {summary['response_rate']:.1f}%",
                    start_datetime=follow_up_date,
                    end_datetime=follow_up_date + timedelta(hours=1),
                    all_day=False,
                    event_type="follow_up",
                    status="scheduled",
                    priority="high" if summary["response_rate"] > 50 else "medium",
                    lead_id=lead.id,
                    lead_name=lead.full_name,
                    lead_email=lead.email,
                    lead_phone=lead.phone or lead.mobile,
                    lead_company=lead.company,
                    notes=f"Follow up on active conversation (ID: {conversation_id})",
                    reminder_minutes=30,
                    email_reminders=True
                )
                
                calendar_db.add(event)
                calendar_db.commit()
                calendar_db.refresh(event)
                
                # Invalidate cache
                redis_client.delete(f"leads_with_upcoming_events:{lead.id}")
                
                return event
            
            return None
            
        except Exception as e:
            print(f"Error syncing conversation to calendar: {e}")
            return None
    
    def get_lead_engagement_score(
        self,
        lead_id: int,
        outreach_db: Session = None,
        calendar_db: Session = None
    ) -> Dict[str, Any]:
        """Calculate engagement score for a lead based on outreach and calendar data"""
        cache_key = f"lead_engagement:{lead_id}"
        cached_data = redis_client.get(cache_key)
        
        if cached_data:
            return json.loads(cached_data)
            
        try:
            score = 0
            factors = []
            
            total_messages = outreach_db.query(OutreachMessage).filter(
                OutreachMessage.lead_id == lead_id
            ).count()
            
            conversations = outreach_db.query(Conversation).filter(
                Conversation.lead_id == lead_id
            ).all()
            
            total_conversations = len(conversations)
            active_conversations = len([c for c in conversations if c.status == "open"])
            
            events = calendar_db.query(Event).filter(Event.lead_id == lead_id).all()
            completed_events = len([e for e in events if e.status == "completed"])
            upcoming_events = len([e for e in events if e.start_datetime > datetime.utcnow()])
            
            if total_messages > 0:
                score += 10
                factors.append("Has been contacted")
            
            if total_conversations > 0:
                score += 20
                factors.append("Has active conversations")
            
            if active_conversations > 0:
                score += 30
                factors.append("Has ongoing conversations")
            
            if completed_events > 0:
                score += 25
                factors.append("Has attended meetings")
            
            if upcoming_events > 0:
                score += 15
                factors.append("Has scheduled meetings")
            
            for conversation in conversations:
                summary = conversation_service.get_conversation_summary(conversation.id, outreach_db)
                if summary["response_rate"] > 0:
                    score += min(summary["response_rate"] / 2, 25)
                    factors.append(f"Response rate: {summary['response_rate']:.1f}%")
            
            if score >= 80:
                level = "high"
            elif score >= 50:
                level = "medium"
            elif score >= 20:
                level = "low"
            else:
                level = "none"
            
            result = {
                "lead_id": lead_id,
                "engagement_score": min(score, 100),
                "engagement_level": level,
                "factors": factors,
                "metrics": {
                    "total_messages": total_messages,
                    "total_conversations": total_conversations,
                    "active_conversations": active_conversations,
                    "completed_events": completed_events,
                    "upcoming_events": upcoming_events
                }
            }
            
            # Cache result
            redis_client.setex(
                cache_key,
                settings.REDIS_CACHE_TTL,
                json.dumps(result)
            )
            
            return result
            
        except Exception as e:
            print(f"Error calculating engagement score: {e}")
            return {
                "lead_id": lead_id,
                "engagement_score": 0,
                "engagement_level": "none",
                "factors": [],
                "metrics": {}
            }
    
    def bulk_sync_lead_data(
        self,
        lead_ids: List[int] = None,
        outreach_db: Session = None,
        lead_parser_db: Session = None,
        calendar_db: Session = None
    ) -> Dict[str, Any]:
        """Bulk sync data between outreach system and other modules"""
        cache_key = f"bulk_sync_leads:{':'.join(map(str, lead_ids or []))}"
        cached_data = redis_client.get(cache_key)
        
        if cached_data:
            return json.loads(cached_data)
            
        try:
            results = {
                "synced_leads": 0,
                "created_events": 0,
                "updated_contact_status": 0,
                "errors": []
            }
            
            if lead_ids:
                leads = lead_parser_db.query(Lead).filter(Lead.id.in_(lead_ids)).all()
            else:
                recent_messages = outreach_db.query(OutreachMessage.lead_id).filter(
                    OutreachMessage.sent_at >= datetime.utcnow() - timedelta(days=30)
                ).distinct().all()
                
                lead_ids = [msg[0] for msg in recent_messages]
                leads = lead_parser_db.query(Lead).filter(Lead.id.in_(lead_ids)).all()
            
            for lead in leads:
                try:
                    messages = outreach_db.query(OutreachMessage).filter(
                        OutreachMessage.lead_id == lead.id
                    ).all()
                    
                    for message in messages:
                        platform_name = message.platform.name if message.platform else "Unknown"
                        if self.sync_lead_contact_status(lead.id, platform_name, outreach_db, lead_parser_db):
                            results["updated_contact_status"] += 1
                    
                    conversations = outreach_db.query(Conversation).filter(
                        and_(
                            Conversation.lead_id == lead.id,
                            Conversation.status == "open"
                        )
                    ).all()
                    
                    for conversation in conversations:
                        event = self.sync_conversation_to_calendar(
                            conversation.id, True, outreach_db, calendar_db, lead_parser_db
                        )
                        if event:
                            results["created_events"] += 1
                    
                    results["synced_leads"] += 1
                    
                except Exception as e:
                    results["errors"].append(f"Lead {lead.id}: {str(e)}")
            
            # Cache results
            redis_client.setex(
                cache_key,
                settings.REDIS_CACHE_TTL,
                json.dumps(results)
            )
            
            return results
            
        except Exception as e:
            return {
                "synced_leads": 0,
                "created_events": 0,
                "updated_contact_status": 0,
                "errors": [f"Bulk sync error: {str(e)}"]
            }

integration_service = IntegrationService()