"""Document extraction adapters and registry."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Type

from data_extract.extract.adapter import ExtractorAdapter
from data_extract.extract.csv import CsvExtractorAdapter
from data_extract.extract.docx import DocxExtractorAdapter
from data_extract.extract.excel import ExcelExtractorAdapter
from data_extract.extract.pdf import PdfExtractorAdapter
from data_extract.extract.pptx import PptxExtractorAdapter
from data_extract.extract.txt import TxtExtractorAdapter

EXTRACTOR_REGISTRY: Dict[str, Type[ExtractorAdapter]] = {
    ".pdf": PdfExtractorAdapter,
    ".docx": DocxExtractorAdapter,
    ".xlsx": ExcelExtractorAdapter,
    ".xls": ExcelExtractorAdapter,
    ".xlsm": ExcelExtractorAdapter,
    ".pptx": PptxExtractorAdapter,
    ".csv": CsvExtractorAdapter,
    ".tsv": CsvExtractorAdapter,
    ".txt": TxtExtractorAdapter,
    ".text": TxtExtractorAdapter,
    ".md": TxtExtractorAdapter,
    ".log": TxtExtractorAdapter,
}

SUPPORTED_EXTENSIONS = set(EXTRACTOR_REGISTRY.keys())


def get_extractor(file_path: Path) -> ExtractorAdapter:
    """Return an extractor adapter for the file extension."""
    extension = file_path.suffix.lower()
    adapter_class = EXTRACTOR_REGISTRY.get(extension)
    if adapter_class is None:
        supported = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        raise ValueError(
            f"Unsupported file extension: {extension or '<none>'}. Supported extensions: {supported}"
        )
    return adapter_class()


def is_supported(file_path: Path) -> bool:
    """Return whether file extension has a registered adapter."""
    return file_path.suffix.lower() in SUPPORTED_EXTENSIONS


__all__ = [
    "ExtractorAdapter",
    "PdfExtractorAdapter",
    "DocxExtractorAdapter",
    "ExcelExtractorAdapter",
    "PptxExtractorAdapter",
    "CsvExtractorAdapter",
    "TxtExtractorAdapter",
    "get_extractor",
    "is_supported",
    "SUPPORTED_EXTENSIONS",
]
