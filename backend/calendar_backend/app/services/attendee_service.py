"""
Attendee Service - Manage event attendees and responses
"""

from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from calendar_backend.app.models.calendar_models import EventAttendee, Event
from calendar_backend.app.models.lead_parser_models import Lead
from calendar_backend.app.models.schemas import AttendeeCreateSchema, AttendeeUpdateSchema, AttendeeResponseSchema

logger = logging.getLogger(__name__)

class AttendeeService:
    """Service for managing event attendees"""
    
    def __init__(self, calendar_db: Session, lead_parser_db: Session = None):
        self.calendar_db = calendar_db
        self.lead_parser_db = lead_parser_db
    
    def add_attendee(self, event_id: int, attendee_data: AttendeeCreateSchema) -> Optional[EventAttendee]:
        """
        Add a new attendee to an event
        """
        try:
            # Check if event exists and belongs to user
            event = self.calendar_db.query(Event).filter(
                Event.id == event_id,
                Event.user_id == attendee_data.user_id
            ).first()
            if not event:
                logger.error(f"Event {event_id} not found or not accessible for user {attendee_data.user_id}")
                return None
            
            # Create attendee
            attendee = EventAttendee(
                event_id=event_id,
                name=attendee_data.name,
                email=attendee_data.email,
                phone=attendee_data.phone,
                company=attendee_data.company,
                job_title=attendee_data.job_title,
                lead_id=attendee_data.lead_id,
                is_organizer=attendee_data.is_organizer,
                is_required=attendee_data.is_required,
                response_notes=attendee_data.response_notes,
                user_id=attendee_data.user_id
            )
            
            # If lead_id is provided, fetch additional info from lead parser
            if attendee_data.lead_id and self.lead_parser_db:
                lead = self._get_lead_by_id(attendee_data.lead_id, attendee_data.user_id)
                if lead:
                    # Update attendee info with lead data if not provided
                    if not attendee.name:
                        attendee.name = lead.display_name
                    if not attendee.email:
                        attendee.email = lead.email
                    if not attendee.phone:
                        attendee.phone = lead.phone or lead.mobile
                    if not attendee.company:
                        attendee.company = lead.company
                    if not attendee.job_title:
                        attendee.job_title = lead.job_title
            
            self.calendar_db.add(attendee)
            self.calendar_db.commit()
            self.calendar_db.refresh(attendee)
            
            logger.info(f"Added attendee {attendee.id} to event {event_id} for user {attendee_data.user_id}")
            return attendee
            
        except Exception as e:
            self.calendar_db.rollback()
            logger.error(f"Error adding attendee to event {event_id}: {e}")
            return None
    
    def get_attendee_by_id(self, attendee_id: int, user_id: str) -> Optional[EventAttendee]:
        """
        Get an attendee by ID for a specific user
        """
        try:
            attendee = self.calendar_db.query(EventAttendee).join(Event).filter(
                EventAttendee.id == attendee_id,
                Event.user_id == user_id
            ).first()
            if not attendee:
                logger.error(f"Attendee {attendee_id} not found or not accessible for user {user_id}")
                return None
            return attendee
        except Exception as e:
            logger.error(f"Error getting attendee {attendee_id} for user {user_id}: {e}")
            return None
    
    def get_event_attendees(self, event_id: int, user_id: str, include_lead_info: bool = True) -> List[EventAttendee]:
        """
        Get all attendees for an event for a specific user
        """
        try:
            attendees = self.calendar_db.query(EventAttendee).join(Event).filter(
                EventAttendee.event_id == event_id,
                Event.user_id == user_id
            ).all()
            
            # Add lead information if requested
            if include_lead_info and self.lead_parser_db:
                for attendee in attendees:
                    if attendee.lead_id:
                        lead = self._get_lead_by_id(attendee.lead_id, user_id)
                        if lead:
                            attendee.lead_info = lead
            
            return attendees
            
        except Exception as e:
            logger.error(f"Error getting attendees for event {event_id} for user {user_id}: {e}")
            return []
    
    def update_attendee(self, attendee_id: int, attendee_data: AttendeeUpdateSchema) -> Optional[EventAttendee]:
        """
        Update an existing attendee
        """
        try:
            attendee = self.calendar_db.query(EventAttendee).join(Event).filter(
                EventAttendee.id == attendee_id,
                Event.user_id == attendee_data.user_id
            ).first()
            if not attendee:
                logger.error(f"Attendee {attendee_id} not found or not accessible for user {attendee_data.user_id}")
                return None
            
            # Update fields that are provided
            update_fields = attendee_data.dict(exclude_unset=True)
            for field, value in update_fields.items():
                if hasattr(attendee, field):
                    setattr(attendee, field, value)
            
            self.calendar_db.commit()
            self.calendar_db.refresh(attendee)
            
            logger.info(f"Updated attendee {attendee_id} for user {attendee_data.user_id}")
            return attendee
            
        except Exception as e:
            self.calendar_db.rollback()
            logger.error(f"Error updating attendee {attendee_id}: {e}")
            return None
    
    def remove_attendee(self, attendee_id: int, user_id: str) -> bool:
        """
        Remove an attendee from an event for a specific user
        """
        try:
            attendee = self.calendar_db.query(EventAttendee).join(Event).filter(
                EventAttendee.id == attendee_id,
                Event.user_id == user_id
            ).first()
            if not attendee:
                logger.error(f"Attendee {attendee_id} not found or not accessible for user {user_id}")
                return False
            
            self.calendar_db.delete(attendee)
            self.calendar_db.commit()
            
            logger.info(f"Removed attendee {attendee_id} for user {user_id}")
            return True
            
        except Exception as e:
            self.calendar_db.rollback()
            logger.error(f"Error removing attendee {attendee_id} for user {user_id}: {e}")
            return False
    
    def update_attendee_response(self, attendee_id: int, status: str, response_notes: str = None, user_id: str = None) -> Optional[EventAttendee]:
        """
        Update an attendee's response status for a specific user
        """
        try:
            attendee = self.calendar_db.query(EventAttendee).join(Event).filter(
                EventAttendee.id == attendee_id,
                Event.user_id == user_id
            ).first()
            if not attendee:
                logger.error(f"Attendee {attendee_id} not found or not accessible for user {user_id}")
                return None
            
            attendee.status = status
            attendee.response_datetime = datetime.utcnow()
            if response_notes:
                attendee.response_notes = response_notes
            
            self.calendar_db.commit()
            self.calendar_db.refresh(attendee)
            
            logger.info(f"Updated response for attendee {attendee_id} for user {user_id}: {status}")
            return attendee
            
        except Exception as e:
            self.calendar_db.rollback()
            logger.error(f"Error updating attendee response {attendee_id} for user {user_id}: {e}")
            return None
    
    def get_attendee_events(self, email: str = None, lead_id: int = None, user_id: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get events for a specific attendee by email or lead_id for a specific user
        """
        try:
            query = self.calendar_db.query(EventAttendee).join(Event).filter(
                Event.user_id == user_id
            )
            
            if email:
                query = query.filter(EventAttendee.email == email)
            elif lead_id:
                query = query.filter(EventAttendee.lead_id == lead_id)
            else:
                return []
            
            attendees = query.order_by(Event.start_datetime.desc()).limit(limit).all()
            
            events = []
            for attendee in attendees:
                event_data = {
                    "attendee_id": attendee.id,
                    "attendee_status": attendee.status.value,
                    "response_datetime": attendee.response_datetime,
                    "event": {
                        "id": attendee.event.id,
                        "title": attendee.event.title,
                        "start_datetime": attendee.event.start_datetime,
                        "end_datetime": attendee.event.end_datetime,
                        "event_type": attendee.event.event_type.value,
                        "status": attendee.event.status.value,
                        "location": attendee.event.location,
                        "meeting_url": attendee.event.meeting_url
                    }
                }
                events.append(event_data)
            
            return events
            
        except Exception as e:
            logger.error(f"Error getting attendee events for user {user_id}: {e}")
            return []
    
    def get_attendee_statistics(self, event_id: int = None, user_id: str = None) -> Dict[str, Any]:
        """
        Get attendee statistics for an event or overall for a specific user
        """
        try:
            query = self.calendar_db.query(EventAttendee).join(Event).filter(
                Event.user_id == user_id
            )
            
            if event_id:
                query = query.filter(EventAttendee.event_id == event_id)
            
            attendees = query.all()
            
            if not attendees:
                return {
                    "total_attendees": 0,
                    "responses_by_status": {},
                    "response_rate": 0.0,
                    "organizer_count": 0,
                    "required_attendees": 0
                }
            
            # Calculate statistics
            total_attendees = len(attendees)
            responses_by_status = {}
            organizer_count = 0
            required_attendees = 0
            responded_count = 0
            
            for attendee in attendees:
                status = attendee.status.value
                responses_by_status[status] = responses_by_status.get(status, 0) + 1
                
                if attendee.is_organizer:
                    organizer_count += 1
                
                if attendee.is_required:
                    required_attendees += 1
                
                if attendee.status.value != "pending":
                    responded_count += 1
            
            response_rate = (responded_count / total_attendees) * 100 if total_attendees > 0 else 0
            
            return {
                "total_attendees": total_attendees,
                "responses_by_status": responses_by_status,
                "response_rate": response_rate,
                "organizer_count": organizer_count,
                "required_attendees": required_attendees,
                "responded_count": responded_count
            }
            
        except Exception as e:
            logger.error(f"Error getting attendee statistics for user {user_id}: {e}")
            return {}
    
    def bulk_add_attendees(self, event_id: int, attendees_data: List[AttendeeCreateSchema]) -> List[EventAttendee]:
        """
        Add multiple attendees to an event at once
        """
        try:
            # Check if event exists and belongs to user
            event = self.calendar_db.query(Event).filter(
                Event.id == event_id,
                Event.user_id == attendees_data[0].user_id
            ).first()
            if not event:
                logger.error(f"Event {event_id} not found or not accessible for user {attendees_data[0].user_id}")
                return []
            
            created_attendees = []
            
            for attendee_data in attendees_data:
                if attendee_data.user_id != event.user_id:
                    logger.error(f"User ID mismatch for attendee in event {event_id}")
                    continue
                
                attendee = EventAttendee(
                    event_id=event_id,
                    name=attendee_data.name,
                    email=attendee_data.email,
                    phone=attendee_data.phone,
                    company=attendee_data.company,
                    job_title=attendee_data.job_title,
                    lead_id=attendee_data.lead_id,
                    is_organizer=attendee_data.is_organizer,
                    is_required=attendee_data.is_required,
                    response_notes=attendee_data.response_notes,
                    user_id=attendee_data.user_id
                )
                
                # Fetch lead info if available
                if attendee_data.lead_id and self.lead_parser_db:
                    lead = self._get_lead_by_id(attendee_data.lead_id, attendee_data.user_id)
                    if lead:
                        if not attendee.name:
                            attendee.name = lead.display_name
                        if not attendee.email:
                            attendee.email = lead.email
                        if not attendee.phone:
                            attendee.phone = lead.phone or lead.mobile
                        if not attendee.company:
                            attendee.company = lead.company
                        if not attendee.job_title:
                            attendee.job_title = lead.job_title
                
                self.calendar_db.add(attendee)
                created_attendees.append(attendee)
            
            self.calendar_db.commit()
            
            # Refresh all attendees
            for attendee in created_attendees:
                self.calendar_db.refresh(attendee)
            
            logger.info(f"Added {len(created_attendees)} attendees to event {event_id} for user {event.user_id}")
            return created_attendees
            
        except Exception as e:
            self.calendar_db.rollback()
            logger.error(f"Error bulk adding attendees to event {event_id}: {e}")
            return []
    
    def sync_attendee_with_lead(self, attendee_id: int, user_id: str) -> Optional[EventAttendee]:
        """
        Sync attendee information with lead data for a specific user
        """
        try:
            attendee = self.calendar_db.query(EventAttendee).join(Event).filter(
                EventAttendee.id == attendee_id,
                Event.user_id == user_id
            ).first()
            if not attendee or not attendee.lead_id or not self.lead_parser_db:
                logger.error(f"Attendee {attendee_id} not found, no lead_id, or lead_parser_db unavailable for user {user_id}")
                return attendee
            
            lead = self._get_lead_by_id(attendee.lead_id, user_id)
            if not lead:
                logger.error(f"Lead {attendee.lead_id} not found for user {user_id}")
                return attendee
            
            # Update attendee with latest lead information
            attendee.name = lead.display_name
            attendee.email = lead.email
            attendee.phone = lead.phone or lead.mobile
            attendee.company = lead.company
            attendee.job_title = lead.job_title
            
            self.calendar_db.commit()
            self.calendar_db.refresh(attendee)
            
            logger.info(f"Synced attendee {attendee_id} with lead {attendee.lead_id} for user {user_id}")
            return attendee
            
        except Exception as e:
            self.calendar_db.rollback()
            logger.error(f"Error syncing attendee {attendee_id} with lead for user {user_id}: {e}")
            return None
    
    def _get_lead_by_id(self, lead_id: int, user_id: str) -> Optional[Lead]:
        if not self.lead_parser_db:
            logger.warning("lead_parser_db is not available")
            return None
        try:
            return self.lead_parser_db.query(Lead).filter(
                Lead.id == lead_id,
                Lead.user_id == user_id
            ).first()
        except Exception as e:
            logger.error(f"Error getting lead {lead_id} for user {user_id}: {e}")
            return None