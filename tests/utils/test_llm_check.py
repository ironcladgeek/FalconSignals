"""Tests for LLM configuration checking utilities."""

import os
from unittest.mock import patch

import pytest

from src.utils.llm_check import (
    check_llm_configuration,
    get_fallback_warning_message,
    log_llm_status,
)


@pytest.mark.unit
class TestCheckLLMConfiguration:
    """Test LLM configuration checking."""

    @patch.dict(os.environ, {}, clear=True)
    def test_check_llm_configuration_no_provider_no_keys(self):
        """Test checking configuration with no provider and no keys."""
        is_configured, provider = check_llm_configuration()
        assert not is_configured
        assert provider is None

    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test_key"}, clear=True)
    def test_check_llm_configuration_anthropic_available(self):
        """Test checking configuration with Anthropic key available."""
        is_configured, provider = check_llm_configuration()
        assert is_configured
        assert provider == "Anthropic"

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"}, clear=True)
    def test_check_llm_configuration_openai_available(self):
        """Test checking configuration with OpenAI key available."""
        is_configured, provider = check_llm_configuration()
        assert is_configured
        assert provider == "OpenAI"

    @patch.dict(
        os.environ, {"ANTHROPIC_API_KEY": "test_key", "OPENAI_API_KEY": "test_key"}, clear=True
    )
    def test_check_llm_configuration_anthropic_preferred(self):
        """Test that Anthropic is preferred when both keys are available."""
        is_configured, provider = check_llm_configuration()
        assert is_configured
        assert provider == "Anthropic"

    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "your_anthropic_api_key_here"}, clear=True)
    def test_check_llm_configuration_placeholder_key_ignored(self):
        """Test that placeholder keys are ignored."""
        is_configured, provider = check_llm_configuration()
        assert not is_configured
        assert provider is None

    def test_check_llm_configuration_local_provider(self):
        """Test checking configuration for local provider."""
        is_configured, provider = check_llm_configuration("local")
        assert is_configured
        assert provider == "Local"

    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test_key"}, clear=True)
    def test_check_llm_configuration_specific_anthropic_provider(self):
        """Test checking configuration for specific Anthropic provider."""
        is_configured, provider = check_llm_configuration("anthropic")
        assert is_configured
        assert provider == "Anthropic"

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"}, clear=True)
    def test_check_llm_configuration_specific_openai_provider(self):
        """Test checking configuration for specific OpenAI provider."""
        is_configured, provider = check_llm_configuration("openai")
        assert is_configured
        assert provider == "OpenAI"

    @patch.dict(os.environ, {}, clear=True)
    def test_check_llm_configuration_specific_provider_not_available(self):
        """Test checking configuration for specific provider when not available."""
        is_configured, provider = check_llm_configuration("anthropic")
        assert not is_configured
        assert provider is None

    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "your_anthropic_api_key_here"}, clear=True)
    def test_check_llm_configuration_specific_provider_placeholder_ignored(self):
        """Test that placeholder keys are ignored for specific providers."""
        is_configured, provider = check_llm_configuration("anthropic")
        assert not is_configured
        assert provider is None


@pytest.mark.unit
class TestLogLLMStatus:
    """Test LLM status logging."""

    @patch("src.utils.llm_check.logger")
    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test_key"}, clear=True)
    def test_log_llm_status_configured(self, mock_logger):
        """Test logging when LLM is configured."""
        result = log_llm_status()
        assert result is True
        mock_logger.info.assert_called_once_with(
            "LLM configured: Using Anthropic for AI-powered analysis"
        )

    @patch("src.utils.llm_check.logger")
    @patch.dict(os.environ, {}, clear=True)
    def test_log_llm_status_not_configured(self, mock_logger):
        """Test logging when LLM is not configured."""
        result = log_llm_status()
        assert result is False
        mock_logger.warning.assert_called_once()

    @patch("src.utils.llm_check.logger")
    @patch.dict(os.environ, {}, clear=True)
    def test_log_llm_status_local_provider_not_available(self, mock_logger):
        """Test logging for local provider when not available."""
        result = log_llm_status("local")
        assert result is True  # Local provider is always considered "configured"
        # Note: Currently local provider logs info when "configured", not warning
        mock_logger.info.assert_called_once_with(
            "LLM configured: Using Local for AI-powered analysis"
        )


@pytest.mark.unit
class TestGetFallbackWarningMessage:
    """Test fallback warning message generation."""

    def test_get_fallback_warning_message_default(self):
        """Test default fallback warning message."""
        message = get_fallback_warning_message()
        assert "RULE-BASED MODE" in message
        assert "ANTHROPIC_API_KEY" in message
        assert "OPENAI_API_KEY" in message

    def test_get_fallback_warning_message_local_provider(self):
        """Test fallback warning message for local provider."""
        message = get_fallback_warning_message("local")
        assert "Local LLM not available" in message
        assert "ollama serve" in message
        assert "ollama list" in message

    def test_get_fallback_warning_message_case_insensitive(self):
        """Test that provider name is case insensitive."""
        message1 = get_fallback_warning_message("LOCAL")
        message2 = get_fallback_warning_message("local")
        assert message1 == message2

    def test_get_fallback_warning_message_other_provider(self):
        """Test fallback warning message for other providers."""
        message = get_fallback_warning_message("anthropic")
        assert "RULE-BASED MODE" in message
        assert "No LLM configured" in message


@pytest.mark.unit
class TestEnvironmentVariableHandling:
    """Test environment variable handling."""

    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "valid_key"}, clear=True)
    def test_valid_anthropic_key_recognized(self):
        """Test that valid Anthropic keys are recognized."""
        is_configured, provider = check_llm_configuration("anthropic")
        assert is_configured
        assert provider == "Anthropic"

    @patch.dict(os.environ, {"OPENAI_API_KEY": "valid_key"}, clear=True)
    def test_valid_openai_key_recognized(self):
        """Test that valid OpenAI keys are recognized."""
        is_configured, provider = check_llm_configuration("openai")
        assert is_configured
        assert provider == "OpenAI"

    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": ""}, clear=True)
    def test_empty_anthropic_key_ignored(self):
        """Test that empty Anthropic keys are ignored."""
        is_configured, provider = check_llm_configuration("anthropic")
        assert not is_configured
        assert provider is None

    @patch.dict(os.environ, {"OPENAI_API_KEY": ""}, clear=True)
    def test_empty_openai_key_ignored(self):
        """Test that empty OpenAI keys are ignored."""
        is_configured, provider = check_llm_configuration("openai")
        assert not is_configured
        assert provider is None
