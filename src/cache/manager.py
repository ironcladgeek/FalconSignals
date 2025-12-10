"""Cache manager for API responses and processed data."""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

from src.utils.logging import get_logger

if TYPE_CHECKING:
    from src.data.price_manager import PriceDataManager

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

    def __init__(
        self,
        cache_dir: str | Path = "data/cache",
        use_unified_prices: bool = True,
    ):
        """Initialize cache manager.

        Args:
            cache_dir: Directory for cache files
            use_unified_prices: If True, use PriceDataManager for price data (CSV storage)
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._memory_cache = {}
        self._use_unified_prices = use_unified_prices
        self._price_manager: Optional["PriceDataManager"] = None
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

        For historical analysis, tries to find cache files that contain data
        available on or before the specified date.

        For price data (format: TICKER_prices_START_END.json):
        - Looks for files where END >= as_of_date (data available on that date)

        For other data (format: TICKER_type_DATE.json):
        - Looks for files where DATE <= as_of_date (created on or before that date)

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

            # Filter files based on type (price vs other data)
            valid_files = []
            for file_path in matching_files:
                filename = file_path.stem  # Remove .json extension
                parts = filename.split("_")

                # Check if this is price data (has format: TICKER_prices_START_END)
                if "prices" in parts:
                    # For price data, extract start and end dates
                    try:
                        price_idx = parts.index("prices")
                        if price_idx + 2 < len(parts):
                            start_date = parts[price_idx + 1]
                            end_date = parts[price_idx + 2]
                            # Valid if end_date <= as_of_date (no future data)
                            # This ensures we only use cache files that don't contain future data
                            if (
                                len(start_date) == 10
                                and len(end_date) == 10
                                and end_date <= as_of_date
                            ):
                                valid_files.append((end_date, file_path))
                                logger.debug(
                                    f"Price cache {file_path.name} covers {start_date} to {end_date}, "
                                    f"valid for as_of_date {as_of_date}"
                                )
                            else:
                                logger.debug(
                                    f"Price cache {file_path.name} end date {end_date} is after {as_of_date}, skipping"
                                )
                    except (ValueError, IndexError):
                        pass

                # For other data types, look for single date in filename
                elif "prices" not in parts:
                    for part in parts:
                        if len(part) == 10 and part[4] == "-" and part[7] == "-":
                            # For non-price data, use date <= as_of_date
                            if part <= as_of_date:
                                valid_files.append((part, file_path))
                                logger.debug(
                                    f"Cache {file_path.name} dated {part} is <= {as_of_date}"
                                )
                            break

            if not valid_files:
                logger.debug(f"No historical cache found for {ticker} as of {as_of_date}")
                return None

            # Use the most recent valid file
            valid_files.sort(key=lambda x: x[0], reverse=True)
            most_recent_date, most_recent_file = valid_files[0]

            with open(most_recent_file, "r") as f:
                cached = json.load(f)
                logger.debug(
                    f"Found historical cache for {ticker} as of {as_of_date}: "
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
            # For fundamental_enriched, use date (historical or current)
            if type_name == "fundamental-enriched":
                if params_parts and len(params_parts[0]) == 10 and params_parts[0][4] == "-":
                    # Date format (YYYY-MM-DD)
                    filename = f"{ticker}_fundamental_{params_parts[0]}.json"
                else:
                    # Legacy fallback: use today's date
                    fetch_date = datetime.now().strftime("%Y-%m-%d")
                    filename = f"{ticker}_fundamental_{fetch_date}.json"
            # For news_sentiment, use date range if available (like prices)
            elif type_name == "news-sentiment":
                if len(params_parts) >= 2:
                    # Has date range: news_sentiment:TICKER:START_DATE:END_DATE
                    params_str = "_".join(params_parts)
                    filename = f"{ticker}_news_{params_str}.json"
                elif not params_parts:
                    # No date params, use today's date as fallback
                    fetch_date = datetime.now().strftime("%Y-%m-%d")
                    filename = f"{ticker}_news_{fetch_date}.json"
                else:
                    # Single param (legacy)
                    params_str = "_".join(params_parts)
                    filename = f"{ticker}_news_{params_str}.json"
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

    @property
    def price_manager(self) -> "PriceDataManager":
        """Get or create the PriceDataManager instance.

        Returns:
            PriceDataManager for unified price storage
        """
        if self._price_manager is None:
            from src.data.price_manager import PriceDataManager

            prices_dir = self.cache_dir / "prices"
            self._price_manager = PriceDataManager(prices_dir=prices_dir)
        return self._price_manager

    def get_unified_prices(
        self,
        ticker: str,
        start_date=None,
        end_date=None,
    ):
        """Get price data from unified CSV storage.

        Args:
            ticker: Stock ticker symbol
            start_date: Start date (optional)
            end_date: End date (optional)

        Returns:
            DataFrame with price data or empty DataFrame if not found
        """
        if not self._use_unified_prices:
            return None
        return self.price_manager.get_prices(ticker, start_date, end_date)

    def store_unified_prices(
        self,
        ticker: str,
        prices: list[dict],
        append: bool = True,
    ) -> int:
        """Store price data in unified CSV storage.

        Args:
            ticker: Stock ticker symbol
            prices: List of price dictionaries
            append: If True, merge with existing data

        Returns:
            Number of rows stored
        """
        if not self._use_unified_prices:
            return 0
        return self.price_manager.store_prices(ticker, prices, append=append)

    def get_unified_latest_price(self, ticker: str) -> Optional[Any]:
        """Get latest price from unified CSV storage.

        Args:
            ticker: Stock ticker symbol

        Returns:
            Price data dictionary or None
        """
        if not self._use_unified_prices:
            return None
        return self.price_manager.get_latest_price(ticker)

    def get_unified_price_at_date(
        self,
        ticker: str,
        target_date,
        tolerance_days: int = 5,
    ) -> Optional[Any]:
        """Get price for a specific date from unified storage.

        Args:
            ticker: Stock ticker symbol
            target_date: Target date
            tolerance_days: Days to look back for non-trading days

        Returns:
            Price data dictionary or None
        """
        if not self._use_unified_prices:
            return None
        return self.price_manager.get_price_at_date(ticker, target_date, tolerance_days)

    def find_latest_by_prefix(self, key_prefix: str) -> Optional[Any]:
        """Find the most recent cache entry matching a key prefix.

        Searches cache directory for files matching the given key prefix pattern.
        Returns the data from the most recently created cache entry.

        Args:
            key_prefix: Cache key prefix to search for (e.g., "news_finbert:RELY" or "news:RELY")

        Returns:
            Cached data from the most recent matching entry, or None if not found
        """
        matching_files = []

        # Convert key prefix to filename pattern
        # Support flexible matching: "news:RELY" -> "RELY_news*.json"
        # This will match RELY_news-finbert*.json, RELY_news-sentiment*.json, etc.
        parts = key_prefix.split(":")
        if len(parts) >= 2:
            type_name = parts[0].replace("_", "-")
            ticker = parts[1].upper()
            # Use wildcard to match any news-related files
            pattern = f"{ticker}_{type_name}*.json"
        else:
            # Fallback pattern
            pattern = f"*{key_prefix}*.json"

        # Find matching files
        for file_path in self.cache_dir.glob(pattern):
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
                    matching_files.append((entry.created_at, entry.data, entry.key))
            except Exception as e:
                logger.warning(f"Error reading cache file {file_path}: {e}")
                continue

        if not matching_files:
            return None

        # Return data from most recent entry
        matching_files.sort(key=lambda x: x[0], reverse=True)
        latest_created, latest_data, latest_key = matching_files[0]
        logger.debug(f"Found latest cache for prefix '{key_prefix}': {latest_key}")
        return latest_data
