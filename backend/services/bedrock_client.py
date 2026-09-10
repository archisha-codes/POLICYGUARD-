# backend/services/bedrock_client.py
# Centralized Bedrock (Amazon Nova) LLM client for POLICYGUARD

import os
import json
import boto3
import re
from typing import Dict, List, Any
from datetime import datetime


class BedrockNovaClient:
    """
    Bedrock Runtime client wrapper for Amazon Nova models.
    """

    def __init__(
        self,
        model_id: str = None,
        region_name: str = None,
        temperature: float = 0.0,
    ):
        self.model_id = model_id or os.getenv(
            "NOVA_MODEL_ID", "amazon.nova-micro-v1:0"
        )
        self.region_name = region_name or os.getenv(
            "BEDROCK_REGION", "us-east-1"
        )
        self.temperature = temperature
        self.client = boto3.client(
            "bedrock-runtime", region_name=self.region_name
        )

    def invoke(
        self,
        prompt: str,
        system_prompt: str = None,
        max_tokens: int = 1000,
        temperature: float = None,  # <--- ADDED THIS ARGUMENT
        top_p: float = 0.9,
    ) -> Dict[str, Any]:
        """
        Invoke Amazon Nova model with Messages API format.
        Allows overriding temperature per-request.
        """
        # Use the passed temperature if provided, otherwise use the class default
        active_temperature = temperature if temperature is not None else self.temperature

        try:
            body = {
                "messages": [
                    {
                        "role": "user",
                        "content": [{"text": prompt}]
                    }
                ],
                "inferenceConfig": {
                    "temperature": active_temperature, # <--- UPDATED THIS
                    "topP": top_p,
                    "max_new_tokens": max_tokens, 
                }
            }

            if system_prompt:
                body["system"] = [{"text": system_prompt}]

            response = self.client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(body),
                contentType="application/json",
                accept="application/json",
            )

            payload = json.loads(response["body"].read())
            
            # Check for content filtering (Guardrails)
            output = payload.get("output", {})
            message = output.get("message", {})
            content = message.get("content", [])
            stop_reason = payload.get("stopReason")
            
            response_text = ""
            if content and len(content) > 0:
                response_text = content[0].get("text", "")

            # If text is the specific error string you saw
            if "blocked by our content filters" in response_text:
                 return {
                    "status": "error",
                    "text": response_text,
                    "error": "Content Filter Triggered",
                    "timestamp": datetime.utcnow().isoformat(),
                }

            return {
                "status": "success",
                "text": response_text,
                "tokens_used": payload.get("usage", {}).get("totalTokens", "unknown"),
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            return {
                "status": "error",
                "text": "",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }

    def parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse JSON from model response, handling markdown code blocks.
        """
        response_text = response_text.strip()

        # Try direct parsing first
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            pass

        # Try extracting from code blocks
        match = re.search(r"```json(.*?)```", response_text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1).strip())
            except json.JSONDecodeError:
                pass

        # Return fallback with raw text
        return {
            "status": "parse_error",
            "raw_output": response_text[:500],
            "message": "Failed to parse JSON from response",
        }


_bedrock_client = None

def get_bedrock_client() -> BedrockNovaClient:
    global _bedrock_client
    if _bedrock_client is None:
        _bedrock_client = BedrockNovaClient()
    return _bedrock_client