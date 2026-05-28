import os
import json
import re
import warnings
import logging
from typing import Dict, Any, Optional
import litellm
from diatax.core.exceptions import LLMError, LLMNetworkError, LLMFormatError

# Silencing LiteLLM logs and help messages
warnings.filterwarnings("ignore")
logging.getLogger("litellm").setLevel(logging.ERROR)
litellm.set_verbose = False
litellm.suppress_debug_info = True
litellm.drop_params = True

class LLMService:
    """
    Unified service for interaction with Large Language Models.
    Abstracts different providers (Gemini, Groq, OpenAI) via LiteLLM.
    """

    def __init__(self):
        self._setup_environment()

    def _setup_environment(self):
        """Ensures that necessary variables are present for LiteLLM."""
        # Note: API Keys are handled by main.py and config.py using the system keyring.
        pass

    def send_request(self, prompt: str, system_prompt: str = "", model: str = "gemini/gemini-pro", schema: Dict = None) -> Dict[str, Any]:
        """
        Sends a request to the LLM and processes the response.
        Supports structured output via manual parsing if JSON mode is not available.
        """
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            response = litellm.completion(
                model=model,
                messages=messages,
                temperature=0.2,
                max_tokens=4000
            )

            content = response.choices[0].message.content

            if schema:
                # 1. Try to extract from markdown code blocks (best practice)
                json_block = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
                if json_block:
                    try:
                        return json.loads(json_block.group(1))
                    except json.JSONDecodeError:
                        pass # Try fallback regex

                # 2. Try to extract raw JSON object
                json_match = re.search(r'(\{.*\})', content, re.DOTALL)
                if json_match:
                    try:
                        # Clean common artifacts
                        clean_json = json_match.group(1).strip()
                        return json.loads(clean_json)
                    except json.JSONDecodeError:
                        raise LLMFormatError("The LLM returned a malformed JSON.")
                else:
                    # Special cases for boolean/simple results
                    if "approved" in content.lower():
                        return {"approved": True, "feedback": "", "improvements": []}
                    raise LLMFormatError("No structured JSON found in the LLM response.")

            return {"text": content}

        except Exception as e:
            if "litellm" in str(e).lower():
                raise LLMNetworkError(f"Network error in LLM: {str(e)}")
            raise LLMError(f"Unexpected error in LLMService: {str(e)}")

    def estimate_tokens(self, text: str) -> int:
        """Rough estimation of tokens based on character count (conservative)."""
        return len(text) // 4
