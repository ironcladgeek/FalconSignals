"""Logging configuration and setup."""

import sys
from pathlib import Path

from loguru import logger

from src.config.schemas import LoggingConfig

# Remove default loguru handler to prevent premature logging during imports
logger.remove()


def setup_logging(config: LoggingConfig) -> None:
    """Configure logging based on configuration.

    Args:
        config: Logging configuration
    """
    # Remove any existing handlers (defensive, should already be removed at module init)
    logger.remove()

    # Create logs directory if it doesn't exist
    log_path = Path(config.log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Determine log format
    if config.format == "json":
        fmt = (
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        )
    else:
        fmt = (
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        )

    # Add console handler
    logger.add(
        sys.stdout,
        format=fmt,
        level=config.level,
        colorize=True,
        backtrace=True,
        diagnose=True,
    )

    # Add file handler with rotation
    logger.add(
        config.log_file,
        format=fmt,
        level=config.level,
        rotation=f"{config.max_log_size_mb} MB",
        retention=config.backup_count,
        backtrace=True,
        diagnose=True,
    )


def get_logger(name: str = __name__):
    """Get logger instance.

    Args:
        name: Logger name, typically __name__

    Returns:
        Configured logger instance
    """
    return logger.bind(name=name)
