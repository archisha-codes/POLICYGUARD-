# backend/app.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from agents.rag_bridge import retrieve_relevant_rules
from agents.compliance_agent import analyze_with_granite
# import database session logic here

app = FastAPI()

class TransactionRequest(BaseModel):
    transaction_id: str
    description: str
    amount: float
    # ... other fields

@app.post("/api/analyze")
async def analyze_transaction(txn: TransactionRequest):
    # 1. Deterministic Rule Check (Fast Fail)
    # e.g., if amount > 1M and KYC is missing -> Reject immediately
    
    # 2. RAG Retrieval (Archisha's part)
    # Convert txn to a query string, e.g., "International transfer of 50k USD to high risk country"
    query = f"{txn.description} amount {txn.amount}"
    policy_context = retrieve_relevant_rules(query)
    
    # 3. Granite Analysis (Your part)
    ai_verdict = analyze_with_granite(txn.dict(), policy_context)
    
    # 4. Save to DB (SQLAlchemy)
    # ... save_to_db(txn, ai_verdict) ...
    
    return {
        "status": "success",
        "analysis": ai_verdict, # JSON from Granite
        "evidence": policy_context # Show which rules were checked
    }