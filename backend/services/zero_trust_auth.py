"""Zero-Trust Authentication & Authorization for POLICYGUARD

Document Requirements:
- JWT auth with short expiry
- Role-based access control (RBAC)
- Service-to-service validation
- Every API call authenticated, authorized, and logged
"""

import jwt
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from functools import wraps
from enum import Enum


class Role(Enum):
    """User roles for RBAC."""
    ADMIN = "admin"
    COMPLIANCE_OFFICER = "compliance_officer"
    AUDITOR = "auditor"
    MANAGER = "manager"
    READONLY_REGULATOR = "readonly_regulator"


class Permissions(Enum):
    """Fine-grained permissions."""
    VIEW_TRANSACTIONS = "view_transactions"
    APPROVE_TRANSACTIONS = "approve_transactions"
    VIEW_PII = "view_pii"
    MODIFY_POLICIES = "modify_policies"
    OVERRIDE_DECISIONS = "override_decisions"
    EXPORT_AUDIT_LOGS = "export_audit_logs"
    MANAGE_USERS = "manage_users"


# Role to Permissions Mapping
ROLE_PERMISSIONS = {
    Role.ADMIN: list(Permissions),
    Role.COMPLIANCE_OFFICER: [
        Permissions.VIEW_TRANSACTIONS,
        Permissions.APPROVE_TRANSACTIONS,
        Permissions.VIEW_PII,
        Permissions.OVERRIDE_DECISIONS
    ],
    Role.AUDITOR: [
        Permissions.VIEW_TRANSACTIONS,
        Permissions.EXPORT_AUDIT_LOGS
    ],
    Role.MANAGER: [
        Permissions.VIEW_TRANSACTIONS,
        Permissions.MODIFY_POLICIES
    ],
    Role.READONLY_REGULATOR: [
        Permissions.VIEW_TRANSACTIONS,
        Permissions.EXPORT_AUDIT_LOGS
    ]
}


class ZeroTrustAuthManager:
    """Zero-Trust authentication and authorization manager."""
    
    def __init__(self, secret_key: str = None):
        """Initialize with JWT secret key."""
        self.secret_key = secret_key or secrets.token_urlsafe(32)
        self.algorithm = "HS256"
        self.access_token_expiry = timedelta(minutes=15)  # Short expiry for security
        self.refresh_token_expiry = timedelta(days=7)
        
    def generate_access_token(self, user_id: str, role: Role, 
                             metadata: Dict = None) -> str:
        """Generate JWT access token."""
        payload = {
            "user_id": user_id,
            "role": role.value,
            "permissions": [p.value for p in ROLE_PERMISSIONS[role]],
            "exp": datetime.utcnow() + self.access_token_expiry,
            "iat": datetime.utcnow(),
            "type": "access"
        }
        
        if metadata:
            payload["metadata"] = metadata
        
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return token
    
    def generate_refresh_token(self, user_id: str) -> str:
        """Generate JWT refresh token."""
        payload = {
            "user_id": user_id,
            "exp": datetime.utcnow() + self.refresh_token_expiry,
            "iat": datetime.utcnow(),
            "type": "refresh"
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str) -> Dict:
        """Verify and decode JWT token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return {"valid": True, "payload": payload}
        except jwt.ExpiredSignatureError:
            return {"valid": False, "error": "Token expired"}
        except jwt.InvalidTokenError as e:
            return {"valid": False, "error": str(e)}
    
    def check_permission(self, token: str, required_permission: Permissions) -> Dict:
        """Check if token has required permission."""
        verification = self.verify_token(token)
        
        if not verification["valid"]:
            return {"authorized": False, "reason": verification["error"]}
        
        payload = verification["payload"]
        user_permissions = payload.get("permissions", [])
        
        if required_permission.value in user_permissions:
            return {
                "authorized": True,
                "user_id": payload["user_id"],
                "role": payload["role"]
            }
        else:
            return {
                "authorized": False,
                "reason": f"Permission '{required_permission.value}' denied"
            }
    
    def generate_service_token(self, service_name: str, 
                              allowed_operations: List[str]) -> str:
        """Generate service-to-service authentication token."""
        payload = {
            "service_name": service_name,
            "allowed_operations": allowed_operations,
            "exp": datetime.utcnow() + timedelta(hours=1),
            "iat": datetime.utcnow(),
            "type": "service"
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def verify_service_token(self, token: str, operation: str) -> bool:
        """Verify service-to-service token for specific operation."""
        verification = self.verify_token(token)
        
        if not verification["valid"]:
            return False
        
        payload = verification["payload"]
        
        if payload.get("type") != "service":
            return False
        
        allowed_ops = payload.get("allowed_operations", [])
        return operation in allowed_ops


# Decorator for endpoint protection
def require_permission(permission: Permissions):
    """Decorator to protect endpoints with permission check."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Extract token from request (pseudo-code)
            token = kwargs.get('auth_token') or kwargs.get('headers', {}).get('Authorization')
            
            if not token:
                return {"error": "No authentication token provided"}, 401
            
            auth_manager = ZeroTrustAuthManager()
            auth_result = auth_manager.check_permission(token, permission)
            
            if not auth_result["authorized"]:
                return {"error": auth_result["reason"]}, 403
            
            # Add user context to kwargs
            kwargs['user_context'] = {
                "user_id": auth_result["user_id"],
                "role": auth_result["role"]
            }
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


# Example for hackathon demo
if __name__ == "__main__":
    auth_manager = ZeroTrustAuthManager()
    
    # Generate tokens for different roles
    admin_token = auth_manager.generate_access_token(
        user_id="admin_001",
        role=Role.ADMIN
    )
    
    auditor_token = auth_manager.generate_access_token(
        user_id="auditor_001",
        role=Role.AUDITOR
    )
    
    print("\n=== ACCESS TOKENS GENERATED ===")
    print(f"Admin Token: {admin_token[:50]}...")
    print(f"Auditor Token: {auditor_token[:50]}...")
    
    # Verify permissions
    print("\n=== PERMISSION CHECKS ===")
    
    # Admin can view PII
    result = auth_manager.check_permission(admin_token, Permissions.VIEW_PII)
    print(f"Admin VIEW_PII: {result['authorized']}")
    
    # Auditor cannot view PII
    result = auth_manager.check_permission(auditor_token, Permissions.VIEW_PII)
    print(f"Auditor VIEW_PII: {result['authorized']} - {result.get('reason', '')}")
    
    # Service-to-service token
    service_token = auth_manager.generate_service_token(
        service_name="compliance-agent",
        allowed_operations=["analyze_transaction", "log_verdict"]
    )
    print(f"\nService Token: {service_token[:50]}...")
    print(f"Can analyze: {auth_manager.verify_service_token(service_token, 'analyze_transaction')}")
