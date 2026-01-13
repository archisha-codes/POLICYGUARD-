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
    Handles model invocation, error handling, and response parsing.
    """

    def __init__(
        self,
        model_id: str = None,
        region_name: str = None,
        temperature: float = 0.0,
    ):
        """
        Initialize Bedrock Nova client with configuration from environment.
        
        Args:
            model_id: Nova model ID (e.g., amazon.nova-micro-v1:0)
            region_name: AWS region for Bedrock (e.g., us-east-1)
            temperature: Sampling temperature (0.0-1.0, 0 for deterministic)
        """
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
        max_tokens: int = 512,
        top_p: float = 0.9,
    ) -> Dict[str, Any]:
        """
        Invoke Amazon Nova model with given prompt.
        
        Args:
            prompt: User prompt
            system_prompt: System instructions (optional)
            max_tokens: Maximum tokens in response
            top_p: Top-P sampling parameter
        
        Returns:
            dict: Response with status, text, and metadata
        """
        try:
            body = {
                "inputText": prompt,
                "textGenerationConfig": {
                    "temperature": self.temperature,
                    "topP": top_p,
                    "maxTokenCount": max_tokens,
                },
            }

            if system_prompt:
                body["system"] = system_prompt

            response = self.client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(body),
                contentType="application/json",
                accept="application/json",
            )

            payload = json.loads(response["body"].read())
            response_text = (
                payload.get("outputText")
                or payload.get("results", [{}])[0].get("outputText", "")
            )

            return {
                "status": "success",
                "text": response_text,
                "tokens_used": response.get("ResponseMetadata", {}).get(
                    "HTTPHeaders", {}
                ).get("x-amzn-bedrock-output-tokens", "unknown"),
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
        
        Args:
            response_text: Raw response text from model
        
        Returns:
            dict: Parsed JSON or fallback structure
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


# Singleton instance for application-wide use
_bedrock_client = None


def get_bedrock_client() -> BedrockNovaClient:
    """Get or create global Bedrock Nova client instance."""
    global _bedrock_client
    if _bedrock_client is None:
        _bedrock_client = BedrockNovaClient()
    return _bedrock_client


def health_check() -> Dict[str, Any]:
    """Test Bedrock connectivity with a simple prompt."""
    client = get_bedrock_client()
    result = client.invoke(
        prompt='Return JSON: {"status": "ok", "model": "nova"}',
        max_tokens=64,
    )
    return result
