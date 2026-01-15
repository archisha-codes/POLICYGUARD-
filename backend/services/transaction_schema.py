"""Transaction schema validation for Kinesis streaming.

Defines Pydantic models for transaction data validation with JSON schema support.
Ensures all streamed transactions meet compliance requirements before processing.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class TransactionType(str, Enum):
    """Valid transaction types for compliance categorization."""
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    TRANSFER = "transfer"
    PAYMENT = "payment"
    REFUND = "refund"


class TransactionStatus(str, Enum):
    """Transaction processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    APPROVED = "approved"
    REJECTED = "rejected"
    MANUAL_REVIEW = "manual_review"


class TransactionRequest(BaseModel):
    """Schema for incoming transaction from Kinesis stream."""
    
    transaction_id: str = Field(
        ...,
        description="Unique transaction identifier",
        min_length=1
    )
    customer_id: str = Field(
        ...,
        description="Customer identifier",
        min_length=1
    )
    amount: float = Field(
        ...,
        gt=0,
        description="Transaction amount"
    )
    currency: str = Field(
        default="INR",
        regex="^[A-Z]{3}$",
        description="ISO 4217 currency code"
    )
    transaction_type: TransactionType = Field(
        ...,
        description="Type of transaction"
    )
    description: str = Field(
        ...,
        description="Transaction description",
        min_length=1,
        max_length=500
    )
    source_account: str = Field(
        ...,
        description="Source account identifier",
        min_length=1
    )
    destination_account: str = Field(
        ...,
        description="Destination account identifier",
        min_length=1
    )
    timestamp: Optional[datetime] = Field(
        default=None,
        description="Transaction timestamp (ISO 8601)"
    )
    metadata: Optional[dict] = Field(
        default=None,
        description="Additional transaction metadata"
    )
    
    @validator('transaction_type', pre=True)
    def validate_transaction_type(cls, v):
        """Validate transaction type."""
        if isinstance(v, str):
            return v.lower()
        return v
    
    @validator('timestamp', pre=True, always=True)
    def set_timestamp(cls, v):
        """Set timestamp to current time if not provided."""
        if v is None:
            return datetime.utcnow()
        return v
    
    class Config:
        use_enum_values = True
        json_schema_extra = {
            "example": {
                "transaction_id": "TXN20250115001",
                "customer_id": "CUST12345",
                "amount": 50000.00,
                "currency": "INR",
                "transaction_type": "transfer",
                "description": "Fund transfer to account",
                "source_account": "ACC001",
                "destination_account": "ACC002",
                "timestamp": "2025-01-15T17:00:00Z"
            }
        }


class ComplianceVerdict(BaseModel):
    """Compliance analysis result."""
    
    transaction_id: str
    verdict: str = Field(
        ...,
        description="Compliance verdict: Compliant, Non-Compliant, Manual Review"
    )
    confidence: float = Field(
        ...,
        ge=0,
        le=1,
        description="Confidence score (0-1)"
    )
    risk_score: float = Field(
        default=0,
        ge=0,
        le=1,
        description="Risk score (0-1)"
    )
    applicable_policies: List[str] = Field(
        default=[],
        description="List of applicable policy IDs"
    )
    reasoning: str = Field(
        description="Detailed reasoning for verdict"
    )
    required_actions: List[str] = Field(
        default=[],
        description="Recommended actions for this transaction"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Analysis timestamp"
    )
    
    class Config:
        use_enum_values = True


class TransactionResult(BaseModel):
    """Final transaction processing result."""
    
    transaction_id: str
    status: TransactionStatus
    compliance_verdict: ComplianceVerdict
    sequence_number: str = Field(
        description="Kinesis sequence number"
    )
    processing_time_ms: float = Field(
        description="Time taken to process in milliseconds"
    )
    errors: List[str] = Field(
        default=[],
        description="Any errors encountered during processing"
    )
    
    class Config:
        use_enum_values = True


def validate_transaction(data: dict) -> tuple[bool, Optional[TransactionRequest], Optional[str]]:
    """
    Validate transaction data against schema.
    
    Args:
        data: Transaction dictionary from Kinesis
    
    Returns:
        Tuple of (is_valid, validated_request, error_message)
    """
    try:
        validated = TransactionRequest(**data)
        return True, validated, None
    except Exception as e:
        logger.warning(f"Transaction validation failed: {e}")
        return False, None, str(e)


def validate_multiple_transactions(data_list: list) -> tuple[List[TransactionRequest], List[dict]]:
    """
    Validate multiple transactions.
    
    Args:
        data_list: List of transaction dictionaries
    
    Returns:
        Tuple of (valid_transactions, invalid_transactions with errors)
    """
    valid = []
    invalid = []
    
    for idx, data in enumerate(data_list):
        is_valid, validated, error = validate_transaction(data)
        if is_valid:
            valid.append(validated)
        else:
            invalid.append({
                'index': idx,
                'data': data,
                'error': error
            })
    
    return valid, invalid
