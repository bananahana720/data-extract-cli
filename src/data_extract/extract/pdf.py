"""PDF extractor adapter."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Tuple

from data_extract.extract.adapter import ExtractorAdapter


class PdfExtractorAdapter(ExtractorAdapter):
    """Extractor for PDF files using pypdf."""

    def __init__(self) -> None:
        super().__init__(format_name="pdf")

    def extract(self, file_path: Path) -> Tuple[str, Dict[str, Any], Dict[str, float]]:
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise RuntimeError("pypdf is required for PDF extraction") from exc

        reader = PdfReader(str(file_path))
        page_texts = []
        non_empty_pages = 0

        for page in reader.pages:
            text = page.extract_text() or ""
            text = text.strip()
            page_texts.append(text)
            if text:
                non_empty_pages += 1

        text = "\n\n".join(page_texts)
        page_count = len(reader.pages)
        confidence = (non_empty_pages / page_count) if page_count else 0.0

        structure = {
            "page_count": page_count,
            "non_empty_pages": non_empty_pages,
        }
        quality = {
            "extraction_confidence": confidence,
        }
        return text, structure, quality
