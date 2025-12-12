"""Resilience patterns for error handling, retries, and fallbacks."""

import time
from functools import wraps
from typing import Any, Callable, TypeVar

from src.utils.errors import (
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
