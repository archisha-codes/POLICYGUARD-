# backend/agents/rule_engine.py
# Deterministic Rule Engine - Optimizes latency by filtering simple transactions
# Only complex/ambiguous transactions are sent to LLM (Bedrock/Granite)

from typing import Dict, List, Tuple, Optional
from enum import Enum
from pydantic import BaseModel
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class RiskLevel(str, Enum):
    """Risk assessment levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    REQUIRES_LLM = "requires_llm"


class RuleDecision(BaseModel):
    """Result of rule engine evaluation"""
    transaction_id: str
    is_compliant: Optional[bool] = None  # Allow None when deferred to AI
    risk_level: RiskLevel
    reason: str
    requires_llm: bool
    triggered_rules: List[str]
    timestamp: datetime


class DeterministicRuleEngine:
    """
    Filters transactions BEFORE sending to LLM.
    Goal: Minimize Bedrock API calls by catching obvious violations early.
    
    Simple rules (no latency):
    - Amount thresholds (>100k without KYC)
    - Sanctioned entity checks
    - Duplicate transaction detection
    - Basic regex patterns (OFAC, PEP lists)
    
    Complex rules (send to LLM):
    - Edge cases, ambiguous descriptions
    - Novel transaction types
    - Contextual compliance analysis
    """

    def __init__(self):
        self.sanctioned_entities = {
            "sanctioned_company", "blocked_entity", "terrorist", "iran",
            "north korea", "ofac_blocked", "uapa", "dprk", "myanmar", "ofac"
        }
        self.high_risk_countries = {"KP", "IR", "CU", "SY", "MM"}
        self.transaction_history = {}  # For duplicate detection

    def evaluate(self, transaction: Dict) -> RuleDecision:
        """
        Fast-path evaluation (<10ms) against RBI Master Directions & PMLA Rules.
        Returns explicit statutory compliance decision or defers ambiguous cases to AI LLM.
        """
        transaction_id = transaction.get("transaction_id", "unknown")
        triggered_rules = []
        
        try:
            amount = float(transaction.get("amount", 0))
            currency = (transaction.get("currency") or "INR").upper()
            description = (transaction.get("description") or "").lower()
            kyc_verified = transaction.get("kyc_verified", False) or transaction.get("kyc_completed", False)
            tx_type = (transaction.get("transaction_type") or "").lower()

            # Statutory Thresholds:
            # - RBI Master Direction: Cash deposit >= ₹50,000 requires PAN / CDD verification (Rule 114B).
            # - PMLA Rule 3(1)(A): Cash transactions >= ₹10,00,000 require Cash Transaction Report (CTR).
            # - FATF / PMLA Structuring: Wire/cash transfers between $9,000-$9,999 or ₹9,00,000-₹9,99,999 evading thresholds.

            # Rule 1: RBI KYC Cash Deposit / Unverified High Amount Check
            if not kyc_verified:
                if (currency == "INR" and amount >= 50000 and "cash" in description) or amount > 100000:
                    triggered_rules.append("HIGH_AMOUNT_NO_KYC")
                    return RuleDecision(
                        transaction_id=transaction_id,
                        is_compliant=False,
                        risk_level=RiskLevel.HIGH,
                        reason=f"RBI KYC Master Direction Violation: Unverified KYC for amount ({currency} {amount:,.2f}) exceeding threshold",
                        requires_llm=False,
                        triggered_rules=triggered_rules,
                        timestamp=datetime.utcnow()
                    )

            # Rule 2: OFAC / UNSC / UAPA Banned Entity Check
            entity_name = (transaction.get("entity_name") or transaction.get("description") or "").lower()
            if any(sanctioned in entity_name for sanctioned in self.sanctioned_entities):
                triggered_rules.append("OFAC_MATCH")
                return RuleDecision(
                    transaction_id=transaction_id,
                    is_compliant=False,
                    risk_level=RiskLevel.HIGH,
                    reason="OFAC / UNSC / UAPA Sanctioned Entity Match: Strictly Prohibited Transaction",
                    requires_llm=False,
                    triggered_rules=triggered_rules,
                    timestamp=datetime.utcnow()
                )

            # Rule 3: High-Risk Jurisdiction (FATF Call for Action)
            country = (transaction.get("country_code") or "").upper()
            if country in self.high_risk_countries or "north korea" in entity_name or "iran" in entity_name:
                triggered_rules.append("HIGH_RISK_COUNTRY")
                return RuleDecision(
                    transaction_id=transaction_id,
                    is_compliant=False,
                    risk_level=RiskLevel.HIGH,
                    reason=f"FATF High-Risk Jurisdiction ({country if country else 'SANCTIONED'}): Enhanced Due Diligence / STR Mandatory",
                    requires_llm=False,
                    triggered_rules=triggered_rules,
                    timestamp=datetime.utcnow()
                )

            # Rule 4: Duplicate Transaction Detection (Anti-Replay)
            tx_hash = self._create_transaction_hash(transaction)
            if tx_hash in self.transaction_history:
                prev_time = self.transaction_history[tx_hash]
                time_diff = (datetime.utcnow() - prev_time).total_seconds()
                if time_diff < 300:  # Duplicate within 5 minutes
                    triggered_rules.append("DUPLICATE_TRANSACTION")
                    return RuleDecision(
                        transaction_id=transaction_id,
                        is_compliant=False,
                        risk_level=RiskLevel.MEDIUM,
                        reason="Duplicate Transaction Warning: Identical transaction detected within 300s window",
                        requires_llm=False,
                        triggered_rules=triggered_rules,
                        timestamp=datetime.utcnow()
                    )
            
            # Record transaction timestamp
            self.transaction_history[tx_hash] = datetime.utcnow()

            # Rule 5: PMLA Structuring / Smurfing Pattern (Evading CTR Limit)
            if ("wire" in description or "transfer" in description or "deposit" in description or "structuring" in description) and \
               ((9000 <= amount <= 9999) or (45000 <= amount <= 49999) or (900000 <= amount <= 999999)):
                triggered_rules.append("STRUCTURING_PATTERN")
                return RuleDecision(
                    transaction_id=transaction_id,
                    is_compliant=False,
                    risk_level=RiskLevel.HIGH,
                    reason="PMLA Rule 3(1)(B) Structuring Violation: Transaction amount structured just below mandatory reporting threshold",
                    requires_llm=False,
                    triggered_rules=triggered_rules,
                    timestamp=datetime.utcnow()
                )

            # Rule 6: Low-Risk Verified Transaction (Auto-Approve)
            if amount < 5000 and kyc_verified:
                triggered_rules.append("AUTO_APPROVED_LOW_RISK")
                return RuleDecision(
                    transaction_id=transaction_id,
                    is_compliant=True,
                    risk_level=RiskLevel.LOW,
                    reason="Low-Risk Verified Transaction: Amount within safe velocity threshold with verified CDD",
                    requires_llm=False,
                    triggered_rules=triggered_rules,
                    timestamp=datetime.utcnow()
                )

            # Rule 7: Medium-Risk - Requires Contextual RAG / LLM Evaluation
            if 5000 <= amount <= 100000:
                triggered_rules.append("MEDIUM_AMOUNT_REQUIRES_ANALYSIS")
                return RuleDecision(
                    transaction_id=transaction_id,
                    is_compliant=None,
                    risk_level=RiskLevel.REQUIRES_LLM,
                    reason="Transaction requires contextual RAG regulatory analysis against active RBI Master Circulars",
                    requires_llm=True,
                    triggered_rules=triggered_rules,
                    timestamp=datetime.utcnow()
                )

            # Default: Ambiguous/Complex Case - Send to LLM
            triggered_rules.append("AMBIGUOUS_CASE")
            return RuleDecision(
                transaction_id=transaction_id,
                is_compliant=None,
                risk_level=RiskLevel.REQUIRES_LLM,
                reason="Ambiguous Transaction: Deferring to Gemini Compliance Co-Pilot with Grounded RAG context",
                requires_llm=True,
                triggered_rules=triggered_rules,
                timestamp=datetime.utcnow()
            )

        except Exception as e:
            logger.error(f"Rule engine error for {transaction_id}: {str(e)}")
            triggered_rules.append("ERROR_IN_EVALUATION")
            return RuleDecision(
                transaction_id=transaction_id,
                is_compliant=None,
                risk_level=RiskLevel.REQUIRES_LLM,
                reason=f"Error in rule evaluation: {str(e)}",
                requires_llm=True,
                triggered_rules=triggered_rules,
                timestamp=datetime.utcnow()
            )

    def _create_transaction_hash(self, transaction: Dict) -> str:
        """Create unique hash for duplicate detection"""
        import hashlib
        tx_str = f"{transaction.get('entity_name')}{transaction.get('amount')}{transaction.get('description')}"
        return hashlib.md5(tx_str.encode()).hexdigest()

    def get_stats(self) -> Dict:
        """Return rule engine statistics"""
        return {
            "cached_transactions": len(self.transaction_history),
            "sanctioned_entities_count": len(self.sanctioned_entities),
            "high_risk_countries_count": len(self.high_risk_countries)
        }
