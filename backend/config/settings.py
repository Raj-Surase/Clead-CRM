import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import validator

class Settings(BaseSettings):
    # General Application Settings
    APP_NAME: str = "Sales Pilot Unified Backend"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PORT", "8000"))

    # CORS Settings
    ALLOWED_ORIGINS: List[str] = ["*", "http://localhost:3000", "http://localhost:8080", "https://your-frontend-domain.com"]
    ALLOW_CREDENTIALS: bool = True
    ALLOW_METHODS: List[str] = ["*"]
    ALLOW_HEADERS: List[str] = ["*"]

    # Database Settings
    AUTH_DATABASE_URL: str = os.getenv("AUTH_DATABASE_URL", "mysql+pymysql://root:@localhost:3306/auth_db")
    AUTH_DATABASE_HOST: str = os.getenv("AUTH_DATABASE_HOST", "localhost")
    AUTH_DATABASE_PORT: int = int(os.getenv("AUTH_DATABASE_PORT", "3306"))
    AUTH_DATABASE_NAME: str = os.getenv("AUTH_DATABASE_NAME", "auth_db")
    AUTH_DATABASE_USER: str = os.getenv("AUTH_DATABASE_USER", "root")
    AUTH_DATABASE_PASSWORD: str = os.getenv("AUTH_DATABASE_PASSWORD", "")

    LEAD_DATABASE_URL: str = os.getenv("LEAD_DATABASE_URL", "mysql+pymysql://root:@localhost:3306/lead_parser_db")
    LEAD_DATABASE_HOST: str = os.getenv("LEAD_DATABASE_HOST", "localhost")
    LEAD_DATABASE_PORT: int = int(os.getenv("LEAD_DATABASE_PORT", "3306"))
    LEAD_DATABASE_NAME: str = os.getenv("LEAD_DATABASE_NAME", "lead_parser_db")
    LEAD_DATABASE_USER: str = os.getenv("LEAD_DATABASE_USER", "root")
    LEAD_DATABASE_PASSWORD: str = os.getenv("LEAD_DATABASE_PASSWORD", "")

    CALENDAR_DATABASE_URL: str = os.getenv("CALENDAR_DATABASE_URL", "mysql+pymysql://root:@localhost:3306/calendar_db")
    CALENDAR_DATABASE_HOST: str = os.getenv("CALENDAR_DATABASE_HOST", "localhost")
    CALENDAR_DATABASE_PORT: int = int(os.getenv("CALENDAR_DATABASE_PORT", "3306"))
    CALENDAR_DATABASE_NAME: str = os.getenv("CALENDAR_DATABASE_NAME", "calendar_db")
    CALENDAR_DATABASE_USER: str = os.getenv("CALENDAR_DATABASE_USER", "root")
    CALENDAR_DATABASE_PASSWORD: str = os.getenv("CALENDAR_DATABASE_PASSWORD", "")

    OUTREACH_DATABASE_URL: str = os.getenv("OUTREACH_DATABASE_URL", "mysql+pymysql://root:@localhost:3306/outreach_db")
    OUTREACH_DATABASE_HOST: str = os.getenv("OUTREACH_DATABASE_HOST", "localhost")
    OUTREACH_DATABASE_PORT: int = int(os.getenv("OUTREACH_DATABASE_PORT", "3306"))
    OUTREACH_DATABASE_NAME: str = os.getenv("OUTREACH_DATABASE_NAME", "outreach_db")
    OUTREACH_DATABASE_USER: str = os.getenv("OUTREACH_DATABASE_USER", "root")
    OUTREACH_DATABASE_PASSWORD: str = os.getenv("OUTREACH_DATABASE_PASSWORD", "")

    ACTIVITY_DATABASE_URL: str = os.getenv("ACTIVITY_DATABASE_URL", "mysql+pymysql://root:@localhost:3306/ai_sales_activity_tracker")
    ACTIVITY_DATABASE_HOST: str = os.getenv("ACTIVITY_DATABASE_HOST", "localhost")
    ACTIVITY_DATABASE_PORT: int = int(os.getenv("ACTIVITY_DATABASE_PORT", "3306"))
    ACTIVITY_DATABASE_NAME: str = os.getenv("ACTIVITY_DATABASE_NAME", "ai_sales_activity_tracker")
    ACTIVITY_DATABASE_USER: str = os.getenv("ACTIVITY_DATABASE_USER", "root")
    ACTIVITY_DATABASE_PASSWORD: str = os.getenv("ACTIVITY_DATABASE_PASSWORD", "")

    # Lead Parser Settings
    ALLOWED_EXTENSIONS: List[str] = os.getenv("ALLOWED_EXTENSIONS", "csv,xlsx,xls,json").split(",")
    MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", "10000000"))  # 10 MB
    UPLOAD_DIR: str = os.path.join(os.path.dirname(__file__), "..", "uploads")

    # Calendar Backend Settings
    CALENDAR_LEAD_PARSER_API_URL: str = os.getenv("CALENDAR_LEAD_PARSER_API_URL", "http://127.0.0.1:8000/leads")
    CALENDAR_DEFAULT_TIMEZONE: str = os.getenv("DEFAULT_TIMEZONE", "UTC")
    CALENDAR_SUPPORTED_TIMEZONES: List[str] = [
        "UTC", "America/New_York", "America/Los_Angeles", 
        "Europe/London", "Europe/Paris", "Asia/Tokyo"
    ]
    CALENDAR_DEFAULT_PAGE_SIZE: int = int(os.getenv("CALENDAR_DEFAULT_PAGE_SIZE", "50"))
    CALENDAR_MAX_PAGE_SIZE: int = int(os.getenv("CALENDAR_MAX_PAGE_SIZE", "100"))
    CALENDAR_MAX_EVENT_DURATION_HOURS: int = int(os.getenv("CALENDAR_MAX_EVENT_DURATION_HOURS", "24"))
    CALENDAR_DEFAULT_EVENT_DURATION_MINUTES: int = int(os.getenv("CALENDAR_DEFAULT_EVENT_DURATION_MINUTES", "60"))
    CALENDAR_MAX_ATTENDEES_PER_EVENT: int = int(os.getenv("CALENDAR_MAX_ATTENDEES_PER_EVENT", "100"))
    CALENDAR_MAX_RECURRING_INSTANCES: int = int(os.getenv("CALENDAR_MAX_RECURRING_INSTANCES", "365"))
    CALENDAR_DEFAULT_RECURRING_END_DATE_MONTHS: int = int(os.getenv("CALENDAR_DEFAULT_RECURRING_END_DATE_MONTHS", "12"))
    CALENDAR_AUTO_CREATE_EVENTS_FROM_LEADS: bool = os.getenv("CALENDAR_AUTO_CREATE_EVENTS_FROM_LEADS", "True").lower() == "true"
    CALENDAR_DEFAULT_LEAD_EVENT_DURATION_MINUTES: int = int(os.getenv("CALENDAR_DEFAULT_LEAD_EVENT_DURATION_MINUTES", "30"))
    CALENDAR_LEAD_EVENT_TYPES: List[str] = os.getenv("CALENDAR_LEAD_EVENT_TYPES", "initial_call,demo,follow_up,closing,meeting").split(",")

    # Outreach Backend Settings
    OUTREACH_API_KEY: str = os.getenv("OUTREACH_API_KEY", "")
    OUTREACH_FACEBOOK_APP_ID: Optional[str] = os.getenv("OUTREACH_FACEBOOK_APP_ID")
    OUTREACH_FACEBOOK_APP_SECRET: Optional[str] = os.getenv("OUTREACH_FACEBOOK_APP_SECRET")
    OUTREACH_INSTAGRAM_APP_ID: Optional[str] = os.getenv("OUTREACH_INSTAGRAM_APP_ID")
    OUTREACH_INSTAGRAM_APP_SECRET: Optional[str] = os.getenv("OUTREACH_INSTAGRAM_APP_SECRET")
    OUTREACH_WHATSAPP_BUSINESS_ACCOUNT_ID: Optional[str] = os.getenv("OUTREACH_WHATSAPP_BUSINESS_ACCOUNT_ID")
    OUTREACH_WHATSAPP_ACCESS_TOKEN: Optional[str] = os.getenv("OUTREACH_WHATSAPP_ACCESS_TOKEN")
    OUTREACH_RATE_LIMIT_PER_MINUTE: int = int(os.getenv("OUTREACH_RATE_LIMIT_PER_MINUTE", "100"))
    OUTREACH_WEBHOOK_SECRET: str = os.getenv("OUTREACH_WEBHOOK_SECRET", "your-webhook-secret")
    OUTREACH_ENCRYPTION_KEY: str = os.getenv("OUTREACH_ENCRYPTION_KEY", "g3nGSZarfw0IiWVWT2mYEBjBg7YbgM4oApUUo20HBDo=")

    # Activity Tracker Settings
    ACTIVITY_API_V1_STR: str = os.getenv("ACTIVITY_API_V1_STR", "/api/v1")
    ACTIVITY_TRACK_REQUEST_BODY: bool = os.getenv("ACTIVITY_TRACK_REQUEST_BODY", "True").lower() == "true"
    ACTIVITY_TRACK_RESPONSE_BODY: bool = os.getenv("ACTIVITY_TRACK_RESPONSE_BODY", "True").lower() == "true"
    ACTIVITY_MAX_BODY_SIZE: int = int(os.getenv("ACTIVITY_MAX_BODY_SIZE", "10000"))
    ACTIVITY_EXCLUDED_PATHS: List[str] = [
        "/health",
        "/api/files",
        "/api/files/{id}/status",
        "/api/leads/stats",
        "/api/leads/{id}/duplicates",
        "/api/leads/{id}/events",
        "/api/leads/{id}/events/summary",
        "/api/leads/{id}/follow-up-suggestions",
        "/api/leads/upcoming-events",
        "/api/events/upcoming",
        "/api/events/stats",
        "/api/events/{id}/attendees",
        "/api/events/{id}/conflicts",
        "/api/availability/next-slot",
        "/api/availability/suggest-times",
        "/api/calendar/summary",
        "/leads/statistics-overview",
        "/leads",
        "/leads/{id}",
        "/leads/search/",
        "/leads/group/{field}",
        "/leads/filters/options",
        "/leads/{id}/outreach-history",
        "/platforms/user/{id}/connected",
        "/platforms/user/{id}/available",
        "/platforms/{id}/auth-url/{user_id}",
        "/outreach/messages/{id}",
        "/outreach/messages",
        "/conversations/{id}",
        "/conversations/lead/{id}",
        "/conversations/messages/{id}",
        "/integration/sync-status/{id}",
        "/integration/sync-history",
        "/outreach-statistics/overall"
    ]

    # Security Settings (shared across modules)
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here-change-in-production")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

    # Redis Settings
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # Email Settings
    EMAIL_HOST: str = os.getenv("EMAIL_HOST", "smtp.gmail.com")
    EMAIL_PORT: int = int(os.getenv("EMAIL_PORT", "587"))
    EMAIL_USERNAME: Optional[str] = os.getenv("EMAIL_USERNAME")
    EMAIL_PASSWORD: Optional[str] = os.getenv("EMAIL_PASSWORD")
    EMAIL_FROM: Optional[str] = os.getenv("EMAIL_FROM")
    EMAIL_USE_TLS: bool = os.getenv("EMAIL_USE_TLS", "True").lower() == "true"

    # SMS Configuration
    TWILIO_ACCOUNT_SID: Optional[str] = os.getenv("TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN: Optional[str] = os.getenv("TWILIO_AUTH_TOKEN")
    TWILIO_PHONE_NUMBER: Optional[str] = os.getenv("TWILIO_PHONE_NUMBER")

    encryption_key: str = "g3nGSZarfw0IiWVWT2mYEBjBg7YbgM4oApUUo20HBDo="

    @validator('ALLOWED_ORIGINS', 'CALENDAR_SUPPORTED_TIMEZONES', 'ALLOWED_EXTENSIONS', 'CALENDAR_LEAD_EVENT_TYPES', pre=True)
    def parse_list(cls, v):
        if isinstance(v, str):
            return [item.strip() for item in v.split(',')]
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

settings = Settings()

# Ensure upload directory exists
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)