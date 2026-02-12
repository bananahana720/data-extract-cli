"""Extractor adapter base for package-local extraction implementations.

This replaces legacy brownfield wrappers with direct extractors that return the
current greenfield Document model.
"""

from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Tuple
from uuid import uuid4

from data_extract import __version__
from data_extract.core.models import Document, DocumentType, Metadata


class ExtractorAdapter(ABC):
    """Base adapter for format-specific extractors.

    Subclasses extract raw text and lightweight structure metadata from a file.
    The adapter handles conversion into Document + Metadata consistently.
    """

    def __init__(self, format_name: str) -> None:
        self.format_name = format_name

    def process(self, input_data: Path) -> Document:
        """Extract and convert file to a Document model."""
        file_path = Path(input_data)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        text, structure, quality_scores = self.extract(file_path)

        metadata = self._build_metadata(
            file_path,
            text=text,
            structure=structure,
            quality_scores=quality_scores,
        )

        return Document(
            id=self._generate_document_id(file_path),
            text=text,
            entities=[],
            metadata=metadata,
            structure=structure,
        )

    @abstractmethod
    def extract(self, file_path: Path) -> Tuple[str, Dict[str, Any], Dict[str, float]]:
        """Return (text, structure, quality_scores) for the file."""

    def _build_metadata(
        self,
        file_path: Path,
        text: str,
        structure: Dict[str, Any],
        quality_scores: Dict[str, float],
    ) -> Metadata:
        """Create consistent metadata for extracted documents."""
        completeness = 1.0 if text.strip() else 0.0
        quality_flags = ["incomplete_extraction"] if completeness == 0.0 else []
        ocr_confidence_raw = structure.get("ocr_confidence") if isinstance(structure, dict) else {}
        ocr_confidence: Dict[int, float] = {}
        if isinstance(ocr_confidence_raw, dict):
            for page_key, score in ocr_confidence_raw.items():
                try:
                    page_num = int(page_key)
                    value = float(score)
                except (TypeError, ValueError):
                    continue
                if 0.0 <= value <= 1.0:
                    ocr_confidence[page_num] = value

        document_type = self._guess_document_type(file_path)
        document_average_confidence = quality_scores.get(
            "ocr_confidence",
            quality_scores.get("extraction_confidence", 1.0),
        )

        return Metadata(
            source_file=file_path,
            file_hash=self._compute_file_hash(file_path),
            processing_timestamp=datetime.now(timezone.utc),
            tool_version=__version__,
            config_version="1.0.0",
            document_type=document_type,
            document_subtype=self.format_name.lower(),
            quality_scores=quality_scores,
            quality_flags=quality_flags,
            ocr_confidence=ocr_confidence,
            completeness_ratio=completeness,
            entity_tags=[],
            entity_counts={},
            section_context=None,
            config_snapshot={},
            validation_report={
                "quarantine_recommended": completeness == 0.0,
                "document_average_confidence": document_average_confidence,
                "quality_flags": quality_flags,
            },
        )

    @staticmethod
    def _compute_file_hash(file_path: Path) -> str:
        """Compute SHA256 hash for provenance and retry change checks."""
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    @staticmethod
    def _generate_document_id(file_path: Path) -> str:
        """Generate stable-ish id with stem prefix and UUID suffix."""
        stem = file_path.stem.replace(" ", "_").replace("-", "_")
        return f"{stem}_{str(uuid4())[:8]}"

    @staticmethod
    def _guess_document_type(file_path: Path) -> str:
        """Best-effort document type mapping for metadata."""
        suffix = file_path.suffix.lower()
        if suffix in {".xlsx", ".xls", ".xlsm", ".csv", ".tsv"}:
            return DocumentType.MATRIX.value
        if suffix in {".pdf", ".docx", ".pptx", ".txt", ".md", ".log"}:
            return DocumentType.REPORT.value
        return DocumentType.EXPORT.value
