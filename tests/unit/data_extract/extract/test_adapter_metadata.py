from pathlib import Path
from typing import Any, Dict, Tuple

from data_extract.extract.adapter import ExtractorAdapter


class _SyntheticExtractor(ExtractorAdapter):
    def __init__(self) -> None:
        super().__init__(format_name="pdf")

    def extract(self, file_path: Path) -> Tuple[str, Dict[str, Any], Dict[str, float]]:
        _ = file_path
        return (
            "synthetic text",
            {
                "page_count": 2,
                "non_empty_pages": 2,
                "ocr_confidence": {1: 0.91, 2: 0.95},
            },
            {
                "extraction_confidence": 1.0,
                "ocr_confidence": 0.93,
            },
        )


def test_adapter_maps_ocr_confidence_structure_into_metadata(tmp_path: Path) -> None:
    input_file = tmp_path / "input.pdf"
    input_file.write_text("placeholder", encoding="utf-8")

    document = _SyntheticExtractor().process(input_file)

    assert document.metadata.ocr_confidence == {1: 0.91, 2: 0.95}
    assert document.metadata.quality_scores["ocr_confidence"] == 0.93
    assert document.metadata.validation_report["document_average_confidence"] == 0.93
