"""Cache management for false positives."""

import hashlib
import json
from typing import Set

import structlog  # type: ignore[import-not-found]

from ..config import CACHE_DIR

logger = structlog.get_logger()


class CacheManager:
    """Manages false positive caching."""

    def __init__(self):
        """Initialize cache manager."""
        self.cache_file = CACHE_DIR / "false_positives.json"
        self.false_positive_hashes: Set[str] = self._load_false_positives()

    def _load_false_positives(self) -> Set[str]:
        """Load false positive hashes from cache."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, "r") as f:
                    data = json.load(f)
                    hashes = set(data.get("hashes", []))
                    logger.info("loaded_false_positives", count=len(hashes))
                    return hashes
            except Exception as e:
                logger.warning("failed_to_load_false_positives", error=str(e))
        return set()

    def save_false_positives(self) -> None:
        """Save false positive hashes to cache."""
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        try:
            with open(self.cache_file, "w") as f:
                json.dump({"hashes": list(self.false_positive_hashes)}, f)
            logger.info("saved_false_positives", count=len(self.false_positive_hashes))
        except Exception as e:
            logger.error("failed_to_save_false_positives", error=str(e))

    def is_false_positive(self, file_path: str, line_number: int, match: str) -> bool:
        """Check if a finding is a false positive."""
        finding_hash = self.calculate_hash(file_path, line_number, match)
        return finding_hash in self.false_positive_hashes

    def mark_false_positive(self, file_path: str, line_number: int, match: str) -> None:
        """Mark a finding as a false positive."""
        finding_hash = self.calculate_hash(file_path, line_number, match)
        self.false_positive_hashes.add(finding_hash)

    @staticmethod
    def calculate_hash(file_path: str, line_number: int, match: str) -> str:
        """Calculate hash for deduplication."""
        content = f"{file_path}:{line_number}:{match}"
        return hashlib.md5(content.encode()).hexdigest()
