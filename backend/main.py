from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import logging
import uvicorn
from contextlib import asynccontextmanager
from sqlalchemy import text

from auth_backend.main import app as auth_app
from auth_backend.app.middleware.auth_middleware import AuthMiddleware
from lead_backend.main import app as lead_app
from calendar_backend.main import app as calendar_app
from outreach_backend.main import app as outreach_app
from config.settings import settings  # Use root config
from lead_backend.app.database.connection import engine as lead_engine
from calendar_backend.app.database.connection import calendar_engine as calendar_engine
from outreach_backend.app.database import engine as outreach_engine
from auth_backend.database.connection import engine as auth_engine

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Unified Sales Pilot Backend")
    yield
    logger.info("Shutting down Unified Sales Pilot Backend")

app = FastAPI(
    title="Sales Pilot Unified Backend",
    description="Unified API for Lead Parsing, Calendar Management and Outreach System",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

app.add_middleware(AuthMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount sub-applications
app.mount("/auth", auth_app)
app.mount("/leads", lead_app)
app.mount("/calendar", calendar_app)
app.mount("/outreach/api/v1", outreach_app)

@app.get("/")
async def root():
    return {
        "message": "Sales Pilot Unified Backend API with Authentication",
        "version": "1.0.0",
        "services": {
            "authentication": "/auth",
            "lead_parser": "/leads",
            "calendar": "/calendar",
            "outreach": "/outreach/api/v1",
        }
    }

@app.get("/health")
async def health_check():
    services_status = {
        "lead_parser": "healthy",
        "calendar": "healthy",
        "outreach": "healthy",
        "auth": "healthy"
    }
    try:
        # Check database connections
        with lead_engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        with calendar_engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        with outreach_engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        with auth_engine.connect() as connection:
            connection.execute(text("SELECT 1"))  # Verify route_mappings
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "services": services_status
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "error": str(e),
            "services": services_status
        }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )