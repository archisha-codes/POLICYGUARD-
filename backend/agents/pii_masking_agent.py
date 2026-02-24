"""PII Masking Agent for POLICYGUARD - CRITICAL SECURITY COMPONENT"""

import re
import hashlib
import secrets
import json
from typing import Dict, List, Optional, Tuple 
from datetime import datetime
from cryptography.fernet import Fernet
import base64


class PIIMaskingAgent:
    """Enterprise-grade PII masking with tokenization."""
    
    # Indian PII Patterns
    PAN_PATTERN = r'[A-Z]{5}[0-9]{4}[A-Z]{1}'
    AADHAAR_PATTERN = r'\d{4}\s?\d{4}\s?\d{4}|\d{12}'
    ACCOUNT_PATTERN = r'\b\d{9,18}\b'
    
    def __init__(self, encryption_key: Optional[bytes] = None):
        """Initialize PII masking agent."""
        self.encryption_key = encryption_key or Fernet.generate_key()
        self.cipher = Fernet(self.encryption_key)
        self.token_vault = {}  # In-memory vault (use Redis/DB in production)
        self.audit_log = []
        
    def mask_transaction(self, transaction: Dict) -> Dict:
        """Mask all PII in transaction data."""
        masked_txn = transaction.copy()
        audit_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "transaction_id": transaction.get("transaction_id"),
            "masked_fields": []
        }
        
        # Mask PAN
        if "pan" in masked_txn:
            original = masked_txn["pan"]
            masked_txn["pan"], token = self.mask_pan(original)
            audit_entry["masked_fields"].append("pan")
        
        # Mask Aadhaar
        if "aadhaar" in masked_txn:
            original = masked_txn["aadhaar"]
            masked_txn["aadhaar"], token = self.mask_aadhaar(original)
            audit_entry["masked_fields"].append("aadhaar")
        
        # Mask Account Number
        if "account_number" in masked_txn:
            original = masked_txn["account_number"]
            masked_txn["account_number"], token = self.mask_account(original)
            audit_entry["masked_fields"].append("account_number")
        
        # Scan description for embedded PII
        if "description" in masked_txn:
            masked_txn["description"] = self.scan_and_mask_text(masked_txn["description"])
        
        self.audit_log.append(audit_entry)
        return masked_txn
    
    def mask_pan(self, pan: str) -> Tuple[str, str]:
        """Mask PAN: ABCDE1234F -> XXXXX1234X"""
        if not re.match(self.PAN_PATTERN, pan):
            return pan, None
        
        # Generate deterministic hash for tokenization
        pan_hash = hashlib.sha256(pan.encode()).hexdigest()[:16]
        token = f"PAN_{pan_hash}"
        
        # Store mapping (reversible)
        encrypted_pan = self.cipher.encrypt(pan.encode()).decode()
        self.token_vault[token] = encrypted_pan
        
        # Return masked PAN
        masked = f"XXXXX{pan[5:9]}X"
        return masked, token
    
    def mask_aadhaar(self, aadhaar: str) -> Tuple[str, str]:  # <--- Fixed typo Ttuple
        """Mask Aadhaar: 1234 5678 9012 -> XXXX XXXX 9012"""
        clean_aadhaar = re.sub(r'\s', '', aadhaar)
        if not re.match(r'^\d{12}$', clean_aadhaar):
            return aadhaar, None
        
        # Hash and tokenize
        aadhaar_hash = hashlib.sha256(clean_aadhaar.encode()).hexdigest()[:16]
        token = f"AADHAAR_{aadhaar_hash}"
        
        # Store encrypted
        encrypted_aadhaar = self.cipher.encrypt(clean_aadhaar.encode()).decode()
        self.token_vault[token] = encrypted_aadhaar
        
        # Mask: Show last 4 digits only
        masked = f"XXXX XXXX {clean_aadhaar[-4:]}"
        return masked, token
    
    def mask_account(self, account_number: str) -> Tuple[str, str]:
        """Mask Account Number: 1234567890123 -> XXXXXXXXX3456"""
        clean_account = re.sub(r'\D', '', account_number)
        if len(clean_account) < 9:
            return account_number, None
        
        # Hash and tokenize
        account_hash = hashlib.sha256(clean_account.encode()).hexdigest()[:16]
        token = f"ACCT_{account_hash}"
        
        # Store encrypted
        encrypted_account = self.cipher.encrypt(clean_account.encode()).decode()
        self.token_vault[token] = encrypted_account
        
        # Mask: Show last 4 digits
        masked = 'X' * (len(clean_account) - 4) + clean_account[-4:]
        return masked, token
    
    def scan_and_mask_text(self, text: str) -> str:
        """Scan text and mask any embedded PII."""
        # Mask PANs in text
        text = re.sub(self.PAN_PATTERN, lambda m: self.mask_pan(m.group())[0], text)
        
        # Mask Aadhaar in text
        text = re.sub(self.AADHAAR_PATTERN, lambda m: self.mask_aadhaar(m.group())[0], text)
        
        # Mask potential account numbers
        text = re.sub(self.ACCOUNT_PATTERN, lambda m: self.mask_account(m.group())[0], text)
        
        return text
    
    def unmask(self, token: str) -> Optional[str]:
        """Unmask PII using token (for authorized access)."""
        if token not in self.token_vault:
            return None
        
        encrypted_value = self.token_vault[token]
        decrypted = self.cipher.decrypt(encrypted_value.encode()).decode()
        
        # Log access
        self.audit_log.append({
            "timestamp": datetime.utcnow().isoformat(),
            "action": "unmask",
            "token": token
        })
        
        return decrypted
    
    def get_irreversible_hash(self, pii_value: str) -> str:
        """Generate irreversible hash for PII (for analytics)."""
        # Add salt for security
        salt = secrets.token_bytes(32)
        hash_value = hashlib.pbkdf2_hmac('sha256', pii_value.encode(), salt, 100000)
        return base64.b64encode(hash_value).decode()
    
    def get_audit_trail(self) -> List[Dict]:
        """Return complete audit trail."""
        return self.audit_log
    
    def export_tokens(self) -> Dict:
        """Export token vault (for secure storage)."""
        return {
            "encryption_key": base64.b64encode(self.encryption_key).decode(),
            "tokens": self.token_vault,
            "exported_at": datetime.utcnow().isoformat()
        }
    
    @staticmethod
    def validate_pan(pan: str) -> bool:
        """Validate PAN format."""
        return bool(re.match(PIIMaskingAgent.PAN_PATTERN, pan))
    
    @staticmethod
    def validate_aadhaar(aadhaar: str) -> bool:
        """Validate Aadhaar format."""
        clean = re.sub(r'\s', '', aadhaar)
        return bool(re.match(r'^\d{12}$', clean))