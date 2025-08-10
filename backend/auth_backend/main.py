"""
Authentication backend main application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import logging
from datetime import datetime
from sqlalchemy import text
import redis

from auth_backend.app.routes import auth_router, user_router, onboarding_router
from auth_backend.app.middleware.rate_limiter import RateLimitMiddleware
from auth_backend.database.connection import engine, Base
from calendar_backend.app.database.connection import get_database_health, test_all_connections
from config.settings import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Redis connection
redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)

# Create FastAPI app
app = FastAPI(
    title="Sales Pilot Authentication API",
    description="Authentication and onboarding system for Sales Pilot",
    version="1.0.0",
    docs_url="/auth/docs",
    redoc_url="/auth/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add rate limiting middleware
# app.add_middleware(RateLimitMiddleware)

# Create uploads directory for profile pictures
uploads_dir = os.path.join(os.getcwd(), "uploads")
os.makedirs(uploads_dir, exist_ok=True)

# Mount static files for profile pictures
if os.path.exists(uploads_dir):
    app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")

# Include routers
app.include_router(auth_router)
app.include_router(user_router, prefix="/user")
app.include_router(onboarding_router, prefix="/onboarding")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Sales Pilot Authentication API",
        "version": "1.0.0",
        "docs": "/auth/docs",
        "endpoints": {
            "authentication": "/auth",
            "user_profile": "/auth/profile",
            "company_profile": "/auth/company",
            "onboarding": "/auth/onboarding"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        db_health = get_database_health()
        connections = test_all_connections()
        all_healthy = all("healthy" in status for status in db_health.values()) and connections["all_connected"]
        
        # Test Redis connection
        redis_client.ping()
        
        return {
            "status": "healthy" if all_healthy else "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": settings.APP_VERSION,
            "service": "authentication",
            "database": db_health,
            "redis": "healthy",
            "integrations": {
                "lead_parser": "configured" if settings.LEAD_DATABASE_URL else "not_configured"
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": settings.APP_VERSION,
            "service": "authentication",
            "database": {"error": str(e)} if not isinstance(e, redis.RedisError) else db_health,
            "redis": "unhealthy" if isinstance(e, redis.RedisError) else "healthy",
            "integrations": {"error": str(e)}
        }

@app.on_event("startup")
async def startup_event():
    """Startup event handler"""
    logger.info("Starting Authentication API...")
    
    # Create database tables if they don't exist
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created/verified successfully")
        
        # Test Redis connection
        redis_client.ping()
        logger.info("Redis connection established successfully")
    except Exception as e:
        logger.error(f"Startup failed: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler"""
    logger.info("Shutting down Authentication API...")