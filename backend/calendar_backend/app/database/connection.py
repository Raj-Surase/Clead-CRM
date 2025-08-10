from datetime import datetime
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from typing import Generator
import logging
from sqlalchemy import text

from config.settings import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Calendar Database Configuration
calendar_engine = create_engine(
    settings.CALENDAR_DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=settings.DEBUG
)

CalendarSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=calendar_engine)
CalendarBase = declarative_base()

# Lead Parser Database Configuration (for integration)
lead_parser_engine = create_engine(
    settings.LEAD_DATABASE_URL,
    poolclass=QueuePool,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=settings.DEBUG
)

LeadParserSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=lead_parser_engine)
LeadParserBase = declarative_base()

# Metadata for database introspection
calendar_metadata = MetaData()
lead_parser_metadata = MetaData()

def get_calendar_db() -> Generator[Session, None, None]:
    """
    Dependency to get calendar database session
    """
    db = CalendarSessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def get_lead_parser_db() -> Generator[Session, None, None]:
    """
    Dependency to get lead parser database session
    """
    db = LeadParserSessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Lead parser database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def create_calendar_tables():
    """
    Create all calendar database tables
    """
    try:
        CalendarBase.metadata.create_all(bind=calendar_engine)
        logger.info("Calendar database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating calendar database tables: {e}")
        raise

def create_lead_parser_tables():
    """
    Create all lead parser database tables (if needed)
    """
    try:
        LeadParserBase.metadata.create_all(bind=lead_parser_engine)
        logger.info("Lead parser database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating lead parser database tables: {e}")
        raise

def test_calendar_connection():
    """
    Test calendar database connection
    """
    try:
        with calendar_engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            logger.info("Calendar database connection successful")
            return True
    except Exception as e:
        logger.error(f"Calendar database connection failed: {e}")
        return False

def test_lead_parser_connection():
    """
    Test lead parser database connection
    """
    try:
        with lead_parser_engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            logger.info("Lead parser database connection successful")
            return True
    except Exception as e:
        logger.error(f"Lead parser database connection failed: {e}")
        return False

def test_all_connections():
    """
    Test all database connections
    """
    calendar_ok = test_calendar_connection()
    lead_parser_ok = test_lead_parser_connection()
    
    return {
        "calendar_db": calendar_ok,
        "lead_parser_db": lead_parser_ok,
        "all_connected": calendar_ok and lead_parser_ok
    }

def get_database_health():
    """
    Get database health status
    """
    try:
        # Test calendar database
        with calendar_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        calendar_status = "healthy"
    except Exception as e:
        calendar_status = f"unhealthy: {str(e)}"
    
    try:
        # Test lead parser database
        with lead_parser_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        lead_parser_status = "healthy"
    except Exception as e:
        lead_parser_status = f"unhealthy: {str(e)}"
    
    return {
        "calendar_database": calendar_status,
        "lead_parser_database": lead_parser_status,
        "timestamp": datetime.utcnow().isoformat()
    }

# Initialize databases on import
if __name__ == "__main__":
    print("Testing database connections...")
    connections = test_all_connections()
    print(f"Connection status: {connections}")
    
    if connections["all_connected"]:
        print("Creating database tables...")
        create_calendar_tables()
        print("Database setup completed successfully!")
    else:
        print("Database connection failed. Please check your configuration.")