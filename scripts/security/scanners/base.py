"""Abstract base class for security scanners."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Set

import structlog  # type: ignore[import-not-found]

from ..config import SCANIGNORE_FILE, SKIP_DIRS
from ..models import SecurityFinding

logger = structlog.get_logger()


class AbstractScanner(ABC):
    """Abstract base class for all security scanners."""

    def __init__(self, project_root: Path):
        """Initialize scanner with project root."""
        self.project_root = project_root
        self.findings: List[SecurityFinding] = []
        self.scan_ignore_patterns: Set[str] = self._load_scan_ignore()

    def _load_scan_ignore(self) -> Set[str]:
        """Load patterns from .scanignore file."""
        patterns = set()
        if SCANIGNORE_FILE.exists():
            with open(SCANIGNORE_FILE, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        patterns.add(line)
            logger.info("loaded_scanignore", patterns=len(patterns))
        return patterns

    def should_scan_file(self, file_path: Path) -> bool:
        """Check if file should be scanned based on ignore patterns."""
        try:
            relative_path = file_path.relative_to(self.project_root)
        except ValueError:
            # File is outside project root
            return False

        path_str = str(relative_path)

        # Check against ignore patterns
        for pattern in self.scan_ignore_patterns:
            if pattern in path_str or path_str.startswith(pattern):
                return False

        # Skip common directories
        for parent in file_path.parents:
            if parent.name in SKIP_DIRS:
                return False

        return True

    def add_finding(self, finding: SecurityFinding) -> None:
        """Add a security finding to the collection."""
        self.findings.append(finding)

    def get_findings(self) -> List[SecurityFinding]:
        """Get all findings from this scanner."""
        return self.findings

    @abstractmethod
    def scan(self, **kwargs) -> List[SecurityFinding]:
        """Execute the security scan.

        Returns:
            List of security findings
        """
        pass

    def __str__(self) -> str:
        """String representation of scanner."""
        return f"{self.__class__.__name__}(findings={len(self.findings)})"
