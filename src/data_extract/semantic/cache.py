"""Cache management for semantic analysis models and results."""

import hashlib
import logging
import shutil
from pathlib import Path
from typing import Any, Dict, Optional

import joblib

logger = logging.getLogger(__name__)


class CacheManager:
    """Singleton cache manager for semantic analysis models.

    Manages persistent caching of TF-IDF vectorizers and sparse matrices
    using joblib serialization with SHA256 content hashing.
    """

    _instance: Optional["CacheManager"] = None
    _initialized: bool = False

    def __new__(cls) -> "CacheManager":
        """Create or return singleton instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, cache_dir: Optional[Path] = None, max_size_mb: int = 500):
        """Initialize cache manager.

        Args:
            cache_dir: Directory for cache storage (default: .data-extract-cache/models/)
            max_size_mb: Maximum cache size in MB (default: 500)
        """
        # Only initialize once
        if self._initialized:
            return

        self.cache_dir = cache_dir or Path(".data-extract-cache/models/")
        self.max_size_mb = max_size_mb
        self.compression_level = 3  # joblib compression level
        self._cache_hits = 0
        self._cache_misses = 0
        self._cache_index: Dict[str, Dict[str, Any]] = {}

        # Create cache directory if it doesn't exist
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Load cache index
        self._load_cache_index()

        self._initialized = True
        logger.info(f"CacheManager initialized with directory: {self.cache_dir}")

    def _load_cache_index(self) -> None:
        """Load cache index from disk."""
        index_file = self.cache_dir / "cache_index.joblib"
        if index_file.exists():
            try:
                self._cache_index = joblib.load(index_file)
                logger.debug(f"Loaded cache index with {len(self._cache_index)} entries")
            except Exception as e:
                logger.warning(f"Failed to load cache index: {e}")
                self._cache_index = {}
        else:
            self._cache_index = {}

    def _save_cache_index(self) -> None:
        """Save cache index to disk."""
        index_file = self.cache_dir / "cache_index.joblib"
        try:
            joblib.dump(self._cache_index, index_file, compress=self.compression_level)
        except Exception as e:
            logger.error(f"Failed to save cache index: {e}")

    def generate_cache_key(self, content: str, config: Any) -> str:
        """Generate SHA256-based cache key from content and configuration.

        Args:
            content: Text content to hash
            config: Configuration object with get_cache_key_components method

        Returns:
            Cache key string (format: tfidf_v1_[sha256[:8]])
        """
        # Combine content with config components for unique key
        hasher = hashlib.sha256()
        hasher.update(content.encode("utf-8"))

        # Add config components to hash
        if hasattr(config, "get_cache_key_components"):
            for component in config.get_cache_key_components():
                hasher.update(str(component).encode("utf-8"))

        hash_hex = hasher.hexdigest()[:8]
        return f"tfidf_v1_{hash_hex}"

    def get(self, key: str) -> Optional[Any]:
        """Retrieve cached object by key.

        Args:
            key: Cache key

        Returns:
            Cached object or None if not found
        """
        cache_file = self.cache_dir / f"{key}.joblib"

        if not cache_file.exists():
            self._cache_misses += 1
            logger.debug(f"Cache miss for key: {key}")
            return None

        try:
            data = joblib.load(cache_file)
            self._cache_hits += 1

            # Update access time in index
            if key in self._cache_index:
                import time

                self._cache_index[key]["last_access"] = time.time()
                self._save_cache_index()

            logger.debug(f"Cache hit for key: {key}")
            return data
        except Exception as e:
            logger.error(f"Failed to load cache for key {key}: {e}")
            self._cache_misses += 1

            # Remove corrupted cache entry
            self._remove_cache_entry(key)
            return None

    def set(self, key: str, value: Any) -> None:
        """Store object in cache.

        Args:
            key: Cache key
            value: Object to cache
        """
        # Check cache size and perform LRU eviction if needed
        self._ensure_cache_size()

        cache_file = self.cache_dir / f"{key}.joblib"

        try:
            joblib.dump(value, cache_file, compress=self.compression_level)

            # Update cache index
            import time

            file_size = cache_file.stat().st_size
            self._cache_index[key] = {
                "file": str(cache_file),
                "size_bytes": file_size,
                "created": time.time(),
                "last_access": time.time(),
            }
            self._save_cache_index()

            logger.debug(f"Cached object with key: {key} (size: {file_size / 1024:.1f} KB)")
        except Exception as e:
            logger.error(f"Failed to cache object with key {key}: {e}")

    def _ensure_cache_size(self) -> None:
        """Ensure cache size is within limits using LRU eviction."""
        total_size = sum(entry["size_bytes"] for entry in self._cache_index.values())
        max_size_bytes = self.max_size_mb * 1024 * 1024

        if total_size <= max_size_bytes:
            return

        # Sort by last access time (LRU)
        sorted_entries = sorted(self._cache_index.items(), key=lambda x: x[1].get("last_access", 0))

        # Remove oldest entries until size is within limit
        for key, entry in sorted_entries:
            if total_size <= max_size_bytes * 0.9:  # Keep 10% buffer
                break

            self._remove_cache_entry(key)
            total_size -= entry["size_bytes"]
            logger.info(f"Evicted cache entry {key} (LRU)")

    def _remove_cache_entry(self, key: str) -> None:
        """Remove a cache entry.

        Args:
            key: Cache key to remove
        """
        if key in self._cache_index:
            entry = self._cache_index[key]
            cache_file = Path(entry["file"])

            if cache_file.exists():
                try:
                    cache_file.unlink()
                except Exception as e:
                    logger.error(f"Failed to remove cache file {cache_file}: {e}")

            del self._cache_index[key]
            self._save_cache_index()

    def clear(self) -> None:
        """Clear all cached entries."""
        try:
            shutil.rmtree(self.cache_dir)
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            self._cache_index = {}
            self._save_cache_index()
            self._cache_hits = 0
            self._cache_misses = 0
            logger.info("Cache cleared successfully")
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        total_size = sum(entry["size_bytes"] for entry in self._cache_index.values())
        hit_ratio = (
            self._cache_hits / (self._cache_hits + self._cache_misses)
            if (self._cache_hits + self._cache_misses) > 0
            else 0.0
        )

        return {
            "cache_hits": self._cache_hits,
            "cache_misses": self._cache_misses,
            "hit_ratio": hit_ratio,
            "num_entries": len(self._cache_index),
            "total_size_mb": total_size / (1024 * 1024),
            "max_size_mb": self.max_size_mb,
            "cache_dir": str(self.cache_dir),
        }

    def warm_cache(self, common_configs: list) -> None:
        """Warm cache with common configurations.

        Args:
            common_configs: List of common configuration tuples
        """
        # This would be implemented to pre-compute common configurations
        # For now, it's a placeholder for future enhancement
        logger.info(f"Cache warming requested for {len(common_configs)} configurations")
        # TODO: Implement cache warming strategy

    @classmethod
    def _reset(cls) -> None:
        """Reset singleton instance (for testing only).

        WARNING: This method should only be used in test environments
        to ensure proper test isolation. Using it in production code
        will break the singleton pattern and may lead to unexpected behavior.
        """
        cls._instance = None
        cls._initialized = False
        logger.debug("CacheManager singleton reset (test mode)")
