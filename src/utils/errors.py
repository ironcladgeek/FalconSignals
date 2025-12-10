"""Custom exceptions and error handling utilities."""

from enum import Enum


class ErrorSeverity(str, Enum):
    """Error severity levels."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class NordInvestException(Exception):
    """Base exception for NordInvest application."""

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


class DataProviderException(NordInvestException):
    """Exception from data providers."""

    def __init__(
        self,
        message: str,
        provider: str | None = None,
        error_code: str = "DATA_PROVIDER_ERROR",
        **kwargs,
    ):
        """Initialize data provider exception."""
        context = kwargs.get("context", {})
        if provider:
            context["provider"] = provider
        super().__init__(message, error_code=error_code, context=context)


class ConfigurationException(NordInvestException):
    """Exception from configuration issues."""

    def __init__(self, message: str, error_code: str = "CONFIG_ERROR", **kwargs):
        """Initialize configuration exception."""
        super().__init__(message, error_code=error_code, **kwargs)


class AnalysisException(NordInvestException):
    """Exception from analysis modules."""

    def __init__(self, message: str, error_code: str = "ANALYSIS_ERROR", **kwargs):
        """Initialize analysis exception."""
        super().__init__(message, error_code=error_code, **kwargs)


class CacheException(NordInvestException):
    """Exception from cache operations."""

    def __init__(self, message: str, error_code: str = "CACHE_ERROR", **kwargs):
        """Initialize cache exception."""
        super().__init__(message, error_code=error_code, **kwargs)


class APIException(NordInvestException):
    """Exception from API calls."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        error_code: str = "API_ERROR",
        **kwargs,
    ):
        """Initialize API exception."""
        context = kwargs.get("context", {})
        if status_code:
            context["status_code"] = status_code
        super().__init__(message, error_code=error_code, context=context)


class RetryableException(NordInvestException):
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


class FallbackException(NordInvestException):
    """Exception indicating fallback to alternative strategy."""

    def __init__(self, message: str, error_code: str = "FALLBACK_ERROR", **kwargs):
        """Initialize fallback exception."""
        super().__init__(message, error_code=error_code, **kwargs)


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

    if isinstance(error, NordInvestException):
        return error.error_code in retryable_codes

    # Check for rate limit errors in error message (yfinance RuntimeError)
    error_msg = str(error).lower()
    if "rate limit" in error_msg or "too many requests" in error_msg:
        return True

    return False


def should_fallback(error: Exception) -> bool:
    """Determine if fallback strategy should be used.

    Args:
        error: Exception to check

    Returns:
        True if fallback should be attempted
    """
    fallback_codes = [
        "DATA_PROVIDER_ERROR",
        "API_ERROR",
        "CONNECTION_ERROR",
    ]

    if isinstance(error, NordInvestException):
        return error.error_code in fallback_codes

    return False
