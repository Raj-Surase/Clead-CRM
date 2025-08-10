from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config.settings import settings

# Main outreach database
engine = create_engine(
    settings.OUTREACH_DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Lead parser database (read-only access)
lead_parser_engine = create_engine(
    settings.LEAD_DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=False
)

LeadParserSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=lead_parser_engine)

# Calendar database (read-only access)
calendar_engine = create_engine(
    settings.CALENDAR_DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=False
)

CalendarSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=calendar_engine)

Base = declarative_base()

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Dependency to get lead parser database session
def get_lead_parser_db():
    db = LeadParserSessionLocal()
    try:
        yield db
    finally:
        db.close()

# Dependency to get calendar database session
def get_calendar_db():
    db = CalendarSessionLocal()
    try:
        yield db
    finally:
        db.close()

