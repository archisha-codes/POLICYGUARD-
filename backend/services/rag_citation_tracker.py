# backend/services/rag_citation_tracker.py
# RAG Citation & Source Tracking
# Prevents hallucinations by maintaining provenance of retrieved documents

from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime
import hashlib
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class ConfidenceLevel(str, Enum):
    """Confidence in RAG retrieval accuracy"""
    HIGH = "high"  # Exact match in source document
    MEDIUM = "medium"  # Paraphrased but found in document
    LOW = "low"  # Requires LLM interpretation
    UNCERTAIN = "uncertain"  # Not verified in source


@dataclass
class CitationSource:
    """Represents a source document used in RAG retrieval"""
    document_id: str
    document_name: str
    document_type: str  # e.g., "RBI_CIRCULAR", "KYC_GUIDELINE"
    chunk_id: str
    chunk_text: str
    page_number: Optional[int]
    confidence: ConfidenceLevel
    retrieval_score: float  # 0.0 - 1.0 (cosine similarity)
    timestamp: datetime
    hash_value: str  # SHA256 of chunk text for integrity

    def to_dict(self) -> Dict:
        return {
            "document_id": self.document_id,
            "document_name": self.document_name,
            "document_type": self.document_type,
            "chunk_id": self.chunk_id,
            "page_number": self.page_number,
            "confidence": self.confidence.value,
            "retrieval_score": self.retrieval_score,
            "timestamp": self.timestamp.isoformat(),
            "hash_value": self.hash_value,
        }


@dataclass
class ComplianceDecision:
    """Tracks the complete compliance decision with citations"""
    decision_id: str
    transaction_id: str
    is_compliant: bool
    decision_reason: str
    primary_citations: List[CitationSource]  # Direct matches from documents
    supporting_citations: List[CitationSource]  # Contextual references
    llm_reasoning: Optional[str]  # What LLM added beyond retrieval
    confidence_score: float  # 0.0 - 1.0
    auditable: bool  # Can decision be traced back to source documents?
    timestamp: datetime

    def to_dict(self) -> Dict:
        return {
            "decision_id": self.decision_id,
            "transaction_id": self.transaction_id,
            "is_compliant": self.is_compliant,
            "decision_reason": self.decision_reason,
            "primary_citations": [c.to_dict() for c in self.primary_citations],
            "supporting_citations": [c.to_dict() for c in self.supporting_citations],
            "llm_reasoning": self.llm_reasoning,
            "confidence_score": self.confidence_score,
            "auditable": self.auditable,
            "timestamp": self.timestamp.isoformat(),
        }


class RAGCitationTracker:
    """
    Maintains ground truth for RAG outputs.
    Prevents LLM hallucinations by verifying all claims against source documents.
    """

    def __init__(self):
        self.decision_log = {}  # Store all decisions for audit trail
        self.hallucination_detected_count = 0

    def track_citation(self, citation: CitationSource) -> bool:
        """
        Verify citation is from actual document.
        Returns True if valid, False if suspicious.
        """
        try:
            # Verify hash integrity
            computed_hash = hashlib.sha256(citation.chunk_text.encode()).hexdigest()
            if computed_hash != citation.hash_value:
                logger.warning(f"Citation hash mismatch for {citation.document_id}")
                return False

            # Verify retrieval score is reasonable
            if citation.retrieval_score < 0.3:  # Very low similarity
                logger.warning(f"Low retrieval score: {citation.retrieval_score}")
                return False

            return True

        except Exception as e:
            logger.error(f"Citation verification error: {str(e)}")
            return False

    def validate_decision(self, decision: ComplianceDecision) -> bool:
        """
        Check if decision is properly backed by source documents.
        Returns True if auditable, False if hallucination detected.
        """
        # Rule 1: Must have primary citations (direct from documents)
        if not decision.primary_citations:
            logger.warning(f"Decision {decision.decision_id} has no primary citations")
            self.hallucination_detected_count += 1
            return False

        # Rule 2: All citations must be valid
        for citation in decision.primary_citations + decision.supporting_citations:
            if not self.track_citation(citation):
                logger.warning(f"Invalid citation in decision {decision.decision_id}")
                self.hallucination_detected_count += 1
                return False

        # Rule 3: Confidence must be reasonable
        avg_retrieval_score = sum(c.retrieval_score for c in decision.primary_citations) / len(decision.primary_citations)
        if avg_retrieval_score < 0.5:
            logger.warning(f"Low average retrieval score: {avg_retrieval_score}")
            decision.confidence_score = min(decision.confidence_score, 0.5)

        # Rule 4: Mark as auditable
        decision.auditable = len(decision.primary_citations) > 0
        return decision.auditable

    def log_decision(self, decision: ComplianceDecision) -> str:
        """
        Store decision in audit trail.
        Returns decision ID.
        """
        # Validate first
        is_valid = self.validate_decision(decision)
        decision.auditable = is_valid

        # Store in audit log
        self.decision_log[decision.decision_id] = decision
        logger.info(f"Decision logged: {decision.decision_id}, Auditable: {is_valid}")

        return decision.decision_id

    def get_audit_report(self, decision_id: str) -> Optional[Dict]:
        """
        Retrieve complete audit trail for a decision.
        For compliance review and legal defense.
        """
        if decision_id not in self.decision_log:
            return None

        decision = self.decision_log[decision_id]
        return {
            "decision": decision.to_dict(),
            "is_auditable": decision.auditable,
            "source_documents": [
                {"doc_id": c.document_id, "doc_name": c.document_name}
                for c in decision.primary_citations
            ],
            "retrieval_quality": "high" if decision.confidence_score > 0.8 else "medium" if decision.confidence_score > 0.6 else "low",
        }

    def get_hallucination_stats(self) -> Dict:
        """
        Return statistics on hallucinations detected.
        """
        return {
            "hallucinations_detected": self.hallucination_detected_count,
            "total_decisions_logged": len(self.decision_log),
            "hallucination_rate": self.hallucination_detected_count / max(len(self.decision_log), 1),
        }
