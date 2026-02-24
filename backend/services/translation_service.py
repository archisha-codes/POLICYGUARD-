# backend/services/translation_service.py
import logging
from typing import Dict, Tuple
from services.bedrock_client import get_bedrock_client

logger = logging.getLogger(__name__)

class TranslationService:
    """
    Enterprise Translation Layer using LLM (Granite/Nova).
    Ensures banking terminology is preserved during translation.
    """
    def __init__(self):
        self.client = get_bedrock_client()
        self.supported_languages = ["es", "fr", "zh", "hi", "de"] # Spanish, French, Chinese, Hindi, German

    def detect_and_translate(self, text: str) -> Tuple[str, str]:
        """
        Detects language and translates to English if necessary.
        Returns: (translated_text_en, original_language_code)
        """
        # Quick heuristic: If mostly ASCII, assume English (Optimization)
        if all(ord(c) < 128 for c in text.replace(" ", "")):
            return text, "en"

        prompt = f"""
        You are a Banking Translation Engine.
        Task: Identify the language of the text below and translate it to English.
        
        Input Text: "{text}"
        
        Output format (JSON):
        {{
            "detected_language": "code (e.g., es, hi, fr)",
            "translated_text": "English translation here"
        }}
        """
        
        try:
            response = self.client.invoke(prompt=prompt, max_tokens=200, temperature=0.0)
            if response["status"] == "success":
                data = self.client.parse_json_response(response["text"])
                return data.get("translated_text", text), data.get("detected_language", "en")
        except Exception as e:
            logger.error(f"Translation Error: {e}")
        
        return text, "en"  # Fallback

    def translate_back(self, text_en: str, target_lang: str) -> str:
        """Translates English response back to target language."""
        if target_lang == "en":
            return text_en
            
        prompt = f"""
        You are a Banking Translation Engine.
        Task: Translate this English compliance report to {target_lang}.
        Keep technical terms like 'AML', 'KYC', 'PEP' intact.
        
        Input: "{text_en}"
        
        Output: The translated text only.
        """
        
        try:
            response = self.client.invoke(prompt=prompt, max_tokens=1000, temperature=0.1)
            if response["status"] == "success":
                return response["text"].strip()
        except Exception as e:
            logger.error(f"Back-Translation Error: {e}")
            
        return text_en