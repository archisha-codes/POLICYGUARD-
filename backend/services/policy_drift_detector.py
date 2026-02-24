import time
import uuid
import json
from datetime import datetime

# Import Gemini Client
try:
    from services.gemini_client import get_llm_client
except ImportError:
    from gemini_client import get_llm_client


class PolicyDriftDetector:
    """
    OpenSearch-free Policy Drift Detector.
    Uses in-memory storage instead of external vector DB.
    """

    # In-memory simulated drift store
    _simulated_drifts = []

    def __init__(self):
        # OpenSearch completely removed
        self.client = None

    # ---------------------------------------------------
    # DRIFT CHECK
    # ---------------------------------------------------
    def check_for_drift(self, simulate=False):

        if simulate:
            return self.simulate_drift()

        # Return latest simulated drift if exists
        if self._simulated_drifts:
            latest = self._simulated_drifts[-1]
            return {
                "status": "active",
                "drift_id": latest["drift_id"],
                "message": "Active policy drift detected.",
                "details": latest["content"]
            }

        return {
            "status": "stable",
            "message": "No policy drift detected. System operating normally."
        }

    # ---------------------------------------------------
    # DRIFT SIMULATION (Gemini Powered)
    # ---------------------------------------------------
    def simulate_drift(self):

        drift_id = f"DRIFT-SIM-{int(time.time())}"

        llm = get_llm_client()

        prompt = f"""
        You are a strict financial regulatory authority (RBI, SEC, FATF).
        Generate a brand new regulatory amendment.

        Mention this simulation ID exactly once: {drift_id}

        Return STRICT JSON format:
        {{
            "document_name": "string",
            "section": "string",
            "content": "detailed regulatory amendment text"
        }}
        """

        response = llm.invoke(prompt=prompt, temperature=0.8)

        # Default fallback
        document_name = f"Regulatory_Update_{datetime.now().year}_SIMULATION.pdf"
        section = "Section 4.2 - Enhanced Due Diligence"
        content = f"""
        [SIMULATED AMENDMENT {drift_id}]
        Enhanced Due Diligence required for all cross-border
        transactions exceeding INR 4,50,000.
        """

        if response.get("status") == "success":
            try:
                ai_data = llm.parse_json_response(response["text"])
                if ai_data:
                    document_name = ai_data.get("document_name", document_name)
                    section = ai_data.get("section", section)
                    content = ai_data.get("content", content)
            except Exception as e:
                print(f"⚠️ Gemini parse failed: {e}")

        # Store drift in memory instead of OpenSearch
        drift_record = {
            "drift_id": drift_id,
            "document": document_name,
            "section": section,
            "content": content,
            "timestamp": datetime.utcnow().isoformat()
        }

        self._simulated_drifts.append(drift_record)

        print(f"✅ Drift simulated (memory mode): {drift_id}")

        return {
            "status": "active",
            "drift_id": drift_id,
            "message": "New regulatory amendment detected.",
            "details": content
        }

    # ---------------------------------------------------
    # CLEAR SIMULATIONS
    # ---------------------------------------------------
    def clear_simulations(self):
        self._simulated_drifts.clear()
        return {
            "status": "cleared",
            "message": "All simulated drifts cleared."
        }