# backend/app.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from agents.rag_bridge import retrieve_relevant_rules
from agents.compliance_agent import analyze_with_granite
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Transaction, ComplianceLog, datetime
import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

app = FastAPI()

# Database Setup (SQlite for local, or RDS URL)
SQLALCHEMY_DATABASE_URL = "sqlite:///./policyguard.db" 
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

class TransactionRequest(BaseModel):
    transaction_id: str
    description: str
    amount: float
    # ... other fields

@app.post("/api/analyze")
async def analyze_transaction(txn: TransactionRequest):
    # 1. Deterministic Rule Check (Fast Fail)
    # e.g., if amount > 1M and KYC is missing -> Reject immediately
    
    # 2. RAG Retrieval 
    # Convert txn to a query string, e.g., "International transfer of 50k USD to high risk country"
    query = f"{txn.description} amount {txn.amount}"
    policy_context = retrieve_relevant_rules(query)
    
    # 3. Granite Analysis (Your part)
    ai_verdict = analyze_with_granite(txn.dict(), policy_context)
    
    # 4. Save to DB (SQLAlchemy)
    db = SessionLocal()
    try:
        # Save Transaction
        db_txn = Transaction(
            transaction_id=txn.transaction_id,
            amount=txn.amount,
            description=txn.description,
            # Add other fields from txn request
            status="Processed"
        )
        db.add(db_txn)
        db.commit()

        # Save Compliance Log
        db_log = ComplianceLog(
            transaction_id=txn.transaction_id,
            verdict=ai_verdict.get("verdict"),
            risk_score=ai_verdict.get("risk_score"),
            explanation=ai_verdict.get("explanation"),
            violation_tags=ai_verdict.get("violated_rules"),
            cited_rules=policy_context # Storing the evidence context
        )
        db.add(db_log)
        db.commit()
    except Exception as e:
        print(f"DB Error: {e}")
    finally:
        db.close()
    
    return {
        "status": "success",
        "analysis": ai_verdict, # JSON from Granite
        "evidence": policy_context # Show which rules were checked
    }