from __future__ import annotations

import json
import logging
import os
import re
from typing import Any, Protocol

from django.conf import settings

logger = logging.getLogger(__name__)


class AIProvider(Protocol):
    def generate(
        self,
        prompt: str,
        *,
        max_tokens: int = 1024,
        response_json: bool = False,
        response_schema: dict[str, Any] | None = None,
    ) -> str: ...


class GeminiProvider:
    _client: Any = None

    def __init__(self, api_key: str, model: str) -> None:
        self.api_key = api_key
        self.model = model

    def _get_client(self) -> Any:
        if GeminiProvider._client is None:
            from google import genai

            GeminiProvider._client = genai.Client(api_key=self.api_key)
        return GeminiProvider._client

    def generate(
        self,
        prompt: str,
        *,
        max_tokens: int = 1024,
        response_json: bool = False,
        response_schema: dict[str, Any] | None = None,
    ) -> str:
        client = self._get_client()
        kwargs: dict[str, Any] = {
            "model": self.model,
            "contents": prompt,
        }
        
        config_dict: dict[str, Any] = {"max_output_tokens": max_tokens}
        
        if response_schema:
            config_dict["response_mime_type"] = "application/json"
            config_dict["response_schema"] = response_schema
        elif response_json:
            config_dict["response_mime_type"] = "application/json"
            
        kwargs["config"] = config_dict
        
        response = client.models.generate_content(**kwargs)
        return str(response.text or "Analysis currently unavailable.")


def get_provider() -> AIProvider:
    gemini_key = os.environ.get("GEMINI_API_KEY")
    if gemini_key:
        logger.info("Using Gemini AI provider")
        return GeminiProvider(
            api_key=gemini_key,
            model=settings.GEMINI_MODEL,
        )

    raise ValueError(
        "No AI API key configured. Set GEMINI_API_KEY in your .env file."
    )




def _strip_code_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        first_newline = text.find("\n")
        if first_newline != -1:
            text = text[first_newline + 1 :]
        if text.endswith("```"):
            text = text[:-3].strip()
    return text


def generate_analysis(
    prompt: str,
    *,
    max_tokens: int = 1024,
    response_json: bool = False,
    response_schema: dict[str, Any] | None = None,
) -> str | dict[str, Any]:
    provider = get_provider()
    raw = provider.generate(
        prompt,
        max_tokens=max_tokens,
        response_json=response_json,
        response_schema=response_schema,
    )
    if response_json or response_schema:
        cleaned = _strip_code_fences(raw)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            # Fallback: Try to find JSON block with regex
            match = re.search(r"(\{.*\})", cleaned, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1))
                except json.JSONDecodeError:
                    pass
            logger.error("Provider returned invalid JSON: %s", raw[:200])
            raise
    return raw
