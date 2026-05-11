from __future__ import annotations

import json
import logging
import os
from typing import Protocol

from django.conf import settings

logger = logging.getLogger(__name__)


class AIProvider(Protocol):
    def generate(
        self, prompt: str, *, max_tokens: int = 1024, response_json: bool = False
    ) -> str: ...


class AnthropicProvider:
    _client = None

    def __init__(self, api_key: str, model: str) -> None:
        self.api_key = api_key
        self.model = model

    def _get_client(self):
        if AnthropicProvider._client is None:
            import anthropic

            AnthropicProvider._client = anthropic.Anthropic(api_key=self.api_key)
        return AnthropicProvider._client

    def generate(
        self, prompt: str, *, max_tokens: int = 1024, response_json: bool = False
    ) -> str:
        client = self._get_client()
        extra_kwargs = {}
        if response_json:
            prompt += (
                "\n\nYou MUST respond with valid JSON only. "
                "No markdown formatting, no backticks, no explanation."
            )
            extra_kwargs["extra_headers"] = {"anthropic-beta": "max-tokens-3-5-sonnet-2024-07-15"}
        message = client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
            **extra_kwargs,
        )
        text = message.content[0].text
        return text


class GeminiProvider:
    _client = None

    def __init__(self, api_key: str, model: str) -> None:
        self.api_key = api_key
        self.model = model

    def _get_client(self):
        if GeminiProvider._client is None:
            from google import genai

            GeminiProvider._client = genai.Client(api_key=self.api_key)
        return GeminiProvider._client

    def generate(
        self, prompt: str, *, max_tokens: int = 1024, response_json: bool = False
    ) -> str:
        client = self._get_client()
        kwargs = {
            "model": self.model,
            "contents": prompt,
        }
        if response_json:
            kwargs["config"] = {
                "response_mime_type": "application/json",
                "max_output_tokens": max_tokens,
            }
        response = client.models.generate_content(**kwargs)
        return response.text or "Analysis currently unavailable."


def get_provider() -> AIProvider:
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    if anthropic_key:
        logger.info("Using Anthropic AI provider")
        return AnthropicProvider(
            api_key=anthropic_key,
            model=settings.ANTHROPIC_MODEL,
        )

    gemini_key = os.environ.get("GEMINI_API_KEY")
    if gemini_key:
        logger.info("Using Gemini AI provider")
        return GeminiProvider(
            api_key=gemini_key,
            model=settings.GEMINI_MODEL,
        )

    raise ValueError(
        "No AI API key configured. Set ANTHROPIC_API_KEY or GEMINI_API_KEY in your .env file."
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
    prompt: str, *, max_tokens: int = 1024, response_json: bool = False
) -> str | dict:
    provider = get_provider()
    raw = provider.generate(prompt, max_tokens=max_tokens, response_json=response_json)
    if response_json:
        cleaned = _strip_code_fences(raw)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            logger.error("Provider returned invalid JSON: %s", raw[:200])
            raise
    return raw
