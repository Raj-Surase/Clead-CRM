from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta, time
import pytz
import logging
import json

from calendar_backend.app.models.calendar_models import Event
from calendar_backend.app.models.schemas import AvailabilityCheckSchema, AvailabilitySlotSchema, AvailabilityResponseSchema

logger = logging.getLogger(__name__)

class AvailabilityService:
    WORKING_HOURS_START = "10:00"
    WORKING_HOURS_END = "17:00"
    WORKING_DAYS = [0, 1, 2, 3, 4]  # Monday to Friday

    def __init__(self, calendar_db: Session, redis_client=None):
        self.calendar_db = calendar_db
        self.redis_client = redis_client

    def check_availability(self, availability_request: AvailabilityCheckSchema) -> Dict[str, Any]:
        try:
            cache_key = f"availability:{availability_request.user_id}:{availability_request.start_date.isoformat()}:{availability_request.end_date.isoformat()}:{availability_request.duration_minutes}"
            if self.redis_client:
                cached_result = self.redis_client.get(cache_key)
                if cached_result:
                    logger.info(f"Cache hit for availability: {cache_key}")
                    return json.loads(cached_result)

            start_date = availability_request.start_date
            end_date = availability_request.end_date

            slots = self._generate_time_slots(
                start_date,
                end_date,
                availability_request.duration_minutes,
                self.WORKING_HOURS_START,
                self.WORKING_HOURS_END,
                True
            )

            slots_by_day = {}
            for slot_start, slot_end in slots:
                day_key = slot_start.date().isoformat()
                if day_key not in slots_by_day:
                    slots_by_day[day_key] = []

                conflicts = self._check_slot_conflicts(slot_start, slot_end, availability_request.user_id, availability_request.buffer_minutes)

                slot_info = AvailabilitySlotSchema(
                    start_datetime=slot_start,
                    end_datetime=slot_end,
                    is_available=not conflicts
                )

                if conflicts:
                    conflict = conflicts[0]
                    slot_info.conflicting_event_id = conflict.id
                    slot_info.conflicting_event_title = conflict.title

                slots_by_day[day_key].append(slot_info)

            total_slots = sum(len(slots) for slots in slots_by_day.values())
            available_count = sum(len([s for s in slots if s.is_available]) for slots in slots_by_day.values())
            busy_count = total_slots - available_count

            result = {
                "start_date": availability_request.start_date.isoformat(),
                "end_date": availability_request.end_date.isoformat(),
                "timezone": availability_request.timezone,
                "slots_by_day": {
                    day: [slot.dict() for slot in slots]
                    for day, slots in slots_by_day.items()
                },
                "total_slots": total_slots,
                "available_count": available_count,
                "busy_count": busy_count
            }

            if self.redis_client:
                self.redis_client.setex(cache_key, 300, json.dumps(result))

            return result

        except Exception as e:
            logger.error(f"Error checking availability for user {availability_request.user_id}: {str(e)}", exc_info=True)
            return {
                "start_date": availability_request.start_date.isoformat(),
                "end_date": availability_request.end_date.isoformat(),
                "timezone": availability_request.timezone,
                "slots_by_day": {},
                "total_slots": 0,
                "available_count": 0,
                "busy_count": 0
            }

    def find_next_available_slot(self, duration_minutes: int, timezone: str = "UTC", user_id: str = None, days_ahead: int = 30) -> Dict[str, Any]:
        try:
            cache_key = f"next_slot:{user_id}:{duration_minutes}:{timezone}:{days_ahead}"
            if self.redis_client:
                cached_result = self.redis_client.get(cache_key)
                if cached_result:
                    logger.info(f"Cache hit for next slot: {cache_key}")
                    return json.loads(cached_result)

            tz = pytz.timezone(timezone)
            start_from = datetime.now(tz).replace(microsecond=0)
            end_search = start_from + timedelta(days=days_ahead)

            slots = self._generate_time_slots(
                start_from, end_search, duration_minutes,
                self.WORKING_HOURS_START, self.WORKING_HOURS_END,
                True
            )

            available_slots = []
            slots_by_day = {}

            for slot_start, slot_end in slots:
                day_key = slot_start.date().isoformat()
                if day_key not in slots_by_day:
                    slots_by_day[day_key] = []

                conflicts = self._check_slot_conflicts(slot_start, slot_end, user_id)
                if not conflicts:
                    slot_info = {
                        "start_datetime": slot_start.isoformat(),
                        "end_datetime": slot_end.isoformat(),
                        "duration_minutes": duration_minutes,
                        "timezone": timezone
                    }
                    slots_by_day[day_key].append(slot_info)
                    available_slots.append(slot_info)
                    if len(available_slots) >= 3:
                        break

            result = {"slots_by_day": slots_by_day}
            if len(available_slots) < 3:
                logger.warning(f"Could not find 3 available slots within the specified period for user {user_id}")
                result["message"] = "Insufficient available slots found"

            if self.redis_client:
                self.redis_client.setex(cache_key, 3600, json.dumps(result))

            return result

        except Exception as e:
            logger.error(f"Error finding next available slots for user {user_id}: {str(e)}", exc_info=True)
            return {"message": f"Error finding slots: {str(e)}", "slots_by_day": {}}

    def get_busy_times(self, start_date: datetime, end_date: datetime, user_id: str = None) -> List[Dict[str, Any]]:
        try:
            cache_key = f"busy_times:{user_id}:{start_date.isoformat()}:{end_date.isoformat()}"
            if self.redis_client:
                cached_result = self.redis_client.get(cache_key)
                if cached_result:
                    logger.info(f"Cache hit for busy times: {cache_key}")
                    return json.loads(cached_result)

            query = self.calendar_db.query(Event).filter(
                and_(
                    Event.start_datetime < end_date,
                    Event.end_datetime > start_date,
                    Event.status.in_(["scheduled", "confirmed", "in_progress"])
                )
            )

            if user_id:
                query = query.filter(Event.user_id == user_id)

            events = query.order_by(Event.start_datetime).all()

            busy_times = []
            for event in events:
                busy_times.append({
                    "start_datetime": event.start_datetime,
                    "end_datetime": event.end_datetime,
                    "event_id": event.id,
                    "event_title": event.title,
                    "event_type": event.event_type.value,
                    "priority": event.priority.value
                })

            if self.redis_client:
                self.redis_client.setex(cache_key, 300, json.dumps(busy_times))

            return busy_times

        except Exception as e:
            logger.error(f"Error getting busy times for user {user_id}: {str(e)}", exc_info=True)
            return []

    def suggest_meeting_times(self, duration_minutes: int, preferred_times: List[str] = None, timezone: str = "UTC", user_id: str = None, days_ahead: int = 7) -> Dict[str, Any]:
        try:
            preferred_times_key = ':'.join(preferred_times) if preferred_times else 'none'
            cache_key = f"suggest_times:{user_id}:{duration_minutes}:{preferred_times_key}:{timezone}:{days_ahead}"
            if self.redis_client:
                cached_result = self.redis_client.get(cache_key)
                if cached_result:
                    logger.info(f"Cache hit for suggest times: {cache_key}")
                    return json.loads(cached_result)

            suggestions = []
            tz = pytz.timezone(timezone)
            start_from = datetime.now(tz).replace(microsecond=0)
            end_search = start_from + timedelta(days=days_ahead)

            if not preferred_times:
                preferred_times = ["10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00"]

            slots_by_day = {}
            current_date = start_from.date()
            end_date = end_search.date()

            while current_date <= end_date:
                if current_date.weekday() not in self.WORKING_DAYS:
                    current_date += timedelta(days=1)
                    continue

                day_key = current_date.isoformat()
                slots_by_day[day_key] = []

                for preferred_time in preferred_times:
                    hour, minute = map(int, preferred_time.split(':'))
                    if not (10 <= hour < 17):
                        continue

                    slot_start = datetime.combine(current_date, time(hour, minute)).replace(tzinfo=tz)
                    slot_end = slot_start + timedelta(minutes=duration_minutes)

                    if slot_start <= datetime.now(tz):
                        continue

                    conflicts = self._check_slot_conflicts(slot_start, slot_end, user_id)

                    if not conflicts:
                        day_offset = (current_date - start_from.date()).days
                        score = self._calculate_time_slot_score(slot_start, preferred_time, day_offset)

                        slot_info = {
                            "start_datetime": slot_start.isoformat(),
                            "end_datetime": slot_end.isoformat(),
                            "score": score,
                            "day_name": slot_start.strftime("%A"),
                            "time_slot": preferred_time,
                            "timezone": timezone
                        }
                        slots_by_day[day_key].append(slot_info)
                        suggestions.append(slot_info)

                current_date += timedelta(days=1)

            suggestions.sort(key=lambda x: x["score"], reverse=True)

            result = {"slots_by_day": {k: v for k, v in slots_by_day.items() if v}}

            if self.redis_client:
                self.redis_client.setex(cache_key, 3600, json.dumps(result))

            return result

        except Exception as e:
            logger.error(f"Error suggesting meeting times for user {user_id}: {e}", exc_info=True)
            return {"slots_by_day": {}}

    def _generate_time_slots(self, start_date: datetime, end_date: datetime, duration_minutes: int,
                           working_hours_start: str, working_hours_end: str, exclude_weekends: bool) -> List[Tuple[datetime, datetime]]:
        slots = []
        tz = start_date.tzinfo
        current_date = start_date.date()
        end_date_only = end_date.date()

        start_hour, start_minute = map(int, working_hours_start.split(':'))
        end_hour, end_minute = map(int, working_hours_end.split(':'))

        while current_date <= end_date_only:
            if exclude_weekends and current_date.weekday() not in self.WORKING_DAYS:
                current_date += timedelta(days=1)
                continue

            day_start = datetime.combine(current_date, time(start_hour, start_minute)).replace(tzinfo=tz)
            day_end = datetime.combine(current_date, time(end_hour, end_minute)).replace(tzinfo=tz)

            slot_start = day_start
            while slot_start + timedelta(minutes=duration_minutes) <= day_end:
                slot_end = slot_start + timedelta(minutes=duration_minutes)

                if slot_start > datetime.now(tz):
                    slots.append((slot_start, slot_end))

                slot_start += timedelta(minutes=15)

            current_date += timedelta(days=1)

        return slots

    def _check_slot_conflicts(self, slot_start: datetime, slot_end: datetime, user_id: str = None, buffer_minutes: int = 0) -> List[Event]:
        check_start = slot_start - timedelta(minutes=buffer_minutes)
        check_end = slot_end + timedelta(minutes=buffer_minutes)

        cache_key = f"slot_conflicts:{user_id}:{check_start.isoformat()}:{check_end.isoformat()}:{buffer_minutes}"
        if self.redis_client:
            cached_result = self.redis_client.get(cache_key)
            if cached_result:
                logger.info(f"Cache hit for slot conflicts: {cache_key}")
                return [Event.parse_raw(event) for event in json.loads(cached_result)]

        query = self.calendar_db.query(Event).filter(
            and_(
                Event.start_datetime < check_end,
                Event.end_datetime > check_start,
                Event.status.in_(["scheduled", "confirmed", "in_progress"])
            )
        )

        if user_id:
            query = query.filter(Event.user_id == user_id)

        conflicts = query.all()

        if self.redis_client:
            self.redis_client.setex(cache_key, 300, json.dumps([event.dict() for event in conflicts]))

        return conflicts

    def _calculate_time_slot_score(self, slot_datetime: datetime, preferred_time: str, day_offset: int) -> float:
        score = 100.0
        score -= day_offset * 5
        hour = slot_datetime.hour
        if 10 <= hour <= 12:
            score += 10
        elif 13 <= hour <= 15:
            score += 5
        elif hour < 10 or hour > 16:
            score -= 20
        if slot_datetime.weekday() in self.WORKING_DAYS:
            score += 10
        if 1 <= slot_datetime.weekday() <= 3:
            score += 5
        return max(0, score)

    def get_calendar_summary(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None, user_id: str = None) -> Dict[str, Any]:
        try:
            cache_key = f"calendar_summary:{user_id}:{start_date.isoformat() if start_date else 'none'}:{end_date.isoformat() if end_date else 'none'}"
            if self.redis_client:
                cached_result = self.redis_client.get(cache_key)
                if cached_result:
                    logger.info(f"Cache hit for calendar summary: {cache_key}")
                    return json.loads(cached_result)

            logger.debug(f"Fetching calendar summary for start_date={start_date}, end_date={end_date}, user_id={user_id}")

            query = self.calendar_db.query(Event)

            if start_date is not None:
                if start_date.tzinfo:
                    start_date = start_date.replace(tzinfo=None)
                query = query.filter(Event.start_datetime >= start_date)

            if end_date is not None:
                if end_date.tzinfo:
                    end_date = end_date.replace(tzinfo=None)
                query = query.filter(Event.start_datetime <= end_date)

            if user_id:
                query = query.filter(Event.user_id == user_id)

            events = query.all()

            total_events = len(events)
            total_duration = 0.0
            for event in events:
                if event.start_datetime and event.end_datetime:
                    duration = (event.end_datetime - event.start_datetime).total_seconds() / 60
                    total_duration += duration

            events_by_day = {}
            for event in events:
                if event.start_datetime:
                    day = event.start_datetime.date().isoformat()
                    if day not in events_by_day:
                        events_by_day[day] = []
                    events_by_day[day].append({
                        "id": event.id,
                        "title": event.title,
                        "date": event.start_datetime.strftime("%D %Y"),
                        "start_time": event.start_datetime.strftime("%H:%M"),
                        "duration": (
                            (event.end_datetime - event.start_datetime).total_seconds() / 60
                            if event.end_datetime and event.start_datetime
                            else 0
                        ),
                        "type": event.event_type.value if hasattr(event.event_type, 'value') else event.event_type,
                        "status": event.status.value if hasattr(event.status, 'value') else event.status,
                        "lead_id": event.lead_id,
                        "lead_name": event.lead_name,
                        "priority": event.priority.value if hasattr(event.priority, 'value') else event.priority,
                        "location": event.location
                    })

            busiest_day = max(events_by_day.keys(), key=lambda x: len(events_by_day[x])) if events_by_day else None

            summary = {
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None,
                "total_events": total_events,
                "total_duration_minutes": total_duration,
                "average_duration_minutes": total_duration / total_events if total_events > 0 else 0,
                "events_by_day": events_by_day,
                "busiest_day": busiest_day,
                "busiest_day_event_count": len(events_by_day.get(busiest_day, [])) if busiest_day else 0
            }

            if self.redis_client:
                self.redis_client.setex(cache_key, 3600, json.dumps(summary))

            return summary

        except Exception as e:
            logger.error(f"Error getting calendar summary for user {user_id}: {str(e)}", exc_info=True)
            return {
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None,
                "total_events": 0,
                "total_duration_minutes": 0,
                "average_duration_minutes": 0,
                "events_by_day": {},
                "busiest_day": None,
                "busiest_day_event_count": 0
            }