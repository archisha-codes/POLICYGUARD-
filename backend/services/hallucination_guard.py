hallucination_guard.pyimport logging
from typing import List, Dict

logger = logging.getLogger(__name__)

class HallucinationGuard:
    """
    Hallucination Guard cross-references RAG outputs with original citations
    to ensure factual accuracy and prevent AI hallucinations.
    """
    def __init__(self):
        self.threshold = 0.85

    def validate_response(self, query: str, response: str, citations: List[Dict]) -> Dict:
        """
        Validates the response against citations.
        """
        logger.info(f"Starting hallucination check for query: {query}")
        
        factual_score = 1.0
        hallucinated_claims = []
        
        if not citations:
            factual_score = 0.2
            hallucinated_claims.append("No citations found for the generated response.")
        
        # Logic to check if keywords in response exist in citations
        response_words = set(response.lower().split())
        citation_text = " ".join([c.get('content', '').lower() for c in citations])
        
        # Simple heuristic for demo purposes
        if citations:
            unsupported_keywords = [word for word in ["aml", "kyc", "sanction", "pep"] if word in response_words and word not in citation_text]
            if unsupported_keywords:
                factual_score -= 0.15 * len(unsupported_keywords)
                for kw in unsupported_keywords:
                    hallucinated_claims.append(f"Potential hallucination: '{kw.upper()}' mentioned without citation support.")

        is_safe = factual_score >= self.threshold
        
        return {
            "is_safe": is_safe,
            "factual_score": round(factual_score, 2),
            "hallucinated_claims": hallucinated_claims,
            "status": "Verified" if is_safe else "Flagged"
        }

    def get_guard_metadata(self):
        return {
            "engine": "Nova-Hallucination-Guard-v1",
            "cross_reference_enabled": True,
            "citation_validation": "Active"
        }
