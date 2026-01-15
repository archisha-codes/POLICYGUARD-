# backend/database.py
# PostgreSQL (RDS) Integration with Connection Pooling
# Provides database session management for transaction persistence

import os
from typing import Generator
from sqlalchemy import create_engine, pool, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
import logging

logger = logging.getLogger(__name__)

# Database Configuration
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_NAME = os.getenv("DB_NAME", "policyguard")
DB_ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# RDS Connection String (PostgreSQL)
if DB_ENVIRONMENT == "production":
    # RDS Production Database
    DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
else:
    # Local Development Database
    DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


class DatabaseConfig:
    """Database connection and pooling configuration"""
    
    # Connection Pool Settings (for high concurrency)
    POOL_SIZE = 10  # Number of connections to keep in pool
    MAX_OVERFLOW = 20  # Additional connections if pool exhausted
    POOL_TIMEOUT = 30  # Timeout waiting for connection
    POOL_RECYCLE = 3600  # Recycle connections after 1 hour
    
    # Performance Settings
    ECHO_SQL = os.getenv("ECHO_SQL", "false").lower() == "true"
    CONNECT_ARGS = {
        "connect_timeout": 10,
        "application_name": "policyguard_backend",
    }


# Create SQLAlchemy Engine with Connection Pooling
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=DatabaseConfig.POOL_SIZE,
    max_overflow=DatabaseConfig.MAX_OVERFLOW,
    pool_timeout=DatabaseConfig.POOL_TIMEOUT,
    pool_recycle=DatabaseConfig.POOL_RECYCLE,
    echo=DatabaseConfig.ECHO_SQL,
    connect_args=DatabaseConfig.CONNECT_ARGS,
)


# Connection Pool Event Listeners (for monitoring)
@event.listens_for(pool.Pool, "connect")
def receive_connect(dbapi_connection, connection_record):
    """Log successful connections"""
    logger.debug(f"Database connection established: {dbapi_connection}")


@event.listens_for(pool.Pool, "checkout")
def receive_checkout(dbapi_connection, connection_record, connection_proxy):
    """Log connection checkouts from pool"""
    logger.debug(f"Connection checked out from pool")


@event.listens_for(pool.Pool, "checkin")
def receive_checkin(dbapi_connection, connection_record):
    """Log connection returns to pool"""
    logger.debug(f"Connection returned to pool")


@event.listens_for(pool.Pool, "detach")
def receive_detach(dbapi_connection, connection_record):
    """Log connection detachments (errors/timeout)"""
    logger.warning(f"Connection detached from pool (error/timeout)")


# Session Factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency for FastAPI to inject database sessions.
    Automatically closes session after request.
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


def init_db():
    """Initialize database tables (creates them if they don't exist)"""
    try:
        from models import Base  # Import all models
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        raise


def health_check() -> bool:
    """
    Check if database connection is healthy.
    Used for liveness/readiness probes.
    """
    try:
        with engine.connect() as connection:
            result = connection.execute("SELECT 1")
            return result.fetchone() is not None
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        return False


def get_pool_stats() -> dict:
    """
    Return connection pool statistics for monitoring.
    """
    pool_obj = engine.pool
    return {
        "pool_size": DatabaseConfig.POOL_SIZE,
        "max_overflow": DatabaseConfig.MAX_OVERFLOW,
        "checked_out_connections": pool_obj.checkedout() if hasattr(pool_obj, "checkedout") else "N/A",
        "pool_id": id(pool_obj),
    }
