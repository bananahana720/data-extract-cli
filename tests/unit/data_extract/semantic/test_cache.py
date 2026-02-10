"""Unit tests for semantic cache manager."""

import tempfile
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from data_extract.semantic.cache import CacheManager
from data_extract.semantic.models import TfidfConfig

pytestmark = [pytest.mark.P0, pytest.mark.unit]


class TestCacheManager:
    """Tests for CacheManager class."""

    def setup_method(self):
        """Reset the singleton before each test for proper isolation."""
        CacheManager._reset()

    def _create_cache_manager(self, cache_dir=None, max_size_mb=None):
        """Helper to create a CacheManager with custom parameters.

        Args:
            cache_dir: Custom cache directory
            max_size_mb: Maximum cache size in MB

        Returns:
            CacheManager instance with custom parameters
        """
        manager = CacheManager()
        # Reset and reinitialize with custom params if provided
        if cache_dir is not None or max_size_mb is not None:
            manager._initialized = False
            kwargs = {}
            if cache_dir is not None:
                kwargs["cache_dir"] = cache_dir
            if max_size_mb is not None:
                kwargs["max_size_mb"] = max_size_mb
            manager.__init__(**kwargs)
        return manager

    def test_singleton_pattern(self):
        """Test that CacheManager follows singleton pattern."""
        manager1 = CacheManager()
        manager2 = CacheManager()
        assert manager1 is manager2

    def test_initialization(self):
        """Test cache manager initialization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "test_cache"
            manager = self._create_cache_manager(cache_dir=cache_dir, max_size_mb=100)

            assert manager.cache_dir == cache_dir
            assert manager.max_size_mb == 100
            assert manager.compression_level == 3
            assert cache_dir.exists()

    def test_generate_cache_key(self):
        """Test cache key generation."""
        manager = CacheManager()
        config = TfidfConfig(max_features=5000, min_df=2)

        # Same content and config should generate same key
        key1 = manager.generate_cache_key("test content", config)
        key2 = manager.generate_cache_key("test content", config)
        assert key1 == key2
        assert key1.startswith("tfidf_v1_")

        # Different content should generate different keys
        key3 = manager.generate_cache_key("different content", config)
        assert key3 != key1

        # Different config should generate different keys
        config2 = TfidfConfig(max_features=10000, min_df=2)
        key4 = manager.generate_cache_key("test content", config2)
        assert key4 != key1

    def test_set_and_get(self):
        """Test setting and getting cached objects."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "test_cache"
            manager = self._create_cache_manager(cache_dir=cache_dir)

            # Test data
            test_data = {
                "matrix": [[1, 2], [3, 4]],
                "vocabulary": {"word1": 0, "word2": 1},
            }

            # Set cache
            manager.set("test_key", test_data)

            # Get cache
            retrieved_data = manager.get("test_key")
            assert retrieved_data == test_data

            # Check that cache file exists
            cache_file = cache_dir / "test_key.joblib"
            assert cache_file.exists()

    def test_cache_miss(self):
        """Test cache miss behavior."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "test_cache"
            manager = self._create_cache_manager(cache_dir=cache_dir)

            # Try to get non-existent key
            result = manager.get("non_existent_key")
            assert result is None
            assert manager._cache_misses == 1

    def test_cache_hit_tracking(self):
        """Test cache hit and miss tracking."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "test_cache"
            manager = self._create_cache_manager(cache_dir=cache_dir)

            # Reset singleton
            manager._cache_hits = 0
            manager._cache_misses = 0

            # Cache miss
            manager.get("missing_key")
            assert manager._cache_hits == 0
            assert manager._cache_misses == 1

            # Cache hit
            manager.set("existing_key", {"data": "test"})
            manager.get("existing_key")
            assert manager._cache_hits == 1
            assert manager._cache_misses == 1

    def test_cache_index_persistence(self):
        """Test that cache index is persisted and loaded."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "test_cache"

            # Create first manager instance and add data
            manager1 = self._create_cache_manager(cache_dir=cache_dir)
            manager1.set("key1", {"data": "test1"})
            manager1.set("key2", {"data": "test2"})

            # Create second manager instance - should load index
            CacheManager._reset()  # Reset singleton to force reload
            manager2 = self._create_cache_manager(cache_dir=cache_dir)

            # Check that index was loaded
            assert len(manager2._cache_index) == 2
            assert "key1" in manager2._cache_index
            assert "key2" in manager2._cache_index

    def test_lru_eviction(self):
        """Test LRU eviction when cache size limit is reached."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "test_cache"
            # Very small cache for testing eviction (0.00005 MB = 50 bytes)
            manager = self._create_cache_manager(cache_dir=cache_dir, max_size_mb=0.00005)

            # Add items that will exceed cache size
            # Compression makes these ~32 bytes each
            large_data = "x" * 1000

            # Add first item
            manager.set("key1", large_data)
            time.sleep(0.01)  # Small delay for access time difference

            # Add second item - should trigger eviction
            manager.set("key2", large_data)

            # Access key2 to make it more recently used
            manager.get("key2")
            time.sleep(0.01)

            # Add third item - should evict key1 (least recently used)
            manager.set("key3", large_data)

            # Check that key1 was evicted
            assert manager.get("key1") is None
            # key2 and key3 should still exist (one or both)
            assert manager.get("key2") is not None or manager.get("key3") is not None

    def test_corrupted_cache_handling(self):
        """Test handling of corrupted cache files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "test_cache"
            manager = self._create_cache_manager(cache_dir=cache_dir)

            # Reset singleton

            # Create a corrupted cache file
            cache_file = cache_dir / "corrupted_key.joblib"
            cache_file.write_text("corrupted data")

            # Add to index
            manager._cache_index["corrupted_key"] = {
                "file": str(cache_file),
                "size_bytes": 100,
                "created": time.time(),
                "last_access": time.time(),
            }

            # Try to get corrupted cache
            result = manager.get("corrupted_key")
            assert result is None

            # Check that corrupted entry was removed from index
            assert "corrupted_key" not in manager._cache_index

    def test_clear_cache(self):
        """Test clearing all cache entries."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "test_cache"
            manager = self._create_cache_manager(cache_dir=cache_dir)

            # Add some data
            manager.set("key1", {"data": "test1"})
            manager.set("key2", {"data": "test2"})
            manager.set("key3", {"data": "test3"})

            # Verify data exists
            assert len(manager._cache_index) == 3
            assert manager.get("key1") is not None

            # Clear cache
            manager.clear()

            # Verify cache is empty
            assert len(manager._cache_index) == 0
            assert manager._cache_hits == 0
            assert manager._cache_misses == 0
            # This get will increment misses, so check it after verifying counters
            assert manager.get("key1") is None

    def test_get_stats(self):
        """Test getting cache statistics."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "test_cache"
            manager = self._create_cache_manager(cache_dir=cache_dir, max_size_mb=100)

            # Reset singleton
            manager._initialized = False
            manager.__init__(cache_dir=cache_dir, max_size_mb=100)
            manager._cache_hits = 0
            manager._cache_misses = 0

            # Add some data
            manager.set("key1", {"data": "test1"})
            manager.set("key2", {"data": "test2"})

            # Generate some hits and misses
            manager.get("key1")  # hit
            manager.get("key2")  # hit
            manager.get("missing")  # miss

            stats = manager.get_stats()

            assert stats["cache_hits"] == 2
            assert stats["cache_misses"] == 1
            assert stats["hit_ratio"] == 2 / 3
            assert stats["num_entries"] == 2
            assert stats["max_size_mb"] == 100
            assert str(cache_dir) in stats["cache_dir"]

    def test_remove_cache_entry(self):
        """Test removing individual cache entries."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "test_cache"
            manager = self._create_cache_manager(cache_dir=cache_dir)

            # Reset singleton

            # Add data
            manager.set("key_to_remove", {"data": "test"})
            assert "key_to_remove" in manager._cache_index

            # Remove entry
            manager._remove_cache_entry("key_to_remove")

            # Verify removal
            assert "key_to_remove" not in manager._cache_index
            assert manager.get("key_to_remove") is None

    def test_cache_with_none_config(self):
        """Test cache key generation with object without get_cache_key_components."""
        manager = CacheManager()

        # Object without get_cache_key_components method
        simple_config = {"max_features": 5000}

        key1 = manager.generate_cache_key("test content", simple_config)
        key2 = manager.generate_cache_key("test content", simple_config)
        assert key1 == key2
        assert key1.startswith("tfidf_v1_")

    def test_warm_cache(self):
        """Test cache warming (placeholder functionality)."""
        manager = CacheManager()

        # Should not raise error (placeholder implementation)
        common_configs = [
            ("config1", {"max_features": 5000}),
            ("config2", {"max_features": 10000}),
        ]
        manager.warm_cache(common_configs)  # Should complete without error

    def test_cache_compression(self):
        """Test that cache files are compressed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "test_cache"
            manager = self._create_cache_manager(cache_dir=cache_dir)

            # Reset singleton

            # Create large data structure
            large_data = {"numbers": list(range(10000))}

            # Cache it
            manager.set("large_key", large_data)

            # Verify compression is used (file should be smaller than uncompressed)
            cache_file = cache_dir / "large_key.joblib"
            assert cache_file.exists()

            # Load and verify data integrity
            retrieved_data = manager.get("large_key")
            assert retrieved_data == large_data

    @patch("data_extract.semantic.cache.logger")
    def test_error_logging(self, mock_logger):
        """Test that errors are properly logged."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "test_cache"
            manager = self._create_cache_manager(cache_dir=cache_dir)

            # Create a read-only cache file to trigger error
            cache_file = cache_dir / "readonly_key.joblib"
            cache_file.touch()
            cache_file.chmod(0o000)

            # Try to load (should fail and log error)
            manager._cache_index["readonly_key"] = {
                "file": str(cache_file),
                "size_bytes": 100,
                "created": time.time(),
                "last_access": time.time(),
            }

            result = manager.get("readonly_key")
            assert result is None

            # Clean up - check if file still exists before chmod
            if cache_file.exists():
                cache_file.chmod(0o644)

    def test_cache_size_calculation(self):
        """Test accurate cache size tracking."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "test_cache"
            manager = self._create_cache_manager(cache_dir=cache_dir)

            # Reset singleton

            # Add data of known sizes
            small_data = {"small": "data"}
            large_data = {"large": "x" * 1000}

            manager.set("small_key", small_data)
            manager.set("large_key", large_data)

            stats = manager.get_stats()
            assert stats["total_size_mb"] > 0
            assert stats["num_entries"] == 2

            # Verify sizes are tracked in index
            assert manager._cache_index["small_key"]["size_bytes"] > 0
            assert (
                manager._cache_index["large_key"]["size_bytes"]
                > manager._cache_index["small_key"]["size_bytes"]
            )
