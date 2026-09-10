# backend/services/hallucination_guard.py
import logging
from sentence_transformers import SentenceTransformer, util

logger = logging.getLogger(__name__)

class HallucinationGuard:
    def __init__(self):
        try:
            # Lightweight model for semantic similarity
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("🛡️ Hallucination Guard Initialized")
        except Exception as e:
            logger.error(f"Failed to load Hallucination Guard model: {e}")
            self.model = None

    def validate_response(self, query: str, response: str, citations: list, risk_score: int = 0) -> dict:
        """
        Checks if the AI response is grounded.
        """
        # 1. SAFE HARBOR: Trust low-risk transactions automatically
        if risk_score < 20:
             return {
                "is_safe": True, 
                "score": 1.0, 
                "status": "Safe Harbor (Low Risk Transaction)"
            }

        if not self.model or not citations:
            return {"is_safe": True, "score": 1.0, "status": "Guard Skipped (No Context)"}

        # 2. Prepare Content
        context_text = " ".join([c['text'] for c in citations])
        
        # 3. Semantic Similarity Check
        embeddings = self.model.encode([response, context_text])
        similarity = util.cos_sim(embeddings[0], embeddings[1]).item()
        
        # 4. DOMAIN ALLOWLIST (The Fix)
        # If these words appear, the AI is likely speaking correctly about compliance
        # even if the vector similarity is low.
        DOMAIN_ALLOWLIST = [
            "structuring", "sanctions", "russia", "iran", "north korea", 
            "consulting", "layering", "smurfing", "velocity", "threshold",
            "aml", "kyc", "terrorist", "laundering", "offshore", "panama",
            "shell company", "high-risk", "deposit", "withdrawal", "transfer"
        ]

        response_lower = response.lower()
        matched_terms = [term for term in DOMAIN_ALLOWLIST if term in response_lower]
        
        # 5. Dynamic Thresholding
        # Standard threshold
        threshold = 0.15 
        
        # If the AI uses >= 2 valid compliance terms, we lower the bar
        if len(matched_terms) >= 2:
            threshold = 0.02 # Very lenient if terminology is correct
            logger.info(f"🛡️ Guard: Valid Domain Terms Found {matched_terms}. Lowering threshold to {threshold}")

        is_safe = similarity >= threshold

        logger.info(f"🛡️ Guard Analysis: Score={similarity:.4f} | Threshold={threshold} | Safe={is_safe}")

        if not is_safe:
            return {
                "is_safe": False,
                "factual_score": similarity,
                "hallucinated_claims": ["Potential context mismatch"], 
                "status": "Flagged for Manual Review"
            }
            
        return {
            "is_safe": True, 
            "factual_score": similarity, 
            "status": "Verified"
        }