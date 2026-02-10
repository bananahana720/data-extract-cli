"""Unit test fixtures for CLI module testing.

Provides lightweight fixtures for unit testing CLI components including
batch processing, summary reporting, and incremental state management.
"""

from pathlib import Path
from typing import Any, Callable, Dict, List

import pytest

from data_extract.cli.summary import QualityMetrics, SummaryReport

# ============================================================================
# DIRECTORY FIXTURES
# ============================================================================


@pytest.fixture
def temp_source_dir(tmp_path: Path) -> Path:
    """Create temporary source directory with test files."""
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    return source_dir


@pytest.fixture
def temp_output_dir(tmp_path: Path) -> Path:
    """Create temporary output directory."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir


@pytest.fixture
def temp_work_dir(tmp_path: Path) -> Path:
    """Create temporary working directory for state files."""
    work_dir = tmp_path / "work"
    work_dir.mkdir()
    return work_dir


# ============================================================================
# FILE FIXTURES
# ============================================================================


@pytest.fixture
def sample_pdf_files(temp_source_dir: Path) -> List[Path]:
    """Create sample PDF files in source directory."""
    files = []
    for i in range(3):
        file_path = temp_source_dir / f"document_{i}.pdf"
        file_path.write_bytes(b"PDF content %d" % i)
        files.append(file_path)
    return files


@pytest.fixture
def sample_docx_files(temp_source_dir: Path) -> List[Path]:
    """Create sample DOCX files in source directory."""
    files = []
    for i in range(2):
        file_path = temp_source_dir / f"document_{i}.docx"
        file_path.write_bytes(b"DOCX content %d" % i)
        files.append(file_path)
    return files


@pytest.fixture
def sample_xlsx_files(temp_source_dir: Path) -> List[Path]:
    """Create sample XLSX files in source directory."""
    files = []
    for i in range(2):
        file_path = temp_source_dir / f"spreadsheet_{i}.xlsx"
        file_path.write_bytes(b"XLSX content %d" % i)
        files.append(file_path)
    return files


@pytest.fixture
def mixed_files(
    sample_pdf_files: List[Path],
    sample_docx_files: List[Path],
    sample_xlsx_files: List[Path],
) -> List[Path]:
    """Combined list of all sample files."""
    return sample_pdf_files + sample_docx_files + sample_xlsx_files


@pytest.fixture
def nested_directory_structure(temp_source_dir: Path) -> Dict[str, List[Path]]:
    """Create nested directory structure with files."""
    # Create subdirectories
    subdir1 = temp_source_dir / "subdir1"
    subdir2 = temp_source_dir / "subdir2"
    nested = subdir1 / "nested"

    subdir1.mkdir()
    subdir2.mkdir()
    nested.mkdir()

    # Create files in different locations
    files = {
        "root": [temp_source_dir / "root.pdf"],
        "subdir1": [subdir1 / "doc1.pdf", subdir1 / "doc2.docx"],
        "subdir2": [subdir2 / "sheet1.xlsx"],
        "nested": [nested / "deep.pdf"],
    }

    for file_list in files.values():
        for file_path in file_list:
            file_path.write_bytes(b"test content")

    return files


# ============================================================================
# STATE FILE FIXTURES
# ============================================================================


@pytest.fixture
def sample_state_data() -> Dict[str, Any]:
    """Sample state file data."""
    return {
        "version": "1.0",
        "source_dir": "/path/to/source",
        "output_dir": "/path/to/output",
        "config_hash": "abc123",
        "processed_at": "2025-11-30T10:00:00Z",
        "files": {
            "/path/to/source/doc1.pdf": {
                "hash": "hash1",
                "processed_at": "2025-11-30T09:55:00Z",
                "output_path": "/path/to/output/doc1.json",
                "size_bytes": 1024,
            },
            "/path/to/source/doc2.pdf": {
                "hash": "hash2",
                "processed_at": "2025-11-30T09:56:00Z",
                "output_path": "/path/to/output/doc2.json",
                "size_bytes": 2048,
            },
        },
    }


# ============================================================================
# SUMMARY FIXTURES
# ============================================================================


@pytest.fixture
def sample_quality_metrics() -> QualityMetrics:
    """Sample quality metrics for testing."""
    return QualityMetrics(
        avg_quality=0.85,
        excellent_count=45,
        good_count=30,
        review_count=10,
        flagged_count=2,
        entity_count=150,
        readability_score=65.5,
        duplicate_percentage=5.2,
    )


@pytest.fixture
def sample_summary_report(sample_quality_metrics: QualityMetrics) -> SummaryReport:
    """Sample summary report for testing."""
    return SummaryReport(
        files_processed=10,
        files_failed=2,
        chunks_created=85,
        errors=("Error 1: Failed to process file A", "Error 2: Invalid format in file B"),
        quality_metrics=sample_quality_metrics,
        timing={
            "extract": 1500.0,
            "normalize": 800.0,
            "chunk": 600.0,
            "semantic": 1200.0,
            "output": 400.0,
        },
        config={
            "chunk_size": 512,
            "overlap": 50,
            "min_quality": 0.7,
        },
        next_steps=(
            "Review 2 flagged chunks for quality issues",
            "Process 5 remaining files in queue",
            "Export results to TXT format",
        ),
        processing_duration_ms=4500.0,
    )


@pytest.fixture
def minimal_summary_report() -> SummaryReport:
    """Minimal summary report without quality metrics."""
    return SummaryReport(
        files_processed=5,
        files_failed=0,
        chunks_created=42,
        errors=(),
        quality_metrics=None,
        timing={
            "extract": 500.0,
            "normalize": 200.0,
            "chunk": 150.0,
            "semantic": 0.0,
            "output": 100.0,
        },
        config={},
        next_steps=(),
    )


# ============================================================================
# TIMING FIXTURES
# ============================================================================


@pytest.fixture
def sample_timing_data() -> Dict[str, float]:
    """Sample timing data for per-stage breakdown."""
    return {
        "extract": 2500.0,
        "normalize": 1200.0,
        "chunk": 800.0,
        "semantic": 1500.0,
        "output": 500.0,
    }


# ============================================================================
# MOCK FILE HELPERS
# ============================================================================


@pytest.fixture
def create_test_file() -> Callable[[Path, bytes], Path]:
    """Helper function to create test files with specific content."""

    def _create(path: Path, content: bytes = b"test content") -> Path:
        """Create a test file at the specified path."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return path

    return _create
