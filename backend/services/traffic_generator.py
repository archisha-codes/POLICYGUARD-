import os
import json
import random
from datetime import datetime
from dotenv import load_dotenv

from services.gemini_client import get_llm_client

# Load environment variables
load_dotenv()

class TrafficGenerator:
    def __init__(self):
        try:
            self.llm = get_llm_client()
            print("✅ INFO:PolicyGuard-API: Gemini AI is ONLINE and working correctly.")
        except Exception as e:
            self.llm = None
            print(f"❌ ERROR:PolicyGuard-API: Gemini AI failed to initialize. Error: {e}")

    def generate_transaction(self, type="compliant"):
        """
        Generates a transaction based on the scenario:
        - compliant: Normal transaction
        - non_compliant: Clear violation (e.g., Sanctioned Country)
        - flagged: Suspicious pattern (e.g., Structuring/Smurfing)
        - escalated: Critical risk (e.g., Terror Financing/Dark Web)
        """
        # 1. Try Generating with AI
        if self.llm:
            prompt = f"""
            Generate a single realistic financial transaction in strict JSON format.
            The transaction scenario is: {type.upper()}.
            
            RULES FOR GENERATION:
            - If 'compliant': Use a normal amount (e.g., 500-50000), low risk country (US, IN, UK), and normal description (Salary, Rent).
            - If 'non_compliant': Use a sanctioned country (North Korea, Iran) OR an amount > 1,000,000.
            - If 'flagged': Use a suspicious description (e.g., 'structuring', 'cash deposit below threshold') OR an amount just below limit (e.g., 49,999).
            - If 'escalated': Use a high-risk description (e.g., 'shell company', 'facilitation payment', 'dark web') AND high amount.

            JSON Schema:
            {{
                "transaction_id": "TXN-[RANDOM_ALPHANUMERIC]",
                "amount": [FLOAT_VALUE],
                "currency": "INR",
                "source_account": "ACC-[RANDOM]",
                "destination_account": "ACC-[RANDOM]",
                "description": "[A REALISTIC NARRATIVE DESCRIPTION MATCHING THE SCENARIO]",
                "timestamp": "{datetime.utcnow().isoformat()}",
                "customer_id": "CUST-[RANDOM]",
                "transaction_type": "transfer/cash_deposit/wire_transfer/etc.",
                "simulation": true
            }}
            """

            try:
                response = self.llm.invoke(
                    prompt=prompt,
                    system_prompt="You are a strict data generator. Output ONLY valid JSON. No markdown formatting.",
                    temperature=0.8
                )
                
                if response["status"] == "success":
                    clean_text = response["text"].replace("```json", "").replace("```", "").strip()
                    return json.loads(clean_text)
            except Exception as e:
                print(f"⚠️ Error generating AI transaction: {e}. Switching to fallback.")
                
        # 2. Return Fallback if AI is missing or fails
        return self._get_fallback_transaction(type)

    def _get_fallback_transaction(self, type):
        """
        Hardcoded scenarios to ensure simulation works even without AI.
        """
        timestamp = datetime.utcnow().isoformat()
        random_id = int(datetime.utcnow().timestamp()) + random.randint(1, 1000)
        
        base_txn = {
            "transaction_id": f"TXN-FALLBACK-{random_id}",
            "currency": "INR",
            "timestamp": timestamp,
            "customer_id": f"CUST-FB-{random.randint(10,99)}",
            "transaction_type": "transfer",
            "source_account": "ACC-SOURCE-FALLBACK",
            "destination_account": "ACC-DEST-FALLBACK",
            "simulation": True
        }

        if type == "non_compliant":
            base_txn.update({
                "amount": 2500000.0, # High amount
                "description": "Transfer to North Korea based entity for goods",
                "destination_account": "ACC-NK-SANCTIONED"
            })
        elif type == "flagged":
            base_txn.update({
                "amount": 49900.0, # Just below threshold (structuring)
                "description": "Cash deposit just below reporting threshold",
                "transaction_type": "cash_deposit"
            })
        elif type == "escalated":
            base_txn.update({
                "amount": 5000000.0,
                "description": "Consultancy fee for facilitation payment to offshore shell company",
                "transaction_type": "wire_transfer"
            })
        else: # Compliant
            base_txn.update({
                "amount": float(random.randint(1000, 20000)),
                "description": "Monthly rent payment for apartment",
                "transaction_type": "transfer"
            })
            
        return base_txn