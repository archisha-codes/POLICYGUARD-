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
RAW_DATABASE_URL = os.getenv("DATABASE_URL")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_NAME = os.getenv("DB_NAME", "policyguard")
DB_ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
USE_SQLITE = os.getenv("USE_SQLITE", "True").lower() == "true"

# Determine Connection String
if RAW_DATABASE_URL:
    # Standard DATABASE_URL (Render Postgres, Supabase, Neon)
    DATABASE_URL = RAW_DATABASE_URL.replace("postgres://", "postgresql://", 1) if RAW_DATABASE_URL.startswith("postgres://") else RAW_DATABASE_URL
    logger.info(f"Using DATABASE_URL environment variable for connection.")
    engine = create_engine(
        DATABASE_URL,
        poolclass=QueuePool,
        pool_size=10,
        max_overflow=20,
        pool_timeout=30,
        pool_recycle=3600
    )
elif USE_SQLITE or not os.getenv("DB_HOST"):
    # Development / Standalone Cloud Demo: Use Local SQLite
    DATABASE_URL = "sqlite:///./policyguard.db"
    logger.info(f"Using Local SQLite Database: {DATABASE_URL}")
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False} # Required for SQLite with FastAPI
    )
elif DB_ENVIRONMENT == "production" and os.getenv("DB_HOST"):
    # Production with external PostgreSQL instance (AWS RDS / External Postgres)
    DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    engine = create_engine(
        DATABASE_URL,
        poolclass=QueuePool,
        pool_size=10,
        max_overflow=20,
        pool_timeout=30,
        pool_recycle=3600
    )
else:
    # Local SQLite Fallback
    DATABASE_URL = "sqlite:///./policyguard.db"
    logger.info(f"Using Local SQLite Database: {DATABASE_URL}")
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}
    )

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
    """Initialize tables and seed initial transactions if empty"""
    try:
        from models import Base, Transaction
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized successfully.")

        db = SessionLocal()
        try:
            # Ensure PMLA Structuring sample transaction 2 exists for rich demo data
            existing_struct2 = db.query(Transaction).filter_by(transaction_id="TXN_STRUCT_002").first()
            if not existing_struct2:
                struct2 = Transaction(
                    transaction_id="TXN_STRUCT_002",
                    customer_id="CUST_STRUCT_02",
                    customer_name="Structuring Subject B",
                    amount=9950.0,
                    currency="USD",
                    transaction_type="wire_transfer",
                    description="Sequential cash deposits split under PMLA threshold",
                    status="non_compliant",
                    risk_score=88,
                    flagged_reasons=["STRUCTURING_PATTERN"],
                    ai_explanation="Multiple sequential deposits below $10,000 reporting threshold detected."
                )
                db.add(struct2)
                db.commit()
                logger.info("Seeded TXN_STRUCT_002 for PMLA Structuring demo.")
        except Exception as se:
            db.rollback()
            logger.warning(f"Seed transaction failed: {se}")
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"Database initialization note: {e}")