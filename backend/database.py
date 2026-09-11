# backend/database.py
import os
import logging
from typing import Generator
from sqlalchemy import create_engine, event, pool, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from dotenv import load_dotenv

# Load env vars immediately to ensure they are available
load_dotenv()

logger = logging.getLogger(__name__)

# Configuration
RAW_DATABASE_URL = os.getenv("DATABASE_URL")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_NAME = os.getenv("DB_NAME", "policyguard")
DB_ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

def create_db_engine():
    raw_url = os.getenv("DATABASE_URL")
    use_sqlite_val = os.getenv("USE_SQLITE", "true").strip().lower()
    use_sqlite = use_sqlite_val == "true"
    host = os.getenv("DB_HOST")
    
    if raw_url:
        # Standard DATABASE_URL (Render Postgres, Supabase, Neon)
        url = raw_url.replace("postgres://", "postgresql://", 1) if raw_url.startswith("postgres://") else raw_url
        logger.info("Using DATABASE_URL environment variable for database connection.")
        return create_engine(
            url,
            poolclass=QueuePool,
            pool_size=10,
            max_overflow=20,
            pool_timeout=30,
            pool_recycle=3600
        )
    elif use_sqlite or not host or host in ("localhost", "127.0.0.1", "::1"):
        # Local Development or Standalone Cloud Demo: Use Local SQLite
        url = "sqlite:///./policyguard.db"
        logger.info(f"Using Local SQLite Database: {url}")
        return create_engine(
            url,
            connect_args={"check_same_thread": False}
        )
    else:
        # Explicit external host specified
        url = f"postgresql://{DB_USER}:{DB_PASSWORD}@{host}:{DB_PORT}/{DB_NAME}"
        logger.info(f"Using external PostgreSQL host: {host}:{DB_PORT}")
        return create_engine(
            url,
            poolclass=QueuePool,
            pool_size=10,
            max_overflow=20,
            pool_timeout=30,
            pool_recycle=3600
        )

engine = create_db_engine()
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
    """Initialize tables and seed initial transactions if empty with SQLite fallback."""
    global engine, SessionLocal
    
    db_initialized = False
    
    # Try primary engine first
    try:
        from models import Base, Transaction
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        Base.metadata.create_all(bind=engine)
        logger.info("Primary database initialized successfully.")
        db_initialized = True
    except Exception as primary_err:
        logger.warning(f"Primary database connection failed ({primary_err}). Falling back to local SQLite database.")
        try:
            sqlite_url = "sqlite:///./policyguard.db"
            engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})
            SessionLocal.configure(bind=engine)
            from models import Base, Transaction
            Base.metadata.create_all(bind=engine)
            logger.info("Local SQLite database initialized successfully via fallback.")
            db_initialized = True
        except Exception as fallback_err:
            logger.error(f"Fallback SQLite initialization error: {fallback_err}")
            db_initialized = False

    if db_initialized:
        try:
            db = SessionLocal()
            try:
                from models import Transaction
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
        except Exception as session_err:
            logger.warning(f"Failed to open DB session for seeding: {session_err}")
