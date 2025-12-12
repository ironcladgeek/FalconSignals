"""Configuration management system."""

from .loader import ConfigLoader, load_config
from .schemas import Config

__all__ = ["Config", "ConfigLoader", "load_config", "get_config"]

# Singleton config instance
_config_instance: Config | None = None


def get_config() -> Config:
    """Get the singleton configuration instance.

    Returns:
        The loaded Config object

    Raises:
        RuntimeError: If config hasn't been loaded yet
    """
    global _config_instance

    if _config_instance is None:
        # Lazy load on first access
        _config_instance = load_config()

    return _config_instance
