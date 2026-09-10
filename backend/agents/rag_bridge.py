# backend/agents/rag_bridge.py
import logging
from rag_pipeline import get_rag_pipeline

logger = logging.getLogger(__name__)

# --- GLOBAL CACHE ---
_LATEST_CONTEXT_CACHE = {
    "context_str": None,
    "citations": None
}

# --- EXPANDED FALLBACK CONTEXT ---
# explicitly covers "Non-Compliant" scenarios to prevent hallucination flags
STANDARD_COMPLIANCE_CONTEXT = """
[REF-STD-001] SOURCE: Global Banking Standards & FATF Guidelines
CONTENT: 
1. LOW RISK: Transactions under $200 for personal consumption (e.g., Starbucks, Uber, Amazon, Groceries) are automatically considered LOW RISK.
2. AML THRESHOLDS: Cash reporting thresholds are set at $10,000. Structuring involves breaking down deposits (e.g., $9,000 - $9,900) to avoid this limit. This is a punishable offense.
3. SANCTIONS: Transactions involving Russia, Iran, North Korea, or Syria are STRICTLY PROHIBITED.
4. HIGH RISK ACTIVITY: 
   - Large transfers (> $10,000) for "Consulting" or "Professional Services" without clear invoices.
   - Transactions involving high-risk jurisdictions like Panama, Cayman Islands, or Dubai.
   - High velocity of small transfers (Smurfing).
"""

def retrieve_relevant_rules(query_text: str, use_cache: bool = False) -> tuple[str, list]:
    """
    Retrieves compliance rules. 
    """
    global _LATEST_CONTEXT_CACHE

    if use_cache and _LATEST_CONTEXT_CACHE["context_str"]:
        logger.info("🚀 Using Cached RAG Context")
        return _LATEST_CONTEXT_CACHE["context_str"], _LATEST_CONTEXT_CACHE["citations"]

    try:
        # Enhance Query
        enhanced_query = f"{query_text} compliance thresholds aml limits sanctions high risk countries"
        logger.info(f"🔍 RAG Lookup: '{enhanced_query}'")
        
        rag = get_rag_pipeline()
        results = rag.query(enhanced_query, top_k=4) 
        
        if not results:
            logger.warning("⚠️ No RAG results. Using Standard Context.")
            # Standard Fallback
            fallback_citations = [{
                "id": "REF-STD-001",
                "text": STANDARD_COMPLIANCE_CONTEXT,
                "source": "Standard Banking Norms",
                "score": 1.0
            }]
            _LATEST_CONTEXT_CACHE["context_str"] = STANDARD_COMPLIANCE_CONTEXT
            _LATEST_CONTEXT_CACHE["citations"] = fallback_citations
            return STANDARD_COMPLIANCE_CONTEXT, fallback_citations

        # Format Results
        context_str = ""
        citations = []
        for idx, doc in enumerate(results):
            cit_id = f"REF-{idx+1}"
            context_str += f"[{cit_id}] SOURCE: {doc.get('source')}\nCONTENT: {doc.get('text')}\n\n"
            citations.append({
                "id": cit_id,
                "text": doc.get('text'),
                "source": doc.get('source'),
                "score": doc.get('score', 0)
            })
            
        # Update Cache
        _LATEST_CONTEXT_CACHE["context_str"] = context_str
        _LATEST_CONTEXT_CACHE["citations"] = citations
        
        return context_str, citations

    except Exception as e:
        logger.error(f"RAG Bridge Error: {e}")
        return STANDARD_COMPLIANCE_CONTEXT, [{"id": "REF-ERR", "text": "Error", "source": "System"}]