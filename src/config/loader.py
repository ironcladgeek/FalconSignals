"""Configuration loading and management."""

import os
from pathlib import Path

import yaml
from dotenv import load_dotenv

from .schemas import Config


class ConfigLoader:
    """Load and validate configuration from YAML files."""

    def __init__(self, config_path: str | Path | None = None):
        """Initialize configuration loader.

        Args:
            config_path: Path to config file. If None, tries config/local.yaml
                        then config/default.yaml in project root.
        """
        self.config_path = self._resolve_config_path(config_path)
        self._load_env()

    def _resolve_config_path(self, provided_path: str | Path | None) -> Path:
        """Resolve configuration file path.

        Args:
            provided_path: Explicitly provided config path

        Returns:
            Path to configuration file

        Raises:
            FileNotFoundError: If no config file is found
        """
        if provided_path:
            path = Path(provided_path)
            if path.exists():
                return path
            raise FileNotFoundError(f"Config file not found: {path}")

        # Try local config first, then default
        project_root = Path(__file__).parent.parent.parent
        local_config = project_root / "config" / "local.yaml"
        default_config = project_root / "config" / "default.yaml"

        if local_config.exists():
            return local_config
        if default_config.exists():
            return default_config

        raise FileNotFoundError(f"No config file found at {local_config} or {default_config}")

    def _load_env(self) -> None:
        """Load environment variables from .env file if present."""
        project_root = Path(__file__).parent.parent.parent
        env_file = project_root / ".env"

        if env_file.exists():
            load_dotenv(env_file)

    def load(self) -> Config:
        """Load and validate configuration.

        Returns:
            Validated Config object

        Raises:
            yaml.YAMLError: If YAML parsing fails
            ValueError: If configuration validation fails
        """
        with open(self.config_path, "r") as f:
            raw_config = yaml.safe_load(f)

        if raw_config is None:
            raw_config = {}

        # Expand environment variables in config
        raw_config = self._expand_env_vars(raw_config)

        # Validate and return config
        return Config(**raw_config)

    def _expand_env_vars(self, config: dict, prefix: str = "") -> dict:
        """Recursively expand environment variables in config.

        Supports ${VAR_NAME} syntax for environment variable substitution.

        Args:
            config: Configuration dictionary
            prefix: Current config path prefix for error messages

        Returns:
            Configuration with expanded environment variables
        """
        expanded = {}

        for key, value in config.items():
            current_path = f"{prefix}.{key}" if prefix else key

            if isinstance(value, dict):
                expanded[key] = self._expand_env_vars(value, current_path)
            elif isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                env_var = value[2:-1]
                env_value = os.getenv(env_var)
                if env_value is None:
                    raise ValueError(
                        f"Environment variable not found: {env_var} "
                        f"(required by config.{current_path})"
                    )
                expanded[key] = env_value
            else:
                expanded[key] = value

        return expanded

    def get_config_path(self) -> Path:
        """Get the resolved configuration file path.

        Returns:
            Path to configuration file
        """
        return self.config_path


def load_config(config_path: str | Path | None = None) -> Config:
    """Convenience function to load configuration.

    Args:
        config_path: Path to config file. If None, tries config/local.yaml
                    then config/default.yaml.

    Returns:
        Validated Config object

    Raises:
        FileNotFoundError: If no config file is found
        ValueError: If configuration validation fails
    """
    loader = ConfigLoader(config_path)
    return loader.load()
