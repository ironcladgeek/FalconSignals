"""LLM configuration and client initialization."""

import os

from src.config.schemas import LLMConfig
from src.utils.logging import get_logger

logger = get_logger(__name__)


def initialize_llm_client(config: LLMConfig):
    """Initialize LLM client based on configuration.

    Args:
        config: LLM configuration

    Returns:
        Initialized LLM client (CrewAI LLM object or LangChain client)

    Raises:
        ValueError: If provider is not supported or credentials are missing
    """
    provider = config.provider.lower()

    if provider == "anthropic":
        return _initialize_anthropic(config)
    elif provider == "openai":
        return _initialize_openai(config)
    elif provider == "local":
        return _initialize_local(config)
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")


def _initialize_anthropic(config: LLMConfig):
    """Initialize Anthropic Claude client.

    Args:
        config: LLM configuration

    Returns:
        Anthropic client

    Raises:
        ValueError: If ANTHROPIC_API_KEY is not set
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError(
            "ANTHROPIC_API_KEY environment variable not set. "
            "Please set it before using Anthropic provider."
        )

    try:
        from langchain_anthropic import ChatAnthropic

        client = ChatAnthropic(
            model=config.model,
            api_key=api_key,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            timeout=config.timeout_seconds,
        )
        logger.debug(f"Initialized Anthropic client with model: {config.model}")
        return client
    except ImportError:
        raise ValueError(
            "langchain-anthropic package not installed. "
            "Install it with: pip install langchain-anthropic"
        ) from None


def _initialize_openai(config: LLMConfig):
    """Initialize OpenAI client.

    Args:
        config: LLM configuration

    Returns:
        OpenAI client

    Raises:
        ValueError: If OPENAI_API_KEY is not set
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY environment variable not set. "
            "Please set it before using OpenAI provider."
        )

    try:
        from langchain_openai import ChatOpenAI

        client = ChatOpenAI(
            model=config.model,
            api_key=api_key,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            timeout=config.timeout_seconds,
        )
        logger.debug(f"Initialized OpenAI client with model: {config.model}")
        return client
    except ImportError:
        raise ValueError(
            "langchain-openai package not installed. Install it with: pip install langchain-openai"
        ) from None


def _initialize_local(config: LLMConfig):
    """Initialize local LLM client (Ollama) using CrewAI's LLM.

    Args:
        config: LLM configuration

    Returns:
        CrewAI LLM object configured for Ollama

    Raises:
        ValueError: If local LLM setup fails
    """
    try:
        from crewai.llm import LLM

        # CrewAI uses "ollama/model_name" format
        client = LLM(
            model=f"ollama/{config.model}",
            base_url="http://localhost:11434",
            temperature=config.temperature,
        )
        logger.info(f"Initialized local Ollama LLM with model: {config.model}")
        return client
    except ImportError:
        raise ValueError(
            "crewai or litellm package not installed. Install it with: pip install crewai litellm"
        ) from None
    except Exception as e:
        raise ValueError(
            f"Failed to initialize local LLM. Make sure Ollama is running (ollama serve) "
            f"and the model '{config.model}' is available (ollama list). Error: {e}"
        ) from e
