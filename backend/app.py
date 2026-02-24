import os
import logging
from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any, Union
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException, Security, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel, Field

# Load Environment Variables
load_dotenv()

# --- IMPORTS ---
from database import get_db, init_db
from models import Transaction, ComplianceLog, FeedbackLoop
from services.transaction_schema import TransactionRequest
from services.zero_trust_auth import ZeroTrustAuthManager, Role
from services.audit_logger import TamperProofAuditLogger
from services.email_alerts import EmailAlertSystem
from services.hallucination_guard import HallucinationGuard
from services.policy_drift_detector import PolicyDriftDetector
from services.translation_service import TranslationService
from services.traffic_generator import TrafficGenerator
from agents.compliance_agent import analyze_transaction as ai_analyze_transaction
from services.gemini_client import get_llm_client

# Agent Imports
from agents.rule_engine import DeterministicRuleEngine
from agents.pii_masking_agent import PIIMaskingAgent
from agents.rag_bridge import retrieve_relevant_rules

# --- CONFIGURATION ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("PolicyGuard-API")

app = FastAPI(title="PolicyGuard Enterprise API")

# CORS (Enable for Frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# --- Service Instantiation (Global) ---
traffic_gen = TrafficGenerator() 
drift_detector = PolicyDriftDetector()

# Initialize Components
auth_manager = ZeroTrustAuthManager(secret_key=os.getenv("JWT_SECRET", "dev-secret-key"))
security_scheme = HTTPBearer()

# Agents & Services
pii_masker = PIIMaskingAgent()
audit_logger = TamperProofAuditLogger()
rule_engine = DeterministicRuleEngine()
email_service = EmailAlertSystem()
hallucination_guard = HallucinationGuard()
translator = TranslationService()

# 1. Add the Schema for the Chat Request
class ChatRequest(BaseModel):
    message: str

# 2. Add the System Persona for the Chatbot
CHAT_SYSTEM_PROMPT = """You are PolicyGuard's AI Compliance Assistant, an expert in financial compliance, regulations, and risk management. You specialize in:

1. **KYC (Know Your Customer)**
2. **AML (Anti-Money Laundering)**
3. **Regulatory Frameworks (RBI, PMLA, FATF)**
4. **Transaction Risk Assessment**
5. **Compliance Policies**

When responding:
- Provide accurate, practical guidance based on current regulations
- Reference specific regulatory sections when applicable
- Keep responses clear, structured, and in Markdown formatting.
If asked about a specific transaction, analyze the risk factors and provide a balanced assessment."""

class AlertActionRequest(BaseModel):
    transaction_id: str
    action: str
    notes: Optional[str] = None

# --- DATA MODELS (SCHEMAS) ---

class LoginRequest(BaseModel):
    role: str = "compliance_officer"
    email: str

class SimulationConfig(BaseModel):
    override_cash_limit: float = Field(default=None)
    hypothetical_regulation: str = Field(default=None)

class TransactionAnalysisRequest(BaseModel):
    transaction_id: str
    amount: float
    currency: str
    description: str
    transaction_type: str
    customer_id: str
    source_account: str
    destination_account: str
    simulation: Optional[bool] = False
    kyc_verified: Optional[bool] = False

class FeedbackRequest(BaseModel):
    transaction_id: str
    customer_id: str
    ai_verdict: str
    human_verdict: str
    notes: str

class TrafficSimulationRequest(BaseModel):
    scenario: str = Field(..., description="Options: compliant, non_compliant, flagged, escalated")

class TransactionResponse(BaseModel):
    transaction_id: str
    customer_name: Optional[str] = "Unknown"
    customer_id: str
    amount: float
    currency: str
    transaction_type: str
    status: str
    risk_score: float
    ai_explanation: Optional[str] = None
    created_at: datetime
    flagged_reasons: Optional[List[Any]] = [] 

    class Config:
        from_attributes = True

# --- AUTH HELPER ---

def verify_auth(credentials: HTTPAuthorizationCredentials = Security(security_scheme)):
    token = credentials.credentials
    verification = auth_manager.verify_token(token)
    
    if not verification["valid"]:
        raise HTTPException(status_code=401, detail=verification["error"])
    
    payload = verification["payload"]
    metadata = payload.get("metadata", {})
    
    return {
        "user_id": payload["user_id"],
        "role": payload["role"],
        "email": metadata.get("email", "admin@policyguard.com")
    }

# --- CORE LOGIC HELPER ---

def process_transaction_core(
    txn_data: dict, 
    db: Session, 
    user_context: Optional[dict] = None, 
    background_tasks: Optional[BackgroundTasks] = None
):
    """
    Analyzes transaction, routes to Gemini if needed, saves to DB, returns result.
    """
    # 1. Rule Engine Check
    rule_verdict = rule_engine.evaluate(txn_data)
    
    # SAFELY CONVERT TO DICT 
    if hasattr(rule_verdict, "model_dump"):
        rv = rule_verdict.model_dump()
    elif hasattr(rule_verdict, "dict"):
        rv = rule_verdict.dict()
    else:
        rv = rule_verdict if isinstance(rule_verdict, dict) else vars(rule_verdict)

    rv_risk_level = str(rv.get("risk_level", "low")).split('.')[-1].lower() 
    rv_requires_llm = rv.get("requires_llm", False)
    rv_reason = rv.get("reason", "Routine Check")
    rv_violations = rv.get("triggered_rules", [])

    desc = txn_data.get("description", "").lower()
    is_suspicious_sim = "structuring" in desc or "laundering" in desc or txn_data.get("amount", 0) > 900000

    # Default Deterministic Values
    final_verdict = "Compliant"
    risk_score = 10
    ai_explanation = f"Automated Check: {rv_reason}"
    flagged_reasons = rv_violations

    # Catch Deterministic High Risk First
    if rv_risk_level == "high" or is_suspicious_sim:
        final_verdict = "Non-Compliant"
        risk_score = 85

    # 2. 🧠 GEMINI LLM INTEGRATION
    elif rv_requires_llm:
        logger.info(f"🧠 Routing {txn_data['transaction_id']} to Gemini LLM...")
        try:
            retrieved_policies, _ = retrieve_relevant_rules(desc)
            llm_response = ai_analyze_transaction(txn_data, retrieved_policies)
            
            if llm_response.get("status") == "success":
                analysis = llm_response.get("analysis", {})
                raw_verdict = analysis.get("verdict", "manual review").lower()
                
                if raw_verdict == "compliant":
                    final_verdict = "Compliant"
                    risk_score = analysis.get("risk_score", 10)
                elif raw_verdict == "non-compliant":
                    final_verdict = "Non-Compliant"
                    risk_score = analysis.get("risk_score", 85)
                elif raw_verdict == "escalated":
                    final_verdict = "Escalated"
                    risk_score = analysis.get("risk_score", 95)
                else:
                    final_verdict = "Manual Review"
                    risk_score = analysis.get("risk_score", 50)
                    
                ai_explanation = analysis.get("explanation", "AI analysis complete.")
                flagged_reasons = analysis.get("violated_rules", [])
            else:
                raise ValueError("LLM response status was not success.")
        except Exception as e:
            logger.error(f"Gemini Integration Error: {e}")
            final_verdict = "Manual Review"
            risk_score = 100
            ai_explanation = "Gemini Analysis Failed - Escalated for human review."

    # 3. Create Transaction Record
    ts_val = txn_data.get("timestamp")
    if isinstance(ts_val, str):
        try:
            ts = datetime.fromisoformat(ts_val)
        except ValueError:
            ts = datetime.utcnow()
    else:
        ts = ts_val or datetime.utcnow()

    db_txn = Transaction(
        transaction_id=txn_data["transaction_id"],
        amount=txn_data["amount"],
        currency=txn_data["currency"],
        description=txn_data["description"],
        transaction_type=txn_data["transaction_type"],
        customer_id=txn_data["customer_id"],
        source_account=txn_data["source_account"],
        destination_account=txn_data["destination_account"],
        created_at=ts, 
        status=final_verdict.lower().replace("-", "_"),
        risk_score=risk_score,
        is_simulation=txn_data.get("simulation", False),
        ai_explanation=ai_explanation,
        flagged_reasons=flagged_reasons
    )
    db.add(db_txn)
    
    # 4. Create Compliance Log
    comp_log = ComplianceLog(
        transaction_id=txn_data["transaction_id"],
        verdict=final_verdict,
        risk_score=risk_score,
        explanation=db_txn.ai_explanation,
        violation_tags=db_txn.flagged_reasons,
        timestamp=datetime.utcnow()
    )
    db.add(comp_log)
    
    try:
        db.commit()
        db.refresh(db_txn)
        
        # 5. Log to the Tamper-Proof Audit Logger
        user_id = user_context.get("email", "system") if user_context else "system"
        audit_logger.log_compliance_decision(
            transaction_id=db_txn.transaction_id,
            verdict=final_verdict,
            risk_score=risk_score,
            explanation=ai_explanation,
            violated_rules=flagged_reasons,
            user_id=user_id
        )

        return db_txn
    except Exception as e:
        db.rollback()
        logger.error(f"Database Error: {e}")
        raise e

# --- ENDPOINTS ---

@app.on_event("startup")
def startup():
    init_db()
    logger.info("PolicyGuard System: ONLINE")

@app.get("/api/health")
def health_check():
    return {"status": "online", "system": "PolicyGuard"}

@app.post("/api/auth/login")
def login(request: LoginRequest):
    role_map = {
        "admin": Role.ADMIN,
        "compliance_officer": Role.COMPLIANCE_OFFICER,
        "auditor": Role.AUDITOR
    }
    selected_role = role_map.get(request.role, Role.COMPLIANCE_OFFICER)
    
    token = auth_manager.generate_access_token(
        user_id=f"user_{request.email.split('@')[0]}",
        role=selected_role,
        metadata={"email": request.email}
    )
    
    # Track the login action in the tamper-proof ledger
    audit_logger.log_auth_event(
        user_id=request.email,
        action="User Login",
        success=True
    )
    
    return {
        "access_token": token, 
        "token_type": "bearer",
        "user": {"email": request.email, "role": selected_role.value}
    }

@app.get("/api/transactions")
def get_transactions(limit: int = 50, offset: int = 0, db: Session = Depends(get_db)):
    return db.query(Transaction).order_by(Transaction.created_at.desc()).offset(offset).limit(limit).all()

@app.get("/api/stats")
def get_dashboard_stats(db: Session = Depends(get_db)):
    today = datetime.utcnow().date()
    today_datetime = datetime.combine(today, datetime.min.time())
    
    txns_today = db.query(Transaction).filter(Transaction.created_at >= today_datetime).count()
    total_txns = db.query(Transaction).count()
    
    compliant_count = db.query(Transaction).filter(Transaction.status == "compliant").count()
    compliance_rate = (compliant_count / total_txns * 100) if total_txns > 0 else 100.0
    
    pending_count = db.query(Transaction).filter(Transaction.status == "pending").count()
    active_alerts = db.query(Transaction).filter(Transaction.risk_score > 80).count()

    return {
        "transactions_today": txns_today,
        "compliance_rate": round(compliance_rate, 1),
        "pending_reviews": pending_count,
        "active_alerts": active_alerts,
        "total_transactions": total_txns
    }

@app.get("/api/alerts", response_model=List[TransactionResponse])
def get_alerts(
    db: Session = Depends(get_db),
    user_context: dict = Depends(verify_auth)
):
    alerts = db.query(Transaction).filter(
        (Transaction.risk_score > 70) | 
        (Transaction.status.in_(["flagged", "non_compliant", "manual_review"]))
    ).order_by(Transaction.created_at.desc()).limit(20).all()
    return alerts

@app.post("/api/alerts/action")
def handle_alert_action(
    req: AlertActionRequest,
    db: Session = Depends(get_db),
    user_context: dict = Depends(verify_auth)
):
    logger.info(f"🚨 Alert action '{req.action}' for txn {req.transaction_id} by {user_context.get('email')}")
    
    # Track the action in the tamper-proof ledger
    audit_logger._append_entry(
        event_type=f"ALERT_{req.action.upper()}",
        description=f"User {user_context.get('email')} performed '{req.action}' on alert for transaction {req.transaction_id}",
        data={
            "transaction_id": req.transaction_id,
            "user_id": user_context.get('email'),
            "action": req.action
        }
    )
    return {"status": "success", "message": f"Action {req.action} logged successfully"}

# ✅ FIXED: Map the cryptographic audit trail directly to the frontend
@app.get("/api/audit-logs")
def get_audit_logs(
    limit: int = 100,
    db: Session = Depends(get_db),
    user_context: dict = Depends(verify_auth)
):
    """Fetch structured logs from the tamper-proof ledger."""
    chain = audit_logger.get_audit_trail(limit=limit)
    
    formatted_logs = []
    for entry in chain:
        data = entry.get("data", {})
        
        # Determine the best entity identifier for the UI
        entity = data.get("transaction_id") or data.get("user_id") or "System"
        
        formatted_logs.append({
            "id": str(entry["entry_id"]),
            "action": entry["event_type"],
            "entity": str(entity),
            "timestamp": entry["timestamp"],
            "description": entry["description"]
        })
        
    # Reverse to show newest first
    return formatted_logs[::-1]

@app.post("/api/analyze")
async def analyze_transaction(
    txn: TransactionAnalysisRequest, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user_context: dict = Depends(verify_auth)
):
    return process_transaction_core(
        txn_data=txn.dict(),
        db=db, 
        user_context=user_context, 
        background_tasks=background_tasks
    )

@app.post("/api/chat")
def handle_chat(
    chat_req: ChatRequest, 
    user_context: dict = Depends(verify_auth)
):
    logger.info(f"💬 Chat message received from {user_context.get('email')}")
    try:
        gemini = get_llm_client()
        reply = gemini.invoke_chat(
            prompt=chat_req.message, 
            system_prompt=CHAT_SYSTEM_PROMPT
        )
        return {"reply": reply}
    except Exception as e:
        logger.error(f"Chat Endpoint Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to process chat request.")

@app.post("/api/simulate/drift")
async def simulate_drift():
    return drift_detector.simulate_drift()

@app.post("/api/simulate/traffic")
async def simulate_traffic(
    background_tasks: BackgroundTasks,
    request: TrafficSimulationRequest, 
    db: Session = Depends(get_db)
):
    sim_type = request.scenario
    logger.info(f"🎲 Generating AI Traffic Simulation: {sim_type}")
    
    try:
        raw_txn = traffic_gen.generate_transaction(sim_type)
    except Exception as e:
        logger.error(f"GenAI Failed: {e}")
        raw_txn = traffic_gen._get_fallback_transaction(sim_type)

    try:
        system_context = {"user_id": "system_simulation", "role": "admin"}
        saved_txn = process_transaction_core(
            txn_data=raw_txn, 
            db=db,
            user_context=system_context,
            background_tasks=background_tasks
        )
        
        return {
            "status": "success",
            "message": "Simulation Injected",
            "data": {
                "transaction_id": saved_txn.transaction_id,
                "verdict": saved_txn.status,
                "risk_score": saved_txn.risk_score,
                "explanation": saved_txn.ai_explanation
            }
        }
    except Exception as e:
        logger.error(f"Simulate Traffic Error: {e}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

@app.post("/api/feedback")
def submit_feedback(
    feedback: FeedbackRequest,
    db: Session = Depends(get_db),
    user_context: dict = Depends(verify_auth)
):
    logger.info(f"📝 Feedback received for {feedback.transaction_id}")
    
    new_feedback = FeedbackLoop(
        original_transaction_id=feedback.transaction_id,
        customer_id=feedback.customer_id,
        ai_verdict=feedback.ai_verdict,
        human_verdict=feedback.human_verdict,
        feedback_notes=feedback.notes
    )
    db.add(new_feedback)
    
    txn = db.query(Transaction).filter(Transaction.transaction_id == feedback.transaction_id).first()
    if txn:
        txn.status = feedback.human_verdict.lower().replace(" ", "_")
        if txn.ai_explanation:
            txn.ai_explanation += f" [OVERRIDE by {user_context['email']}: {feedback.notes}]"
        else:
            txn.ai_explanation = f"[OVERRIDE by {user_context['email']}: {feedback.notes}]"
    
    # Track the manual override in the tamper-proof ledger
    audit_logger._append_entry(
        event_type="HUMAN_OVERRIDE",
        description=f"User {user_context.get('email')} overrode AI verdict to '{feedback.human_verdict}' for transaction {feedback.transaction_id}. Notes: {feedback.notes}",
        data={
            "transaction_id": feedback.transaction_id,
            "user_id": user_context.get('email'),
            "old_verdict": feedback.ai_verdict,
            "new_verdict": feedback.human_verdict
        }
    )

    db.commit()
    return {"status": "Feedback recorded"}

@app.post("/api/admin/check-drift")
async def trigger_drift_check(
    simulate: bool = False,
    user_context: dict = Depends(verify_auth)
):
    user_role = user_context.get('role')
    if user_role not in [Role.ADMIN.value, Role.COMPLIANCE_OFFICER.value]:
        raise HTTPException(status_code=403, detail="Admin or Compliance Officer access required")
        
    logger.info(f"✅ Drift Check Triggered by {user_role}")
    
    # Track the admin action
    audit_logger._append_entry(
        event_type="POLICY_DRIFT_CHECK",
        description=f"User {user_context.get('email')} triggered a policy drift check (simulate={simulate})",
        data={"user_id": user_context.get('email'), "simulate": simulate}
    )

    result = drift_detector.check_for_drift(simulate=simulate)
    return result