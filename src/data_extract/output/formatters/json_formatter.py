"""JSON formatter for chunk output."""

import json
import time
from pathlib import Path
from typing import Any, Iterable

from .base import BaseFormatter, FormattingResult


class JsonFormatter(BaseFormatter):
    """Formats chunks as JSON output."""

    def __init__(self, validate: bool = True, write_bom: bool = True) -> None:
        """Initialize JSON formatter.

        Args:
            validate: Whether to validate output against schema
            write_bom: Whether to write UTF-8 BOM for compatibility tooling
        """
        self.validate = validate
        self.write_bom = write_bom

    def format_chunks(
        self, chunks: Iterable[Any], output_path: Path, **kwargs: Any
    ) -> FormattingResult:
        """Format chunks as JSON and write to file.

        Args:
            chunks: List of chunks to format
            output_path: Path to write JSON file
            **kwargs: Additional options

        Returns:
            FormattingResult with operation details
        """

        start_time = time.time()

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert iterator to list if necessary
        chunk_list: list[Any] = list(chunks) if not isinstance(chunks, list) else chunks

        # Track unique source documents
        source_documents: set[str] = set()

        # Convert chunks to JSON-serializable format
        output_data: dict[str, Any] = {
            "metadata": {
                "chunk_count": len(chunk_list),
                "processing_version": "1.0.0",
                "source_documents": [],
            },
            "chunks": [],
            "content": "",
        }

        # Process each chunk
        from data_extract.services.chunk_io import chunk_to_dict

        for chunk in chunk_list:
            chunk_data = chunk_to_dict(chunk)
            output_data["chunks"].append(chunk_data)
            metadata = chunk_data.get("metadata", {})
            source_file = metadata.get("source_file")
            if source_file:
                source_documents.add(str(source_file))

        # Add collected source documents to output metadata
        output_data["metadata"]["source_documents"] = sorted(list(source_documents))
        output_data["content"] = "\n\n".join(
            str(chunk.get("text", "")) for chunk in output_data["chunks"]
        ).strip()

        if self.validate:
            self._validate_output_data(output_data)

        encoding = "utf-8-sig" if self.write_bom else "utf-8"
        with open(output_path, "w", encoding=encoding) as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        duration = time.time() - start_time

        return FormattingResult(
            output_path=output_path,
            chunk_count=len(chunk_list),
            total_size=output_path.stat().st_size if output_path.exists() else 0,
            metadata={},
            format_type="json",
            duration_seconds=duration,
            errors=[],
        )

    @staticmethod
    def _validate_output_data(output_data: dict[str, Any]) -> None:
        """Perform lightweight schema checks and JSON round-trip validation."""
        metadata = output_data.get("metadata")
        chunks = output_data.get("chunks")
        content = output_data.get("content")

        if not isinstance(metadata, dict):
            raise ValueError("JSON output metadata must be an object")
        if not isinstance(chunks, list):
            raise ValueError("JSON output chunks must be a list")
        if not isinstance(content, str):
            raise ValueError("JSON output content must be a string")

        for chunk in chunks:
            if not isinstance(chunk, dict):
                raise ValueError("Each chunk must be an object")
            if "id" not in chunk or "text" not in chunk:
                raise ValueError("Each chunk must include id and text fields")

        # Round-trip once to ensure generated payload is JSON-safe.
        reparsed = json.loads(json.dumps(output_data, ensure_ascii=False))
        if reparsed.get("metadata", {}).get("chunk_count") != len(chunks):
            raise ValueError("chunk_count does not match chunk payload length")
