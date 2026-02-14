"""CSV formatter for chunk output."""

import csv
import time
from pathlib import Path
from typing import Any, Iterable, Optional

from .base import BaseFormatter, FormattingResult


class CsvFormatter(BaseFormatter):
    """Formats chunks as CSV output."""

    def __init__(self, max_text_length: Optional[int] = None, validate: bool = True) -> None:
        """Initialize CSV formatter.

        Args:
            max_text_length: Maximum text length before truncation
            validate: Whether to validate output
        """
        self.max_text_length = max_text_length
        self.validate = validate

    def format_chunks(
        self, chunks: Iterable[Any], output_path: Path, **kwargs: Any
    ) -> FormattingResult:
        """Format chunks as CSV and write to file.

        Args:
            chunks: List of chunks to format
            output_path: Path to write CSV file
            **kwargs: Additional options

        Returns:
            FormattingResult with operation details
        """

        start_time = time.time()

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert iterator to list if necessary
        if not isinstance(chunks, list):
            chunks = list(chunks)

        # Write CSV file with UTF-8-sig encoding
        with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            # Write header
            writer.writerow(
                [
                    "chunk_id",
                    "source_file",
                    "section_context",
                    "chunk_text",
                    "entity_tags",
                    "quality_score",
                    "word_count",
                    "token_count",
                    "processing_version",
                    "warnings",
                ]
            )
            # Write chunk data
            for chunk in chunks:
                chunk_text = getattr(chunk, "text", str(chunk))
                warnings = ""

                # Handle text truncation
                if self.max_text_length and len(chunk_text) > self.max_text_length:
                    chunk_text = chunk_text[: self.max_text_length] + "…"
                    warnings = "TRUNCATED"

                # Extract metadata fields if available
                source_file = ""
                section_context = ""
                entity_tags = ""
                quality_score = ""
                word_count = ""
                token_count = ""
                processing_version = ""

                if hasattr(chunk, "metadata") and chunk.metadata is not None:
                    metadata = chunk.metadata
                    if hasattr(metadata, "source_file") and metadata.source_file:
                        source_file = str(metadata.source_file)
                    if hasattr(metadata, "section_context") and metadata.section_context:
                        section_context = metadata.section_context
                    if hasattr(metadata, "entity_tags") and metadata.entity_tags:
                        entity_tags = "; ".join(
                            getattr(e, "entity_id", str(e)) for e in metadata.entity_tags
                        )
                    if hasattr(metadata, "quality") and metadata.quality:
                        quality = metadata.quality
                        if hasattr(quality, "overall"):
                            quality_score = str(quality.overall)
                    if hasattr(metadata, "word_count"):
                        word_count = str(metadata.word_count)
                    if hasattr(metadata, "token_count"):
                        token_count = str(metadata.token_count)
                    if hasattr(metadata, "processing_version") and metadata.processing_version:
                        processing_version = metadata.processing_version

                # Use chunk attributes if metadata doesn't have them
                if not word_count and hasattr(chunk, "word_count"):
                    word_count = str(chunk.word_count)
                if not token_count and hasattr(chunk, "token_count"):
                    token_count = str(chunk.token_count)
                if not section_context and hasattr(chunk, "section_context"):
                    section_context = chunk.section_context
                if not quality_score and hasattr(chunk, "quality_score"):
                    quality_score = str(chunk.quality_score)

                # Use chunk's actual ID, fallback to blank if not available
                chunk_id = getattr(chunk, "id", "")

                writer.writerow(
                    [
                        chunk_id,
                        source_file,
                        section_context,
                        chunk_text,
                        entity_tags,
                        quality_score,
                        word_count,
                        token_count,
                        processing_version,
                        warnings,
                    ]
                )

        duration = time.time() - start_time

        return FormattingResult(
            output_path=output_path,
            chunk_count=len(chunks),
            total_size=output_path.stat().st_size if output_path.exists() else 0,
            metadata={},
            format_type="csv",
            duration_seconds=duration,
            errors=[],
        )
