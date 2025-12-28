"""Utility to check LLM configuration and warn about fallbacks."""

import os
from typing import Optional

from src.utils.logging import get_logger

logger = get_logger(__name__)


def check_llm_configuration(provider: Optional[str] = None) -> tuple[bool, Optional[str]]:
    """Check if LLM is properly configured.

    Args:
        provider: Optional provider name to check (anthropic, openai, local)
                 If None, checks all providers

    Returns:
        Tuple of (is_configured, provider_name)
        - is_configured: True if LLM is properly configured
        - provider_name: Name of the configured provider (e.g., 'Anthropic', 'OpenAI', 'Local')
    """
    # If provider is specified, check only that provider
    if provider:
        provider_lower = provider.lower()
        if provider_lower == "local":
            # Local provider doesn't need API keys
            return True, "Local"
        elif provider_lower == "anthropic":
            anthropic_key = os.getenv("ANTHROPIC_API_KEY")
            if anthropic_key and anthropic_key != "your_anthropic_api_key_here":
                return True, "Anthropic"
        elif provider_lower == "openai":
            openai_key = os.getenv("OPENAI_API_KEY")
            if openai_key and openai_key != "your_openai_api_key_here":
                return True, "OpenAI"
        return False, None

    # Check all providers if none specified
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")

    if anthropic_key and anthropic_key != "your_anthropic_api_key_here":
        return True, "Anthropic"
    elif openai_key and openai_key != "your_openai_api_key_here":
        return True, "OpenAI"
    else:
        return False, None


def log_llm_status(provider: Optional[str] = None) -> bool:
    """Log LLM configuration status and return whether it's configured.

    Args:
        provider: Optional provider name to check (anthropic, openai, local)

    Returns:
        True if LLM is configured, False otherwise
    """
    is_configured, provider_name = check_llm_configuration(provider)

    if is_configured:
        logger.info(f"LLM configured: Using {provider_name} for AI-powered analysis")
        return True
    else:
        if provider and provider.lower() == "local":
            logger.warning(
                "⚠️  LOCAL LLM NOT AVAILABLE - Using rule-based analysis fallback. "
                "Make sure Ollama is running with: ollama serve"
            )
        else:
            logger.warning(
                "⚠️  LLM NOT CONFIGURED - Using rule-based analysis fallback. "
                "Set ANTHROPIC_API_KEY or OPENAI_API_KEY environment variable for AI-powered analysis, "
                "or configure provider: local in config to use Ollama. "
                "See .env.sample for setup instructions."
            )
        return False


def get_fallback_warning_message(provider: Optional[str] = None) -> str:
    """Get the warning message for rule-based fallback mode.

    Args:
        provider: Optional provider name that was attempted

    Returns:
        Formatted warning message
    """
    if provider and provider.lower() == "local":
        return (
            "⚠️  RULE-BASED MODE: Local LLM not available.\n"
            "   Make sure Ollama is running: ollama serve\n"
            "   Then verify your model is available: ollama list\n"
            "   Pull models with: ollama pull llama3.1:8b"
        )
    else:
        return (
            "⚠️  RULE-BASED MODE: No LLM configured.\n"
            "   Analysis uses technical indicators and simple rules only.\n"
            "   Options:\n"
            "   - Set ANTHROPIC_API_KEY in .env for Anthropic Claude\n"
            "   - Set OPENAI_API_KEY in .env for OpenAI GPT\n"
            "   - Set provider: local in config and run: ollama serve\n"
            "   See .env.sample for setup instructions."
        )
