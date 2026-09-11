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
    Analyzes transaction with PII masking, deterministic rules, local RAG context, and DB logging.
    """
    # 0. PII Detection & Masking BEFORE Sending to AI or Storing
    masked_txn = pii_masker.mask_transaction(txn_data)

    # 1. Rule Engine Check
    rule_verdict = rule_engine.evaluate(masked_txn)
    
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

    desc = masked_txn.get("description", "").lower()
    is_suspicious_sim = "structuring" in desc or "laundering" in desc or masked_txn.get("amount", 0) > 900000

    # Default Deterministic Values
    final_verdict = "Compliant"
    risk_score = 10
    ai_explanation = f"Automated Rule Check: {rv_reason}"
    flagged_reasons = rv_violations

    # Retrieve RAG Evidence
    retrieved_policies, citations = retrieve_relevant_rules(desc)

    # Catch Deterministic High Risk First
    if rv_risk_level == "high" or is_suspicious_sim:
        final_verdict = "Non-Compliant"
        risk_score = 85
        ai_explanation = f"High Risk Flagged by Deterministic Rules: {rv_reason}"

    # 2. AI CO-PILOT / LOCAL RULE-GROUNDED ANALYSIS
    else:
        logger.info(f"🧠 Evaluating transaction {masked_txn.get('transaction_id')} via Compliance Co-Pilot...")
        try:
            llm_response = ai_analyze_transaction(masked_txn, retrieved_policies)
            
            if llm_response.get("status") == "success":
                analysis = llm_response.get("analysis", {})
                raw_verdict = str(analysis.get("verdict", "manual review")).lower()
                
                if raw_verdict in ["compliant", "approved"]:
                    final_verdict = "Compliant"
                    risk_score = analysis.get("risk_score", 10)
                elif raw_verdict in ["non-compliant", "non_compliant", "rejected", "flagged"]:
                    final_verdict = "Non-Compliant"
                    risk_score = analysis.get("risk_score", 85)
                elif raw_verdict == "escalated":
                    final_verdict = "Escalated"
                    risk_score = analysis.get("risk_score", 95)
                else:
                    final_verdict = "Manual Review"
                    risk_score = analysis.get("risk_score", 50)
                    
                ai_explanation = analysis.get("explanation", "Compliance analysis complete.")
                flagged_reasons = analysis.get("violated_rules", [])
        except Exception as e:
            logger.error(f"Co-Pilot Analysis Error: {e}")
            final_verdict = "Manual Review"
            risk_score = 65
            ai_explanation = f"Rule-Grounded Check: Manual review required due to evaluation exception ({str(e)})"

    # 3. Create Transaction Record
    ts_val = masked_txn.get("timestamp")
    if isinstance(ts_val, str):
        try:
            ts = datetime.fromisoformat(ts_val)
        except ValueError:
            ts = datetime.utcnow()
    else:
        ts = ts_val or datetime.utcnow()

    # 3. Create or Update Transaction Record (Upsert Pattern)
    existing_txn = db.query(Transaction).filter_by(transaction_id=masked_txn["transaction_id"]).first()
    if existing_txn:
        existing_txn.amount = masked_txn["amount"]
        existing_txn.currency = masked_txn.get("currency", "INR")
        existing_txn.description = masked_txn.get("description", "")
        existing_txn.transaction_type = masked_txn.get("transaction_type", "transfer")
        existing_txn.customer_id = masked_txn.get("customer_id", "CUST_001")
        existing_txn.source_account = masked_txn.get("source_account", "ACC_SRC")
        existing_txn.destination_account = masked_txn.get("destination_account", "ACC_DEST")
        existing_txn.status = final_verdict.lower().replace("-", "_")
        existing_txn.risk_score = risk_score
        existing_txn.ai_explanation = ai_explanation
        existing_txn.flagged_reasons = flagged_reasons
        existing_txn.created_at = ts
        db_txn = existing_txn
    else:
        db_txn = Transaction(
            transaction_id=masked_txn["transaction_id"],
            amount=masked_txn["amount"],
            currency=masked_txn.get("currency", "INR"),
            description=masked_txn.get("description", ""),
            transaction_type=masked_txn.get("transaction_type", "transfer"),
            customer_id=masked_txn.get("customer_id", "CUST_001"),
            source_account=masked_txn.get("source_account", "ACC_SRC"),
            destination_account=masked_txn.get("destination_account", "ACC_DEST"),
            created_at=ts, 
            status=final_verdict.lower().replace("-", "_"),
            risk_score=risk_score,
            is_simulation=masked_txn.get("simulation", False),
            ai_explanation=ai_explanation,
            flagged_reasons=flagged_reasons
        )
        db.add(db_txn)
    
    # 4. Create Compliance Log
    comp_log = ComplianceLog(
        transaction_id=masked_txn["transaction_id"],
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
    try:
        init_db()
        logger.info("PolicyGuard System: ONLINE")
    except Exception as e:
        logger.error(f"Database initialization error on startup: {e}")
        logger.info("PolicyGuard System: ONLINE (Degraded/Offline DB mode)")

@app.get("/")
@app.get("/health")
@app.get("/api/health")
def health_check():
    return {"status": "ok", "system": "PolicyGuard", "timestamp": datetime.utcnow().isoformat()}

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
    active_alerts = db.query(Transaction).filter(Transaction.risk_score > 70).count()

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
        entity = data.get("transaction_id") or data.get("user_id") or "System"
        
        formatted_logs.append({
            "id": str(entry["entry_id"]),
            "action": entry["event_type"],
            "entity": str(entity),
            "timestamp": entry["timestamp"],
            "description": entry["description"]
        })
        
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
        context_str, citations = retrieve_relevant_rules(chat_req.message)
        
        reply = None
        if os.getenv("GOOGLE_API_KEY"):
            try:
                gemini = get_llm_client()
                prompt_with_context = f"REGULATORY CONTEXT:\n{context_str}\n\nUSER QUESTION: {chat_req.message}"
                res_text = gemini.invoke_chat(
                    prompt=prompt_with_context, 
                    system_prompt=CHAT_SYSTEM_PROMPT
                )
                if res_text and "apologize" not in res_text.lower():
                    reply = res_text
            except Exception as e:
                logger.warning(f"Gemini chat failed: {e}")
                
        if not reply:
            # Local Grounded Synthesis Engine using retrieved RBI Master Circulars
            if citations and len(citations) > 0:
                cit_text_list = []
                for c in citations[:3]:
                    cit_text_list.append(f"**[{c.get('id', 'RBI-REF')}] {c.get('source', 'RBI Circular')}**:\n> {c.get('text', '').strip()[:350]}...")
                formatted_evidence = "\n\n".join(cit_text_list)
                reply = f"### 📜 RBI Regulatory Knowledge Synthesis\n\nBased on official **RBI Master Circulars** & **PMLA Guidelines** in our knowledge base:\n\n{formatted_evidence}\n\n*Note: High-value or ambiguous transactions require mandatory review by a certified Compliance Officer.*"
            else:
                reply = "I searched the PolicyGuard Regulatory Knowledge Base, but could not find exact matching RBI circular clauses for your specific query. Please try rephrasing your search terms (e.g., 'KYC rules', 'AML thresholds', 'PMLA cash reporting')."
                
        return {"reply": reply, "citations": citations}
    except Exception as e:
        logger.error(f"Chat Endpoint Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process chat request: {str(e)}")


# --- RAG & REGULATORY KNOWLEDGE ENDPOINTS ---

class RAGQueryRequest(BaseModel):
    query: str
    top_k: Optional[int] = 3

@app.post("/api/rag/query")
def query_rag_knowledge(
    req: RAGQueryRequest,
    user_context: dict = Depends(verify_auth)
):
    context_str, citations = retrieve_relevant_rules(req.query)
    return {
        "query": req.query,
        "context": context_str,
        "citations": citations
    }

class RegulationIngestRequest(BaseModel):
    document_title: str
    section: str
    content: str
    source: Optional[str] = "RBI"

@app.post("/api/regulations/ingest")
def ingest_regulation(
    req: RegulationIngestRequest,
    user_context: dict = Depends(verify_auth)
):
    if user_context.get("role") not in [Role.ADMIN.value, Role.COMPLIANCE_OFFICER.value]:
        raise HTTPException(status_code=403, detail="Admin or Compliance Officer access required")
        
    audit_logger.log_policy_change(
        policy_id=req.document_title,
        changed_by=user_context.get("email"),
        old_value={},
        new_value={"section": req.section, "content": req.content}
    )
    return {
        "status": "success",
        "message": f"Regulation '{req.document_title} - {req.section}' ingested successfully into Knowledge Base."
    }

@app.get("/api/regulations/changes")
@app.get("/api/policy-drift/updates")
def get_policy_updates(
    user_context: dict = Depends(verify_auth)
):
    static_updates = [
        {
            "rag_doc_id": "RBI_KYC_CIRCULAR_2025_01",
            "title": "RBI Master Circular - Enhanced KYC/AML Due Diligence",
            "summary": "Mandatory Customer Due Diligence required for cash deposits exceeding ₹50,000.",
            "updated_at": datetime.utcnow().isoformat(),
            "status": "RE_INDEXED"
        },
        {
            "rag_doc_id": "PMLA_STRUCTURING_GUIDELINE",
            "title": "PMLA Threshold Monitoring Update",
            "summary": "Structuring thresholds set to flag sequential transactions approaching ₹10,00,000 limit.",
            "updated_at": (datetime.utcnow() - timedelta(days=2)).isoformat(),
            "status": "RE_INDEXED"
        }
    ]
    
    # Include active simulated drifts
    sim_updates = []
    for d in reversed(drift_detector._simulated_drifts):
        sim_updates.append({
            "rag_doc_id": d.get("drift_id"),
            "title": f"Simulated Regulatory Amendment ({d.get('drift_id')})",
            "summary": d.get("content", "").strip()[:160] + "...",
            "updated_at": d.get("timestamp", datetime.utcnow().isoformat()),
            "status": "ACTIVE_DRIFT"
        })
        
    return {"updates": sim_updates + static_updates}

@app.get("/api/policy-drift/affected/{regId}")
def get_affected_transactions(
    regId: str,
    db: Session = Depends(get_db),
    user_context: dict = Depends(verify_auth)
):
    all_txns = db.query(Transaction).all()
    filtered = []
    reg_lower = regId.lower()

    for t in all_txns:
        reasons_upper = [str(r).upper() for r in (t.flagged_reasons or [])]
        reasons_str = " ".join(reasons_upper)
        desc_str = (t.description or "").lower()
        amt = t.amount or 0.0

        if "kyc" in reg_lower or "rbi_kyc" in reg_lower:
            # STRICTLY KYC, EDD, High Amount No KYC, Cash Deposits
            # Exclude Structuring pattern transactions
            if "STRUCTURING_PATTERN" in reasons_upper or "structuring" in desc_str:
                continue
            if (
                "HIGH_AMOUNT_NO_KYC" in reasons_upper
                or "KYC" in reasons_str
                or "NO_KYC" in reasons_str
                or "cash deposit" in desc_str
                or "overseas" in desc_str
                or "north korea" in desc_str
                or "shell company" in desc_str
                or (amt >= 45000 and "cash" in desc_str)
            ):
                filtered.append(t)
                
        elif "structuring" in reg_lower or "pmla" in reg_lower:
            # STRICTLY Structuring, Split Transfers, PMLA Thresholds
            if (
                "STRUCTURING_PATTERN" in reasons_upper
                or "structuring" in desc_str
                or "split" in desc_str
                or (9000 <= amt <= 10000)
            ):
                filtered.append(t)
                
        elif "drift" in reg_lower:
            # Simulated Drift: Active high-risk transactions
            if t.status != "compliant" or t.risk_score > 60:
                filtered.append(t)
        else:
            if t.status != "compliant" or t.risk_score > 60:
                filtered.append(t)

    result = []
    for t in filtered[:10]:
        # Return accurate risk tags for each specific regulation context
        if t.flagged_reasons and len(t.flagged_reasons) > 0:
            tags = t.flagged_reasons
        elif "structuring" in reg_lower or "pmla" in reg_lower:
            tags = ["STRUCTURING_PATTERN"]
        else:
            tags = ["KYC-001"]

        result.append({
            "transaction_id": t.transaction_id,
            "amount": t.amount,
            "customer_id": t.customer_id,
            "risk_tags": tags
        })
    return {"reg_id": regId, "transactions": result}

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
    
    audit_logger._append_entry(
        event_type="POLICY_DRIFT_CHECK",
        description=f"User {user_context.get('email')} triggered a policy drift check (simulate={simulate})",
        data={"user_id": user_context.get('email'), "simulate": simulate}
    )

    result = drift_detector.check_for_drift(simulate=simulate)
    return result