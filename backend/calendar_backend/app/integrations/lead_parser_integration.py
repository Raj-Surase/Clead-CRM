"""
Lead Parser Integration Service
Handles integration between lead parser and calendar systems
"""

from enum import Enum
from fastapi import HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any
import logging

from calendar_backend.app.models.lead_parser_models import Lead
from calendar_backend.app.models.calendar_models import Event
from calendar_backend.app.models.schemas import (
    LeadEventCreateSchema, LeadEventSummarySchema, EventCreateSchema, EventTypeEnum, EventPriorityEnum, AttendeeCreateSchema, EventResponseSchema
)
from calendar_backend.app.services.event_service import EventService
from config.settings import settings

logger = logging.getLogger(__name__)

class LeadParserIntegration:
    def __init__(self, calendar_db: Session, lead_parser_db: Session):
        self.calendar_db = calendar_db
        self.lead_parser_db = lead_parser_db
        self.api_url = settings.LEAD_DATABASE_URL
    
    def get_lead_by_id(self, lead_id: int, user_id: str) -> Optional[Lead]:
        try:
            lead = self.lead_parser_db.query(Lead).filter(
                Lead.id == lead_id,
                Lead.user_id == user_id
            ).first()
            if not lead:
                logger.error(f"Lead {lead_id} not found for user {user_id}")
            return lead
        except Exception as e:
            logger.error(f"Error getting lead {lead_id} for user {user_id}: {str(e)}", exc_info=True)
            return None
    
    def create_event_from_lead(self, lead_id: int, event_data: LeadEventCreateSchema) -> Optional[Event]:
        """
        Create a calendar event from a lead
        """
        try:
            logger.info(f"Creating event for lead {lead_id} with data: {event_data.dict()} for user {event_data.user_id}")

            lead = self.get_lead_by_id(lead_id, event_data.user_id)
            if not lead:
                raise HTTPException(status_code=404, detail=f"Lead {lead_id} not found for user {event_data.user_id}")
            
            end_datetime = event_data.start_datetime + timedelta(minutes=event_data.duration_minutes)
            
            title = event_data.title
            if not title:
                event_type_str = (
                    event_data.event_type.value.replace('_', ' ').title()
                    if isinstance(event_data.event_type, Enum)
                    else event_data.event_type.replace('_', ' ').title()
                )
                title = f"{event_type_str} - {lead.full_name or 'Lead'}"
                if lead.company:
                    title += f" ({lead.company})"
            
            attendees = []
            if lead.full_name or lead.email or lead.phone or lead.mobile:
                attendees.append(AttendeeCreateSchema(
                    name=lead.full_name or "Unknown",
                    email=lead.email,
                    phone=lead.phone or lead.mobile,
                    company=lead.company,
                    job_title=lead.job_title,
                    lead_id=lead.id,
                    is_organizer=False,
                    is_required=True,
                    user_id=event_data.user_id
                ))
            
            event_create_data = EventCreateSchema(
                title=title,
                description=event_data.description,
                start_datetime=event_data.start_datetime,
                end_datetime=end_datetime,
                event_type=event_data.event_type,
                priority=event_data.priority,
                location=event_data.location,
                meeting_url=event_data.meeting_url,
                lead_id=lead.id,
                lead_name=lead.full_name,
                lead_email=lead.email,
                lead_phone=lead.phone or lead.mobile,
                lead_company=lead.company,
                deal_value=event_data.deal_value,
                deal_stage=event_data.deal_stage,
                deal_probability=event_data.deal_probability,
                notes=event_data.notes,
                reminder_minutes=event_data.reminder_minutes,
                attendees=attendees,
                user_id=event_data.user_id
            )
            
            event_service = EventService(self.calendar_db, self.lead_parser_db)
            event = event_service.create_event(event_create_data)
            
            logger.info(f"Created event {event.id} from lead {lead_id} for user {event_data.user_id}")
            return event
            
        except HTTPException:
            raise
        except Exception as e:
            self.calendar_db.rollback()
            self.lead_parser_db.rollback()
            logger.error(f"Error creating event from lead {lead_id} for user {event_data.user_id}: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Failed to create event: {str(e)}")

    def get_lead_events(self, lead_id: int, user_id: str) -> List[EventResponseSchema]:
        try:
            logger.debug(f"Querying events for lead_id={lead_id} and user_id={user_id}")
            query = self.calendar_db.query(Event).filter(
                Event.lead_id == lead_id,
                Event.user_id == user_id
            ).order_by(Event.start_datetime)
            events = query.all()
            logger.debug(f"Found {len(events)} events for lead_id={lead_id} and user_id={user_id}")
            
            # Convert Event objects to EventResponseSchema
            event_schemas = [EventResponseSchema.from_orm(event) for event in events]
            return event_schemas
        except Exception as e:
            logger.error(f"Error getting events for lead {lead_id} and user {user_id}: {str(e)}", exc_info=True)
            raise

    def get_lead_event_summary(self, lead_id: int, user_id: str) -> LeadEventSummarySchema:
        try:
            logger.debug(f"Fetching event summary for lead {lead_id} and user {user_id}")
            events = self.get_lead_events(lead_id, user_id)
            
            if not events:
                logger.info(f"No events found for lead {lead_id} and user {user_id}")
                return LeadEventSummarySchema(
                    lead_id=lead_id,
                    total_events=0,
                    upcoming_events=0,
                    completed_events=0,
                    cancelled_events=0,
                    total_deal_value=0.0,
                    next_event=None,
                    last_event=None,
                    follow_up_suggestions=None,
                    user_id=user_id
                )
            
            now = datetime.now(timezone.utc)
            upcoming_events = [e for e in events if e.start_datetime > now]
            completed_events = [e for e in events if e.status == "completed"]
            cancelled_events = [e for e in events if e.status == "cancelled"]
            
            total_deal_value = sum(e.deal_value or 0 for e in events)
            
            next_event = next((e for e in events if e.start_datetime > now), None)
            last_event = next((e for e in reversed(events) if e.start_datetime <= now), None)
            
            summary = LeadEventSummarySchema(
                lead_id=lead_id,
                total_events=len(events),
                upcoming_events=len(upcoming_events),
                completed_events=len(completed_events),
                cancelled_events=len(cancelled_events),
                total_deal_value=total_deal_value,
                next_event=next_event,
                last_event=last_event,
                follow_up_suggestions=None,  # Simplified due to removed fields
                user_id=user_id
            )
            
            logger.info(f"Generated event summary for lead {lead_id} and user {user_id}: {summary.dict()}")
            return summary
            
        except Exception as e:
            logger.error(f"Error getting lead event summary for {lead_id} and user {user_id}: {str(e)}", exc_info=True)
            return LeadEventSummarySchema(
                lead_id=lead_id,
                total_events=0,
                upcoming_events=0,
                completed_events=0,
                cancelled_events=0,
                total_deal_value=0.0,
                next_event=None,
                last_event=None,
                follow_up_suggestions=None,
                user_id=user_id
            )

    def get_follow_up_suggestions(self, lead_id: int, user_id: str) -> List[Dict[str, Any]]:
        try:
            lead = self.get_lead_by_id(lead_id, user_id)
            if not lead:
                return []
            
            events = self.get_lead_events(lead_id, user_id)
            suggestions = []
            
            now = datetime.now(timezone.utc)
            last_event = next((e for e in reversed(events) if e.start_datetime <= now), None)
            
            if not events:
                suggestions.append({
                    "type": "initial_contact",
                    "title": "Initial Contact Call",
                    "event_type": EventTypeEnum.INITIAL_CALL,
                    "duration_minutes": 30,
                    "priority": EventPriorityEnum.MEDIUM,
                    "suggested_time": now + timedelta(days=1),
                    "reason": "No prior events for this lead",
                    "confidence_score": 0.8
                })
            
            if last_event:
                days_since_last = (now - last_event.start_datetime).days
                if days_since_last > 7:
                    suggestions.append({
                        "type": "follow_up",
                        "title": "Follow-up Call",
                        "event_type": EventTypeEnum.FOLLOW_UP,
                        "duration_minutes": 15,
                        "priority": EventPriorityEnum.MEDIUM,
                        "suggested_time": now + timedelta(days=1),
                        "reason": f"No contact for {days_since_last} days since last event",
                        "confidence_score": 0.6
                    })
            
            suggestions.sort(key=lambda x: x.get("confidence_score", 0), reverse=True)
            
            return suggestions[:3]
            
        except Exception as e:
            logger.error(f"Error generating follow-up suggestions for lead {lead_id} and user {user_id}: {str(e)}", exc_info=True)
            return []
    
    def sync_lead_updates(self, lead_id: int, user_id: str) -> Dict[str, Any]:
        try:
            lead = self.get_lead_by_id(lead_id, user_id)
            if not lead:
                return {"error": f"Lead not found for user {user_id}"}
            
            events = self.calendar_db.query(Event).filter(
                Event.lead_id == lead_id,
                Event.user_id == user_id
            ).all()
            
            updated_events = []
            for event in events:
                event.lead_name = lead.full_name
                event.lead_email = lead.email
                event.lead_phone = lead.phone or lead.mobile
                event.lead_company = lead.company
                
                for attendee in event.attendees:
                    if attendee.lead_id == lead_id:
                        attendee.name = lead.full_name or "Unknown"
                        attendee.email = lead.email
                        attendee.phone = lead.phone or lead.mobile
                        attendee.company = lead.company
                        attendee.job_title = lead.job_title
                
                updated_events.append({
                    "id": event.id,
                    "title": event.title
                })
            
            self.calendar_db.commit()
            
            logger.info(f"Synced {len(updated_events)} events for lead {lead_id} and user {user_id}")
            
            return {
                "lead_id": lead_id,
                "updated_events_count": len(updated_events),
                "updated_events": updated_events
            }
            
        except Exception as e:
            self.calendar_db.rollback()
            logger.error(f"Error syncing lead updates for {lead_id} and user {user_id}: {str(e)}", exc_info=True)
            return {"error": str(e)}
    
    def get_leads_with_upcoming_events(self, user_id: str, days_ahead: int = 7) -> List[Dict[str, Any]]:
        try:
            end_date = datetime.now(timezone.utc) + timedelta(days=days_ahead)
            
            events = self.calendar_db.query(Event).filter(
                Event.start_datetime <= end_date,
                Event.start_datetime > datetime.now(timezone.utc),
                Event.lead_id.isnot(None),
                Event.status.in_(["scheduled", "confirmed"]),
                Event.user_id == user_id
            ).all()
            
            leads_with_events = {}
            for event in events:
                if event.lead_id not in leads_with_events:
                    lead = self.get_lead_by_id(event.lead_id, user_id)
                    if lead:
                        leads_with_events[event.lead_id] = {
                            "lead": lead.to_dict(),
                            "events": []
                        }
                
                if event.lead_id in leads_with_events:
                    leads_with_events[event.lead_id]["events"].append({
                        "id": event.id,
                        "title": event.title,
                        "start_datetime": event.start_datetime,
                        "event_type": event.event_type,
                        "status": event.status
                    })
            
            return list(leads_with_events.values())
            
        except Exception as e:
            logger.error(f"Error getting leads with upcoming events for user {user_id}: {str(e)}", exc_info=True)
            return []
    
    def call_lead_parser_api(self, endpoint: str, method: str = "GET", data: Dict[str, Any] = None, user_id: str = None) -> Optional[Dict[str, Any]]:
        try:
            import requests
            url = f"{self.api_url.rstrip('/')}/{endpoint.lstrip('/')}"
            headers = {}
            
            if method.upper() == "GET":
                params = {"user_id": user_id} if user_id else {}
                response = requests.get(url, headers=headers, params=params, timeout=30)
            elif method.upper() == "POST":
                headers["Content-Type"] = "application/json"
                response = requests.post(url, headers=headers, json=data, timeout=30)
            elif method.upper() == "PUT":
                headers["Content-Type"] = "application/json"
                response = requests.put(url, headers=headers, json=data, timeout=30)
            elif method.upper() == "DELETE":
                params = {"user_id": user_id} if user_id else {}
                response = requests.delete(url, headers=headers, params=params, timeout=30)
            else:
                logger.error(f"Unsupported HTTP method: {method}")
                return None
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling lead parser API {endpoint} for user {user_id}: {str(e)}", exc_info=True)
            return None
        except Exception as e:
            logger.error(f"Unexpected error calling lead parser API {endpoint} for user {user_id}: {str(e)}", exc_info=True)
            return None
    
    def get_lead_from_api(self, lead_id: int, user_id: str) -> Optional[Dict[str, Any]]:
        return self.call_lead_parser_api(f"leads/{user_id}/{lead_id}", "GET", user_id=user_id)
    
    def update_lead_via_api(self, lead_id: int, update_data: Dict[str, Any], user_id: str) -> Optional[Dict[str, Any]]:
        update_data["user_id"] = user_id
        return self.call_lead_parser_api(f"leads/{lead_id}", "PUT", update_data, user_id)