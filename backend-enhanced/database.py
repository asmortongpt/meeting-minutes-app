"""
Database connection and session management
Production-ready with connection pooling
"""
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
import logging

from config import settings

logger = logging.getLogger(__name__)

# Create database engine with connection pooling
engine = create_engine(
    settings.DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,  # Number of permanent connections
    max_overflow=40,  # Additional connections when pool is exhausted
    pool_pre_ping=True,  # Test connections before using
    pool_recycle=3600,  # Recycle connections after 1 hour
    echo=settings.DEBUG,  # Log SQL queries in debug mode
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

# Connection event listeners
@event.listens_for(engine, "connect")
def receive_connect(dbapi_conn, connection_record):
    """Configure connection on connect"""
    logger.info("Database connection established")

@event.listens_for(engine, "checkout")
def receive_checkout(dbapi_conn, connection_record, connection_proxy):
    """Check connection on checkout from pool"""
    pass

# Database initialization
def init_db():
    """Initialize database - create all tables"""
    logger.info("Initializing database...")

    # Import all models to ensure they're registered
    from models import (
        User, Role, UserRole, Meeting, MeetingVersion,
        AgendaItem, Attendee, ActionItem, Screenshot,
        Tag, MeetingTag, AuditLog, Integration
    )

    # Create all tables
    Base.metadata.create_all(bind=engine)

    logger.info("Database initialized successfully")

# Database session dependency for FastAPI
def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Health check
def check_db_health() -> bool:
    """Check if database is healthy"""
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False
