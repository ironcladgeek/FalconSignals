"""Unit tests for the errors module."""

from src.utils.errors import (
    ErrorSeverity,
    NordInvestException,
    RateLimitException,
    RetryableException,
    is_retryable_error,
)


class TestErrorSeverity:
    """Test suite for ErrorSeverity enum."""

    def test_severity_values(self):
        """Test all severity values exist."""
        assert ErrorSeverity.INFO.value == "info"
        assert ErrorSeverity.WARNING.value == "warning"
        assert ErrorSeverity.ERROR.value == "error"
        assert ErrorSeverity.CRITICAL.value == "critical"


class TestNordInvestException:
    """Test suite for NordInvestException."""

    def test_basic_initialization(self):
        """Test basic exception initialization."""
        exc = NordInvestException("Something went wrong")

        assert exc.message == "Something went wrong"
        assert exc.severity == ErrorSeverity.ERROR
        assert exc.error_code == "UNKNOWN_ERROR"
        assert exc.context == {}

    def test_custom_severity(self):
        """Test exception with custom severity."""
        exc = NordInvestException("Warning!", severity=ErrorSeverity.WARNING)

        assert exc.severity == ErrorSeverity.WARNING

    def test_custom_error_code(self):
        """Test exception with custom error code."""
        exc = NordInvestException("Error", error_code="CUSTOM_CODE")

        assert exc.error_code == "CUSTOM_CODE"

    def test_with_context(self):
        """Test exception with context."""
        context = {"ticker": "AAPL", "operation": "fetch"}
        exc = NordInvestException("Error", context=context)

        assert exc.context == context

    def test_str_representation(self):
        """Test string representation."""
        exc = NordInvestException("Test error", error_code="TEST_CODE")

        result = str(exc)

        assert "[TEST_CODE]" in result
        assert "Test error" in result


class TestRetryableException:
    """Test suite for RetryableException."""

    def test_default_error_code(self):
        """Test default error code is RETRYABLE_ERROR."""
        exc = RetryableException("Network error")

        assert exc.error_code == "RETRYABLE_ERROR"

    def test_custom_error_code(self):
        """Test custom error code."""
        exc = RetryableException("Timeout", error_code="API_TIMEOUT")

        assert exc.error_code == "API_TIMEOUT"

    def test_inherits_from_nord_invest_exception(self):
        """Test RetryableException inherits correctly."""
        exc = RetryableException("Error")

        assert isinstance(exc, NordInvestException)


class TestRateLimitException:
    """Test suite for RateLimitException."""

    def test_default_initialization(self):
        """Test default initialization."""
        exc = RateLimitException("Rate limited")

        assert exc.error_code == "API_RATE_LIMIT"
        assert exc.message == "Rate limited"

    def test_with_provider(self):
        """Test exception with provider."""
        exc = RateLimitException("Rate limited", provider="yahoo")

        assert exc.context["provider"] == "yahoo"

    def test_without_provider(self):
        """Test exception without provider."""
        exc = RateLimitException("Rate limited")

        assert "provider" not in exc.context

    def test_with_existing_context(self):
        """Test exception with existing context dict merges provider."""
        # When context is passed, provider is added to it
        exc = RateLimitException("Rate limited", provider="finnhub")

        # Provider should be in context
        assert exc.context["provider"] == "finnhub"

    def test_inherits_from_retryable(self):
        """Test RateLimitException inherits correctly."""
        exc = RateLimitException("Error")

        assert isinstance(exc, RetryableException)
        assert isinstance(exc, NordInvestException)


class TestIsRetryableError:
    """Test suite for is_retryable_error function."""

    def test_retryable_exception(self):
        """Test RetryableException is retryable."""
        error = RetryableException("Network error")

        assert is_retryable_error(error) is True

    def test_rate_limit_exception(self):
        """Test RateLimitException is retryable."""
        error = RateLimitException("Too many requests")

        assert is_retryable_error(error) is True

    def test_nord_invest_with_retryable_code(self):
        """Test NordInvestException with retryable error code."""
        error = NordInvestException("Timeout", error_code="API_TIMEOUT")

        assert is_retryable_error(error) is True

    def test_nord_invest_with_non_retryable_code(self):
        """Test NordInvestException with non-retryable error code."""
        error = NordInvestException("Invalid input", error_code="VALIDATION_ERROR")

        assert is_retryable_error(error) is False

    def test_generic_exception_not_retryable(self):
        """Test generic exception is not retryable."""
        error = ValueError("Invalid value")

        assert is_retryable_error(error) is False

    def test_rate_limit_in_message(self):
        """Test exception with 'rate limit' in message is retryable."""
        error = RuntimeError("rate limit exceeded")

        assert is_retryable_error(error) is True

    def test_too_many_requests_in_message(self):
        """Test exception with 'too many requests' in message is retryable."""
        error = Exception("Error: too many requests made to API")

        assert is_retryable_error(error) is True

    def test_case_insensitive_rate_limit(self):
        """Test rate limit detection is case insensitive."""
        error = RuntimeError("RATE LIMIT EXCEEDED")

        assert is_retryable_error(error) is True

    def test_all_retryable_codes(self):
        """Test all retryable error codes."""
        retryable_codes = [
            "RETRYABLE_ERROR",
            "API_TIMEOUT",
            "API_RATE_LIMIT",
            "TEMPORARY_FAILURE",
            "CONNECTION_ERROR",
        ]

        for code in retryable_codes:
            error = NordInvestException("Test", error_code=code)
            assert is_retryable_error(error) is True, f"{code} should be retryable"
