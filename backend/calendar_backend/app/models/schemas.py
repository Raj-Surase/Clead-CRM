"""
Pydantic Schemas for API Request/Response Validation
"""

from pydantic import BaseModel, validator, Field
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, date
from enum import Enum
import logging
import uuid

logger = logging.getLogger(__name__)  # Use standard logging module

# Enums for validation
class EventTypeEnum(str, Enum):
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

class EventStatusEnum(str, Enum):
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    RESCHEDULED = "rescheduled"
    NO_SHOW = "no_show"
    POSTPONED = "postponed"

class EventPriorityEnum(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class AttendeeStatusEnum(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    TENTATIVE = "tentative"
    NO_RESPONSE = "no_response"

class RecurrenceTypeEnum(str, Enum):
    NONE = "none"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"
    CUSTOM = "custom"

# Base schemas
class BaseSchema(BaseModel):
    class Config:
        from_attributes = True
        use_enum_values = True

# Lead Parser Integration Schemas
class LeadSummarySchema(BaseSchema):
    """Summary schema for lead information, aligned with Lead model"""
    id: int
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    full_name: Optional[str] = None
    company: Optional[str] = None
    job_title: Optional[str] = None
    industry: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    website: Optional[str] = None
    linkedin_url: Optional[str] = None
    facebook_url: Optional[str] = None
    instagram_url: Optional[str] = None
    twitter_url: Optional[str] = None
    youtube_url: Optional[str] = None
    tiktok_url: Optional[str] = None
    lead_score: Optional[float] = 0.0
    lead_status: Optional[str] = "new"
    lead_source: Optional[str] = None
    priority: Optional[str] = "medium"
    email_valid: Optional[bool] = False
    phone_valid: Optional[bool] = False
    social_profiles_count: Optional[int] = 0
    data_completeness_score: Optional[float] = 0.0
    contacted_via_email: Optional[bool] = False
    contacted_via_phone: Optional[bool] = False
    contacted_via_linkedin: Optional[bool] = False
    contacted_via_facebook: Optional[bool] = False
    contacted_via_instagram: Optional[bool] = False
    last_contact_date: Optional[datetime] = None
    source_file_name: Optional[str] = None
    source_file_row: Optional[int] = None
    is_duplicate: Optional[bool] = False
    duplicate_of: Optional[int] = None
    user_id: str

class LeadDetailSchema(LeadSummarySchema):
    """Detailed schema for lead information, aligned with Lead model"""
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    additional_data: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None
    tags: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None

class FileUploadResponse(BaseSchema):
    """Schema for file upload response, aligned with FileUpload model"""
    id: int
    filename: str = Field(..., max_length=255)
    original_filename: str = Field(..., max_length=255)
    file_path: str = Field(..., max_length=500)
    file_size: int
    file_type: str = Field(..., max_length=50)
    mime_type: Optional[str] = Field(None, max_length=100)
    status: str = Field(default="uploaded", max_length=50)
    total_rows: int = 0
    processed_rows: int = 0
    successful_rows: int = 0
    failed_rows: int = 0
    duplicate_rows: int = 0
    processing_started_at: Optional[datetime] = None
    processing_completed_at: Optional[datetime] = None
    processing_duration: Optional[float] = None
    error_message: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None
    leads_created: int = 0
    leads_updated: int = 0
    leads_skipped: int = 0
    created_at: datetime
    updated_at: datetime
    user_id: str

# Attendee Schemas
class AttendeeCreateSchema(BaseSchema):
    """Schema for creating a new attendee"""
    name: str = Field(..., min_length=1, max_length=200)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    company: Optional[str] = Field(None, max_length=200)
    job_title: Optional[str] = Field(None, max_length=150)
    lead_id: Optional[int] = None
    is_organizer: bool = False
    is_required: bool = True
    response_notes: Optional[str] = None
    user_id: str

class AttendeeUpdateSchema(BaseSchema):
    """Schema for updating an attendee"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    company: Optional[str] = Field(None, max_length=200)
    job_title: Optional[str] = Field(None, max_length=150)
    is_organizer: Optional[bool] = None
    is_required: Optional[bool] = None
    response_notes: Optional[str] = None
    user_id: str

class AttendeeResponseSchema(BaseSchema):
    """Schema for attendee responses"""
    id: int
    event_id: int
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    job_title: Optional[str] = None
    lead_id: Optional[int] = None
    status: AttendeeStatusEnum
    is_organizer: bool
    is_required: bool
    response_datetime: Optional[datetime] = None
    response_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    user_id: str
    lead_info: Optional[LeadSummarySchema] = None

# Event Schemas
class EventCreateSchema(BaseSchema):
    """Schema for creating a new event"""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    start_datetime: datetime
    end_datetime: datetime
    timezone: str = Field(default="UTC", max_length=50)
    all_day: bool = False
    event_type: EventTypeEnum = EventTypeEnum.MEETING
    priority: EventPriorityEnum = EventPriorityEnum.MEDIUM
    location: Optional[str] = Field(None, max_length=500)
    meeting_url: Optional[str] = Field(None, max_length=1000)
    meeting_id: Optional[str] = Field(None, max_length=100)
    meeting_password: Optional[str] = Field(None, max_length=100)
    lead_id: Optional[int] = None
    lead_name: Optional[str] = Field(None, max_length=200)
    lead_email: Optional[str] = Field(None, max_length=255)
    lead_phone: Optional[str] = Field(None, max_length=50)
    lead_company: Optional[str] = Field(None, max_length=200)
    deal_value: Optional[float] = Field(None, ge=0)
    deal_stage: Optional[str] = Field(None, max_length=50)
    deal_probability: Optional[float] = Field(None, ge=0, le=100)
    recurrence_type: RecurrenceTypeEnum = RecurrenceTypeEnum.NONE
    recurrence_interval: int = Field(default=1, ge=1)
    recurrence_end_date: Optional[datetime] = None
    recurrence_count: Optional[int] = Field(None, ge=1)
    notes: Optional[str] = None
    tags: Optional[str] = Field(None, max_length=500)
    custom_fields: Optional[Dict[str, Any]] = None
    reminder_minutes: Optional[List[int]] = Field(default=[15])
    email_reminders: bool = True
    sms_reminders: bool = False
    attendees: Optional[List[AttendeeCreateSchema]] = Field(default=[])
    user_id: str
    
    @validator('end_datetime')
    def end_after_start(cls, v, values):
        if 'start_datetime' in values and v <= values['start_datetime']:
            raise ValueError('End datetime must be after start datetime')
        return v
    
    @validator('recurrence_end_date')
    def recurrence_end_after_start(cls, v, values):
        if v and 'start_datetime' in values and v <= values['start_datetime']:
            raise ValueError('Recurrence end date must be after start datetime')
        return v

class EventUpdateSchema(BaseSchema):
    """Schema for updating an event"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    start_datetime: Optional[datetime] = None
    end_datetime: Optional[datetime] = None
    timezone: Optional[str] = Field(None, max_length=50)
    all_day: Optional[bool] = None
    event_type: Optional[EventTypeEnum] = None
    status: Optional[EventStatusEnum] = None
    priority: Optional[EventPriorityEnum] = None
    location: Optional[str] = Field(None, max_length=500)
    meeting_url: Optional[str] = Field(None, max_length=1000)
    meeting_id: Optional[str] = Field(None, max_length=100)
    meeting_password: Optional[str] = Field(None, max_length=100)
    deal_value: Optional[float] = Field(None, ge=0)
    deal_stage: Optional[str] = Field(None, max_length=50)
    deal_probability: Optional[float] = Field(None, ge=0, le=100)
    notes: Optional[str] = None
    tags: Optional[str] = Field(None, max_length=500)
    custom_fields: Optional[Dict[str, Any]] = None
    reminder_minutes: Optional[List[int]] = None
    email_reminders: Optional[bool] = None
    sms_reminders: Optional[bool] = None
    user_id: str

class EventResponseSchema(BaseSchema):
    """Schema for event responses"""
    id: int
    title: str
    description: Optional[str] = None
    start_datetime: datetime
    end_datetime: datetime
    timezone: str
    all_day: bool
    event_type: EventTypeEnum
    status: EventStatusEnum
    priority: EventPriorityEnum
    location: Optional[str] = None
    meeting_url: Optional[str] = None
    meeting_id: Optional[str] = None
    meeting_password: Optional[str] = None
    lead_id: Optional[int] = None
    lead_name: Optional[str] = None
    lead_email: Optional[str] = None
    lead_phone: Optional[str] = None
    lead_company: Optional[str] = None
    deal_value: Optional[float] = None
    deal_stage: Optional[str] = None
    deal_probability: Optional[float] = None
    recurrence_type: RecurrenceTypeEnum
    recurrence_interval: int
    recurrence_end_date: Optional[datetime] = None
    recurrence_count: Optional[int] = None
    parent_event_id: Optional[int] = None
    notes: Optional[str] = None
    tags: Optional[str] = None
    custom_fields: Optional[Dict[str, Any]] = None
    reminder_minutes: Optional[List[int]] = None
    email_reminders: bool
    sms_reminders: bool
    duration_minutes: Optional[int] = None
    is_recurring: Optional[bool] = None
    is_past: Optional[bool] = None
    is_upcoming: Optional[bool] = None
    is_active: Optional[bool] = None
    created_at: datetime
    updated_at: datetime
    user_id: str
    attendees: Optional[List[AttendeeResponseSchema]] = None
    attendee_count: Optional[int] = None
    lead_info: Optional[LeadSummarySchema] = None

    @validator('event_type', pre=True)
    def validate_event_type(cls, value):
        if not value:
            logger.warning(f"Invalid event_type: {value}, defaulting to 'meeting'")
            return EventTypeEnum.MEETING
        if isinstance(value, str):
            try:
                return EventTypeEnum(value)
            except ValueError:
                logger.warning(f"Invalid event_type: {value}, defaulting to 'meeting'")
                return EventTypeEnum.MEETING
        return value

# Lead Integration Schemas
class LeadEventCreateSchema(BaseSchema):
    """Schema for creating an event from a lead"""
    event_type: EventTypeEnum = EventTypeEnum.MEETING
    title: Optional[str] = None
    description: Optional[str] = None
    start_datetime: datetime
    duration_minutes: int = Field(default=60, ge=15, le=480)  # 15 minutes to 8 hours
    location: Optional[str] = Field(None, max_length=500)
    meeting_url: Optional[str] = Field(None, max_length=1000)
    priority: EventPriorityEnum = EventPriorityEnum.MEDIUM
    notes: Optional[str] = None
    deal_value: Optional[float] = Field(None, ge=0)
    deal_stage: Optional[str] = Field(None, max_length=50)
    deal_probability: Optional[float] = Field(None, ge=0, le=100)
    reminder_minutes: Optional[List[int]] = Field(default=[15, 30])
    user_id: str
    
    @validator('event_type', pre=True)
    def validate_event_type(cls, value):
        logger.info(f"Validating event_type: {value}, type: {type(value)}")
        if isinstance(value, str):
            try:
                validated_event = EventTypeEnum[value.upper()]
                logger.info(f"Converted event_type to {validated_event}")
                return validated_event
            except KeyError:
                logger.error(f"Invalid event type: {value}. Must be one of {[e.value for e in EventTypeEnum]}")
                raise ValueError(f"Invalid event type: {value}. Must be one of {[e.value for e in EventTypeEnum]}")
        elif isinstance(value, EventTypeEnum):
            logger.info(f"Event_type is already EventTypeEnum: {value}")
            return value
        logger.error(f"Event type must be a string or EventTypeEnum, got {type(value)}")
        raise ValueError(f"Event type must be a string or EventTypeEnum, got {type(value)}")

    @validator('title')
    def generate_title_if_empty(cls, v, values):
        if not v and 'event_type' in values:
            event_type = values['event_type']
            event_type_str = (
                event_type.value.replace('_', ' ').title()
                if isinstance(event_type, Enum)
                else event_type.replace('_', ' ').title()
            )
            return f"{event_type_str} - Lead Follow-up"
        return v

class FollowUpSuggestionSchema(BaseSchema):
    """Schema for follow-up event suggestions"""
    type: str
    title: str
    event_type: EventTypeEnum
    duration_minutes: int
    priority: EventPriorityEnum
    suggested_time: datetime
    reason: str
    confidence_score: Optional[float] = Field(None, ge=0, le=1)

class LeadEventSummarySchema(BaseSchema):
    """Schema for lead event summary"""
    lead_id: int
    total_events: int
    upcoming_events: int
    completed_events: int
    cancelled_events: int
    total_deal_value: Optional[float] = None
    next_event: Optional[EventResponseSchema] = None
    last_event: Optional[EventResponseSchema] = None
    follow_up_suggestions: Optional[List[FollowUpSuggestionSchema]] = None
    user_id: str

# Availability Schemas
class AvailabilityCheckSchema(BaseSchema):
    """Schema for checking availability"""
    start_date: datetime
    end_date: datetime
    duration_minutes: int = Field(default=60, ge=15)
    timezone: str = Field(default="UTC", max_length=50)
    working_hours_start: str = Field(default="09:00", pattern=r"^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    working_hours_end: str = Field(default="17:00", pattern=r"^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    exclude_weekends: bool = True
    buffer_minutes: int = Field(default=0, ge=0)
    user_id: str

class AvailabilitySlotSchema(BaseSchema):
    """Schema for availability time slots"""
    start_datetime: datetime
    end_datetime: datetime
    is_available: bool
    conflicting_event_id: Optional[int] = None
    conflicting_event_title: Optional[str] = None

class AvailabilityResponseSchema(BaseSchema):
    """Schema for availability check response"""
    start_date: datetime
    end_date: datetime
    timezone: str
    available_slots: List[AvailabilitySlotSchema]
    total_slots: int
    available_count: int
    busy_count: int
    user_id: str

# Statistics Schemas
class EventStatsSchema(BaseModel):
    total_events: int
    upcoming_events: int
    completed_events: int
    cancelled_events: int
    events_this_week: int
    events_this_month: int
    events_by_type: Dict[str, int]
    events_by_status: Dict[str, int]
    events_by_priority: Dict[str, int]
    average_event_duration: Optional[float] = 0.0
    total_deal_value: float
    user_id: str

# Pagination Schemas
class PaginationSchema(BaseSchema):
    """Schema for pagination metadata"""
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=50, ge=1, le=100)
    total: int
    total_pages: int
    has_next: bool
    has_prev: bool

class PaginatedEventsSchema(BaseSchema):
    """Schema for paginated events response"""
    events: List[EventResponseSchema]
    pagination: PaginationSchema
    user_id: str

# Filter Schemas
class EventFilterSchema(BaseSchema):
    """Schema for event filtering"""
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=50, ge=1, le=100)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    event_type: Optional[EventTypeEnum] = None
    status: Optional[EventStatusEnum] = None
    priority: Optional[EventPriorityEnum] = None
    lead_id: Optional[int] = None
    search: Optional[str] = Field(None, max_length=255)
    created_by: Optional[str] = Field(None, max_length=100)
    order_by: str = Field(default="start_datetime")
    order_direction: str = Field(default="asc", pattern="^(asc|desc)$")
    include_attendees: bool = False
    include_lead_info: bool = False
    user_id: str

# Response Schemas
class SuccessResponseSchema(BaseSchema):
    """Schema for success responses"""
    message: str
    data: Optional[Any] = None

class ErrorResponseSchema(BaseSchema):
    """Schema for error responses"""
    detail: str
    status_code: int
    timestamp: datetime
    path: Optional[str] = None
    method: Optional[str] = None

class HealthCheckSchema(BaseSchema):
    """Schema for health check response"""
    status: str
    timestamp: datetime
    version: str
    database: Dict[str, str]
    integrations: Dict[str, str]