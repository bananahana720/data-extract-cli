"""Base formatter interface and common functionality."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class FormattingResult:
    """Result of formatting operation."""

    output_path: Path
    chunk_count: int
    total_size: int
    metadata: dict[str, Any]
    format_type: str = "txt"  # Default format type
    duration_seconds: float = 0.0  # Duration of the formatting operation
    errors: list[str] | None = None  # List of any errors that occurred

    def __post_init__(self) -> None:
        # Initialize errors as empty list if None
        if self.errors is None:
            object.__setattr__(self, "errors", [])

    @property
    def file_size_bytes(self) -> int:
        """Backward-compatible alias for total_size."""
        return self.total_size


class BaseFormatter(ABC):
    """Base class for all output formatters."""

    @abstractmethod
    def format_chunks(
        self, chunks: list[Any], output_path: Path, **kwargs: Any
    ) -> FormattingResult:
        """Format chunks and write to output path.

        Args:
            chunks: List of chunks to format
            output_path: Path to write output
            **kwargs: Additional formatter-specific options

        Returns:
            FormattingResult with details of operation
        """
        pass
