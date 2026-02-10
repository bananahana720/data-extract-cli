"""CSV/TSV extractor adapter."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Dict, Tuple

from data_extract.extract.adapter import ExtractorAdapter


class CsvExtractorAdapter(ExtractorAdapter):
    """Extractor for CSV-like tabular files."""

    def __init__(self) -> None:
        super().__init__(format_name="csv")

    def extract(self, file_path: Path) -> Tuple[str, Dict[str, Any], Dict[str, float]]:
        raw = file_path.read_text(encoding="utf-8", errors="ignore")
        sample = raw[:2048]
        delimiter = ","
        try:
            dialect = csv.Sniffer().sniff(sample)
            delimiter = dialect.delimiter
        except csv.Error:
            if file_path.suffix.lower() == ".tsv":
                delimiter = "\t"

        reader = csv.reader(raw.splitlines(), delimiter=delimiter)
        rows = list(reader)
        if not rows:
            return "", {"row_count": 0, "column_count": 0}, {"extraction_confidence": 0.0}

        header = rows[0]
        body = rows[1:] if len(rows) > 1 else []
        lines = [" | ".join(header)]
        for row in body:
            lines.append(" | ".join(str(cell) for cell in row))

        text = "\n".join(lines)
        structure = {
            "row_count": len(rows),
            "column_count": len(header),
            "delimiter": delimiter,
        }
        quality = {
            "extraction_confidence": 1.0,
        }
        return text, structure, quality
