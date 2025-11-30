"""Tests for resilience patterns and error handling."""

import pytest

from src.utils.errors import (
    APIException,
    DataProviderException,
    RetryableException,
    is_retryable_error,
    should_fallback,
)
from src.utils.resilience import CircuitBreaker, RateLimiter, fallback, graceful_degrade, retry


@pytest.mark.unit
class TestErrorHandling:
    """Test suite for error handling and resilience."""

    def test_retryable_error_detection(self):
        """Test detection of retryable errors."""
        retryable_error = RetryableException("Test error")
        assert is_retryable_error(retryable_error)

        api_error = APIException("API failed", status_code=500)
        assert not is_retryable_error(api_error)

    def test_fallback_error_detection(self):
        """Test detection of errors requiring fallback."""
        provider_error = DataProviderException("Provider failed", provider="test")
        assert should_fallback(provider_error)

    def test_circuit_breaker(self):
        """Test circuit breaker pattern."""
        breaker = CircuitBreaker(failure_threshold=2)

        def failing_operation():
            raise ValueError("Test error")

        def working_operation():
            return "success"

        # First failure
        with pytest.raises(ValueError):
            breaker.call(failing_operation)

        assert breaker.state == "closed"
        assert breaker.failure_count == 1

        # Second failure - opens circuit
        with pytest.raises(ValueError):
            breaker.call(failing_operation)

        assert breaker.state == "open"

        # Attempt in open state
        with pytest.raises(RuntimeError, match="Circuit breaker open"):
            breaker.call(working_operation)


@pytest.mark.unit
class TestRateLimiter:
    """Test rate limiter."""

    def test_rate_limiter_denies_excess_requests(self):
        """Test rate limiter denies excess requests."""
        limiter = RateLimiter(rate=3, period=1.0)

        # Should allow first 3 operations
        assert limiter.acquire(1)
        assert limiter.acquire(1)
        assert limiter.acquire(1)

        # Should deny 4th without delay
        assert not limiter.acquire(1)


@pytest.mark.unit
class TestResilience:
    """Test suite for resilience patterns."""

    def test_graceful_degrade_decorator(self):
        """Test graceful degradation decorator."""

        @graceful_degrade(default_value=[])
        def failing_operation():
            raise RuntimeError("Operation failed")

        result = failing_operation()
        assert result == []

    def test_retry_decorator(self):
        """Test retry decorator."""
        attempt_count = 0

        @retry(max_attempts=3, initial_delay=0.01)
        def flaky_operation():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 3:
                raise RetryableException("Temporary failure")
            return "success"

        result = flaky_operation()
        assert result == "success"
        assert attempt_count == 3

    def test_fallback_decorator(self):
        """Test fallback decorator."""

        @fallback(fallback_func=lambda: "fallback_result")
        def primary_operation():
            raise RuntimeError("Primary failed")

        result = primary_operation()
        assert result == "fallback_result"
