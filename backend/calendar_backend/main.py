from fastapi import FastAPI, Depends, HTTPException, Query, Path, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import logging
from contextlib import asynccontextmanager
import redis
import json
from config.settings import settings

from calendar_backend.app.models.schemas import (
    AttendeeCreateSchema, AttendeeResponseSchema, AttendeeStatusEnum, AttendeeUpdateSchema,
    AvailabilityCheckSchema, EventCreateSchema, EventFilterSchema, EventPriorityEnum,
    EventResponseSchema, EventStatsSchema, EventStatusEnum, EventTypeEnum, EventUpdateSchema,
    FollowUpSuggestionSchema, HealthCheckSchema, LeadEventCreateSchema, LeadEventSummarySchema,
    PaginatedEventsSchema, PaginationSchema
)
from calendar_backend.app.database.connection import (
    get_calendar_db, get_lead_parser_db, 
    create_calendar_tables, test_all_connections,
    get_database_health
)
from calendar_backend.app.services.event_service import EventService
from calendar_backend.app.services.attendee_service import AttendeeService
from calendar_backend.app.services.availability_service import AvailabilityService
from calendar_backend.app.integrations.lead_parser_integration import LeadParserIntegration

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Redis client
redis_client = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=0,
    decode_responses=True
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Calendar Backend Application")
    connections = test_all_connections()
    if not connections["all_connected"]:
        logger.error("Database connection failed during startup")
    else:
        logger.info("Database connections successful")
        create_calendar_tables()
    # Test Redis connection
    try:
        redis_client.ping()
        logger.info("Redis connection successful")
    except redis.ConnectionError as e:
        logger.error(f"Redis connection failed: {e}")
    yield
    logger.info("Shutting down Calendar Backend Application")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Calendar Backend API for managing client meetings, calls, and events",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_current_user() -> str:
    return "12e80c63-cb37-4bc6-a555-7268285d33d6"

# Health check endpoint
@app.get("/health", response_model=HealthCheckSchema, tags=["Health"])
async def health_check():
    try:
        db_health = get_database_health()
        redis_status = "healthy" if redis_client.ping() else "unhealthy"
        return HealthCheckSchema(
            status="healthy" if all("healthy" in status for status in db_health.values()) and redis_status == "healthy" else "unhealthy",
            timestamp=datetime.utcnow(),
            version=settings.APP_VERSION,
            database=db_health,
            integrations={
                "lead_parser": "configured" if settings.LEAD_DATABASE_URL else "not_configured",
                "redis": redis_status
            }
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthCheckSchema(
            status="unhealthy",
            timestamp=datetime.utcnow(),
            version=settings.APP_VERSION,
            database={"error": str(e)},
            integrations={"error": str(e), "redis": "unhealthy"}
        )

# Event Management Endpoints
@app.post("/api/events", response_model=EventResponseSchema, status_code=status.HTTP_201_CREATED, tags=["Events"])
async def create_event(
    event_data: EventCreateSchema,
    calendar_db: Session = Depends(get_calendar_db),
    lead_parser_db: Session = Depends(get_lead_parser_db),
    user_id: str = Depends(get_current_user)
):
    try:
        event_service = EventService(calendar_db, lead_parser_db, redis_client)
        event = event_service.create_event(event_data)
        if not event:
            raise HTTPException(status_code=400, detail="Failed to create event")
        # Invalidate relevant caches
        redis_client.delete(f"events:{user_id}:*")
        redis_client.delete(f"upcoming_events:{user_id}")
        return event
    except Exception as e:
        logger.error(f"Error creating event for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/users/{user_id}/events", response_model=PaginatedEventsSchema, tags=["Events"])
async def get_events(
    user_id: str = Path(..., regex="^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    event_type: Optional[EventTypeEnum] = Query(None),
    status: Optional[EventStatusEnum] = Query(None),
    priority: Optional[EventPriorityEnum] = Query(None),
    lead_id: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    order_by: str = Query("start_datetime"),
    order_direction: str = Query("asc", regex="^(asc|desc)$"),
    include_attendees: bool = Query(False),
    include_lead_info: bool = Query(False),
    calendar_db: Session = Depends(get_calendar_db),
    lead_parser_db: Session = Depends(get_lead_parser_db),
):
    try:
        filters = EventFilterSchema(
            page=page,
            per_page=per_page,
            start_date=start_date,
            end_date=end_date,
            event_type=event_type,
            status=status,
            priority=priority,
            lead_id=lead_id,
            search=search,
            order_by=order_by,
            order_direction=order_direction,
            include_attendees=include_attendees,
            include_lead_info=include_lead_info,
            user_id=user_id
        )
        cache_key = f"events:{user_id}:{filters.hash()}"
        cached_result = redis_client.get(cache_key)
        if cached_result:
            logger.info(f"Cache hit for events: {cache_key}")
            return PaginatedEventsSchema.parse_raw(cached_result)
        
        event_service = EventService(calendar_db, lead_parser_db, redis_client)
        events, total_count = event_service.get_events(filters)
        
        total_pages = (total_count + per_page - 1) // per_page
        has_next = page < total_pages
        has_prev = page > 1
        
        pagination = PaginationSchema(
            page=page,
            per_page=per_page,
            total=total_count,
            total_pages=total_pages,
            has_next=has_next,
            has_prev=has_prev
        )
        
        result = PaginatedEventsSchema(
            events=events,
            pagination=pagination,
            user_id=user_id
        )
        
        # Cache the result for 5 minutes
        redis_client.setex(cache_key, 300, json.dumps(jsonable_encoder(result)))
        return result
    except Exception as e:
        logger.error(f"Error getting events for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/users/{user_id}/events/upcoming", response_model=List[EventResponseSchema], tags=["Events"])
async def get_upcoming_events(
    user_id: str = Path(..., regex="^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"),
    limit: int = Query(10, ge=1, le=50),
    calendar_db: Session = Depends(get_calendar_db),
    lead_parser_db: Session = Depends(get_lead_parser_db),
):
    try:
        cache_key = f"upcoming_events:{user_id}:{limit}"
        cached_result = redis_client.get(cache_key)
        if cached_result:
            logger.info(f"Cache hit for upcoming events: {cache_key}")
            return json.loads(cached_result)
        
        event_service = EventService(calendar_db, lead_parser_db, redis_client)
        events = event_service.get_upcoming_events(limit, user_id)
        
        # Cache for 1 hour
        redis_client.setex(cache_key, 3600, json.dumps(jsonable_encoder(events)))
        return events
    except Exception as e:
        logger.error(f"Error getting upcoming events for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/users/{user_id}/events/stats", response_model=EventStatsSchema, tags=["Events"])
async def get_event_statistics(
    user_id: str = Path(..., regex="^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    calendar_db: Session = Depends(get_calendar_db),
):
    try:
        cache_key = f"event_stats:{user_id}:{start_date.isoformat() if start_date else 'none'}:{end_date.isoformat() if end_date else 'none'}"
        cached_result = redis_client.get(cache_key)
        if cached_result:
            logger.info(f"Cache hit for event stats: {cache_key}")
            return EventStatsSchema.parse_raw(cached_result)
        
        event_service = EventService(calendar_db, None, redis_client)
        stats = event_service.get_event_statistics(start_date, end_date, user_id)
        
        # Cache for 1 hour
        redis_client.setex(cache_key, 3600, json.dumps(jsonable_encoder(stats)))
        return stats
    except Exception as e:
        logger.error(f"Error getting event statistics for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Attendee Management Endpoints
@app.post("/api/events/{event_id}/attendees", response_model=AttendeeResponseSchema, status_code=status.HTTP_201_CREATED, tags=["Attendees"])
async def add_attendee(
    event_id: int = Path(..., ge=1),
    attendee_data: AttendeeCreateSchema = ...,
    calendar_db: Session = Depends(get_calendar_db),
    lead_parser_db: Session = Depends(get_lead_parser_db),
):
    try:
        attendee_service = AttendeeService(calendar_db, lead_parser_db)
        attendee = attendee_service.add_attendee(event_id, attendee_data)
        if not attendee:
            raise HTTPException(status_code=400, detail="Failed to add attendee")
        # Invalidate event cache
        redis_client.delete(f"events:{attendee_data.user_id}:*")
        return attendee
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding attendee to event {event_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/users/{user_id}/events/{event_id}/attendees", response_model=List[AttendeeResponseSchema], tags=["Attendees"])
async def get_event_attendees(
    user_id: str = Path(..., regex="^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"),
    event_id: int = Path(..., ge=1),
    include_lead_info: bool = Query(True),
    calendar_db: Session = Depends(get_calendar_db),
    lead_parser_db: Session = Depends(get_lead_parser_db),
):
    try:
        attendee_service = AttendeeService(calendar_db, lead_parser_db)
        attendees = attendee_service.get_event_attendees(event_id, user_id, include_lead_info)
        return attendees
    except Exception as e:
        logger.error(f"Error getting attendees for event {event_id} for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/users/{user_id}/events/{event_id}", response_model=EventResponseSchema, tags=["Events"])
async def get_event(
    user_id: str = Path(..., regex="^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"),
    event_id: int = Path(..., ge=1),
    include_attendees: bool = Query(True),
    include_lead_info: bool = Query(True),
    calendar_db: Session = Depends(get_calendar_db),
    lead_parser_db: Session = Depends(get_lead_parser_db),
):
    try:
        cache_key = f"event:{user_id}:{event_id}:{include_attendees}:{include_lead_info}"
        cached_result = redis_client.get(cache_key)
        if cached_result:
            logger.info(f"Cache hit for event: {cache_key}")
            return EventResponseSchema.parse_raw(cached_result)
        
        event_service = EventService(calendar_db, lead_parser_db, redis_client)
        event = event_service.get_event_by_id(event_id, user_id, include_attendees, include_lead_info)
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        
        # Cache for 5 minutes
        redis_client.setex(cache_key, 300, json.dumps(jsonable_encoder(event)))
        return event
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting event {event_id} for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/events/{event_id}", response_model=EventResponseSchema, tags=["Events"])
async def update_event(
    event_id: int = Path(..., ge=1),
    event_data: EventUpdateSchema = ...,
    calendar_db: Session = Depends(get_calendar_db),
    user_id: str = Depends(get_current_user)
):
    try:
        event_service = EventService(calendar_db, None, redis_client)
        event = event_service.update_event(event_id, event_data)
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        # Invalidate relevant caches
        redis_client.delete(f"events:{user_id}:*")
        redis_client.delete(f"upcoming_events:{user_id}")
        redis_client.delete(f"event:{user_id}:{event_id}:*")
        return event
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating event {event_id} for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/users/{user_id}/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Events"])
async def delete_event(
    user_id: str = Path(..., regex="^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"),
    event_id: int = Path(..., ge=1),
    calendar_db: Session = Depends(get_calendar_db),
):
    try:
        event_service = EventService(calendar_db, None, redis_client)
        success = event_service.delete_event(event_id, user_id)
        if not success:
            raise HTTPException(status_code=404, detail="Event not found")
        # Invalidate relevant caches
        redis_client.delete(f"events:{user_id}:*")
        redis_client.delete(f"upcoming_events:{user_id}")
        redis_client.delete(f"event:{user_id}:{event_id}:*")
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting event {event_id} for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/attendees/{attendee_id}", response_model=AttendeeResponseSchema, tags=["Attendees"])
async def update_attendee(
    attendee_id: int = Path(..., ge=1),
    attendee_data: AttendeeUpdateSchema = ...,
    calendar_db: Session = Depends(get_calendar_db),
):
    try:
        attendee_service = AttendeeService(calendar_db)
        attendee = attendee_service.update_attendee(attendee_id, attendee_data)
        if not attendee:
            raise HTTPException(status_code=404, detail="Attendee not found")
        # Invalidate event cache
        redis_client.delete(f"events:{attendee_data.user_id}:*")
        return attendee
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating attendee {attendee_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/users/{user_id}/attendees/{attendee_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Attendees"])
async def remove_attendee(
    user_id: str = Path(..., regex="^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"),
    attendee_id: int = Path(..., ge=1),
    calendar_db: Session = Depends(get_calendar_db),
):
    try:
        attendee_service = AttendeeService(calendar_db)
        success = attendee_service.remove_attendee(attendee_id, user_id)
        if not success:
            raise HTTPException(status_code=404, detail="Attendee not found")
        # Invalidate event cache
        redis_client.delete(f"events:{user_id}:*")
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing attendee {attendee_id} for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/users/{user_id}/attendees/{attendee_id}/response", response_model=AttendeeResponseSchema, tags=["Attendees"])
async def update_attendee_response(
    user_id: str = Path(..., regex="^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"),
    attendee_id: int = Path(..., ge=1),
    status: AttendeeStatusEnum = ...,
    response_notes: Optional[str] = None,
    calendar_db: Session = Depends(get_calendar_db),
):
    try:
        attendee_service = AttendeeService(calendar_db)
        attendee = attendee_service.update_attendee_response(attendee_id, status.value, response_notes, user_id)
        if not attendee:
            raise HTTPException(status_code=404, detail="Attendee not found")
        # Invalidate event cache
        redis_client.delete(f"events:{user_id}:*")
        return attendee
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating attendee response {attendee_id} for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Availability Endpoints
@app.post("/api/availability/check", tags=["Availability"])
async def check_availability(
    availability_request: AvailabilityCheckSchema,
    calendar_db: Session = Depends(get_calendar_db),
    user_id: str = Depends(get_current_user)
):
    try:
        cache_key = f"availability:{user_id}:{availability_request.start_date.isoformat()}:{availability_request.end_date.isoformat()}:{availability_request.duration_minutes}"
        cached_result = redis_client.get(cache_key)
        if cached_result:
            logger.info(f"Cache hit for availability: {cache_key}")
            return json.loads(cached_result)
        
        availability_service = AvailabilityService(calendar_db, redis_client)
        availability = availability_service.check_availability(availability_request)
        
        # Cache for 5 minutes
        redis_client.setex(cache_key, 300, json.dumps(jsonable_encoder(availability)))
        return availability
    except Exception as e:
        logger.error(f"Error checking availability for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/users/{user_id}/availability/next-slot", tags=["Availability"])
async def find_next_available_slot(
    user_id: str = Path(..., regex="^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"),
    duration_minutes: int = Query(..., ge=15, le=480),
    timezone: str = Query("UTC"),
    days_ahead: int = Query(30, ge=1, le=90),
    calendar_db: Session = Depends(get_calendar_db),
):
    try:
        cache_key = f"next_slot:{user_id}:{duration_minutes}:{timezone}:{days_ahead}"
        cached_result = redis_client.get(cache_key)
        if cached_result:
            logger.info(f"Cache hit for next slot: {cache_key}")
            return json.loads(cached_result)
        
        availability_service = AvailabilityService(calendar_db, redis_client)
        slots = availability_service.find_next_available_slot(duration_minutes, timezone, user_id, days_ahead)
        
        # Cache for 1 hour
        redis_client.setex(cache_key, 3600, json.dumps(jsonable_encoder(slots)))
        return slots
    except Exception as e:
        logger.error(f"Error finding next available slots for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/users/{user_id}/availability/suggest-times", tags=["Availability"])
async def suggest_meeting_times(
    user_id: str = Path(..., regex="^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"),
    duration_minutes: int = Query(..., ge=15, le=480),
    preferred_times: Optional[List[str]] = Query(None),
    timezone: str = Query("UTC"),
    days_ahead: int = Query(7, ge=1, le=30),
    calendar_db: Session = Depends(get_calendar_db),
):
    try:
        preferred_times_key = ':'.join(preferred_times) if preferred_times else 'none'
        cache_key = f"suggest_times:{user_id}:{duration_minutes}:{preferred_times_key}:{timezone}:{days_ahead}"
        cached_result = redis_client.get(cache_key)
        if cached_result:
            logger.info(f"Cache hit for suggest times: {cache_key}")
            return json.loads(cached_result)
        
        availability_service = AvailabilityService(calendar_db, redis_client)
        suggestions = availability_service.suggest_meeting_times(duration_minutes, preferred_times, timezone, user_id, days_ahead)
        
        # Cache for 1 hour
        redis_client.setex(cache_key, 3600, json.dumps(jsonable_encoder(suggestions)))
        return suggestions
    except Exception as e:
        logger.error(f"Error suggesting meeting times for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Lead Integration Endpoints
@app.post("/api/leads/{lead_id}/events", response_model=EventResponseSchema, status_code=status.HTTP_201_CREATED, tags=["Lead Integration"])
async def create_event_from_lead(
    lead_id: int = Path(..., ge=1),
    event_data: LeadEventCreateSchema = ...,
    calendar_db: Session = Depends(get_calendar_db),
    lead_parser_db: Session = Depends(get_lead_parser_db),
    user_id: str = Depends(get_current_user)
):
    try:
        logger.info(f"Received request to create event for lead {lead_id}: {event_data.dict()} for user {user_id}")
        if event_data.start_datetime.tzinfo is None:
            event_data.start_datetime = event_data.start_datetime.replace(tzinfo=timezone.utc)
        
        integration = LeadParserIntegration(calendar_db, lead_parser_db)
        event = integration.create_event_from_lead(lead_id, event_data)
        if not event:
            raise HTTPException(status_code=400, detail="Failed to create event from lead")
        
        # Invalidate relevant caches
        redis_client.delete(f"events:{user_id}:*")
        redis_client.delete(f"upcoming_events:{user_id}")
        return event
    except ValueError as e:
        logger.error(f"Validation error for lead {lead_id} for user {user_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating event for lead {lead_id} for user {user_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/users/{user_id}/leads/{lead_id}/events", response_model=List[EventResponseSchema], tags=["Lead Integration"])
async def get_lead_events(
    user_id: str = Path(..., regex="^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"),
    lead_id: int = Path(..., ge=1),
    calendar_db: Session = Depends(get_calendar_db),
    lead_parser_db: Session = Depends(get_lead_parser_db),
):
    try:
        cache_key = f"lead_events:{user_id}:{lead_id}"
        cached_result = redis_client.get(cache_key)
        if cached_result:
            logger.info(f"Cache hit for lead events: {cache_key}")
            return json.loads(cached_result)
        
        integration = LeadParserIntegration(calendar_db, lead_parser_db)
        events = integration.get_lead_events(lead_id, user_id)
        
        # Cache for 5 minutes
        redis_client.setex(cache_key, 300, json.dumps(jsonable_encoder(events)))
        return events
    except Exception as e:
        logger.error(f"Error getting events for lead {lead_id} for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/users/{user_id}/leads/{lead_id}/events/summary", response_model=LeadEventSummarySchema, tags=["Lead Integration"])
async def get_lead_event_summary(
    user_id: str = Path(..., regex="^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"),
    lead_id: int = Path(..., ge=1),
    calendar_db: Session = Depends(get_calendar_db),
    lead_parser_db: Session = Depends(get_lead_parser_db),
):
    try:
        cache_key = f"lead_event_summary:{user_id}:{lead_id}"
        cached_result = redis_client.get(cache_key)
        if cached_result:
            logger.info(f"Cache hit for lead event summary: {cache_key}")
            return LeadEventSummarySchema.parse_raw(cached_result)
        
        integration = LeadParserIntegration(calendar_db, lead_parser_db)
        summary = integration.get_lead_event_summary(lead_id, user_id)
        
        # Cache for 5 minutes
        redis_client.setex(cache_key, 300, json.dumps(jsonable_encoder(summary)))
        return summary
    except Exception as e:
        logger.error(f"Error getting event summary for lead {lead_id} for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/users/{user_id}/leads/{lead_id}/follow-up-suggestions", response_model=List[FollowUpSuggestionSchema], tags=["Lead Integration"])
async def get_follow_up_suggestions(
    user_id: str = Path(..., regex="^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"),
    lead_id: int = Path(..., ge=1),
    calendar_db: Session = Depends(get_calendar_db),
    lead_parser_db: Session = Depends(get_lead_parser_db),
):
    try:
        cache_key = f"follow_up_suggestions:{user_id}:{lead_id}"
        cached_result = redis_client.get(cache_key)
        if cached_result:
            logger.info(f"Cache hit for follow-up suggestions: {cache_key}")
            return json.loads(cached_result)
        
        integration = LeadParserIntegration(calendar_db, lead_parser_db)
        suggestions = integration.get_follow_up_suggestions(lead_id, user_id)
        
        # Cache for 1 hour
        redis_client.setex(cache_key, 3600, json.dumps(jsonable_encoder(suggestions)))
        return suggestions
    except Exception as e:
        logger.error(f"Error getting follow-up suggestions for lead {lead_id} for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/leads/{lead_id}/sync", tags=["Lead Integration"])
async def sync_lead_updates(
    lead_id: int = Path(..., ge=1),
    calendar_db: Session = Depends(get_calendar_db),
    lead_parser_db: Session = Depends(get_lead_parser_db),
    user_id: str = Depends(get_current_user)
):
    try:
        integration = LeadParserIntegration(calendar_db, lead_parser_db)
        result = integration.sync_lead_updates(lead_id, user_id)
        # Invalidate relevant caches
        redis_client.delete(f"events:{user_id}:*")
        redis_client.delete(f"lead_events:{user_id}:{lead_id}")
        redis_client.delete(f"lead_event_summary:{user_id}:{lead_id}")
        return result
    except Exception as e:
        logger.error(f"Error syncing lead updates for lead {lead_id} for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/users/{user_id}/leads/upcoming-events", tags=["Lead Integration"])
async def get_leads_with_upcoming_events(
    user_id: str = Path(..., regex="^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"),
    days_ahead: int = Query(7, ge=1, le=30),
    calendar_db: Session = Depends(get_calendar_db),
    lead_parser_db: Session = Depends(get_lead_parser_db),
):
    try:
        cache_key = f"leads_upcoming:{user_id}:{days_ahead}"
        cached_result = redis_client.get(cache_key)
        if cached_result:
            logger.info(f"Cache hit for leads with upcoming events: {cache_key}")
            return json.loads(cached_result)
        
        integration = LeadParserIntegration(calendar_db, lead_parser_db)
        leads = integration.get_leads_with_upcoming_events(user_id, days_ahead)
        
        # Cache for 1 hour
        redis_client.setex(cache_key, 3600, json.dumps(jsonable_encoder({"leads": leads})))
        return {"leads": leads}
    except Exception as e:
        logger.error(f"Error getting leads with upcoming events for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/users/{user_id}/calendar/summary", tags=["Utilities"])
async def get_calendar_summary(
    user_id: str = Path(..., regex="^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"),
    start_date: datetime = Query(None),
    end_date: datetime = Query(None),
    calendar_db: Session = Depends(get_calendar_db),
):
    try:
        cache_key = f"calendar_summary:{user_id}:{start_date.isoformat() if start_date else 'none'}:{end_date.isoformat() if end_date else 'none'}"
        cached_result = redis_client.get(cache_key)
        if cached_result:
            logger.info(f"Cache hit for calendar summary: {cache_key}")
            return json.loads(cached_result)
        
        availability_service = AvailabilityService(calendar_db, redis_client)
        summary = availability_service.get_calendar_summary(start_date, end_date, user_id)
        
        # Cache for 1 hour
        redis_client.setex(cache_key, 3600, json.dumps(jsonable_encoder(summary)))
        return summary
    except Exception as e:
        logger.error(f"Error getting calendar summary for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/users/{user_id}/events/{event_id}/conflicts", tags=["Utilities"])
async def check_event_conflicts(
    user_id: str = Path(..., regex="^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"),
    event_id: int = Path(..., ge=1),
    calendar_db: Session = Depends(get_calendar_db),
):
    try:
        cache_key = f"event_conflicts:{user_id}:{event_id}"
        cached_result = redis_client.get(cache_key)
        if cached_result:
            logger.info(f"Cache hit for event conflicts: {cache_key}")
            return json.loads(cached_result)
        
        event_service = EventService(calendar_db, None, redis_client)
        event = event_service.get_event_by_id(event_id, user_id, False, False)
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        
        conflicts = event_service.check_conflicts(event.start_datetime, event.end_datetime, event_id, user_id)
        result = {
            "event_id": event_id,
            "has_conflicts": len(conflicts) > 0,
            "conflict_count": len(conflicts),
            "conflicts": [
                {
                    "id": conflict.id,
                    "title": conflict.title,
                    "start_datetime": conflict.start_datetime,
                    "end_datetime": conflict.end_datetime,
                    "event_type": conflict.event_type.value,
                    "status": conflict.status.value
                }
                for conflict in conflicts
            ]
        }
        
        # Cache for 5 minutes
        redis_client.setex(cache_key, 300, json.dumps(jsonable_encoder(result)))
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking conflicts for event {event_id} for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.utcnow().isoformat(),
            "path": str(request.url.path),
            "method": request.method
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "status_code": 500,
            "timestamp": datetime.utcnow().isoformat(),
            "path": str(request.url.path),
            "method": request.method
        }
    )