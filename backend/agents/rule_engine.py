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
            "north korea", "ofac_blocked"
        }
        self.high_risk_countries = {"KP", "IR", "CU", "SY"}
        self.transaction_history = {}  # For duplicate detection

    def evaluate(self, transaction: Dict) -> RuleDecision:
        """
        Fast-path evaluation: Returns decision in <10ms (no LLM call).
        If no clear decision, returns requires_llm=True for Granite analysis.
        """
        transaction_id = transaction.get("transaction_id", "unknown")
        triggered_rules = []
        
        try:
            # Rule 1: Check Amount Thresholds (KYC Rule)
            if not transaction.get("kyc_verified", False):
                amount = float(transaction.get("amount", 0))
                if amount > 100000:  # >100K requires KYC
                    triggered_rules.append("HIGH_AMOUNT_NO_KYC")
                    return RuleDecision(
                        transaction_id=transaction_id,
                        is_compliant=False,
                        risk_level=RiskLevel.HIGH,
                        reason="Transaction amount exceeds 100K without KYC verification",
                        requires_llm=False,
                        triggered_rules=triggered_rules,
                        timestamp=datetime.utcnow()
                    )

            # Rule 2: Sanctioned Entity Check (OFAC)
            entity_name = transaction.get("entity_name", "").lower()
            if any(sanctioned in entity_name for sanctioned in self.sanctioned_entities):
                triggered_rules.append("OFAC_MATCH")
                return RuleDecision(
                    transaction_id=transaction_id,
                    is_compliant=False,
                    risk_level=RiskLevel.HIGH,
                    reason="Entity matches OFAC/sanctioned entities list",
                    requires_llm=False,
                    triggered_rules=triggered_rules,
                    timestamp=datetime.utcnow()
                )

            # Rule 3: High-Risk Country Check (AML)
            country = transaction.get("country_code", "").upper()
            if country in self.high_risk_countries:
                triggered_rules.append("HIGH_RISK_COUNTRY")
                return RuleDecision(
                    transaction_id=transaction_id,
                    is_compliant=False,
                    risk_level=RiskLevel.HIGH,
                    reason=f"Transaction from high-risk country: {country}",
                    requires_llm=False,
                    triggered_rules=triggered_rules,
                    timestamp=datetime.utcnow()
                )

            # Rule 4: Duplicate Transaction Detection
            tx_hash = self._create_transaction_hash(transaction)
            if tx_hash in self.transaction_history:
                prev_time = self.transaction_history[tx_hash]
                time_diff = (datetime.utcnow() - prev_time).total_seconds()
                if time_diff < 300:  # Same transaction within 5 minutes
                    triggered_rules.append("DUPLICATE_TRANSACTION")
                    return RuleDecision(
                        transaction_id=transaction_id,
                        is_compliant=False,
                        risk_level=RiskLevel.MEDIUM,
                        reason="Duplicate transaction detected (same within 5 min)",
                        requires_llm=False,
                        triggered_rules=triggered_rules,
                        timestamp=datetime.utcnow()
                    )
            
            # Record this transaction
            self.transaction_history[tx_hash] = datetime.utcnow()

            # Rule 5: AML Pattern - Rapid Small Transactions (Structuring)
            description = transaction.get("description", "").lower()
            amount = float(transaction.get("amount", 0))
            if ("wire" in description or "transfer" in description) and \
               (9000 < amount < 11000):  # Structuring pattern (avoiding 10k reporting)
                triggered_rules.append("STRUCTURING_PATTERN")
                return RuleDecision(
                    transaction_id=transaction_id,
                    is_compliant=False,
                    risk_level=RiskLevel.HIGH,
                    reason="Potential structuring detected (amount in 9-11k range)",
                    requires_llm=False,
                    triggered_rules=triggered_rules,
                    timestamp=datetime.utcnow()
                )

            # Rule 6: Low-Risk Transaction (Auto-Approve)
            if amount < 5000 and transaction.get("kyc_verified", False):
                triggered_rules.append("AUTO_APPROVED_LOW_RISK")
                return RuleDecision(
                    transaction_id=transaction_id,
                    is_compliant=True,
                    risk_level=RiskLevel.LOW,
                    reason="Low-risk transaction (verified customer, <5K)",
                    requires_llm=False,
                    triggered_rules=triggered_rules,
                    timestamp=datetime.utcnow()
                )

            # Rule 7: Medium-Risk - Send to LLM for contextual analysis
            if 5000 <= amount <= 100000:
                triggered_rules.append("MEDIUM_AMOUNT_REQUIRES_ANALYSIS")
                return RuleDecision(
                    transaction_id=transaction_id,
                    is_compliant=None,
                    risk_level=RiskLevel.REQUIRES_LLM,
                    reason="Transaction requires contextual Gemini compliance analysis",
                    requires_llm=True,
                    triggered_rules=triggered_rules,
                    timestamp=datetime.utcnow()
                )

            # Default: Unknown/Edge case - Send to LLM
            triggered_rules.append("AMBIGUOUS_CASE")
            return RuleDecision(
                transaction_id=transaction_id,
                is_compliant=None,
                risk_level=RiskLevel.REQUIRES_LLM,
                reason="Transaction requires Gemini LLM analysis (ambiguous case)",
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
    REQUIRES_LLM = "requires_llm"  # Send to Granite/Bedrock


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
            "north korea", "ofac_blocked"
        }
        self.high_risk_countries = {"KP", "IR", "CU", "SY"}
        self.transaction_history = {}  # For duplicate detection

    def evaluate(self, transaction: Dict) -> RuleDecision:
        """
        Fast-path evaluation: Returns decision in <10ms (no LLM call).
        If no clear decision, returns requires_llm=True for Granite analysis.
        """
        transaction_id = transaction.get("transaction_id", "unknown")
        triggered_rules = []
        
        try:
            # Rule 1: Check Amount Thresholds (KYC Rule)
            if not transaction.get("kyc_verified", False):
                amount = float(transaction.get("amount", 0))
                if amount > 100000:  # >100K requires KYC
                    triggered_rules.append("HIGH_AMOUNT_NO_KYC")
                    return RuleDecision(
                        transaction_id=transaction_id,
                        is_compliant=False,
                        risk_level=RiskLevel.HIGH,
                        reason="Transaction amount exceeds 100K without KYC verification",
                        requires_llm=False,
                        triggered_rules=triggered_rules,
                        timestamp=datetime.utcnow()
                    )

            # Rule 2: Sanctioned Entity Check (OFAC)
            entity_name = transaction.get("entity_name", "").lower()
            if any(sanctioned in entity_name for sanctioned in self.sanctioned_entities):
                triggered_rules.append("OFAC_MATCH")
                return RuleDecision(
                    transaction_id=transaction_id,
                    is_compliant=False,
                    risk_level=RiskLevel.HIGH,
                    reason="Entity matches OFAC/sanctioned entities list",
                    requires_llm=False,
                    triggered_rules=triggered_rules,
                    timestamp=datetime.utcnow()
                )

            # Rule 3: High-Risk Country Check (AML)
            country = transaction.get("country_code", "").upper()
            if country in self.high_risk_countries:
                triggered_rules.append("HIGH_RISK_COUNTRY")
                return RuleDecision(
                    transaction_id=transaction_id,
                    is_compliant=False,
                    risk_level=RiskLevel.HIGH,
                    reason=f"Transaction from high-risk country: {country}",
                    requires_llm=False,
                    triggered_rules=triggered_rules,
                    timestamp=datetime.utcnow()
                )

            # Rule 4: Duplicate Transaction Detection
            tx_hash = self._create_transaction_hash(transaction)
            if tx_hash in self.transaction_history:
                prev_time = self.transaction_history[tx_hash]
                time_diff = (datetime.utcnow() - prev_time).total_seconds()
                if time_diff < 300:  # Same transaction within 5 minutes
                    triggered_rules.append("DUPLICATE_TRANSACTION")
                    return RuleDecision(
                        transaction_id=transaction_id,
                        is_compliant=False,
                        risk_level=RiskLevel.MEDIUM,
                        reason="Duplicate transaction detected (same within 5 min)",
                        requires_llm=False,
                        triggered_rules=triggered_rules,
                        timestamp=datetime.utcnow()
                    )
            
            # Record this transaction
            self.transaction_history[tx_hash] = datetime.utcnow()

            # Rule 5: AML Pattern - Rapid Small Transactions (Structuring)
            description = transaction.get("description", "").lower()
            amount = float(transaction.get("amount", 0))
            if ("wire" in description or "transfer" in description) and \
               (9000 < amount < 11000):  # Structuring pattern (avoiding 10k reporting)
                triggered_rules.append("STRUCTURING_PATTERN")
                return RuleDecision(
                    transaction_id=transaction_id,
                    is_compliant=False,
                    risk_level=RiskLevel.HIGH,
                    reason="Potential structuring detected (amount in 9-11k range)",
                    requires_llm=False,
                    triggered_rules=triggered_rules,
                    timestamp=datetime.utcnow()
                )

            # Rule 6: Low-Risk Transaction (Auto-Approve)
            if amount < 5000 and transaction.get("kyc_verified", False):
                triggered_rules.append("AUTO_APPROVED_LOW_RISK")
                return RuleDecision(
                    transaction_id=transaction_id,
                    is_compliant=True,
                    risk_level=RiskLevel.LOW,
                    reason="Low-risk transaction (verified customer, <5K)",
                    requires_llm=False,
                    triggered_rules=triggered_rules,
                    timestamp=datetime.utcnow()
                )

            # Rule 7: Medium-Risk - Send to LLM for contextual analysis
            if 5000 <= amount <= 100000:
                triggered_rules.append("MEDIUM_AMOUNT_REQUIRES_ANALYSIS")
                return RuleDecision(
                    transaction_id=transaction_id,
                    is_compliant=None,
                    risk_level=RiskLevel.REQUIRES_LLM,
                    reason="Transaction requires contextual compliance analysis",
                    requires_llm=True,
                    triggered_rules=triggered_rules,
                    timestamp=datetime.utcnow()
                )

            # Default: Unknown/Edge case - Send to LLM
            triggered_rules.append("AMBIGUOUS_CASE")
            return RuleDecision(
                transaction_id=transaction_id,
                is_compliant=None,
                risk_level=RiskLevel.REQUIRES_LLM,
                reason="Transaction requires Granite LLM analysis (ambiguous case)",
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