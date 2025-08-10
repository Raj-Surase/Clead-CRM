"""
Calendar Models - Main calendar system database schema
These models represent the calendar backend database tables
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, JSON, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum as PyEnum
from calendar_backend.app.database.connection import CalendarBase

# Enums for better type safety and validation
class EventType(PyEnum):
    MEETING = "meeting"
    CALL = "call"
    APPOINTMENT = "appointment"
    DEMO = "demo"
    PRESENTATION = "presentation"
    CONSULTATION = "consultation"
    NEGOTIATION = "negotiation"
    CLOSING = "closing"
    FOLLOW_UP = "follow_up"
    INITIAL_CALL = "initial_call"
    DISCOVERY = "discovery"
    PROPOSAL = "proposal"
    CONTRACT_REVIEW = "contract_review"
    ONBOARDING = "onboarding"
    CHECK_IN = "check_in"
    TRAINING = "training"
    SUPPORT = "support"
    OTHER = "other"

class EventStatus(PyEnum):
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    RESCHEDULED = "rescheduled"
    NO_SHOW = "no_show"
    POSTPONED = "postponed"

class EventPriority(PyEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class AttendeeStatus(PyEnum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    TENTATIVE = "tentative"
    NO_RESPONSE = "no_response"

class RecurrenceType(PyEnum):
    NONE = "none"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"
    CUSTOM = "custom"

class ReminderType(PyEnum):
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    POPUP = "popup"

class Event(CalendarBase):
    """
    Main events table for calendar system
    """
    __tablename__ = "events"
    
    # Primary fields
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Date and time fields
    start_datetime = Column(DateTime, nullable=False, index=True)
    end_datetime = Column(DateTime, nullable=False, index=True)
    timezone = Column(String(50), default="UTC", nullable=False)
    all_day = Column(Boolean, default=False, nullable=False)
    
    # Event classification
    event_type = Column(Enum(EventType), default=EventType.MEETING, nullable=False, index=True)
    status = Column(Enum(EventStatus), default=EventStatus.SCHEDULED, nullable=False, index=True)
    priority = Column(Enum(EventPriority), default=EventPriority.MEDIUM, nullable=False, index=True)
    
    # Location and meeting details
    location = Column(String(500), nullable=True)
    meeting_url = Column(String(1000), nullable=True)
    meeting_id = Column(String(100), nullable=True)
    meeting_password = Column(String(100), nullable=True)
    
    # Lead integration fields
    lead_id = Column(Integer, nullable=True, index=True)  # Foreign key to leads table
    lead_name = Column(String(200), nullable=True)
    lead_email = Column(String(255), nullable=True)
    lead_phone = Column(String(50), nullable=True)
    lead_company = Column(String(200), nullable=True)
    
    # Deal/opportunity tracking
    deal_value = Column(Float, nullable=True)
    deal_stage = Column(String(50), nullable=True)
    deal_probability = Column(Float, nullable=True)  # 0-100
    
    # Recurrence fields
    recurrence_type = Column(Enum(RecurrenceType), default=RecurrenceType.NONE, nullable=False)
    recurrence_interval = Column(Integer, default=1, nullable=False)  # Every N days/weeks/months
    recurrence_end_date = Column(DateTime, nullable=True)
    recurrence_count = Column(Integer, nullable=True)  # Max occurrences
    parent_event_id = Column(Integer, ForeignKey('events.id'), nullable=True)  # For recurring events
    
    # Additional metadata
    notes = Column(Text, nullable=True)
    tags = Column(String(500), nullable=True)  # Comma-separated tags
    custom_fields = Column(JSON, nullable=True)  # Flexible additional data
    
    # Reminder settings
    reminder_minutes = Column(JSON, nullable=True)  # Array of minutes before event
    email_reminders = Column(Boolean, default=True, nullable=False)
    sms_reminders = Column(Boolean, default=False, nullable=False)
    
    # Audit fields
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    user_id = Column(Integer, nullable=True, index=True)  # Added to match database schema
    
    # Relationships
    attendees = relationship("EventAttendee", back_populates="event", cascade="all, delete-orphan")
    reminders = relationship("EventReminder", back_populates="event", cascade="all, delete-orphan")
    child_events = relationship("Event", backref="parent_event", remote_side=[id])
    
    def __repr__(self):
        return f"<Event(id={self.id}, title='{self.title}', start='{self.start_datetime}', type='{self.event_type}')>"
    
    @property
    def duration_minutes(self):
        """Calculate event duration in minutes"""
        if self.start_datetime and self.end_datetime:
            delta = self.end_datetime - self.start_datetime
            return int(delta.total_seconds() / 60)
        return 0
    
    @property
    def is_recurring(self):
        """Check if event is recurring"""
        return self.recurrence_type != RecurrenceType.NONE
    
    @property
    def is_past(self):
        """Check if event is in the past"""
        if self.end_datetime:
            # Make end_datetime offset-aware (assume UTC)
            end_datetime_aware = self.end_datetime.replace(tzinfo=timezone.utc)
            return end_datetime_aware < datetime.now(timezone.utc)
        return False

    @property
    def is_upcoming(self):
        """Check if event is upcoming"""
        if self.start_datetime:
            # Make start_datetime offset-aware (assume UTC)
            start_datetime_aware = self.start_datetime.replace(tzinfo=timezone.utc)
            return start_datetime_aware > datetime.now(timezone.utc)
        return False

    @property
    def is_active(self):
        """Check if event is currently active"""
        if self.start_datetime and self.end_datetime:
            # Make datetimes offset-aware (assume UTC)
            start_datetime_aware = self.start_datetime.replace(tzinfo=timezone.utc)
            end_datetime_aware = self.end_datetime.replace(tzinfo=timezone.utc)
            now = datetime.now(timezone.utc)
            return start_datetime_aware <= now <= end_datetime_aware
        return False

class EventAttendee(CalendarBase):
    """
    Event attendees table
    """
    __tablename__ = "event_attendees"
    
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey('events.id'), nullable=False, index=True)
    
    # Attendee information
    name = Column(String(200), nullable=False)
    email = Column(String(255), nullable=True, index=True)
    phone = Column(String(50), nullable=True)
    company = Column(String(200), nullable=True)
    job_title = Column(String(150), nullable=True)
    
    # Lead integration
    lead_id = Column(Integer, nullable=True, index=True)  # Reference to lead parser leads table
    
    # Attendee status
    status = Column(Enum(AttendeeStatus), default=AttendeeStatus.PENDING, nullable=False)
    is_organizer = Column(Boolean, default=False, nullable=False)
    is_required = Column(Boolean, default=True, nullable=False)
    
    # Response tracking
    response_datetime = Column(DateTime, nullable=True)
    response_notes = Column(Text, nullable=True)
    
    # Audit fields
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    user_id = Column(Integer, nullable=True, index=True)  # Added to match database schema
    
    # Relationships
    event = relationship("Event", back_populates="attendees")
    
    def __repr__(self):
        return f"<EventAttendee(id={self.id}, event_id={self.event_id}, name='{self.name}', status='{self.status}')>"

class EventReminder(CalendarBase):
    """
    Event reminders table
    """
    __tablename__ = "event_reminders"
    
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey('events.id'), nullable=False, index=True)
    
    # Reminder configuration
    reminder_type = Column(Enum(ReminderType), nullable=False)
    minutes_before = Column(Integer, nullable=False)  # Minutes before event
    
    # Reminder status
    is_sent = Column(Boolean, default=False, nullable=False)
    sent_at = Column(DateTime, nullable=True)
    scheduled_for = Column(DateTime, nullable=True)  # Added to match database schema
    
    # Target information
    recipient_email = Column(String(255), nullable=True)
    recipient_phone = Column(String(50), nullable=True)
    recipient_name = Column(String(200), nullable=True)  # Added to match database schema
    
    # Audit fields
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    user_id = Column(Integer, nullable=True, index=True)  # Added to match database schema
    
    # Relationships
    event = relationship("Event", back_populates="reminders")
    
    def __repr__(self):
        return f"<EventReminder(id={self.id}, event_id={self.event_id}, type='{self.reminder_type}', minutes={self.minutes_before})>"

class EventTemplate(CalendarBase):
    """
    Event templates for quick event creation
    """
    __tablename__ = "event_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Template configuration
    event_type = Column(Enum(EventType), nullable=False)
    duration_minutes = Column(Integer, default=60, nullable=False)
    priority = Column(Enum(EventPriority), default=EventPriority.MEDIUM, nullable=False)
    
    # Default settings
    default_location = Column(String(500), nullable=True)
    default_meeting_url = Column(String(1000), nullable=True)
    default_notes = Column(Text, nullable=True)
    default_tags = Column(String(500), nullable=True)
    
    # Reminder settings
    default_reminder_minutes = Column(JSON, nullable=True)
    default_email_reminders = Column(Boolean, default=True, nullable=False)
    default_sms_reminders = Column(Boolean, default=False, nullable=False)
    
    # Usage tracking
    usage_count = Column(Integer, default=0, nullable=False)
    last_used_at = Column(DateTime, nullable=True)
    
    # Audit fields
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    created_by = Column(String(100), nullable=True)
    
    def __repr__(self):
        return f"<EventTemplate(id={self.id}, name='{self.name}', type='{self.event_type}')>"

class Calendar(CalendarBase):
    """
    Calendar groups for organizing events
    """
    __tablename__ = "calendars"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    color = Column(String(7), default="#3498db", nullable=False)  # Hex color code
    
    # Calendar settings
    is_default = Column(Boolean, default=False, nullable=False)
    is_public = Column(Boolean, default=False, nullable=False)
    timezone = Column(String(50), default="UTC", nullable=False)
    
    # Working hours configuration
    working_hours_start = Column(String(5), default="09:00", nullable=False)  # HH:MM format
    working_hours_end = Column(String(5), default="17:00", nullable=False)    # HH:MM format
    working_days = Column(JSON, default=lambda: [1, 2, 3, 4, 5], nullable=False)  # 1=Monday, 7=Sunday
    
    # Audit fields
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    created_by = Column(String(100), nullable=True)
    
    def __repr__(self):
        return f"<Calendar(id={self.id}, name='{self.name}', color='{self.color}')>"

class EventCategory(CalendarBase):
    """
    Event categories for better organization
    """
    __tablename__ = "event_categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    color = Column(String(7), default="#95a5a6", nullable=False)  # Hex color code
    icon = Column(String(50), nullable=True)  # Icon class or name
    
    # Category settings
    is_active = Column(Boolean, default=True, nullable=False)
    sort_order = Column(Integer, default=0, nullable=False)
    
    # Usage tracking
    event_count = Column(Integer, default=0, nullable=False)
    
    # Audit fields
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    created_by = Column(String(100), nullable=True)
    
    def __repr__(self):
        return f"<EventCategory(id={self.id}, name='{self.name}', color='{self.color}')>"

class LeadEventMapping(CalendarBase):
    """
    Mapping table to track relationships between leads and events
    """
    __tablename__ = "lead_event_mappings"
    
    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, nullable=False, index=True)  # Reference to lead parser leads table
    event_id = Column(Integer, ForeignKey('events.id'), nullable=False, index=True)
    
    # Mapping metadata
    relationship_type = Column(String(50), default="primary", nullable=False)  # primary, secondary, related
    notes = Column(Text, nullable=True)
    
    # Audit fields
    created_at = Column(DateTime, default=func.now(), nullable=False)
    user_id = Column(Integer, nullable=True, index=True)  # Renamed from mapped_by to match database schema
    
    # Relationships
    event = relationship("Event")
    
    def __repr__(self):
        return f"<LeadEventMapping(id={self.id}, lead_id={self.lead_id}, event_id={self.event_id})>"