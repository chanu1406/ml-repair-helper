"""
Database session management
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from backend.app.database.models import Base

# Database URL - defaults to SQLite, can be overridden with env var
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./vehicle_data.db"  # Local SQLite database
)

# For PostgreSQL in production, use:
# DATABASE_URL = "postgresql://user:password@localhost/vehicle_valuation"

# Create engine
# For SQLite, we need check_same_thread=False
connect_args = {"check_same_thread": False} if "sqlite" in DATABASE_URL else {}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    echo=False  # Set to True for SQL query logging
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """
    Initialize database - create all tables
    Call this on application startup
    """
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully")


def get_db() -> Generator[Session, None, None]:
    """
    Dependency for FastAPI to get database session

    Usage in FastAPI:
        @app.get("/endpoint")
        def endpoint(db: Session = Depends(get_db)):
            # use db here
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def drop_all_tables():
    """
    Drop all tables - USE WITH CAUTION!
    Only for development/testing
    """
    Base.metadata.drop_all(bind=engine)
    print("All tables dropped")


def reset_db():
    """
    Reset database - drop and recreate all tables
    Only for development/testing
    """
    drop_all_tables()
    init_db()
    print("Database reset complete")


# Helper function to get a standalone session
def get_session() -> Session:
    """Get a standalone database session (not for FastAPI dependency)"""
    return SessionLocal()
