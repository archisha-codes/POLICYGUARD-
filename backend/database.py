# backend/database.py
import os
import logging
from typing import Generator
from sqlalchemy import create_engine, event, pool
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from dotenv import load_dotenv

# Load env vars immediately to ensure they are available
load_dotenv()

logger = logging.getLogger(__name__)

# Configuration
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_NAME = os.getenv("DB_NAME", "policyguard")
DB_ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
USE_SQLITE = os.getenv("USE_SQLITE", "True").lower() == "true"

# Connection Logic
if DB_ENVIRONMENT == "production":
    # Production: Use AWS RDS (PostgreSQL)
    DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    engine = create_engine(
        DATABASE_URL,
        poolclass=QueuePool,
        pool_size=10,
        max_overflow=20,
        pool_timeout=30,
        pool_recycle=3600
    )
elif USE_SQLITE:
    # Development: Use Local SQLite (No installation required)
    DATABASE_URL = "sqlite:///./policyguard.db"
    logger.info(f"Using Local SQLite Database: {DATABASE_URL}")
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False} # Required for SQLite with FastAPI
    )
else:
    # Development: Explicit Local PostgreSQL
    DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Generator[Session, None, None]:
    """Dependency for FastAPI to get DB session"""
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def init_db():
    """Initialize tables"""
    try:
        from models import Base
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        # Don't raise here in dev to prevent crash loops if DB is flaky
        if DB_ENVIRONMENT == "production":
            raise
# backend/database.py
import os
import logging
from typing import Generator
from sqlalchemy import create_engine, event, pool
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from dotenv import load_dotenv

# Load env vars immediately to ensure they are available
load_dotenv()

logger = logging.getLogger(__name__)

# Configuration
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_NAME = os.getenv("DB_NAME", "policyguard")
DB_ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
USE_SQLITE = os.getenv("USE_SQLITE", "True").lower() == "true"

# Connection Logic
if DB_ENVIRONMENT == "production":
    # Production: Use AWS RDS (PostgreSQL)
    DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    engine = create_engine(
        DATABASE_URL,
        poolclass=QueuePool,
        pool_size=10,
        max_overflow=20,
        pool_timeout=30,
        pool_recycle=3600
    )
elif USE_SQLITE:
    # Development: Use Local SQLite (No installation required)
    DATABASE_URL = "sqlite:///./policyguard.db"
    logger.info(f"Using Local SQLite Database: {DATABASE_URL}")
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False} # Required for SQLite with FastAPI
    )
else:
    # Development: Explicit Local PostgreSQL
    DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Generator[Session, None, None]:
    """Dependency for FastAPI to get DB session"""
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def init_db():
    """Initialize tables"""
    try:
        from models import Base
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        # Don't raise here in dev to prevent crash loops if DB is flaky
        if DB_ENVIRONMENT == "production":
            raise