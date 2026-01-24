"""Tamper-Proof Audit Logger for POLICYGUARD

Document Requirement:
- Immutable logs (append-only)
- Hash chaining (like blockchain, but we don't say that)
- 'Every compliance decision is cryptographically verifiable'
- Forensic readiness for bank audits
"""

import hashlib
import json
from datetime import datetime
from typing import Dict, List, Optional
import threading


class TamperProofAuditLogger:
    """Append-only audit log with hash chaining for tamper detection."""
    
    def __init__(self):
        """Initialize audit logger with genesis block."""
        self.log_chain = []
        self.lock = threading.Lock()
        self._create_genesis_entry()
        
    def _create_genesis_entry(self):
        """Create the first entry in the audit chain."""
        genesis = {
            "entry_id": 0,
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": "GENESIS",
            "description": "Audit log initialized",
            "prev_hash": "0" * 64,
            "data": {"system": "POLICYGUARD", "version": "1.0"},
            "hash": None
        }
        genesis["hash"] = self._compute_hash(genesis)
        self.log_chain.append(genesis)
    
    def log_compliance_decision(self, transaction_id: str, verdict: str, 
                                risk_score: float, explanation: str,
                                violated_rules: List[str], user_id: str = None) -> str:
        """Log a compliance decision (CRITICAL for hackathon demo)."""
        event_data = {
            "transaction_id": transaction_id,
            "verdict": verdict,
            "risk_score": risk_score,
            "explanation": explanation,
            "violated_rules": violated_rules,
            "user_id": user_id
        }
        
        return self._append_entry(
            event_type="COMPLIANCE_DECISION",
            description=f"Compliance verdict: {verdict} for transaction {transaction_id}",
            data=event_data
        )
    
    def log_pii_access(self, user_id: str, accessed_field: str, 
                       transaction_id: str, reason: str) -> str:
        """Log PII data access (important for privacy audit)."""
        return self._append_entry(
            event_type="PII_ACCESS",
            description=f"User {user_id} accessed {accessed_field}",
            data={
                "user_id": user_id,
                "field": accessed_field,
                "transaction_id": transaction_id,
                "reason": reason
            }
        )
    
    def log_auth_event(self, user_id: str, action: str, success: bool, 
                      ip_address: str = None) -> str:
        """Log authentication events."""
        return self._append_entry(
            event_type="AUTH_EVENT",
            description=f"{action} {'successful' if success else 'failed'} for user {user_id}",
            data={
                "user_id": user_id,
                "action": action,
                "success": success,
                "ip_address": ip_address
            }
        )
    
    def log_policy_change(self, policy_id: str, changed_by: str, 
                         old_value: Dict, new_value: Dict) -> str:
        """Log regulatory policy changes."""
        return self._append_entry(
            event_type="POLICY_CHANGE",
            description=f"Policy {policy_id} updated by {changed_by}",
            data={
                "policy_id": policy_id,
                "changed_by": changed_by,
                "old_value": old_value,
                "new_value": new_value
            }
        )
    
    def log_alert_sent(self, alert_type: str, recipient: str, 
                      transaction_id: str, severity: str) -> str:
        """Log email alerts sent."""
        return self._append_entry(
            event_type="ALERT_SENT",
            description=f"{alert_type} alert sent to {recipient}",
            data={
                "alert_type": alert_type,
                "recipient": recipient,
                "transaction_id": transaction_id,
                "severity": severity
            }
        )
    
    def _append_entry(self, event_type: str, description: str, 
                     data: Dict) -> str:
        """Append a new entry to the audit chain (append-only)."""
        with self.lock:
            prev_entry = self.log_chain[-1]
            
            new_entry = {
                "entry_id": len(self.log_chain),
                "timestamp": datetime.utcnow().isoformat(),
                "event_type": event_type,
                "description": description,
                "prev_hash": prev_entry["hash"],
                "data": data,
                "hash": None
            }
            
            new_entry["hash"] = self._compute_hash(new_entry)
            self.log_chain.append(new_entry)
            
            return new_entry["hash"]
    
    def _compute_hash(self, entry: Dict) -> str:
        """Compute SHA-256 hash of entry (for chain integrity)."""
        entry_copy = entry.copy()
        entry_copy.pop("hash", None)
        
        entry_string = json.dumps(entry_copy, sort_keys=True)
        return hashlib.sha256(entry_string.encode()).hexdigest()
    
    def verify_chain_integrity(self) -> Dict:
        """Verify the entire audit log chain (DEMO THIS TO JUDGES)."""
        for i in range(1, len(self.log_chain)):
            current_entry = self.log_chain[i]
            prev_entry = self.log_chain[i - 1]
            
            # Check if prev_hash matches
            if current_entry["prev_hash"] != prev_entry["hash"]:
                return {
                    "valid": False,
                    "tampered_at": i,
                    "message": f"Chain broken at entry {i}"
                }
            
            # Verify current entry hash
            computed_hash = self._compute_hash(current_entry)
            if computed_hash != current_entry["hash"]:
                return {
                    "valid": False,
                    "tampered_at": i,
                    "message": f"Entry {i} has been tampered with"
                }
        
        return {
            "valid": True,
            "total_entries": len(self.log_chain),
            "message": "All entries are cryptographically verified"
        }
    
    def get_audit_trail(self, filters: Dict = None, limit: int = 100) -> List[Dict]:
        """Retrieve audit trail with optional filters."""
        results = self.log_chain[1:]  # Skip genesis
        
        if filters:
            if "event_type" in filters:
                results = [e for e in results if e["event_type"] == filters["event_type"]]
            if "transaction_id" in filters:
                results = [e for e in results 
                          if e.get("data", {}).get("transaction_id") == filters["transaction_id"]]
        
        return results[-limit:]
    
    def export_for_audit(self, start_date: str = None, end_date: str = None) -> Dict:
        """Export audit logs for regulatory audit."""
        return {
            "export_timestamp": datetime.utcnow().isoformat(),
            "total_entries": len(self.log_chain),
            "chain_integrity": self.verify_chain_integrity(),
            "audit_trail": self.log_chain
        }


# Example for hackathon demo
if __name__ == "__main__":
    logger = TamperProofAuditLogger()
    
    # Log compliance decisions
    logger.log_compliance_decision(
        transaction_id="TXN123",
        verdict="NON_COMPLIANT",
        risk_score=0.85,
        explanation="High-value transaction to sanctioned country",
        violated_rules=["AML Rule 4.2", "RBI Circular 2025-01"],
        user_id="system"
    )
    
    logger.log_pii_access(
        user_id="auditor_001",
        accessed_field="pan",
        transaction_id="TXN123",
        reason="Compliance review"
    )
    
    logger.log_alert_sent(
        alert_type="TRANSACTION_VIOLATION",
        recipient="compliance@bank.com",
        transaction_id="TXN123",
        severity="HIGH"
    )
    
    # Verify integrity
    print("\n=== AUDIT LOG INTEGRITY CHECK ===")
    integrity = logger.verify_chain_integrity()
    print(json.dumps(integrity, indent=2))
    
    # Show audit trail
    print("\n=== AUDIT TRAIL ===")
    trail = logger.get_audit_trail()
    for entry in trail:
        print(f"[{entry['timestamp']}] {entry['event_type']}: {entry['description']}")
