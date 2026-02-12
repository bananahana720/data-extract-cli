from __future__ import annotations

from pathlib import Path

import pytest

from data_extract.extract.pdf import PdfExtractorAdapter

pytestmark = [pytest.mark.unit]


def _write_bytes(path: Path, payload: bytes) -> Path:
    path.write_bytes(payload)
    return path


def test_pdf_adapter_recovers_text_stub_payload(tmp_path: Path) -> None:
    file_path = _write_bytes(
        tmp_path / "stub.pdf",
        b"%PDF-1.4\n" + (b"New PDF document content for incremental testing. " * 5),
    )

    text, structure, quality = PdfExtractorAdapter().extract(file_path)

    assert "New PDF document content" in text
    assert structure["fallback"] == "text_stub"
    assert structure["page_count"] == 1
    assert quality["extraction_confidence"] == 0.25


def test_pdf_adapter_recovers_plaintext_payload_without_pdf_header(tmp_path: Path) -> None:
    file_path = _write_bytes(
        tmp_path / "headerless.pdf",
        b"PDF1 sample content used for CLI glob integration tests.",
    )

    text, structure, quality = PdfExtractorAdapter().extract(file_path)

    assert "CLI glob integration" in text
    assert structure["fallback"] == "text_stub"
    assert quality["extraction_confidence"] == 0.25


def test_pdf_adapter_recovers_tiny_plaintext_payload_without_pdf_header(tmp_path: Path) -> None:
    file_path = _write_bytes(tmp_path / "tiny.pdf", b"PDF1")

    text, structure, quality = PdfExtractorAdapter().extract(file_path)

    assert text == "PDF1"
    assert structure["fallback"] == "text_stub"
    assert quality["extraction_confidence"] == 0.25


def test_pdf_adapter_rejects_invalid_header(tmp_path: Path) -> None:
    file_path = _write_bytes(tmp_path / "corrupt.pdf", b"%PDF-corrupt")

    with pytest.raises(Exception):
        PdfExtractorAdapter().extract(file_path)


def test_pdf_adapter_rejects_binary_truncated_payload(tmp_path: Path) -> None:
    file_path = _write_bytes(tmp_path / "truncated.pdf", b"%PDF-1.4\n" + (b"\x00" * 100))

    with pytest.raises(Exception):
        PdfExtractorAdapter().extract(file_path)


def test_pdf_adapter_accepts_empty_file_stub(tmp_path: Path) -> None:
    file_path = _write_bytes(tmp_path / "empty.pdf", b"")

    text, structure, quality = PdfExtractorAdapter().extract(file_path)

    assert text == ""
    assert structure["fallback"] == "empty_stub"
    assert structure["non_empty_pages"] == 0
    assert quality["extraction_confidence"] == 0.0
