# backend/models.py
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, ForeignKey, Boolean, Text
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()

class Transaction(Base):
    __tablename__ = "transactions"
    
    # Primary Keys & IDs
    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String, unique=True, index=True)
    
    # Transaction Details
    customer_id = Column(String, index=True)
    customer_name = Column(String, nullable=True)
    amount = Column(Float)
    currency = Column(String)
    transaction_type = Column(String, nullable=True)
    description = Column(String, nullable=True)
    source_account = Column(String, nullable=True)
    destination_account = Column(String, nullable=True)
    
    # Compliance Status
    status = Column(String, default="pending")  # compliant, non_compliant, flagged
    risk_score = Column(Integer, default=0)     # 0-100
    
    # Analysis Data
    flagged_reasons = Column(JSON, nullable=True)
    ai_explanation = Column(Text, nullable=True)
    
    # Simulation Flag
    is_simulation = Column(Boolean, default=False)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)

class ComplianceLog(Base):
    __tablename__ = "compliance_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String, ForeignKey("transactions.transaction_id"))
    
    verdict = Column(String)
    risk_score = Column(Integer)
    explanation = Column(Text)
    violation_tags = Column(JSON)
    
    timestamp = Column(DateTime, default=datetime.utcnow)

class FeedbackLoop(Base):
    __tablename__ = "feedback_loop"
    
    id = Column(Integer, primary_key=True, index=True)
    original_transaction_id = Column(String, ForeignKey("transactions.transaction_id"))
    customer_id = Column(String, index=True)
    
    ai_verdict = Column(String)
    human_verdict = Column(String)
    feedback_notes = Column(Text)
    
    timestamp = Column(DateTime, default=datetime.utcnow)