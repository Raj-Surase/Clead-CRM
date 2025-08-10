from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import uvicorn
from contextlib import asynccontextmanager
from datetime import datetime
import redis
import logging

from outreach_backend.app.database import engine, get_db, get_lead_parser_db, get_calendar_db
from outreach_backend.app.models import Base
from outreach_backend.app.routers import outreach, platforms, campaigns, conversations, leads, integration, statistics
from config.settings import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Redis connection
redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up outreach system...")
    try:
        # Create database tables
        Base.metadata.create_all(bind=engine)
        # Test Redis connection
        redis_client.ping()
        logger.info("Redis connection established successfully")
    except Exception as e:
        logger.error(f"Startup failed: {e}")
    yield
    logger.info("Shutting down outreach system...")

app = FastAPI(
    title="Outreach System API",
    description="A comprehensive outreach system for managing leads and multi-platform messaging",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(outreach.router, prefix="/outreach", tags=["outreach"])
app.include_router(platforms.router, prefix="/platforms", tags=["platforms"])
app.include_router(campaigns.router, prefix="/campaigns", tags=["campaigns"])
app.include_router(conversations.router, prefix="/conversations", tags=["conversations"])
app.include_router(leads.router, prefix="/leads", tags=["leads"])
app.include_router(integration.router, prefix="/integration", tags=["integration"])
app.include_router(statistics.router, prefix="/outreach-statistics")

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Outreach System API", "version": "1.0.0"}

@app.get("/health")
async def health_check(
    outreach_db: Session = Depends(get_db),
    lead_parser_db: Session = Depends(get_lead_parser_db),
    calendar_db: Session = Depends(get_calendar_db)
):
    """Health check endpoint"""
    try:
        # Test database connections
        outreach_db.execute("SELECT 1")
        lead_parser_db.execute("SELECT 1")
        calendar_db.execute("SELECT 1")
        redis_client.ping()
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "service": "outreach-system-api",
            "outreach_database": "healthy",
            "lead_parser_database": "healthy",
            "calendar_database": "healthy",
            "redis": "healthy"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "service": "outreach-system-api",
            "outreach_database": "unhealthy" if "outreach_db" in str(e).lower() else "healthy",
            "lead_parser_database": "unhealthy" if "lead_db" in str(e).lower() else "healthy",
            "calendar_database": "unhealthy" if "calendar_db" in str(e).lower() else "healthy",
            "redis": "unhealthy" if isinstance(e, redis.RedisError) else "healthy"
        }