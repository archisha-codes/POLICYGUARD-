import os
import json
import logging
import re
import google.generativeai as genai
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class GeminiClient:
    def __init__(self, model_id: str = "gemini-flash-latest"):
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            logger.warning("GOOGLE_API_KEY is not set in environment variables.")
        else:
            # Suppress the deprecation warning clutter in logs if using the old SDK
            import warnings
            warnings.filterwarnings("ignore", category=FutureWarning, module="google.generativeai")
            
        genai.configure(api_key=api_key)
        self.model_id = model_id

    def invoke(
        self,
        prompt: str,
        system_prompt: str = None,
        max_tokens: int = 1500,
        temperature: float = 0.1,
    ) -> Dict[str, Any]:
        """Original method: Enforces JSON output for agentic workflows."""
        try:
            model = genai.GenerativeModel(
                model_name=self.model_id,
                system_instruction=system_prompt
            )
            
            generation_config = genai.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
                response_mime_type="application/json"
            )

            safety_settings = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
            ]

            response = model.generate_content(
                prompt,
                generation_config=generation_config,
                safety_settings=safety_settings
            )
            
            if response.candidates and response.candidates[0].finish_reason.name != 'STOP':
                logger.warning(f"Generation stopped early! Reason: {response.candidates[0].finish_reason.name}")

            return {
                "status": "success",
                "text": response.text,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Gemini API Error: {str(e)}")
            return {
                "status": "error",
                "text": "",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }

    def invoke_chat(self, prompt: str, system_prompt: str = None, temperature: float = 0.7) -> str:
        """New method: Returns standard conversational text/markdown for the Chatbot."""
        try:
            model = genai.GenerativeModel(
                model_name=self.model_id,
                system_instruction=system_prompt
            )
            
            # Note: response_mime_type is omitted so Gemini returns standard conversational text
            generation_config = genai.GenerationConfig(
                temperature=temperature
            )

            response = model.generate_content(
                prompt,
                generation_config=generation_config
            )
            return response.text
            
        except Exception as e:
            logger.error(f"Gemini Chat API Error: {str(e)}")
            return "I apologize, but I encountered an error connecting to my knowledge base. Please try again later."

    def parse_json_response(self, response_text: str) -> Dict[str, Any]:
        if not response_text:
            return {}
            
        try:
            cleaned_text = response_text.strip()
            
            match = re.search(r'```(?:json)?\s*(.*?)\s*```', cleaned_text, re.DOTALL)
            if match:
                cleaned_text = match.group(1).strip()
            else:
                if cleaned_text.startswith("```json"):
                    cleaned_text = cleaned_text[7:]
                elif cleaned_text.startswith("```"):
                    cleaned_text = cleaned_text[3:]
                    
                if cleaned_text.endswith("```"):
                    cleaned_text = cleaned_text[:-3]
                    
                cleaned_text = cleaned_text.strip()

            return json.loads(cleaned_text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini JSON output: {e}\nRaw Output: {response_text}")
            return {}

# Singleton pattern setup
_gemini_client = None

def get_llm_client() -> GeminiClient:
    global _gemini_client
    if _gemini_client is None:
        _gemini_client = GeminiClient()
    return _gemini_client