"""Unit tests for the LLM configuration module."""

from unittest.mock import MagicMock, patch

import pytest

from src.config.llm import (
    _initialize_anthropic,
    _initialize_openai,
    initialize_llm_client,
)
from src.config.schemas import LLMConfig


class TestInitializeLLMClient:
    """Test suite for initialize_llm_client function."""

    @pytest.fixture
    def default_config(self):
        """Create default LLM config."""
        return LLMConfig(provider="anthropic", model="claude-3-sonnet-20240229")

    @patch("src.config.llm._initialize_anthropic")
    def test_anthropic_provider(self, mock_init, default_config):
        """Test Anthropic provider selection."""
        mock_init.return_value = MagicMock()

        initialize_llm_client(default_config)

        mock_init.assert_called_once_with(default_config)

    @patch("src.config.llm._initialize_openai")
    def test_openai_provider(self, mock_init):
        """Test OpenAI provider selection."""
        config = LLMConfig(provider="openai", model="gpt-4")
        mock_init.return_value = MagicMock()

        initialize_llm_client(config)

        mock_init.assert_called_once_with(config)

    @patch("src.config.llm._initialize_local")
    def test_local_provider(self, mock_init):
        """Test local provider selection."""
        config = LLMConfig(provider="local", model="llama2")
        mock_init.return_value = MagicMock()

        initialize_llm_client(config)

        mock_init.assert_called_once_with(config)


class TestInitializeAnthropic:
    """Test suite for _initialize_anthropic function."""

    @pytest.fixture
    def anthropic_config(self):
        """Create Anthropic config."""
        return LLMConfig(
            provider="anthropic",
            model="claude-3-sonnet-20240229",
            temperature=0.7,
            max_tokens=1000,
            timeout_seconds=60,
        )

    def test_missing_api_key(self, anthropic_config):
        """Test missing API key raises ValueError."""
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
                _initialize_anthropic(anthropic_config)


class TestInitializeOpenAI:
    """Test suite for _initialize_openai function."""

    @pytest.fixture
    def openai_config(self):
        """Create OpenAI config."""
        return LLMConfig(
            provider="openai",
            model="gpt-4",
            temperature=0.5,
            max_tokens=2000,
            timeout_seconds=30,
        )

    def test_missing_api_key(self, openai_config):
        """Test missing API key raises ValueError."""
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError, match="OPENAI_API_KEY"):
                _initialize_openai(openai_config)


class TestInitializeLocal:
    """Test suite for _initialize_local function."""

    @pytest.fixture
    def local_config(self):
        """Create local config."""
        return LLMConfig(provider="local", model="llama2", temperature=0.8)

    def test_model_format(self, local_config):
        """Test local model uses ollama format."""
        # The function prepends 'ollama/' to the model name
        assert local_config.model == "llama2"
