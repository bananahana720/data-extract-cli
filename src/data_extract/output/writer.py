"""Output writer for coordinating formatters and organization."""

import json
import logging
import os
import re
import tempfile
import time
from pathlib import Path
from typing import Any, Iterable, Optional

from .formatters import CsvFormatter, JsonFormatter, TxtFormatter
from .formatters.base import BaseFormatter, FormattingResult
from .organization import OrganizationResult, OrganizationStrategy, Organizer

logger = logging.getLogger(__name__)


class OutputWriter:
    """Main entry point for writing formatted output."""

    def __init__(self) -> None:
        """Initialize output writer."""
        self.organizer = Organizer()

    def write(
        self,
        chunks: Iterable[Any],
        output_path: Path,
        format_type: str = "txt",
        per_chunk: bool = False,
        organize: bool = False,
        strategy: Optional[OrganizationStrategy] = None,
        **kwargs: Any,
    ) -> FormattingResult | OrganizationResult:
        """Write chunks to output with specified format and organization.

        Args:
            chunks: List of chunks to write
            output_path: Output file or directory path
            format_type: Output format (json, txt, csv)
            per_chunk: Write each chunk to separate file
            organize: Enable output organization
            strategy: Organization strategy if organize is True
            **kwargs: Additional formatter options

        Returns:
            FormattingResult or OrganizationResult
        """

        # Convert to list if needed for per_chunk processing
        chunk_list: list[Any] = list(chunks) if not isinstance(chunks, list) else chunks

        if organize and strategy is None:
            raise ValueError("Organization enabled but no strategy provided")
        if strategy is not None and not organize:
            raise ValueError("Strategy provided but organization not enabled")

        # Select formatter based on format type
        formatter: BaseFormatter
        if format_type == "json":
            json_formatter_kwargs: dict[str, Any] = {"validate": kwargs.get("validate", True)}
            if "write_bom" in kwargs:
                json_formatter_kwargs["write_bom"] = kwargs["write_bom"]
            formatter = JsonFormatter(**json_formatter_kwargs)
        elif format_type == "txt":
            formatter = TxtFormatter(
                include_metadata=kwargs.get("include_metadata", False),
                delimiter=kwargs.get("delimiter", "━━━ CHUNK {{n}} ━━━"),
            )
        elif format_type == "csv":
            formatter = CsvFormatter(
                max_text_length=kwargs.get("max_text_length"), validate=kwargs.get("validate", True)
            )
        else:
            raise ValueError(f"Unsupported format type: {format_type}")

        # Handle organization if requested
        if organize and strategy is not None:
            if format_type != "txt":
                # Non-TXT organization remains manifest-only for compatibility with
                # existing unit contracts.
                return self.organizer.organize(
                    chunks=chunk_list,
                    output_dir=Path(output_path),
                    strategy=strategy,
                    format_type=format_type,
                )
            return self._write_organized(
                chunk_list=chunk_list,
                output_dir=Path(output_path),
                formatter=formatter,
                format_type=format_type,
                strategy=strategy,
                **kwargs,
            )

        # Handle per-chunk mode
        if per_chunk:
            start_time = time.time()
            output_dir = Path(output_path)
            output_dir.mkdir(parents=True, exist_ok=True)

            total_size = 0
            created_files: list[Path] = []
            preexisting_files: set[Path] = set()
            current_output: Path | None = None
            txt_source_counters: dict[str, int] = {}
            try:
                # Write each chunk to a separate file
                for i, chunk in enumerate(chunk_list, 1):
                    file_ext = format_type if format_type != "txt" else "txt"
                    if format_type == "txt":
                        source_name = self._resolve_txt_source_name(chunk, fallback_index=i)
                        next_index = txt_source_counters.get(source_name, 0) + 1
                        txt_source_counters[source_name] = next_index
                        chunk_output = output_dir / f"{source_name}_chunk_{next_index:03d}.txt"
                    else:
                        chunk_id = getattr(chunk, "id", f"chunk_{i:03d}")
                        chunk_output = output_dir / f"{chunk_id}.{file_ext}"

                    if chunk_output.exists():
                        preexisting_files.add(chunk_output)
                    current_output = chunk_output
                    result = formatter.format_chunks([chunk], chunk_output, **kwargs)
                    total_size += result.total_size
                    created_files.append(chunk_output)
                    current_output = None
            except Exception:
                rollback_paths = list(created_files)
                if current_output is not None:
                    rollback_paths.append(current_output)
                self._cleanup_files(rollback_paths, skip_paths=preexisting_files)
                raise

            # Return a FormattingResult-like object for per_chunk mode
            return FormattingResult(
                output_path=output_dir,
                chunk_count=len(chunk_list),
                total_size=total_size,
                metadata={},
                format_type=format_type,
                duration_seconds=time.time() - start_time,
                errors=[],
            )

        # Direct formatting
        return formatter.format_chunks(chunk_list, Path(output_path), **kwargs)

    @staticmethod
    def _cleanup_files(paths: list[Path], skip_paths: set[Path] | None = None) -> None:
        """Best-effort cleanup for files created in the current operation."""
        protected_paths = skip_paths or set()
        for file_path in reversed(paths):
            if file_path in protected_paths:
                continue
            try:
                file_path.unlink(missing_ok=True)
            except OSError as exc:
                logger.warning("Output rollback failed for %s: %s", file_path, exc)

    @staticmethod
    def _write_text_atomic(output_path: Path, content: str, encoding: str = "utf-8") -> None:
        """Write text file atomically using temp file + fsync + replace."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        temp_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding=encoding,
                dir=output_path.parent,
                prefix=f".{output_path.name}.",
                suffix=".tmp",
                delete=False,
            ) as temp_file:
                temp_path = Path(temp_file.name)
                temp_file.write(content)
                temp_file.flush()
                os.fsync(temp_file.fileno())
            os.replace(temp_path, output_path)
        except Exception:
            if temp_path is not None:
                temp_path.unlink(missing_ok=True)
            raise

    @staticmethod
    def _sanitize_path_part(value: str) -> str:
        """Sanitize a filename segment for cross-platform safety."""
        sanitized = re.sub(r"[<>:\"|?*]", "_", value)
        sanitized = sanitized.replace("/", "_").replace("\\", "_")
        sanitized = re.sub(r"\s+", "_", sanitized)
        sanitized = re.sub(r"_+", "_", sanitized).strip("._")
        return sanitized or "unknown"

    def _resolve_txt_source_name(self, chunk: Any, fallback_index: int) -> str:
        """Resolve source-based stem used for TXT per-chunk filenames."""
        metadata = getattr(chunk, "metadata", None)
        source_file = None
        if isinstance(metadata, dict):
            source_file = metadata.get("source_file")
        elif metadata is not None:
            source_file = getattr(metadata, "source_file", None)

        if source_file:
            source_text = str(source_file)
            source_name = Path(source_text).stem or Path(source_text).name or source_text
        else:
            source_name = str(getattr(chunk, "document_id", f"chunk_{fallback_index:03d}"))
        return self._sanitize_path_part(source_name)

    def _write_organized(
        self,
        *,
        chunk_list: list[Any],
        output_dir: Path,
        formatter: BaseFormatter,
        format_type: str,
        strategy: OrganizationStrategy,
        **kwargs: Any,
    ) -> FormattingResult:
        """Write chunks into organized directory structures."""
        start_time = time.time()
        output_dir.mkdir(parents=True, exist_ok=True)

        file_ext = format_type if format_type != "txt" else "txt"
        created_files: list[Path] = []
        manifest_json = output_dir / "manifest.json"
        manifest_md = output_dir / "MANIFEST.md"
        preexisting_files: set[Path] = set()
        if manifest_json.exists():
            preexisting_files.add(manifest_json)
        if manifest_md.exists():
            preexisting_files.add(manifest_md)
        current_output: Path | None = None
        total_size = 0

        try:
            for i, chunk in enumerate(chunk_list, 1):
                chunk_id = getattr(chunk, "id", f"chunk_{i:03d}")
                if strategy == OrganizationStrategy.BY_DOCUMENT:
                    document_id = getattr(chunk, "document_id", "unknown_document")
                    destination = output_dir / str(document_id)
                elif strategy == OrganizationStrategy.BY_ENTITY:
                    destination = output_dir / "entities"
                else:
                    destination = output_dir

                destination.mkdir(parents=True, exist_ok=True)
                chunk_output = destination / f"{chunk_id}.{file_ext}"
                if chunk_output.exists():
                    preexisting_files.add(chunk_output)
                current_output = chunk_output
                result = formatter.format_chunks([chunk], chunk_output, **kwargs)
                total_size += result.total_size
                created_files.append(chunk_output)
                current_output = None

            manifest_payload = {
                "strategy": strategy.value,
                "chunk_count": len(chunk_list),
                "files": [str(path.relative_to(output_dir)) for path in created_files],
            }
            self._write_text_atomic(
                output_path=manifest_json,
                content=json.dumps(manifest_payload, indent=2),
                encoding="utf-8",
            )

            manifest_lines = [
                "# Output Manifest",
                "",
                f"Strategy: {strategy.value}",
                f"Chunk count: {len(chunk_list)}",
                "",
                "Files:",
            ]
            manifest_lines.extend(
                f"- {path.relative_to(output_dir).as_posix()}" for path in created_files
            )
            self._write_text_atomic(
                output_path=manifest_md,
                content="\n".join(manifest_lines),
                encoding="utf-8",
            )

            return FormattingResult(
                output_path=output_dir,
                chunk_count=len(chunk_list),
                total_size=total_size,
                metadata={"strategy": strategy.value, "manifest": str(manifest_json)},
                format_type=format_type,
                duration_seconds=time.time() - start_time,
                errors=[],
            )
        except Exception:
            rollback_paths = list(created_files)
            rollback_paths.extend([manifest_json, manifest_md])
            if current_output is not None:
                rollback_paths.append(current_output)
            self._cleanup_files(rollback_paths, skip_paths=preexisting_files)
            raise
