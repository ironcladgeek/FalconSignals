"""Resilience patterns for error handling, retries, and fallbacks."""

import time
from functools import wraps
from typing import Any, Callable, TypeVar

from src.utils.errors import (
    APIException,
    RetryableException,
    is_retryable_error,
)
from src.utils.logging import get_logger

logger = get_logger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


def retry(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 30.0,
    exponential_base: float = 2.0,
    on_retry: Callable[[int, Exception], None] | None = None,
) -> Callable[[F], F]:
    """Decorator for retrying operations with exponential backoff.

    Args:
        max_attempts: Maximum number of retry attempts
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay between retries
        exponential_base: Base for exponential backoff
        on_retry: Optional callback on retry (attempt, exception)

    Returns:
        Decorated function
    """

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            attempt = 0
            delay = initial_delay

            while attempt < max_attempts:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    attempt += 1

                    if not is_retryable_error(e) or attempt >= max_attempts:
                        logger.error(
                            f"Operation {func.__name__} failed after {attempt} attempts: {e}"
                        )
                        raise

                    if on_retry:
                        on_retry(attempt, e)

                    logger.warning(
                        f"Operation {func.__name__} failed on attempt {attempt}, "
                        f"retrying in {delay}s: {e}"
                    )

                    time.sleep(delay)
                    delay = min(delay * exponential_base, max_delay)

            return None

        return wrapper  # type: ignore

    return decorator


def fallback(
    fallback_func: Callable[..., Any],
    on_fallback: Callable[[Exception], None] | None = None,
) -> Callable[[F], F]:
    """Decorator for fallback strategy on error.

    Args:
        fallback_func: Function to call on primary failure
        on_fallback: Optional callback on fallback (exception)

    Returns:
        Decorated function
    """

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.warning(f"Operation {func.__name__} failed, attempting fallback: {e}")

                if on_fallback:
                    on_fallback(e)

                try:
                    return fallback_func(*args, **kwargs)
                except Exception as fallback_error:
                    logger.error(f"Fallback also failed for {func.__name__}: {fallback_error}")
                    raise fallback_error from e

        return wrapper  # type: ignore

    return decorator


class CircuitBreaker:
    """Circuit breaker pattern for preventing cascading failures."""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: type[Exception] = Exception,
    ):
        """Initialize circuit breaker.

        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before attempting recovery
            expected_exception: Exception type to track
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception

        self.failure_count = 0
        self.last_failure_time: float | None = None
        self.state = "closed"  # closed, open, half_open

        logger.info(
            f"Circuit breaker initialized: "
            f"threshold={failure_threshold}, timeout={recovery_timeout}s"
        )

    def call(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """Execute function through circuit breaker.

        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result

        Raises:
            RuntimeError: If circuit is open
        """
        if self.state == "open":
            if self._should_attempt_reset():
                self.state = "half_open"
                logger.info("Circuit breaker attempting recovery")
            else:
                raise RuntimeError(f"Circuit breaker open (recovered in {self.recovery_timeout}s)")

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise

    def _on_success(self) -> None:
        """Handle successful call."""
        self.failure_count = 0
        if self.state == "half_open":
            self.state = "closed"
            logger.info("Circuit breaker closed (recovered)")

    def _on_failure(self) -> None:
        """Handle failed call."""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            self.state = "open"
            logger.warning(f"Circuit breaker opened after {self.failure_count} failures")

    def _should_attempt_reset(self) -> bool:
        """Check if recovery timeout has elapsed."""
        if self.last_failure_time is None:
            return False

        return time.time() - self.last_failure_time >= self.recovery_timeout


class RateLimiter:
    """Simple rate limiter with token bucket algorithm."""

    def __init__(self, rate: int, period: float = 1.0):
        """Initialize rate limiter.

        Args:
            rate: Number of operations allowed per period
            period: Time period in seconds
        """
        self.rate = rate
        self.period = period
        self.tokens = rate
        self.last_update = time.time()

        logger.debug(f"Rate limiter initialized: {rate} ops per {period}s")

    def acquire(self, tokens: int = 1) -> bool:
        """Attempt to acquire tokens.

        Args:
            tokens: Number of tokens to acquire

        Returns:
            True if tokens acquired, False if rate limited
        """
        self._refill()

        if self.tokens >= tokens:
            self.tokens -= tokens
            return True

        return False

    def wait_if_needed(self, tokens: int = 1) -> None:
        """Wait until tokens are available.

        Args:
            tokens: Number of tokens needed
        """
        while not self.acquire(tokens):
            time.sleep(0.1)

    def _refill(self) -> None:
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self.last_update
        refill_amount = (elapsed / self.period) * self.rate
        self.tokens = min(self.rate, self.tokens + refill_amount)
        self.last_update = now


def graceful_degrade(
    default_value: Any = None,
    log_error: bool = True,
) -> Callable[[F], F]:
    """Decorator for graceful degradation on error.

    Args:
        default_value: Value to return on error
        log_error: Whether to log the error

    Returns:
        Decorated function
    """

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if log_error:
                    logger.warning(f"Operation {func.__name__} degraded to default: {e}")
                return default_value

        return wrapper  # type: ignore

    return decorator


def timeout(seconds: float) -> Callable[[F], F]:
    """Decorator for operation timeout (basic implementation).

    Note: For true timeout on blocking operations, use signal-based
    or threading-based approaches in production.

    Args:
        seconds: Timeout in seconds

    Returns:
        Decorated function
    """

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start = time.time()

            result = func(*args, **kwargs)

            elapsed = time.time() - start
            if elapsed > seconds:
                logger.warning(
                    f"Operation {func.__name__} exceeded timeout ({elapsed:.2f}s > {seconds}s)"
                )

            return result

        return wrapper  # type: ignore

    return decorator
