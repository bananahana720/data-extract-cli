"""Text extractor adapter."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Tuple

from data_extract.extract.adapter import ExtractorAdapter


class TxtExtractorAdapter(ExtractorAdapter):
    """Extractor for UTF-8-ish plain-text inputs."""

    def __init__(self) -> None:
        super().__init__(format_name="txt")

    def extract(self, file_path: Path) -> Tuple[str, Dict[str, Any], Dict[str, float]]:
        text = file_path.read_text(encoding="utf-8", errors="ignore")
        line_count = len(text.splitlines())
        structure = {
            "line_count": line_count,
            "char_count": len(text),
        }
        quality = {
            "extraction_confidence": 1.0,
        }
        return text, structure, quality
