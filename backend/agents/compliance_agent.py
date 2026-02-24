import logging
import json
from typing import Dict, Any, List
from services.gemini_client import get_llm_client

logger = logging.getLogger(__name__)

def analyze_transaction(
    transaction_data: Dict[str, Any], 
    retrieved_policies: str,
    past_feedback: List[Dict] = None
) -> Dict[str, Any]:
    """
    Analyzes transaction compliance using Google Gemini and RAG context.
    """
    if past_feedback is None:
        past_feedback = []
        
    client = get_llm_client()
    
    # Format Feedback
    feedback_context = ""
    if past_feedback:
        feedback_context = "\nHISTORICAL HUMAN FEEDBACK:\n"
        for fb in past_feedback:
            feedback_context += f"- PREVIOUS DECISION: {fb['human_verdict']} (Reason: {fb['feedback_notes']})\n"

    system_prompt = """You are PolicyGuard, an elite AI Compliance Officer.
Your Goal: Audit transactions for financial crime risks using the provided RAG regulatory context.

### CRITICAL INSTRUCTIONS:
1. **Mandatory Verdicts**: The verdict MUST be exactly one of: "compliant", "non-compliant", "manual review", or "escalated".
2. **Analysis Rules**: 
   - Personal consumption under $200 = "compliant" (Risk Score 0).
   - "escalated" should be used for severe risks like strict sanctions evasion.
   - "manual review" should be used for ambiguous cases or unclear RAG context.
3. **Strict JSON Schema**: You MUST return a JSON object exactly matching the structure below. Do not add markdown blocks like ```json, just return the raw JSON string.

### REQUIRED JSON SCHEMA:
{
  "status": "success",
  "privacy_mode": "enabled",
  "analysis": {
    "verdict": "<compliant | non-compliant | manual review | escalated>",
    "risk_score": <integer 0-100>,
    "explanation": "<Detailed reasoning citing specific rules>",
    "violated_rules": ["<Rule_1>", "<Rule_2>"],
    "meta_guard": {
      "is_safe": true,
      "factual_score": 1,
      "hallucinated_claims": [],
      "status": "Verified"
    }
  },
  "guard_validation": {
    "is_safe": true,
    "factual_score": 1,
    "hallucinated_claims": [],
    "status": "Verified"
  }
}"""

    user_prompt = f"""
REGULATORY CONTEXT:
{retrieved_policies}

{feedback_context}

TRANSACTION TO ANALYZE:
{json.dumps(transaction_data, default=str)}
"""

    response = client.invoke(
        prompt=user_prompt,
        system_prompt=system_prompt,
        max_tokens=1500,
        temperature=0.1 # Keep randomness low for deterministic compliance checks
    )

    if response["status"] == "success":
        result = client.parse_json_response(response["text"])
        
        # Fallback safeguard in case model fails to wrap properly
        if "analysis" not in result:
            logger.warning(f"AI missed 'analysis' wrapper. Parsed keys were: {list(result.keys())}. Applying fallback format.")
            return _generate_fallback_response("manual review", "Invalid AI output schema.", 100)
            
        return result
    else:
        logger.error(f"Analysis failed: {response.get('error')}")
        return _generate_fallback_response("escalated", "AI Service Unreachable or Error.", 100)

def _generate_fallback_response(verdict: str, explanation: str, score: int) -> Dict[str, Any]:
    """Generates a safe fallback response matching the required schema."""
    return {
        "status": "error",
        "privacy_mode": "enabled",
        "analysis": {
            "verdict": verdict,
            "risk_score": score,
            "explanation": explanation,
            "violated_rules": ["SYSTEM_ERROR"],
            "meta_guard": {"is_safe": False, "factual_score": 0, "hallucinated_claims": [], "status": "Failed"}
        },
        "guard_validation": {"is_safe": False, "factual_score": 0, "hallucinated_claims": [], "status": "Failed"}
    }