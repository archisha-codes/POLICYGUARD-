
"""
IBM Granite Prompt Template
Enforces STRICT structured JSON output
Phase-1 Prompt Engineering
Owner: Archisha
"""

SYSTEM_PROMPT = """
You are a Regulatory Compliance AI.
You MUST respond only in valid JSON.
No markdown. No explanations.
"""

USER_PROMPT = """
REGULATORY REQUIREMENT:
{requirement}

POLICY TEXT:
{policy_text}

Return EXACT JSON:
{{
  "compliance_status": "COMPLIANT | NON_COMPLIANT | PARTIALLY_COMPLIANT",
  "risk_score": number between 0 and 100,
  "justification": "short factual reason",
  "evidence": "exact quoted sentence(s)"
}}
"""
