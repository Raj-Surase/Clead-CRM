"""
Database migration script to create authentication tables
"""
from sqlalchemy import text
from auth_backend.database.connection import engine, Base
from auth_backend.app.models import User, UserProfile, CompanyProfile, RefreshToken


def create_database():
    """Create the authentication database if it doesn't exist"""
    # Extract database name from URL
    database_url = str(engine.url)
    if "auth_db" in database_url:
        # Create database
        temp_engine = engine.execution_options(isolation_level="AUTOCOMMIT")
        with temp_engine.connect() as conn:
            try:
                conn.execute(text("CREATE DATABASE IF NOT EXISTS auth_db"))
                print("Database 'auth_db' created successfully")
            except Exception as e:
                print(f"Database creation error (may already exist): {e}")


def create_tables():
    """Create all authentication tables"""
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("All authentication tables created successfully")
        
        # Print table information
        with engine.connect() as conn:
            result = conn.execute(text("SHOW TABLES"))
            tables = [row[0] for row in result]
            print(f"Created tables: {tables}")
            
    except Exception as e:
        print(f"Error creating tables: {e}")
        raise


def drop_tables():
    """Drop all authentication tables (use with caution)"""
    try:
        Base.metadata.drop_all(bind=engine)
        print("All authentication tables dropped successfully")
    except Exception as e:
        print(f"Error dropping tables: {e}")
        raise


if __name__ == "__main__":
    print("Creating authentication database and tables...")
    create_database()
    create_tables()
    print("Migration completed successfully!")

