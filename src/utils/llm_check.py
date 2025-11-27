"""Utility to check LLM configuration and warn about fallbacks."""

import os
from typing import Optional

from src.utils.logging import get_logger

logger = get_logger(__name__)


def check_llm_configuration() -> tuple[bool, Optional[str]]:
    """Check if LLM is properly configured.

    Returns:
        Tuple of (is_configured, provider_name)
        - is_configured: True if at least one LLM API key is found
        - provider_name: Name of the configured provider (e.g., 'Anthropic', 'OpenAI')
    """
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")

    if anthropic_key and anthropic_key != "your_anthropic_api_key_here":
        return True, "Anthropic"
    elif openai_key and openai_key != "your_openai_api_key_here":
        return True, "OpenAI"
    else:
        return False, None


def log_llm_status() -> bool:
    """Log LLM configuration status and return whether it's configured.

    Returns:
        True if LLM is configured, False otherwise
    """
    is_configured, provider = check_llm_configuration()

    if is_configured:
        logger.info(f"LLM configured: Using {provider} for AI-powered analysis")
        return True
    else:
        logger.warning(
            "⚠️  LLM NOT CONFIGURED - Using rule-based analysis fallback. "
            "Set ANTHROPIC_API_KEY or OPENAI_API_KEY environment variable for AI-powered analysis. "
            "See .env.sample for setup instructions."
        )
        return False


def get_fallback_warning_message() -> str:
    """Get the warning message for rule-based fallback mode.

    Returns:
        Formatted warning message
    """
    return (
        "⚠️  RULE-BASED MODE: No LLM configured.\n"
        "   Analysis uses technical indicators and simple rules only.\n"
        "   For AI-powered analysis, set ANTHROPIC_API_KEY in .env file.\n"
        "   See .env.sample for setup instructions."
    )
