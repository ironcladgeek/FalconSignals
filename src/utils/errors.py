"""Custom exceptions and error handling utilities."""

from enum import Enum


class ErrorSeverity(str, Enum):
    """Error severity levels."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class FalconSignalsException(Exception):
    """Base exception for FalconSignals application."""

    def __init__(
        self,
        message: str,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        error_code: str | None = None,
        context: dict | None = None,
    ):
        """Initialize exception.

        Args:
            message: Error message
            severity: Error severity level
            error_code: Optional error code for classification
            context: Optional context dictionary
        """
        self.message = message
        self.severity = severity
        self.error_code = error_code or "UNKNOWN_ERROR"
        self.context = context or {}
        super().__init__(self.message)

    def __str__(self) -> str:
        """Return string representation."""
        return f"[{self.error_code}] {self.message}"


class RetryableException(FalconSignalsException):
    """Exception that indicates operation should be retried."""

    def __init__(self, message: str, error_code: str = "RETRYABLE_ERROR", **kwargs):
        """Initialize retryable exception."""
        super().__init__(message, error_code=error_code, **kwargs)


class RateLimitException(RetryableException):
    """Exception for API rate limit errors requiring exponential backoff."""

    def __init__(self, message: str, provider: str | None = None, **kwargs):
        """Initialize rate limit exception.

        Args:
            message: Error message
            provider: Name of the provider that was rate limited
            **kwargs: Additional context
        """
        context = kwargs.get("context", {})
        if provider:
            context["provider"] = provider
        super().__init__(message, error_code="API_RATE_LIMIT", context=context, **kwargs)


def is_retryable_error(error: Exception) -> bool:
    """Determine if error is retryable.

    Args:
        error: Exception to check

    Returns:
        True if error should be retried
    """
    retryable_codes = [
        "RETRYABLE_ERROR",
        "API_TIMEOUT",
        "API_RATE_LIMIT",
        "TEMPORARY_FAILURE",
        "CONNECTION_ERROR",
    ]

    if isinstance(error, FalconSignalsException):
        return error.error_code in retryable_codes

    # Check for rate limit errors in error message (yfinance RuntimeError)
    error_msg = str(error).lower()
    if "rate limit" in error_msg or "too many requests" in error_msg:
        return True

    return False
