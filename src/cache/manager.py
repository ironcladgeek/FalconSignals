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
        logger.info(f"Cache manager initialized at {self.cache_dir}")

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

    def _get_file_path(self, key: str) -> Path:
        """Get file path for cache key.

        Args:
            key: Cache key

        Returns:
            File path for the key
        """
        # Sanitize key to be filesystem safe
        safe_key = key.replace("/", "_").replace(":", "_")
        return self.cache_dir / f"{safe_key}.json"
