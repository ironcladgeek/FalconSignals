"""Tests for error handling utilities."""

import pytest

from src.utils.errors import (
    AnalysisException,
    APIException,
    CacheException,
    ConfigurationException,
    DataProviderException,
    ErrorSeverity,
    FallbackException,
    NordInvestException,
    RetryableException,
    is_retryable_error,
    should_fallback,
)


@pytest.mark.unit
class TestErrorSeverity:
    """Test ErrorSeverity enum."""

    def test_error_severity_values(self):
        """Test that ErrorSeverity has expected values."""
        assert ErrorSeverity.INFO == "info"
        assert ErrorSeverity.WARNING == "warning"
        assert ErrorSeverity.ERROR == "error"
        assert ErrorSeverity.CRITICAL == "critical"


@pytest.mark.unit
class TestNordInvestException:
    """Test base NordInvestException class."""

    def test_exception_initialization_basic(self):
        """Test basic exception initialization."""
        exc = NordInvestException("Test error")

        assert exc.message == "Test error"
        assert exc.severity == ErrorSeverity.ERROR
        assert exc.error_code == "UNKNOWN_ERROR"
        assert exc.context == {}

    def test_exception_initialization_full(self):
        """Test exception initialization with all parameters."""
        context = {"key": "value"}
        exc = NordInvestException(
            "Test error", severity=ErrorSeverity.WARNING, error_code="TEST_ERROR", context=context
        )

        assert exc.message == "Test error"
        assert exc.severity == ErrorSeverity.WARNING
        assert exc.error_code == "TEST_ERROR"
        assert exc.context == context

    def test_exception_string_representation(self):
        """Test exception string representation."""
        exc = NordInvestException("Test error", error_code="TEST_ERROR")
        assert str(exc) == "[TEST_ERROR] Test error"

    def test_exception_defaults(self):
        """Test exception default values."""
        exc = NordInvestException("Test")
        assert exc.severity == ErrorSeverity.ERROR
        assert exc.error_code == "UNKNOWN_ERROR"
        assert exc.context == {}


@pytest.mark.unit
class TestSpecificExceptions:
    """Test specific exception types."""

    def test_data_provider_exception(self):
        """Test DataProviderException."""
        exc = DataProviderException("Provider failed", provider="yahoo")

        assert exc.error_code == "DATA_PROVIDER_ERROR"
        assert exc.context["provider"] == "yahoo"
        assert isinstance(exc, NordInvestException)

    def test_configuration_exception(self):
        """Test ConfigurationException."""
        exc = ConfigurationException("Config error")

        assert exc.error_code == "CONFIG_ERROR"
        assert isinstance(exc, NordInvestException)

    def test_analysis_exception(self):
        """Test AnalysisException."""
        exc = AnalysisException("Analysis failed")

        assert exc.error_code == "ANALYSIS_ERROR"
        assert isinstance(exc, NordInvestException)

    def test_cache_exception(self):
        """Test CacheException."""
        exc = CacheException("Cache error")

        assert exc.error_code == "CACHE_ERROR"
        assert isinstance(exc, NordInvestException)

    def test_api_exception(self):
        """Test APIException."""
        exc = APIException("API failed", status_code=500)

        assert exc.error_code == "API_ERROR"
        assert exc.context["status_code"] == 500
        assert isinstance(exc, NordInvestException)

    def test_retryable_exception(self):
        """Test RetryableException."""
        exc = RetryableException("Temporary failure")

        assert exc.error_code == "RETRYABLE_ERROR"
        assert isinstance(exc, NordInvestException)

    def test_fallback_exception(self):
        """Test FallbackException."""
        exc = FallbackException("Fallback needed")

        assert exc.error_code == "FALLBACK_ERROR"
        assert isinstance(exc, NordInvestException)


@pytest.mark.unit
class TestErrorClassification:
    """Test error classification functions."""

    def test_is_retryable_error_retryable_exception(self):
        """Test that RetryableException is retryable."""
        exc = RetryableException("Retry me")
        assert is_retryable_error(exc)

    def test_is_retryable_error_api_timeout(self):
        """Test that API timeout errors are retryable."""
        exc = APIException("Timeout", error_code="API_TIMEOUT")
        assert is_retryable_error(exc)

    def test_is_retryable_error_rate_limit(self):
        """Test that rate limit errors are retryable."""
        exc = APIException("Rate limited", error_code="API_RATE_LIMIT")
        assert is_retryable_error(exc)

    def test_is_retryable_error_non_retryable(self):
        """Test that non-retryable errors are not retryable."""
        exc = ConfigurationException("Config error")
        assert not is_retryable_error(exc)

    def test_is_retryable_error_generic_exception(self):
        """Test that generic exceptions are not retryable."""
        exc = ValueError("Generic error")
        assert not is_retryable_error(exc)

    def test_should_fallback_data_provider_error(self):
        """Test that data provider errors should fallback."""
        exc = DataProviderException("Provider failed")
        assert should_fallback(exc)

    def test_should_fallback_api_error(self):
        """Test that API errors should fallback."""
        exc = APIException("API failed")
        assert should_fallback(exc)

    def test_should_fallback_connection_error(self):
        """Test that connection errors should fallback."""
        exc = NordInvestException("Connection failed", error_code="CONNECTION_ERROR")
        assert should_fallback(exc)

    def test_should_fallback_non_fallback_error(self):
        """Test that non-fallback errors should not fallback."""
        exc = ConfigurationException("Config error")
        assert not should_fallback(exc)

    def test_should_fallback_generic_exception(self):
        """Test that generic exceptions should not fallback."""
        exc = RuntimeError("Generic error")
        assert not should_fallback(exc)


@pytest.mark.unit
class TestErrorContext:
    """Test error context handling."""

    def test_exception_context_preservation(self):
        """Test that exception context is preserved."""
        original_context = {"user": "test", "operation": "analysis"}
        exc = NordInvestException("Error", context=original_context)

        assert exc.context == original_context

    def test_exception_context_modification(self):
        """Test that exception context can be modified."""
        exc = NordInvestException("Error")
        exc.context["new_key"] = "new_value"

        assert exc.context["new_key"] == "new_value"

    def test_exception_inheritance_context(self):
        """Test that inherited exceptions handle context correctly."""
        context = {"ticker": "AAPL", "provider": "yahoo"}
        exc = DataProviderException("Failed", provider="yahoo", context=context)

        assert exc.context["provider"] == "yahoo"
        assert exc.context["ticker"] == "AAPL"


@pytest.mark.unit
class TestErrorSeverityHandling:
    """Test error severity handling."""

    def test_error_severity_levels(self):
        """Test different severity levels."""
        info_exc = NordInvestException("Info", severity=ErrorSeverity.INFO)
        warning_exc = NordInvestException("Warning", severity=ErrorSeverity.WARNING)
        error_exc = NordInvestException("Error", severity=ErrorSeverity.ERROR)
        critical_exc = NordInvestException("Critical", severity=ErrorSeverity.CRITICAL)

        assert info_exc.severity == ErrorSeverity.INFO
        assert warning_exc.severity == ErrorSeverity.WARNING
        assert error_exc.severity == ErrorSeverity.ERROR
        assert critical_exc.severity == ErrorSeverity.CRITICAL

    def test_default_severity(self):
        """Test default severity is ERROR."""
        exc = NordInvestException("Test")
        assert exc.severity == ErrorSeverity.ERROR
