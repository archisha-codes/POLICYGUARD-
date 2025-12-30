# backend/models.py
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, ForeignKey
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String, unique=True, index=True)
    amount = Column(Float)
    currency = Column(String)
    sender_id = Column(String)
    receiver_id = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Status: Pending, Approved, Rejected, Flagged
    status = Column(String, default="Pending") 

class ComplianceLog(Base):
    __tablename__ = "compliance_logs"
    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String, ForeignKey("transactions.transaction_id"))
    
    # AI Output
    risk_score = Column(Integer)  # 0-100
    verdict = Column(String)      # "Compliant" or "Non-Compliant"
    violation_tags = Column(JSON) # List of rules violated e.g. ["KYC-01", "AML-03"]
    explanation = Column(String)  # Granite's reasoning
    
    # RAG Evidence
    cited_rules = Column(JSON)    # The chunks retrieved from OpenSearch
    timestamp = Column(DateTime, default=datetime.utcnow)