"""Worker module for profile_pipeline multiprocessing tasks."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path

from src.data_extract.core.models import Document
from src.data_extract.extract import get_extractor, is_supported


@dataclass
class BatchResult:
    """Container for one extracted file result."""

    file_path: Path
    success: bool = False
    error_message: str = ""
    processing_time_ms: float = 0.0
    document_id: str = ""
    text_length: int = 0
    page_count: int = 0
    word_count: int = 0
    ocr_confidence: float | None = None
    quality_flags: list[str] = field(default_factory=list)


def extract_single_file(file_path: Path) -> BatchResult:
    """Extract one file and return structured benchmark data."""
    result = BatchResult(file_path=file_path)

    if not is_supported(file_path):
        result.error_message = f"Unsupported format: {file_path.suffix}"
        return result

    try:
        start_time = time.time()
        adapter = get_extractor(file_path)
        document: Document = adapter.process(file_path)
        elapsed = time.time() - start_time

        result.success = True
        result.processing_time_ms = elapsed * 1000
        result.document_id = document.id
        result.text_length = len(document.text)
        result.page_count = document.structure.get("page_count", 0)
        result.word_count = document.structure.get("word_count", 0)
        result.ocr_confidence = document.metadata.quality_scores.get("ocr_confidence")
        result.quality_flags = list(document.metadata.quality_flags)
    except Exception as exc:
        result.error_message = str(exc)

    return result
