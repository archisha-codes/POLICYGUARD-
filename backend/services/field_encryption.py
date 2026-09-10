"""Field-Level Encryption for POLICYGUARD - Bank-Grade Security

As per document requirement:
- Sensitive fields like PAN, Aadhaar, account numbers encrypted individually
- LLM sees only encrypted/hashed data
- 'The AI never sees raw customer identity'
"""

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes, hmac
from cryptography.hazmat.backends import default_backend
import os
import base64
import json
from typing import Dict, Any, List
from datetime import datetime


class FieldEncryptionManager:
    """Field-level encryption - encrypts specific fields individually."""
    
    # Fields that require encryption
    SENSITIVE_FIELDS = [
        'pan', 'aadhaar', 'account_number', 'account_holder_name',
        'phone', 'email', 'address', 'bank_details',
        'credit_card', 'cvv', 'ssn', 'passport_number'
    ]
    
    def __init__(self, master_key: bytes = None):
        """Initialize with master encryption key."""
        self.master_key = master_key or Fernet.generate_key()
        self.cipher = Fernet(self.master_key)
        self.encryption_log = []
        
    def encrypt_field(self, field_name: str, value: Any) -> Dict:
        """Encrypt a single field value."""
        if value is None:
            return {"encrypted": None, "is_encrypted": False}
        
        # Convert to string for encryption
        value_str = str(value)
        
        # Encrypt
        encrypted_bytes = self.cipher.encrypt(value_str.encode())
        encrypted_b64 = base64.b64encode(encrypted_bytes).decode()
        
        # Log encryption
        self.encryption_log.append({
            "field": field_name,
            "timestamp": datetime.utcnow().isoformat(),
            "action": "encrypt"
        })
        
        return {
            "encrypted": encrypted_b64,
            "is_encrypted": True,
            "field_name": field_name
        }
    
    def decrypt_field(self, encrypted_data: Dict) -> Any:
        """Decrypt a field value."""
        if not encrypted_data.get("is_encrypted"):
            return encrypted_data.get("encrypted")
        
        encrypted_b64 = encrypted_data["encrypted"]
        encrypted_bytes = base64.b64decode(encrypted_b64)
        
        # Decrypt
        decrypted_bytes = self.cipher.decrypt(encrypted_bytes)
        decrypted_str = decrypted_bytes.decode()
        
        # Log decryption
        self.encryption_log.append({
            "field": encrypted_data.get("field_name"),
            "timestamp": datetime.utcnow().isoformat(),
            "action": "decrypt"
        })
        
        return decrypted_str
    
    def encrypt_transaction(self, transaction: Dict) -> Dict:
        """Encrypt all sensitive fields in transaction."""
        encrypted_txn = transaction.copy()
        
        for field in self.SENSITIVE_FIELDS:
            if field in encrypted_txn:
                encrypted_data = self.encrypt_field(field, encrypted_txn[field])
                encrypted_txn[f"{field}_encrypted"] = encrypted_data
                # Replace original with hash for AI processing
                encrypted_txn[field] = f"HASH_{self._hash_value(str(encrypted_txn[field]))[:12]}"
        
        encrypted_txn["encryption_metadata"] = {
            "encrypted_at": datetime.utcnow().isoformat(),
            "encrypted_fields_count": len([f for f in self.SENSITIVE_FIELDS if f in transaction])
        }
        
        return encrypted_txn
    
    def decrypt_transaction(self, encrypted_txn: Dict) -> Dict:
        """Decrypt all encrypted fields in transaction."""
        decrypted_txn = encrypted_txn.copy()
        
        for field in self.SENSITIVE_FIELDS:
            encrypted_key = f"{field}_encrypted"
            if encrypted_key in decrypted_txn:
                decrypted_value = self.decrypt_field(decrypted_txn[encrypted_key])
                decrypted_txn[field] = decrypted_value
                del decrypted_txn[encrypted_key]
        
        return decrypted_txn
    
    def _hash_value(self, value: str) -> str:
        """Generate deterministic hash for a value."""
        h = hashes.Hash(hashes.SHA256(), backend=default_backend())
        h.update(value.encode())
        return h.finalize().hex()
    
    def get_encryption_audit(self) -> List[Dict]:
        """Return encryption audit trail."""
        return self.encryption_log
    
    def rotate_key(self, new_master_key: bytes) -> None:
        """Rotate encryption key (enterprise feature)."""
        old_cipher = self.cipher
        self.cipher = Fernet(new_master_key)
        self.master_key = new_master_key
        
        print(f"Encryption key rotated at {datetime.utcnow().isoformat()}")


# Example for hackathon demo
if __name__ == "__main__":
    encryptor = FieldEncryptionManager()
    
    # Original transaction
    transaction = {
        "transaction_id": "TXN123",
        "pan": "ABCDE1234F",
        "aadhaar": "123456789012",
        "account_number": "9876543210123",
        "amount": 50000,
        "description": "High-value transfer"
    }
    
    print("\n=== ORIGINAL TRANSACTION ===")
    print(json.dumps(transaction, indent=2))
    
    # Encrypt for AI processing
    encrypted = encryptor.encrypt_transaction(transaction)
    print("\n=== ENCRYPTED FOR AI (What LLM Sees) ===")
    print(json.dumps({
        "transaction_id": encrypted["transaction_id"],
        "pan": encrypted["pan"],
        "aadhaar": encrypted["aadhaar"],
        "account_number": encrypted["account_number"],
        "amount": encrypted["amount"]
    }, indent=2))
    
    # Decrypt for authorized access
    decrypted = encryptor.decrypt_transaction(encrypted)
    print("\n=== DECRYPTED (Authorized Access) ===")
    print(json.dumps(decrypted, indent=2))
    
    print("\n=== AUDIT LOG ===")
    print(json.dumps(encryptor.get_encryption_audit(), indent=2))
