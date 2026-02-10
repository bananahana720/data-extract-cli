"""Abstract base class for report generation."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional

from ..models import ScanStatistics, SecurityFinding


class AbstractReporter(ABC):
    """Abstract base class for all report generators."""

    @abstractmethod
    def generate(
        self,
        findings: List[SecurityFinding],
        stats: ScanStatistics,
        output_file: Optional[Path] = None,
    ) -> str:
        """Generate a security report.

        Args:
            findings: List of security findings
            stats: Scan statistics
            output_file: Optional output file path

        Returns:
            Generated report content
        """
        pass

    def save(self, content: str, output_file: Path) -> None:
        """Save report content to file.

        Args:
            content: Report content
            output_file: Output file path
        """
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(content)
