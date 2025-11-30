"""Tests for cache manager functionality."""

import json
from datetime import datetime, timedelta

import pytest

from src.cache.manager import CacheEntry, CacheManager


@pytest.mark.unit
class TestCacheEntry:
    """Test CacheEntry functionality."""

    def test_cache_entry_creation(self):
        """Test creating a cache entry."""
        entry = CacheEntry("test_key", {"data": "value"}, 24)

        assert entry.key == "test_key"
        assert entry.data == {"data": "value"}
        assert entry.ttl_hours == 24
        assert isinstance(entry.created_at, datetime)
        assert entry.expires_at == entry.created_at + timedelta(hours=24)

    def test_cache_entry_not_expired(self):
        """Test that a new cache entry is not expired."""
        entry = CacheEntry("test_key", "data", 1)
        assert not entry.is_expired()

    def test_cache_entry_expired(self):
        """Test that an expired cache entry is detected."""
        # Create entry that expires immediately
        entry = CacheEntry("test_key", "data", 0)
        # Wait a tiny bit to ensure expiry
        import time

        time.sleep(0.001)
        assert entry.is_expired()

    def test_time_to_expiry(self):
        """Test calculating time to expiry."""
        entry = CacheEntry("test_key", "data", 1)
        time_to_expiry = entry.time_to_expiry()

        # Should be close to 1 hour
        assert timedelta(hours=0.99) < time_to_expiry <= timedelta(hours=1)


@pytest.mark.unit
class TestCacheManager:
    """Test CacheManager functionality."""

    @pytest.fixture
    def cache_dir(self, tmp_path):
        """Create a temporary cache directory."""
        return tmp_path / "cache"

    @pytest.fixture
    def cache_manager(self, cache_dir):
        """Create a cache manager instance."""
        return CacheManager(str(cache_dir))

    def test_cache_manager_initialization(self, cache_dir):
        """Test cache manager initialization."""
        manager = CacheManager(str(cache_dir))

        assert manager.cache_dir == cache_dir
        assert cache_dir.exists()  # Directory should be created
        # Note: No entries.json file is created initially

    def test_set_and_get_cache_entry(self, cache_manager):
        """Test setting and getting cache entries."""
        test_data = {"key": "value", "number": 42}

        # Set cache entry
        cache_manager.set("test_key", test_data, ttl_hours=1)

        # Get cache entry
        retrieved = cache_manager.get("test_key")
        assert retrieved == test_data

    def test_get_nonexistent_key(self, cache_manager):
        """Test getting a nonexistent key returns None."""
        assert cache_manager.get("nonexistent") is None

    def test_cache_expiry(self, cache_manager):
        """Test that expired entries are not returned."""
        # Set entry with very short TTL
        cache_manager.set("short_ttl", "data", ttl_hours=0)

        # Wait for expiry
        import time

        time.sleep(0.01)

        # Should return None for expired entry
        assert cache_manager.get("short_ttl") is None

    def test_cache_persistence(self, cache_dir):
        """Test that cache persists across manager instances."""
        # Create first manager and set data
        manager1 = CacheManager(str(cache_dir))
        test_data = {"persistent": True}
        manager1.set("persistent_key", test_data, ttl_hours=24)

        # Create second manager and retrieve data
        manager2 = CacheManager(str(cache_dir))
        retrieved = manager2.get("persistent_key")
        assert retrieved == test_data

    def test_clear_cache(self, cache_manager):
        """Test clearing all cache entries."""
        # Set multiple entries
        cache_manager.set("key1", "value1", ttl_hours=1)
        cache_manager.set("key2", "value2", ttl_hours=1)

        # Verify they exist
        assert cache_manager.get("key1") == "value1"
        assert cache_manager.get("key2") == "value2"

        # Clear cache
        cache_manager.clear()

        # Verify they're gone
        assert cache_manager.get("key1") is None
        assert cache_manager.get("key2") is None

    def test_cleanup_expired_entries(self, cache_manager):
        """Test cleanup of expired entries."""
        # Set one long-lived entry
        cache_manager.set("long", "data", ttl_hours=24)

        # Set one short-lived entry
        cache_manager.set("short", "data", ttl_hours=0)

        # Wait for short entry to expire
        import time

        time.sleep(0.01)

        # Run cleanup
        cache_manager.cleanup_expired()

        # Long entry should still exist, short should be gone
        assert cache_manager.get("long") == "data"
        assert cache_manager.get("short") is None

    def test_get_latest_price(self, cache_manager):
        """Test getting latest price for a ticker."""
        # Create a price cache file directly (simulating real cache file)
        price_data = {
            "latest_price": 102.0,
            "prices": [
                {"close_price": 100.0, "date": "2024-01-01", "currency": "USD"},
                {"close_price": 105.0, "date": "2024-01-02", "currency": "USD"},
                {"close_price": 102.0, "date": "2024-01-03", "currency": "USD"},
            ],
        }

        # Create the cache file with date suffix as expected by get_latest_price
        cache_file = cache_manager.cache_dir / "prices_AAPL_2024-01-01_2024-01-03.json"
        with open(cache_file, "w") as f:
            json.dump(
                {
                    "key": "prices_AAPL_2024-01-01_2024-01-03",
                    "data": price_data,
                    "ttl_hours": 24,
                    "created_at": datetime.now().isoformat(),
                    "expires_at": (datetime.now() + timedelta(hours=24)).isoformat(),
                },
                f,
                indent=2,
                default=str,
            )

        latest_price = cache_manager.get_latest_price("AAPL")
        assert latest_price.close_price == 102.0
        assert latest_price.currency == "USD"

    def test_get_latest_price_no_data(self, cache_manager):
        """Test getting latest price when no data exists."""
        assert cache_manager.get_latest_price("NONEXISTENT") is None

    def test_get_latest_price_empty_list(self, cache_manager):
        """Test getting latest price from empty price list."""
        cache_manager.set("prices_EMPTY", [], ttl_hours=24)
        assert cache_manager.get_latest_price("EMPTY") is None

    def test_cache_size_limits(self, cache_manager):
        """Test cache size limits and eviction."""
        # Set many entries
        for i in range(150):  # More than default max_entries
            cache_manager.set(f"key_{i}", f"value_{i}", ttl_hours=24)

        # Should still work but may have evicted old entries
        # (Exact behavior depends on implementation)
        assert cache_manager.get("key_149") == "value_149"

    def test_concurrent_access(self, cache_manager):
        """Test cache handles concurrent access gracefully."""
        import threading
        import time

        results = []

        def worker(worker_id):
            for i in range(10):
                key = f"worker_{worker_id}_key_{i}"
                cache_manager.set(key, f"value_{i}", ttl_hours=1)
                time.sleep(0.001)  # Small delay
                retrieved = cache_manager.get(key)
                results.append(retrieved == f"value_{i}")

        # Start multiple threads
        threads = []
        for i in range(3):
            t = threading.Thread(target=worker, args=(i,))
            threads.append(t)
            t.start()

        # Wait for all threads
        for t in threads:
            t.join()

        # All operations should have succeeded
        assert all(results)

    def test_corrupted_cache_file_recovery(self, cache_dir):
        """Test recovery from corrupted cache file."""
        # Ensure cache directory exists
        cache_dir.mkdir(parents=True, exist_ok=True)

        # Create a corrupted cache file (simulate a real cache file that got corrupted)
        corrupted_file = cache_dir / "test_key.json"
        corrupted_file.write_text("invalid json content")

        # Create new manager - should handle corruption gracefully
        manager = CacheManager(str(cache_dir))

        # Should still work - corrupted file should be ignored
        manager.set("test", "data", ttl_hours=1)
        assert manager.get("test") == "data"
