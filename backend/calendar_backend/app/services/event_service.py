from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, desc, asc, text
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta, timezone
import logging
import json

from calendar_backend.app.models.calendar_models import Event, EventAttendee, EventReminder, LeadEventMapping
from calendar_backend.app.models.lead_parser_models import Lead
from calendar_backend.app.models.schemas import (
    EventCreateSchema, EventStatsSchema, EventUpdateSchema, EventResponseSchema,
    EventFilterSchema, PaginatedEventsSchema, PaginationSchema
)
from calendar_backend.app.database.connection import get_calendar_db, get_lead_parser_db

logger = logging.getLogger(__name__)

class EventService:
    def __init__(self, calendar_db: Session, lead_parser_db: Session = None, redis_client=None):
        self.calendar_db = calendar_db
        self.lead_parser_db = lead_parser_db
        self.redis_client = redis_client
    
    def create_event(self, event_data: EventCreateSchema) -> Event:
        try:
            event = Event(
                title=event_data.title,
                description=event_data.description,
                start_datetime=event_data.start_datetime,
                end_datetime=event_data.end_datetime,
                timezone=event_data.timezone,
                all_day=event_data.all_day,
                event_type=event_data.event_type,
                priority=event_data.priority,
                location=event_data.location,
                meeting_url=event_data.meeting_url,
                meeting_id=event_data.meeting_id,
                meeting_password=event_data.meeting_password,
                lead_id=event_data.lead_id,
                lead_name=event_data.lead_name,
                lead_email=event_data.lead_email,
                lead_phone=event_data.lead_phone,
                lead_company=event_data.lead_company,
                deal_value=event_data.deal_value,
                deal_stage=event_data.deal_stage,
                deal_probability=event_data.deal_probability,
                recurrence_type=event_data.recurrence_type,
                recurrence_interval=event_data.recurrence_interval,
                recurrence_end_date=event_data.recurrence_end_date,
                recurrence_count=event_data.recurrence_count,
                notes=event_data.notes,
                tags=event_data.tags,
                custom_fields=event_data.custom_fields,
                reminder_minutes=event_data.reminder_minutes,
                email_reminders=event_data.email_reminders,
                sms_reminders=event_data.sms_reminders,
                user_id=event_data.user_id
            )
            
            if event_data.lead_id and self.lead_parser_db and not event_data.lead_name:
                lead = self._get_lead_by_id(event_data.lead_id, event_data.user_id)
                if lead:
                    event.lead_name = lead.display_name
                    event.lead_email = lead.email
                    event.lead_phone = lead.phone or lead.mobile
                    event.lead_company = lead.company
            
            self.calendar_db.add(event)
            self.calendar_db.flush()
            
            if event_data.attendees:
                for attendee_data in event_data.attendees:
                    attendee = EventAttendee(
                        event_id=event.id,
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
                    self.calendar_db.add(attendee)
            
            if event_data.lead_id:
                mapping = LeadEventMapping(
                    lead_id=event_data.lead_id,
                    event_id=event.id,
                    relationship_type="primary",
                    user_id=event_data.user_id
                )
                self.calendar_db.add(mapping)
            
            if event_data.reminder_minutes:
                for minutes in event_data.reminder_minutes:
                    scheduled_for = event_data.start_datetime - timedelta(minutes=minutes)
                    if event_data.email_reminders and event.lead_email:
                        reminder = EventReminder(
                            event_id=event.id,
                            reminder_type="email",
                            minutes_before=minutes,
                            recipient_email=event.lead_email,
                            recipient_name=event.lead_name,
                            scheduled_for=scheduled_for,
                            user_id=event_data.user_id
                        )
                        self.calendar_db.add(reminder)
                    
                    if event_data.sms_reminders and event.lead_phone:
                        reminder = EventReminder(
                            event_id=event.id,
                            reminder_type="sms",
                            minutes_before=minutes,
                            recipient_phone=event.lead_phone,
                            recipient_name=event.lead_name,
                            scheduled_for=scheduled_for,
                            user_id=event_data.user_id
                        )
                        self.calendar_db.add(reminder)
            
            if event_data.recurrence_type.value != "none":
                self._create_recurring_events(event, event_data)
            
            self.calendar_db.commit()
            self.calendar_db.refresh(event)
            
            logger.info(f"Created event {event.id}: {event.title} for user {event_data.user_id}")
            return event
            
        except Exception as e:
            self.calendar_db.rollback()
            logger.error(f"Error creating event for user {event_data.user_id}: {e}")
            raise
    
    def get_event_by_id(self, event_id: int, user_id: str, include_attendees: bool = True, include_lead_info: bool = True) -> Optional[Event]:
        try:
            cache_key = f"event:{user_id}:{event_id}:{include_attendees}:{include_lead_info}"
            if self.redis_client:
                cached_result = self.redis_client.get(cache_key)
                if cached_result:
                    logger.info(f"Cache hit for event: {cache_key}")
                    return EventResponseSchema.parse_raw(cached_result)
            
            query = self.calendar_db.query(Event).filter(
                Event.id == event_id,
                Event.user_id == user_id
            )
            
            if include_attendees:
                query = query.options(joinedload(Event.attendees))
            
            event = query.first()
            
            if event and include_lead_info and event.lead_id and self.lead_parser_db:
                lead = self._get_lead_by_id(event.lead_id, user_id)
                if lead:
                    event.lead_info = lead
            
            if not event:
                logger.error(f"Event {event_id} not found or not accessible for user {user_id}")
            
            if event and self.redis_client:
                event_schema = EventResponseSchema.from_orm(event)
                self.redis_client.setex(cache_key, 300, event_schema.json())

            return event
            
        except Exception as e:
            logger.error(f"Error getting event {event_id} for user {user_id}: {e}")
            return None
    
    def get_events(self, filters: EventFilterSchema) -> Tuple[List[Event], int]:
        try:
            cache_key = f"events:{filters.user_id}:{filters.hash()}"
            if self.redis_client:
                cached_result = self.redis_client.get(cache_key)
                if cached_result:
                    logger.info(f"Cache hit for events: {cache_key}")
                    result = PaginatedEventsSchema.parse_raw(cached_result)
                    return result.events, result.pagination.total
            
            query = self.calendar_db.query(Event).filter(
                Event.user_id == filters.user_id
            )
            
            if filters.start_date:
                query = query.filter(Event.start_datetime >= filters.start_date)
            
            if filters.end_date:
                query = query.filter(Event.end_datetime <= filters.end_date)
            
            if filters.event_type:
                query = query.filter(Event.event_type == filters.event_type)
            
            if filters.status:
                query = query.filter(Event.status == filters.status)
            
            if filters.priority:
                query = query.filter(Event.priority == filters.priority)
            
            if filters.lead_id:
                query = query.filter(Event.lead_id == filters.lead_id)
            
            if filters.search:
                search_term = f"%{filters.search}%"
                query = query.filter(
                    or_(
                        Event.title.ilike(search_term),
                        Event.description.ilike(search_term),
                        Event.lead_name.ilike(search_term),
                        Event.lead_company.ilike(search_term),
                        Event.location.ilike(search_term),
                        Event.notes.ilike(search_term),
                        Event.tags.ilike(search_term)
                    )
                )
            
            total_count = query.count()
            
            order_column = getattr(Event, filters.order_by, Event.start_datetime)
            if filters.order_direction == "desc":
                query = query.order_by(desc(order_column))
            else:
                query = query.order_by(asc(order_column))
            
            offset = (filters.page - 1) * filters.per_page
            query = query.offset(offset).limit(filters.per_page)
            
            if filters.include_attendees:
                query = query.options(joinedload(Event.attendees))
            
            events = query.all()
            
            if filters.include_lead_info and self.lead_parser_db:
                for event in events:
                    if event.lead_id:
                        lead = self._get_lead_by_id(event.lead_id, filters.user_id)
                        if lead:
                            event.lead_info = lead
            
            if self.redis_client:
                event_schemas = [EventResponseSchema.from_orm(e) for e in events]
                result = PaginatedEventsSchema(
                    events=event_schemas,
                    pagination=PaginationSchema(
                        page=filters.page,
                        per_page=filters.per_page,
                        total=total_count,
                        total_pages=(total_count + filters.per_page - 1) // filters.per_page,
                        has_next=filters.page < (total_count + filters.per_page - 1) // filters.per_page,
                        has_prev=filters.page > 1
                    ),
                    user_id=filters.user_id
                )
                self.redis_client.setex(cache_key, 300, result.json())

            
            return events, total_count
            
        except Exception as e:
            logger.error(f"Error getting events for user {filters.user_id}: {e}")
            return [], 0
    
    def update_event(self, event_id: int, event_data: EventUpdateSchema) -> Optional[Event]:
        try:
            event = self.calendar_db.query(Event).filter(
                Event.id == event_id,
                Event.user_id == event_data.user_id
            ).first()
            if not event:
                logger.error(f"Event {event_id} not found or not accessible for user {event_data.user_id}")
                return None
            
            update_fields = event_data.dict(exclude_unset=True)
            for field, value in update_fields.items():
                if hasattr(event, field):
                    setattr(event, field, value)
            
            self.calendar_db.commit()
            self.calendar_db.refresh(event)
            
            if self.redis_client:
                self.redis_client.delete(f"event:{event_data.user_id}:{event_id}:*")
            
            logger.info(f"Updated event {event.id}: {event.title} for user {event_data.user_id}")
            return event
            
        except Exception as e:
            self.calendar_db.rollback()
            logger.error(f"Error updating event {event_id} for user {event_data.user_id}: {e}")
            raise
    
    def delete_event(self, event_id: int, user_id: str) -> bool:
        try:
            event = self.calendar_db.query(Event).filter(
                Event.id == event_id,
                Event.user_id == user_id
            ).first()
            if not event:
                logger.error(f"Event {event_id} not found or not accessible for user {user_id}")
                return False
            
            self.calendar_db.query(EventAttendee).filter(
                EventAttendee.event_id == event_id,
                EventAttendee.user_id == user_id
            ).delete()
            self.calendar_db.query(EventReminder).filter(
                EventReminder.event_id == event_id,
                EventReminder.user_id == user_id
            ).delete()
            self.calendar_db.query(LeadEventMapping).filter(
                LeadEventMapping.event_id == event_id,
                LeadEventMapping.user_id == user_id
            ).delete()
            
            self.calendar_db.delete(event)
            self.calendar_db.commit()
            
            if self.redis_client:
                self.redis_client.delete(f"event:{user_id}:{event_id}:*")
            
            logger.info(f"Deleted event {event_id} for user {user_id}")
            return True
            
        except Exception as e:
            self.calendar_db.rollback()
            logger.error(f"Error deleting event {event_id} for user {user_id}: {e}")
            return False
    
    def get_upcoming_events(self, limit: int = 10, user_id: str = None) -> List[Event]:
        try:
            cache_key = f"upcoming_events:{user_id}:{limit}"
            if self.redis_client:
                cached_result = self.redis_client.get(cache_key)
                if cached_result:
                    logger.info(f"Cache hit for upcoming events: {cache_key}")
                    return [EventResponseSchema.parse_raw(event) for event in json.loads(cached_result)]
            
            query = self.calendar_db.query(Event).filter(
                Event.start_datetime > datetime.utcnow(),
                Event.status.in_(["scheduled", "confirmed"])
            )
            
            if user_id:
                query = query.filter(Event.user_id == user_id)
            
            events = query.order_by(Event.start_datetime).limit(limit).all()
            
            if self.lead_parser_db:
                for event in events:
                    if event.lead_id:
                        lead = self._get_lead_by_id(event.lead_id, user_id)
                        if lead:
                            event.lead_info = lead
            
            if self.redis_client:
                event_schemas = [EventResponseSchema.model_validate(e) for e in events]
                self.redis_client.setex(cache_key, 3600, json.dumps([e.dict() for e in event_schemas]))
            
            return events
            
        except Exception as e:
            logger.error(f"Error getting upcoming events for user {user_id}: {e}")
            return []
    
    def get_event_statistics(self, start_date: datetime = None, end_date: datetime = None, user_id: str = None) -> Dict[str, Any]:
        try:
            cache_key = f"event_stats:{user_id}:{start_date.isoformat() if start_date else 'none'}:{end_date.isoformat() if end_date else 'none'}"
            if self.redis_client:
                cached_result = self.redis_client.get(cache_key)
                if cached_result:
                    logger.info(f"Cache hit for event stats: {cache_key}")
                    return EventStatsSchema.parse_raw(cached_result)
            
            query = self.calendar_db.query(Event)
            
            if start_date:
                query = query.filter(Event.start_datetime >= start_date)
            
            if end_date:
                query = query.filter(Event.end_datetime <= end_date)
            
            if user_id:
                query = query.filter(Event.user_id == user_id)
            
            total_events = query.count()
            upcoming_events = query.filter(Event.start_datetime > datetime.now(timezone.utc)).count()
            completed_events = query.filter(Event.status == "completed").count()
            cancelled_events = query.filter(Event.status == "cancelled").count()
            
            now = datetime.now(timezone.utc)
            week_start = now - timedelta(days=now.weekday())
            month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            events_this_week = query.filter(Event.start_datetime >= week_start).count()
            events_this_month = query.filter(Event.start_datetime >= month_start).count()
            
            events_by_type = {}
            type_results = self.calendar_db.query(Event.event_type, func.count(Event.id)).filter(
                Event.user_id == user_id
            ).group_by(Event.event_type).all()
            for event_type, count in type_results:
                events_by_type[event_type.value] = count
            
            events_by_status = {}
            status_results = self.calendar_db.query(Event.status, func.count(Event.id)).filter(
                Event.user_id == user_id
            ).group_by(Event.status).all()
            for status, count in status_results:
                events_by_status[status.value] = count
            
            events_by_priority = {}
            priority_results = self.calendar_db.query(Event.priority, func.count(Event.id)).filter(
                Event.user_id == user_id
            ).group_by(Event.priority).all()
            for priority, count in priority_results:
                events_by_priority[priority.value] = count
            
            duration_result = self.calendar_db.execute(
                text("SELECT AVG(TIMESTAMPDIFF(MINUTE, start_datetime, end_datetime)) "
                     "FROM events WHERE start_datetime IS NOT NULL AND end_datetime IS NOT NULL AND user_id = :user_id"),
                {"user_id": user_id}
            ).scalar()
            
            average_duration = float(duration_result) if duration_result is not None else 0.0
            
            total_deal_value = self.calendar_db.query(func.sum(Event.deal_value)).filter(
                Event.user_id == user_id
            ).scalar() or 0.0
            
            result = {
                "total_events": total_events,
                "upcoming_events": upcoming_events,
                "completed_events": completed_events,
                "cancelled_events": cancelled_events,
                "events_this_week": events_this_week,
                "events_this_month": events_this_month,
                "events_by_type": events_by_type,
                "events_by_status": events_by_status,
                "events_by_priority": events_by_priority,
                "average_event_duration": average_duration,
                "total_deal_value": total_deal_value
            }
            
            if self.redis_client:
                self.redis_client.setex(cache_key, 3600, json.dumps(result))
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting event statistics for user {user_id}: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Failed to fetch event statistics: {str(e)}")
        
    def check_conflicts(self, start_datetime: datetime, end_datetime: datetime, exclude_event_id: int = None, user_id: str = None) -> List[Event]:
        try:
            cache_key = f"event_conflicts:{user_id}:{start_datetime.isoformat()}:{end_datetime.isoformat()}:{exclude_event_id or 'none'}"
            if self.redis_client:
                cached_result = self.redis_client.get(cache_key)
                if cached_result:
                    logger.info(f"Cache hit for conflicts: {cache_key}")
                    return [EventResponseSchema.parse_raw(event) for event in json.loads(cached_result)]
            
            query = self.calendar_db.query(Event).filter(
                and_(
                    Event.start_datetime < end_datetime,
                    Event.end_datetime > start_datetime,
                    Event.status.in_(["scheduled", "confirmed", "in_progress"])
                )
            )
            
            if exclude_event_id:
                query = query.filter(Event.id != exclude_event_id)
            
            if user_id:
                query = query.filter(Event.user_id == user_id)
            
            conflicts = query.all()
            
            if self.redis_client:
                conflict_schemas = [EventResponseSchema.model_validate(e) for e in conflicts]
                self.redis_client.setex(cache_key, 300, json.dumps([e.dict() for e in conflict_schemas]))
            
            return conflicts
            
        except Exception as e:
            logger.error(f"Error checking conflicts for user {user_id}: {e}")
            return []
    
    def _get_lead_by_id(self, lead_id: int, user_id: str) -> Optional[Lead]:
        if not self.lead_parser_db:
            return None
        
        try:
            cache_key = f"lead:{user_id}:{lead_id}"
            if self.redis_client:
                cached_result = self.redis_client.get(cache_key)
                if cached_result:
                    logger.info(f"Cache hit for lead: {cache_key}")
                    return Lead.parse_raw(cached_result)
            
            lead = self.lead_parser_db.query(Lead).filter(
                Lead.id == lead_id,
                Lead.user_id == user_id
            ).first()
            
            if lead and self.redis_client:
                from calendar_backend.app.models.schemas import LeadResponseSchema  # Add at top
                lead_schema = LeadResponseSchema.from_orm(lead)
                self.redis_client.setex(cache_key, 3600, lead_schema.json())

            
            return lead
        except Exception as e:
            logger.error(f"Error getting lead {lead_id} for user {user_id}: {e}")
            return None
    
    def _create_recurring_events(self, parent_event: Event, event_data: EventCreateSchema):
        try:
            if event_data.recurrence_type.value == "none":
                return
            
            current_start = parent_event.start_datetime
            current_end = parent_event.end_datetime
            duration = current_end - current_start
            
            if event_data.recurrence_type.value == "daily":
                increment = timedelta(days=event_data.recurrence_interval)
            elif event_data.recurrence_type.value == "weekly":
                increment = timedelta(weeks=event_data.recurrence_interval)
            elif event_data.recurrence_type.value == "monthly":
                increment = timedelta(days=30 * event_data.recurrence_interval)
            elif event_data.recurrence_type.value == "yearly":
                increment = timedelta(days=365 * event_data.recurrence_interval)
            else:
                return
            
            instances_created = 0
            max_instances = event_data.recurrence_count or 50
            
            while instances_created < max_instances:
                current_start += increment
                current_end = current_start + duration
                
                if event_data.recurrence_end_date and current_start > event_data.recurrence_end_date:
                    break
                
                recurring_event = Event(
                    title=parent_event.title,
                    description=parent_event.description,
                    start_datetime=current_start,
                    end_datetime=current_end,
                    timezone=parent_event.timezone,
                    all_day=parent_event.all_day,
                    event_type=parent_event.event_type,
                    priority=parent_event.priority,
                    location=parent_event.location,
                    meeting_url=parent_event.meeting_url,
                    meeting_id=parent_event.meeting_id,
                    meeting_password=parent_event.meeting_password,
                    lead_id=parent_event.lead_id,
                    lead_name=parent_event.lead_name,
                    lead_email=parent_event.lead_email,
                    lead_phone=parent_event.lead_phone,
                    lead_company=parent_event.lead_company,
                    deal_value=parent_event.deal_value,
                    deal_stage=parent_event.deal_stage,
                    deal_probability=parent_event.deal_probability,
                    recurrence_type="none",
                    parent_event_id=parent_event.id,
                    notes=parent_event.notes,
                    tags=parent_event.tags,
                    custom_fields=parent_event.custom_fields,
                    reminder_minutes=parent_event.reminder_minutes,
                    email_reminders=parent_event.email_reminders,
                    sms_reminders=parent_event.sms_reminders,
                    user_id=parent_event.user_id
                )
                
                self.calendar_db.add(recurring_event)
                instances_created += 1
            
            logger.info(f"Created {instances_created} recurring instances for event {parent_event.id} for user {parent_event.user_id}")
            
        except Exception as e:
            logger.error(f"Error creating recurring events for user {parent_event.user_id}: {e}")
            raise