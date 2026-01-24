# backend/agents/compliance_agent.py
# Amazon Bedrock (Nova) Integration - Replaces IBM Granite
import os
import json
import boto3
import re

# Bedrock Configuration
BEDROCK_REGION = os.getenv("BEDROCK_REGION", "us-east-1")
NOVA_MODEL_ID = os.getenv("NOVA_MODEL_ID", "amazon.Nova-micro-v1:0")

# Initialize Bedrock Runtime client
# Uses IAM role from compute environment (EC2, Lambda, ECS, etc.)
bedrock = boto3.client("bedrock-runtime", region_name=BEDROCK_REGION)


def call_nova_for_compliance(transaction_data: str, retrieved_policies: str) -> dict:
    """
    Analyzes transaction compliance using Amazon Nova on Bedrock.
    Replaces the previous IBM Granite integration.
    
    Args:
        transaction_data: Transaction details to analyze
        retrieved_policies: Relevant regulatory policies from OpenSearch
    
    Returns:
        dict: Compliance verdict with risk score and explanation
    """
    system_instructions = """
You are PolicyGuard, a strict financial compliance AI.
Analyze transactions against Indian RBI, AML, and PMLA regulations.

Return STRICTLY valid JSON with these keys:
- verdict: "Compliant" | "Non-Compliant" | "Manual Review"
- risk_score: integer 0-100
- explanation: brief reasoning
- violated_rules: list of violated rule references

Do not include any text outside JSON.
"""

    user_prompt = f"""
TRANSACTION:
{transaction_data}

REGULATORY RULES (CONTEXT):
{retrieved_policies}

TASK:
Determine if this transaction violates any rules.
Output purely valid JSON with keys: "verdict" (Compliant/Non-Compliant), "risk_score" (0-100), "explanation", "violated_rules".
"""

    body = {
        "inputText": user_prompt,
        "textGenerationConfig": {
            "temperature": 0.0,  # Deterministic for compliance
            "topP": 0.9,
            "maxTokenCount": 512,
        },
        "system": system_instructions,
    }

    try:
        response = bedrock.invoke_model(
            modelId=NOVA_MODEL_ID,
            body=json.dumps(body),
            contentType="application/json",
            accept="application/json",
        )

        payload = json.loads(response["body"].read())
        response_text = payload.get("outputText") or payload.get("results", [{}])[0].get("outputText", "")
        response_text = response_text.strip()

        # Try to parse JSON directly
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            # If failed, look for JSON in code blocks
            match = re.search(r"```json(.*?)```", response_text, re.DOTALL)
            if match:
                return json.loads(match.group(1).strip())
            else:
                # Fallback if model fails to output JSON
                return {
                    "verdict": "Manual Review",
                    "risk_score": 50,
                    "explanation": "AI output parsing failed. Raw: " + response_text[:100],
                    "violated_rules": [],
                }

    except Exception as e:
        # Handle Bedrock API errors
        return {
            "verdict": "Manual Review",
            "risk_score": 50,
            "explanation": f"Bedrock API error: {str(e)}",
            "violated_rules": [],
        }


def analyze_with_granite(transaction_data, retrieved_policies):
    """
    Deprecated: Use call_nova_for_compliance instead.
    Kept for backward compatibility during migration phase.
    """
    return call_nova_for_compliance(transaction_data, retrieved_policies)
