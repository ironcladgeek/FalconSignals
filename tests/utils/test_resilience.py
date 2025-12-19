"""Unit tests for the resilience module."""

import time

import pytest

from src.utils.errors import RetryableException
from src.utils.resilience import RateLimiter, fallback, retry, timeout


class TestRetryDecorator:
    """Test suite for the retry decorator."""

    def test_retry_succeeds_first_attempt(self):
        """Test function that succeeds on first attempt."""
        call_count = 0

        @retry(max_attempts=3)
        def successful_func():
            nonlocal call_count
            call_count += 1
            return "success"

        result = successful_func()

        assert result == "success"
        assert call_count == 1

    def test_retry_succeeds_after_failure(self):
        """Test function that fails then succeeds."""
        call_count = 0

        @retry(max_attempts=3, initial_delay=0.01)
        def failing_then_success():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise RetryableException("Network error")
            return "success"

        result = failing_then_success()

        assert result == "success"
        assert call_count == 2

    def test_retry_exhausts_attempts(self):
        """Test function that always fails."""

        @retry(max_attempts=3, initial_delay=0.01)
        def always_fails():
            raise RetryableException("Network error")

        with pytest.raises(RetryableException):
            always_fails()

    def test_retry_non_retryable_error(self):
        """Test that non-retryable errors don't retry."""
        call_count = 0

        @retry(max_attempts=3, initial_delay=0.01)
        def raises_value_error():
            nonlocal call_count
            call_count += 1
            raise ValueError("Invalid value")

        with pytest.raises(ValueError):
            raises_value_error()

        # Should only be called once for non-retryable errors
        assert call_count == 1

    def test_retry_on_retry_callback(self):
        """Test on_retry callback is called."""
        retry_attempts = []

        def on_retry_callback(attempt, exception):
            retry_attempts.append((attempt, str(exception)))

        @retry(max_attempts=3, initial_delay=0.01, on_retry=on_retry_callback)
        def failing_twice():
            if len(retry_attempts) < 2:
                raise RetryableException("Network error")
            return "success"

        result = failing_twice()

        assert result == "success"
        assert len(retry_attempts) == 2
        assert retry_attempts[0][0] == 1
        assert "Network error" in retry_attempts[0][1]

    def test_retry_exponential_backoff(self):
        """Test exponential backoff timing."""
        call_times = []

        @retry(max_attempts=3, initial_delay=0.05, exponential_base=2.0)
        def track_timing():
            call_times.append(time.time())
            if len(call_times) < 3:
                raise RetryableException("Retry")
            return "success"

        result = track_timing()

        assert result == "success"
        assert len(call_times) == 3

        # Check delays are approximately exponential
        delay1 = call_times[1] - call_times[0]
        delay2 = call_times[2] - call_times[1]

        # Second delay should be approximately 2x first delay
        assert delay1 > 0.04
        assert delay2 > 0.08


class TestFallbackDecorator:
    """Test suite for the fallback decorator."""

    def test_fallback_primary_succeeds(self):
        """Test that fallback is not called when primary succeeds."""
        fallback_called = False

        def fallback_func(*args, **kwargs):
            nonlocal fallback_called
            fallback_called = True
            return "fallback"

        @fallback(fallback_func)
        def primary_func():
            return "primary"

        result = primary_func()

        assert result == "primary"
        assert fallback_called is False

    def test_fallback_primary_fails(self):
        """Test that fallback is called when primary fails."""

        def fallback_func(*args, **kwargs):
            return "fallback"

        @fallback(fallback_func)
        def primary_func():
            raise ValueError("Primary failed")

        result = primary_func()

        assert result == "fallback"

    def test_fallback_both_fail(self):
        """Test exception when both primary and fallback fail."""

        def fallback_func(*args, **kwargs):
            raise RuntimeError("Fallback also failed")

        @fallback(fallback_func)
        def primary_func():
            raise ValueError("Primary failed")

        with pytest.raises(RuntimeError):
            primary_func()

    def test_fallback_passes_args(self):
        """Test that arguments are passed to fallback."""

        def fallback_func(x, y):
            return x + y

        @fallback(fallback_func)
        def primary_func(x, y):
            raise ValueError("Fail")

        result = primary_func(3, 4)

        assert result == 7

    def test_fallback_on_fallback_callback(self):
        """Test on_fallback callback is called."""
        callback_exception = None

        def on_fallback_callback(exception):
            nonlocal callback_exception
            callback_exception = exception

        def fallback_func():
            return "fallback"

        @fallback(fallback_func, on_fallback=on_fallback_callback)
        def primary_func():
            raise ValueError("Primary error")

        result = primary_func()

        assert result == "fallback"
        assert callback_exception is not None
        assert "Primary error" in str(callback_exception)


class TestRateLimiter:
    """Test suite for RateLimiter class."""

    def test_rate_limiter_initialization(self):
        """Test rate limiter initializes correctly."""
        limiter = RateLimiter(rate=10, period=1.0)

        assert limiter.rate == 10
        assert limiter.period == 1.0
        assert limiter.tokens == 10

    def test_acquire_success(self):
        """Test acquiring tokens when available."""
        limiter = RateLimiter(rate=5, period=1.0)

        assert limiter.acquire(1) is True
        assert limiter.tokens == 4

    def test_acquire_multiple_tokens(self):
        """Test acquiring multiple tokens."""
        limiter = RateLimiter(rate=5, period=1.0)

        assert limiter.acquire(3) is True
        assert limiter.tokens == 2

    def test_acquire_fails_insufficient_tokens(self):
        """Test acquire fails when insufficient tokens."""
        limiter = RateLimiter(rate=2, period=1.0)

        limiter.acquire(2)  # Use all tokens

        assert limiter.acquire(1) is False

    def test_tokens_refill_over_time(self):
        """Test that tokens refill over time."""
        limiter = RateLimiter(rate=10, period=0.1)  # Fast refill for testing

        # Use all tokens
        for _ in range(10):
            limiter.acquire(1)

        assert limiter.acquire(1) is False

        # Wait for refill
        time.sleep(0.15)

        # Should have tokens again
        assert limiter.acquire(1) is True

    def test_tokens_dont_exceed_rate(self):
        """Test that tokens don't exceed max rate."""
        limiter = RateLimiter(rate=5, period=0.1)

        # Wait longer than refill period
        time.sleep(0.3)

        # Tokens should be capped at rate
        limiter._refill()
        assert limiter.tokens <= limiter.rate

    def test_wait_if_needed_no_wait(self):
        """Test wait_if_needed when tokens available."""
        limiter = RateLimiter(rate=5, period=1.0)

        start = time.time()
        limiter.wait_if_needed(1)
        elapsed = time.time() - start

        assert elapsed < 0.1  # Should return immediately

    def test_wait_if_needed_waits(self):
        """Test wait_if_needed when tokens not available."""
        limiter = RateLimiter(rate=1, period=0.2)

        # Use the token
        limiter.acquire(1)

        start = time.time()
        limiter.wait_if_needed(1)
        elapsed = time.time() - start

        # Should have waited for refill
        assert elapsed >= 0.1


class TestTimeoutDecorator:
    """Test suite for the timeout decorator."""

    def test_timeout_fast_function(self):
        """Test function that completes within timeout."""

        @timeout(seconds=1.0)
        def fast_func():
            return "done"

        result = fast_func()

        assert result == "done"

    def test_timeout_slow_function_logs_warning(self):
        """Test function that exceeds timeout logs warning."""
        # Note: This basic timeout implementation doesn't actually stop execution,
        # it only logs a warning

        @timeout(seconds=0.01)
        def slow_func():
            time.sleep(0.1)
            return "done"

        result = slow_func()

        # Function still completes (basic implementation)
        assert result == "done"

    def test_timeout_preserves_function_metadata(self):
        """Test that timeout decorator preserves function metadata."""

        @timeout(seconds=1.0)
        def documented_func():
            """This is the docstring."""
            return "result"

        assert documented_func.__name__ == "documented_func"
        assert "docstring" in documented_func.__doc__


class TestResilienceIntegration:
    """Integration tests combining multiple resilience patterns."""

    def test_retry_with_fallback(self):
        """Test combining retry and fallback decorators."""
        primary_attempts = 0

        def fallback_func():
            return "fallback_result"

        @fallback(fallback_func)
        @retry(max_attempts=2, initial_delay=0.01)
        def unreliable_func():
            nonlocal primary_attempts
            primary_attempts += 1
            raise RetryableException("Always fails")

        result = unreliable_func()

        assert result == "fallback_result"
        assert primary_attempts == 2  # Retried before falling back

    def test_rate_limiter_with_multiple_operations(self):
        """Test rate limiter with burst of operations."""
        limiter = RateLimiter(rate=3, period=0.5)
        results = []

        for i in range(5):
            if limiter.acquire(1):
                results.append(f"op_{i}")
            else:
                results.append(f"limited_{i}")

        # First 3 should succeed, rest should be limited
        assert len([r for r in results if r.startswith("op_")]) == 3
        assert len([r for r in results if r.startswith("limited_")]) == 2
