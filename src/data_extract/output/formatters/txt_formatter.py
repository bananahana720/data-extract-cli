"""Plain text formatter for chunk output."""

import re
from collections import defaultdict
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from .base import BaseFormatter, FormattingResult


class TxtFormatter(BaseFormatter):
    """Formats chunks as plain text output."""

    def __init__(
        self,
        include_metadata: bool = False,
        delimiter: str = "━━━ CHUNK {{n}} ━━━",
        per_chunk: bool = False,
    ):
        """Initialize text formatter.

        Args:
            include_metadata: Whether to include metadata headers
            delimiter: Delimiter between chunks
            per_chunk: Whether to write one file per chunk
        """
        self.include_metadata = include_metadata
        self.delimiter = delimiter
        self.per_chunk = per_chunk

    def format_chunks(
        self, chunks: list[Any], output_path: Path, **kwargs: Any
    ) -> FormattingResult:
        """Format chunks as plain text and write to file.

        Args:
            chunks: List of chunks to format
            output_path: Path to write text file
            **kwargs: Additional options

        Returns:
            FormattingResult with operation details
        """
        import time

        start_time = time.time()

        output_path = Path(output_path)
        if not isinstance(chunks, list):
            if isinstance(chunks, Iterable):
                chunks = list(chunks)
            else:
                chunks = [chunks]

        if self.per_chunk:
            output_dir = output_path
            output_dir.mkdir(parents=True, exist_ok=True)
            source_counters: dict[str, int] = defaultdict(int)

            for chunk in chunks:
                source_stem = self._source_stem(chunk)
                source_counters[source_stem] += 1
                chunk_number = source_counters[source_stem]
                chunk_path = output_dir / f"{source_stem}_chunk_{chunk_number:03d}.txt"

                with open(chunk_path, "w", encoding="utf-8-sig") as f:
                    f.write(self.delimiter.replace("{{n}}", f"{chunk_number:03d}"))
                    f.write("\n\n")
                    self._write_chunk_content(f, chunk)
            total_size = sum(path.stat().st_size for path in output_dir.glob("*.txt"))
            result_output_path = output_dir
        else:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", encoding="utf-8-sig") as f:
                for i, chunk in enumerate(chunks, 1):
                    if i == 1:
                        f.write(self.delimiter.replace("{{n}}", f"{i:03d}"))
                        f.write("\n\n")
                    else:
                        f.write("\n\n")
                        f.write(self.delimiter.replace("{{n}}", f"{i:03d}"))
                        f.write("\n\n")
                    self._write_chunk_content(f, chunk)
            total_size = output_path.stat().st_size if output_path.exists() else 0
            result_output_path = output_path

        duration = time.time() - start_time

        return FormattingResult(
            output_path=result_output_path,
            chunk_count=len(chunks),
            total_size=total_size,
            metadata={},
            format_type="txt",
            duration_seconds=duration,
            errors=[],
        )

    @staticmethod
    def _sanitize_path_part(value: str) -> str:
        """Sanitize a path segment for cross-platform safety."""
        sanitized = re.sub(r"[<>:\"|?*]", "_", value)
        sanitized = sanitized.replace("/", "_").replace("\\", "_")
        sanitized = re.sub(r"\s+", "_", sanitized)
        sanitized = re.sub(r"_+", "_", sanitized).strip("._")
        return sanitized or "unknown"

    def _source_stem(self, chunk: Any) -> str:
        """Extract source file stem from chunk metadata."""
        metadata = getattr(chunk, "metadata", None)
        source_file = None
        if metadata is not None:
            if isinstance(metadata, dict):
                source_file = metadata.get("source_file")
            else:
                source_file = getattr(metadata, "source_file", None)
        source_text = (
            str(source_file) if source_file else str(getattr(chunk, "document_id", "unknown"))
        )
        stem = Path(source_text).stem or Path(source_text).name or source_text
        return self._sanitize_path_part(stem)

    def _write_chunk_content(self, handle: Any, chunk: Any) -> None:
        """Write one chunk body with optional metadata headers."""
        if self.include_metadata and hasattr(chunk, "metadata"):
            metadata = chunk.metadata
            source_file = (
                metadata.get("source_file")
                if isinstance(metadata, dict)
                else getattr(metadata, "source_file", None)
            )
            if source_file:
                handle.write(f"Source: {source_file}\n")

            entity_tags = (
                metadata.get("entity_tags", [])
                if isinstance(metadata, dict)
                else getattr(metadata, "entity_tags", [])
            )
            entity_ids: list[str] = []
            for tag in entity_tags:
                if isinstance(tag, dict):
                    entity_id = tag.get("entity_id") or tag.get("id")
                else:
                    entity_id = getattr(tag, "entity_id", None) or getattr(tag, "id", None)
                if entity_id:
                    entity_ids.append(str(entity_id))
            if entity_ids:
                handle.write(f"Entities: {'; '.join(entity_ids)}\n")

            quality = (
                metadata.get("quality")
                if isinstance(metadata, dict)
                else getattr(metadata, "quality", None)
            )
            if isinstance(quality, dict):
                quality_overall = quality.get("overall")
            else:
                quality_overall = getattr(quality, "overall", None) if quality else None
            if quality_overall is not None:
                handle.write(f"Quality: {float(quality_overall):.2f}\n")
            handle.write("\n")

        if hasattr(chunk, "text"):
            handle.write(chunk.text)
        else:
            handle.write(str(chunk))
