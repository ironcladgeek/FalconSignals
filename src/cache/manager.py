"""Cache manager for API responses and processed data."""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

from src.utils.logging import get_logger

logger = get_logger(__name__)


class CacheEntry:
    """Single cache entry with metadata."""

    def __init__(self, key: str, data: Any, ttl_hours: int):
        """Initialize cache entry.

        Args:
            key: Cache key
            data: Cached data
            ttl_hours: Time-to-live in hours
        """
        self.key = key
        self.data = data
        self.ttl_hours = ttl_hours
        self.created_at = datetime.now()
        self.expires_at = self.created_at + timedelta(hours=ttl_hours)

    def is_expired(self) -> bool:
        """Check if cache entry has expired.

        Returns:
            True if expired, False otherwise
        """
        return datetime.now() > self.expires_at

    def time_to_expiry(self) -> timedelta:
        """Get time until expiry.

        Returns:
            Timedelta until expiry
        """
        return self.expires_at - datetime.now()


class CacheManager:
    """File-based cache manager for structured data.

    Uses JSON format for flexibility and human-readability.
    """

    def __init__(self, cache_dir: str | Path = "data/cache"):
        """Initialize cache manager.

        Args:
            cache_dir: Directory for cache files
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._memory_cache = {}
        logger.debug(f"Cache manager initialized at {self.cache_dir}")

    def get(
        self,
        key: str,
        default: Optional[Any] = None,
    ) -> Optional[Any]:
        """Get value from cache.

        Checks memory cache first, then disk cache.

        Args:
            key: Cache key
            default: Default value if not found

        Returns:
            Cached value or default
        """
        # Check memory cache
        if key in self._memory_cache:
            entry = self._memory_cache[key]
            if not entry.is_expired():
                logger.debug(f"Cache hit (memory): {key}")
                return entry.data
            else:
                del self._memory_cache[key]
                logger.debug(f"Memory cache expired: {key}")

        # Check disk cache
        file_path = self._get_file_path(key)
        if file_path.exists():
            try:
                with open(file_path, "r") as f:
                    cached = json.load(f)

                entry = CacheEntry(
                    key=cached["key"],
                    data=cached["data"],
                    ttl_hours=cached["ttl_hours"],
                )
                entry.created_at = datetime.fromisoformat(cached["created_at"])
                entry.expires_at = datetime.fromisoformat(cached["expires_at"])

                if not entry.is_expired():
                    logger.debug(f"Cache hit (disk): {key}")
                    # Move to memory cache
                    self._memory_cache[key] = entry
                    return entry.data
                else:
                    logger.debug(f"Disk cache expired: {key}")
                    file_path.unlink()
                    return default

            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Failed to load cache file {key}: {e}")
                file_path.unlink()
                return default

        logger.debug(f"Cache miss: {key}")
        return default

    def set(self, key: str, data: Any, ttl_hours: int) -> None:
        """Set value in cache.

        Args:
            key: Cache key
            data: Data to cache
            ttl_hours: Time-to-live in hours
        """
        entry = CacheEntry(key, data, ttl_hours)

        # Store in memory cache
        self._memory_cache[key] = entry

        # Store in disk cache
        file_path = self._get_file_path(key)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            cache_data = {
                "key": entry.key,
                "data": entry.data,
                "ttl_hours": entry.ttl_hours,
                "created_at": entry.created_at.isoformat(),
                "expires_at": entry.expires_at.isoformat(),
            }
            with open(file_path, "w") as f:
                json.dump(cache_data, f, indent=2, default=str)
            logger.debug(f"Cache set (disk): {key} (TTL: {ttl_hours}h)")
        except Exception as e:
            logger.error(f"Failed to write cache file {key}: {e}")

    def delete(self, key: str) -> bool:
        """Delete cache entry.

        Args:
            key: Cache key

        Returns:
            True if deleted, False if not found
        """
        deleted = False

        # Delete from memory cache
        if key in self._memory_cache:
            del self._memory_cache[key]
            deleted = True

        # Delete from disk cache
        file_path = self._get_file_path(key)
        if file_path.exists():
            try:
                file_path.unlink()
                deleted = True
                logger.debug(f"Cache deleted: {key}")
            except Exception as e:
                logger.error(f"Failed to delete cache file {key}: {e}")

        return deleted

    def clear(self) -> None:
        """Clear all cache entries."""
        self._memory_cache.clear()
        for file_path in self.cache_dir.glob("*.json"):
            try:
                file_path.unlink()
            except Exception as e:
                logger.error(f"Failed to delete cache file {file_path}: {e}")
        logger.info("Cache cleared")

    def cleanup_expired(self) -> int:
        """Remove expired cache entries.

        Returns:
            Number of entries removed
        """
        removed = 0

        # Clean memory cache
        expired_keys = [key for key, entry in self._memory_cache.items() if entry.is_expired()]
        for key in expired_keys:
            del self._memory_cache[key]
            removed += 1

        # Clean disk cache
        for file_path in self.cache_dir.glob("*.json"):
            try:
                with open(file_path, "r") as f:
                    cached = json.load(f)
                entry = CacheEntry(
                    key=cached["key"],
                    data=cached["data"],
                    ttl_hours=cached["ttl_hours"],
                )
                entry.created_at = datetime.fromisoformat(cached["created_at"])
                entry.expires_at = datetime.fromisoformat(cached["expires_at"])

                if entry.is_expired():
                    file_path.unlink()
                    removed += 1
            except Exception as e:
                logger.warning(f"Error checking cache file {file_path}: {e}")

        if removed > 0:
            logger.info(f"Removed {removed} expired cache entries")
        return removed

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache stats
        """
        memory_entries = len(self._memory_cache)
        disk_entries = len(list(self.cache_dir.glob("*.json")))
        total_size = sum(f.stat().st_size for f in self.cache_dir.glob("*.json"))

        return {
            "memory_entries": memory_entries,
            "disk_entries": disk_entries,
            "total_size_bytes": total_size,
            "cache_dir": str(self.cache_dir),
        }

    def get_latest_price(self, ticker: str) -> Optional[Any]:
        """Get latest price for a ticker from cache.

        Searches for price cache files matching the ticker pattern
        and returns the latest_price from the most recent file.

        Args:
            ticker: Stock ticker symbol

        Returns:
            Price object with close_price and currency, or None if not found
        """
        try:
            # Search for price cache files matching this ticker
            pattern = f"prices_{ticker.upper()}_*.json"
            matching_files = list(self.cache_dir.glob(pattern))

            if not matching_files:
                logger.debug(f"No price cache found for {ticker}")
                return None

            # Load the most recent file (they should be sorted by name)
            latest_file = sorted(matching_files)[-1]

            with open(latest_file, "r") as f:
                cached = json.load(f)
                data = cached.get("data", {})

                # Extract the latest_price and construct a simple object
                latest_price = data.get("latest_price")
                if latest_price is None:
                    logger.debug(f"No latest_price in cache for {ticker}")
                    return None

                # Get currency from the last price entry
                prices = data.get("prices", [])
                currency = "USD"
                if prices:
                    currency = prices[-1].get("currency", "USD")

                # Return a simple object with close_price and currency
                class PriceData:
                    def __init__(self, price, curr):
                        self.close_price = price
                        self.currency = curr

                logger.debug(f"Found cached price for {ticker}: {latest_price} {currency}")
                return PriceData(latest_price, currency)

        except Exception as e:
            logger.debug(f"Error fetching price cache for {ticker}: {e}")
            return None

    def get_historical_cache(
        self,
        ticker: str,
        as_of_date: str,
    ) -> Optional[Any]:
        """Get cached data for a ticker as of a specific date.

        For historical analysis, tries to find cache files that were created
        on or before the specified date.

        Args:
            ticker: Stock ticker symbol
            as_of_date: Date string in YYYY-MM-DD format

        Returns:
            Cached data or None if not found
        """
        try:
            # Search for cache files matching this ticker
            pattern = f"{ticker.upper()}_*.json"
            matching_files = list(self.cache_dir.glob(pattern))

            if not matching_files:
                logger.debug(f"No historical cache found for {ticker}")
                return None

            # Filter files with dates <= as_of_date
            valid_files = []
            for file_path in matching_files:
                # Try to extract date from filename (YYYY-MM-DD format)
                filename = file_path.stem  # Remove .json extension
                parts = filename.split("_")
                for part in parts:
                    if len(part) == 10 and part[4] == "-" and part[7] == "-":
                        if part <= as_of_date:  # String comparison works for YYYY-MM-DD
                            valid_files.append((part, file_path))
                        break

            if not valid_files:
                logger.debug(f"No historical cache found for {ticker} before {as_of_date}")
                return None

            # Use the most recent valid file
            valid_files.sort(key=lambda x: x[0], reverse=True)
            most_recent_date, most_recent_file = valid_files[0]

            with open(most_recent_file, "r") as f:
                cached = json.load(f)
                logger.debug(
                    f"Found historical cache for {ticker} as of {most_recent_date}: "
                    f"{most_recent_file.name}"
                )
                return cached.get("data")

        except Exception as e:
            logger.debug(f"Error fetching historical cache for {ticker}: {e}")
            return None

    def _get_file_path(self, key: str) -> Path:
        """Get file path for cache key.

        Converts cache key to a consistent, readable filename format.
        Examples:
            prices:AAPL:2025-11-01:2025-12-01 -> AAPL_prices_2025-11-01_2025-12-01.json
            news_sentiment:ZS -> ZS_news_2025-12-02.json
            fundamental_enriched:MSFT -> MSFT_fundamental_2025-12-02.json

        Args:
            key: Cache key in format type:ticker:params

        Returns:
            File path for the key
        """
        # Parse key to create structured filename
        parts = key.split(":")

        if len(parts) >= 2:
            type_name = parts[0].replace("_", "-")
            ticker = parts[1].upper()

            # Format additional params in a readable way
            params_parts = []
            for i, param in enumerate(parts[2:], start=2):
                # If it looks like a date (YYYY-MM-DD), keep as-is
                if len(param) == 10 and param[4] == "-" and param[7] == "-":
                    params_parts.append(param)
                # Otherwise, use generic param naming
                elif param.isdigit():
                    # Common param patterns
                    param_names = ["limit", "maxage", "param3", "param4"]
                    param_idx = i - 2  # Adjust for params starting at index 2
                    if param_idx < len(param_names):
                        params_parts.append(f"{param_names[param_idx]}{param}")
                    else:
                        params_parts.append(param)
                else:
                    params_parts.append(param)

            # Build filename: ticker_type_params.json
            # For fundamental_enriched and news_sentiment, add today's date
            if type_name in ["fundamental-enriched", "news-sentiment"] and not params_parts:
                fetch_date = datetime.now().strftime("%Y-%m-%d")
                if type_name == "fundamental-enriched":
                    filename = f"{ticker}_fundamental_{fetch_date}.json"
                else:  # news-sentiment
                    filename = f"{ticker}_news_{fetch_date}.json"
            elif params_parts:
                params_str = "_".join(params_parts)
                filename = f"{ticker}_{type_name}_{params_str}.json"
            else:
                filename = f"{ticker}_{type_name}.json"
        else:
            # Fallback for non-standard keys
            safe_key = key.replace("/", "_").replace(":", "_")
            filename = f"{safe_key}.json"

        # Sanitize filename
        filename = filename.replace("/", "_")
        return self.cache_dir / filename
