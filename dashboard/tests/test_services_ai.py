from __future__ import annotations

from unittest.mock import patch

import pytest

from dashboard.services.ai import (
    AnthropicProvider,
    GeminiProvider,
    generate_analysis,
    get_provider,
)


class TestGetProvider:
    @patch("dashboard.services.ai.os.environ.get")
    def test_returns_anthropic_when_key_set(self, mock_env_get):
        def env_side_effect(key, default=None):
            values = {"ANTHROPIC_API_KEY": "sk-ant-test123"}
            return values.get(key, default)

        mock_env_get.side_effect = env_side_effect
        provider = get_provider()
        assert isinstance(provider, AnthropicProvider)

    @patch("dashboard.services.ai.os.environ.get")
    def test_returns_gemini_when_only_gemini_key_set(self, mock_env_get):
        def env_side_effect(key, default=None):
            values = {"GEMINI_API_KEY": "test-gemini-key"}
            return values.get(key, default)

        mock_env_get.side_effect = env_side_effect
        provider = get_provider()
        assert isinstance(provider, GeminiProvider)

    @patch("dashboard.services.ai.os.environ.get")
    def test_raises_when_no_key_set(self, mock_env_get):
        mock_env_get.return_value = None
        with pytest.raises(ValueError, match="No AI API key configured"):
            get_provider()


class TestAnthropicProvider:
    def test_generates_text(self):
        provider = AnthropicProvider(
            api_key="sk-test", model="claude-sonnet-4-20250514"
        )
        with patch.object(provider, "_get_client") as mock_client_get:
            mock_client = mock_client_get.return_value
            mock_response = mock_client.messages.create.return_value
            mock_response.content = [type("obj", (), {"text": "Hello"})()]
            result = provider.generate("Say hello")
            assert result == "Hello"


class TestGeminiProvider:
    def test_generates_text(self):
        provider = GeminiProvider(api_key="test-key", model="gemini-2.5-flash")
        with patch.object(provider, "_get_client") as mock_client_get:
            mock_client = mock_client_get.return_value
            mock_response = mock_client.models.generate_content.return_value
            mock_response.text = "Hello"
            result = provider.generate("Say hello")
            assert result == "Hello"


class TestGenerateAnalysis:
    @patch("dashboard.services.ai.get_provider")
    def test_text_mode(self, mock_get_provider):
        mock_provider = mock_get_provider.return_value
        mock_provider.generate.return_value = "Analysis result"
        result = generate_analysis("Analyze BTC")
        assert result == "Analysis result"
        mock_provider.generate.assert_called_once_with(
            "Analyze BTC", max_tokens=1024, response_json=False
        )

    @patch("dashboard.services.ai.get_provider")
    def test_json_mode(self, mock_get_provider):
        mock_provider = mock_get_provider.return_value
        mock_provider.generate.return_value = '{"key": "value"}'
        result = generate_analysis("Return JSON", response_json=True)
        assert result == {"key": "value"}

    @patch("dashboard.services.ai.get_provider")
    def test_json_mode_strips_code_fences(self, mock_get_provider):
        mock_provider = mock_get_provider.return_value
        mock_provider.generate.return_value = (
            '```json\n{"key": "value"}\n```'
        )
        result = generate_analysis("Return JSON", response_json=True)
        assert result == {"key": "value"}
