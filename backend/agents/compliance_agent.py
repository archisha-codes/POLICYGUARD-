# backend/agents/compliance_agent.py
import os
from ibm_watsonx_ai.foundation_models import ModelInference
from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams
import json
import re

# Credentials from your prompt
WATSONX_API_KEY = "kSTCg7uk4kb7qM-OtpQBaI1vHGzLMBzHQxwer6BFPTQG"
PROJECT_ID = "633eed58-706c-487e-94c8-382b368feae3"
GenerateParams = {
    GenParams.DECODING_METHOD: "greedy",
    GenParams.MAX_NEW_TOKENS: 500,
    GenParams.MIN_NEW_TOKENS: 10,
    GenParams.TEMPERATURE: 0, # Deterministic for compliance
}

def analyze_with_granite(transaction_data, retrieved_policies):
    model = ModelInference(
        model_id="ibm/granite-13b-instruct-v2",
        params=GenerateParams,
        credentials={
            "apikey": WATSONX_API_KEY,
            "url": "https://eu-de.ml.cloud.ibm.com
        },
        project_id=PROJECT_ID
    )

    # Prompt Engineering (Strict JSON Output)
    prompt = f"""
    You are PolicyGuard, a strict financial compliance AI.
    Analyze the transaction against the provided regulatory rules.
    
    TRANSACTION:
    {transaction_data}

    REGULATORY RULES (CONTEXT):
    {retrieved_policies}

    TASK:
    Determine if this transaction violates any rules.
    Output purely valid JSON with keys: "verdict" (Compliant/Non-Compliant), "risk_score" (0-100), "explanation", "violated_rules".
    """

    response_text = model.generate_text(prompt=prompt)
    try:
        # Try to parse directly
        return json.loads(response_text)
    except json.JSONDecodeError:
        # If failed, look for code blocks
        match = re.search(r"```json(.*?)```", response_text, re.DOTALL)
        if match:
            return json.loads(match.group(1).strip())
        else:
            # Fallback if model fails to output JSON
            return {
                "verdict": "Manual Review",
                "risk_score": 50,
                "explanation": "AI output parsing failed. Raw: " + response_text[:100],
                "violated_rules": []
            }
