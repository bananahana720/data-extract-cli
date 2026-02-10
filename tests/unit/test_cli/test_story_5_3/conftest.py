"""Story 5-3 specific test fixtures and configuration.

These fixtures extend the shared CLI fixtures for Story 5-3 progress indicators testing.
Supports testing of:
- Progress bar components (AC-5.3-1, AC-5.3-4)
- Quality dashboard and panels (AC-5.3-2, AC-5.3-3)
- NO_COLOR support (AC-5.3-5)
- Memory performance (AC-5.3-6)
- Verbosity levels (AC-5.3-8)
- Continue-on-error pattern (AC-5.3-9)
"""

from dataclasses import dataclass, field
from pathlib import Path

import pytest

# Import shared fixtures from tests/fixtures/cli_fixtures.py
from tests.fixtures.cli_fixtures import (
    EnvVarsController,
    document_factory,
    env_vars_fixture,
    error_corpus_fixture,
    mock_console,
    mock_home_directory,
    no_color_console,
    typer_cli_runner,
)

# Re-export for local use
__all__ = [
    "typer_cli_runner",
    "env_vars_fixture",
    "mock_home_directory",
    "mock_console",
    "no_color_console",
    "document_factory",
    "error_corpus_fixture",
    # Story 5-3 specific fixtures
    "pipeline_stages",
    "progress_test_corpus",
    "verbosity_levels",
    "quality_metrics_sample",
    "preflight_test_files",
    "batch_processing_fixture",
    "memory_profiler_fixture",
]


# ==============================================================================
# Story 5-3 Specific Fixtures
# ==============================================================================


@pytest.fixture
def pipeline_stages() -> list[str]:
    """
    Provide the 5 pipeline stages for progress tracking tests.

    These match the pipeline architecture:
    extract -> normalize -> chunk -> semantic -> output
    """
    return ["extract", "normalize", "chunk", "semantic", "output"]


@dataclass
class ProgressTestCorpus:
    """Test corpus for progress bar testing.

    Provides files of varying sizes and types for realistic progress testing.
    """

    tmp_path: Path
    files: list[Path] = field(default_factory=list)

    def create_small_batch(self, count: int = 5) -> list[Path]:
        """Create small batch of files for quick tests."""
        self.files = []
        for i in range(count):
            file_path = self.tmp_path / f"doc_{i:03d}.txt"
            file_path.write_text(f"Document {i} content " * 50)
            self.files.append(file_path)
        return self.files

    def create_medium_batch(self, count: int = 20) -> list[Path]:
        """Create medium batch for realistic progress testing."""
        self.files = []
        for i in range(count):
            file_path = self.tmp_path / f"doc_{i:03d}.txt"
            file_path.write_text(f"Document {i} content " * 200)
            self.files.append(file_path)
        return self.files

    def create_large_batch(self, count: int = 100) -> list[Path]:
        """Create large batch for memory/performance testing."""
        self.files = []
        for i in range(count):
            file_path = self.tmp_path / f"doc_{i:03d}.txt"
            file_path.write_text(f"Document {i} content " * 100)
            self.files.append(file_path)
        return self.files

    def create_mixed_type_batch(self) -> list[Path]:
        """Create batch with various file types for type breakdown testing."""
        self.files = []
        # Text files
        for i in range(10):
            file_path = self.tmp_path / f"text_{i}.txt"
            file_path.write_text(f"Text content {i}")
            self.files.append(file_path)

        # Create fake PDF headers (won't extract but tests type detection)
        for i in range(5):
            file_path = self.tmp_path / f"doc_{i}.pdf"
            file_path.write_bytes(b"%PDF-1.4\nTest PDF content")
            self.files.append(file_path)

        # Create fake DOCX files
        for i in range(3):
            file_path = self.tmp_path / f"report_{i}.docx"
            file_path.write_bytes(b"PK\x03\x04Test DOCX")
            self.files.append(file_path)

        return self.files

    def create_json_chunks(self, count: int = 5) -> list[Path]:
        """Create JSON chunk files for semantic command testing.

        Creates properly formatted JSON chunk files that match the brownfield
        semantic command expectations. Each file contains a chunk with:
        - id, text, document_id, position_index
        - token_count, word_count, entities
        - section_context, quality_score, readability_scores, metadata

        Args:
            count: Number of chunk files to create

        Returns:
            List of created JSON chunk file paths
        """
        import json

        # Diverse text content to avoid TF-IDF min_df issues
        topics = [
            "financial audit procedures and compliance standards",
            "human resources policies and employee benefits",
            "information technology security protocols and measures",
            "marketing strategies and customer engagement techniques",
            "supply chain management and logistics optimization",
            "research and development innovation processes",
            "quality assurance testing and validation methods",
            "environmental sustainability and corporate responsibility",
            "legal compliance and regulatory requirements",
            "sales performance metrics and revenue analysis",
        ]

        # Shared intro ensures terms appear across docs (satisfies min_df=2)
        common_intro = "This document provides comprehensive analysis and detailed information about corporate operations. "

        self.files = []
        for i in range(count):
            file_path = self.tmp_path / f"chunk_{i:03d}.json"
            # Use modulo to cycle through topics if count > len(topics)
            topic = topics[i % len(topics)]
            # Shared intro + unique topic content ensures term overlap
            text_content = (
                common_intro
                + f"The primary focus is {topic}. "
                + f"Additional context regarding {topic}. " * 8
            )
            chunk_data = {
                "id": f"chunk_{i}",
                "text": text_content,
                "document_id": f"doc_{i}",
                "position_index": i,
                "token_count": 100,
                "word_count": 50,
                "entities": [],
                "section_context": f"Section {i}",
                "quality_score": 0.85,
                "readability_scores": {},
                "metadata": {},
            }
            file_path.write_text(json.dumps(chunk_data, indent=2))
            self.files.append(file_path)
        return self.files


@pytest.fixture
def progress_test_corpus(tmp_path: Path) -> ProgressTestCorpus:
    """
    Provide test corpus for progress bar testing.

    Returns:
        ProgressTestCorpus with methods to create file batches
    """
    return ProgressTestCorpus(tmp_path=tmp_path)


@dataclass
class VerbosityLevel:
    """Definition of a verbosity level for testing."""

    name: str
    flag: str
    description: str
    expected_outputs: list[str]
    unexpected_outputs: list[str]


@pytest.fixture
def verbosity_levels() -> list[VerbosityLevel]:
    """
    Provide verbosity level definitions for testing.

    Returns list matching UX-spec Section 4.1:
    - quiet (-q): Exit code only, errors only
    - normal (default): Summary + key metrics
    - verbose (-v): Detailed per-file info
    - debug (-vv): Full trace + timing
    - trace (-vvv): Maximum detail
    """
    return [
        VerbosityLevel(
            name="quiet",
            flag="-q",
            description="Exit code only, errors only",
            expected_outputs=["Error:"],  # Only errors shown
            unexpected_outputs=["Processing", "Summary", "Progress", "%"],
        ),
        VerbosityLevel(
            name="normal",
            flag="",
            description="Summary + key metrics",
            expected_outputs=["files processed", "Quality"],
            unexpected_outputs=["DEBUG:", "TRACE:"],
        ),
        VerbosityLevel(
            name="verbose",
            flag="-v",
            description="Detailed per-file info",
            expected_outputs=["Processing:", "per file"],
            unexpected_outputs=["DEBUG:", "TRACE:"],
        ),
        VerbosityLevel(
            name="debug",
            flag="-vv",
            description="Full trace + timing",
            expected_outputs=["DEBUG:", "timing", "ms"],
            unexpected_outputs=["TRACE:"],
        ),
        VerbosityLevel(
            name="trace",
            flag="-vvv",
            description="Maximum detail",
            expected_outputs=["TRACE:", "DEBUG:"],
            unexpected_outputs=[],
        ),
    ]


@dataclass
class QualityMetricsSample:
    """Sample quality metrics for dashboard testing."""

    total_files: int = 47
    successful_files: int = 44
    failed_files: int = 3

    # Quality distribution
    excellent_count: int = 34  # >90 quality score
    good_count: int = 7  # 70-90 quality score
    needs_review_count: int = 3  # <70 quality score

    # Suggestions based on analysis
    suggestions: list[str] = field(
        default_factory=lambda: [
            "12 files have similar content. Run `data-extract dedupe` to reduce redundancy.",
            "3 files have low readability scores. Consider simplifying content.",
        ]
    )

    # Learning tip
    learning_tip: str = (
        "Quality scores are based on text density, structure, and semantic coherence."
    )


@pytest.fixture
def quality_metrics_sample() -> QualityMetricsSample:
    """
    Provide sample quality metrics for dashboard testing.

    Returns:
        QualityMetricsSample matching UX-spec Quality Dashboard pattern
    """
    return QualityMetricsSample()


@dataclass
class PreflightTestFiles:
    """Files for preflight validation panel testing."""

    tmp_path: Path
    files: list[Path] = field(default_factory=list)
    expected_warnings: list[str] = field(default_factory=list)

    def create_preflight_corpus(self) -> list[Path]:
        """Create corpus that will generate preflight warnings."""
        self.files = []
        self.expected_warnings = []

        # Normal files (no warnings)
        for i in range(10):
            file_path = self.tmp_path / f"normal_{i}.txt"
            file_path.write_text("Normal content " * 100)
            self.files.append(file_path)

        # Large file (should warn about size)
        large_file = self.tmp_path / "large_report.xlsx"
        large_file.write_bytes(b"PK\x03\x04" + b"x" * 50000)  # 50KB fake XLSX
        self.files.append(large_file)
        self.expected_warnings.append("large_report.xlsx")

        # Low OCR confidence expected (PDF)
        ocr_pdf = self.tmp_path / "scanned_doc.pdf"
        ocr_pdf.write_bytes(b"%PDF-1.4\n" + b"\x00" * 1000)  # Likely OCR needed
        self.files.append(ocr_pdf)
        self.expected_warnings.append("scanned_doc.pdf")

        # Empty file (should warn)
        empty_file = self.tmp_path / "empty_notes.txt"
        empty_file.write_text("")
        self.files.append(empty_file)
        self.expected_warnings.append("empty_notes.txt")

        return self.files


@pytest.fixture
def preflight_test_files(tmp_path: Path) -> PreflightTestFiles:
    """
    Provide files for preflight validation panel testing.

    Returns:
        PreflightTestFiles with corpus and expected warnings
    """
    return PreflightTestFiles(tmp_path=tmp_path)


@dataclass
class BatchProcessingFixture:
    """Fixture for batch processing with progress and error handling."""

    tmp_path: Path
    env_controller: EnvVarsController
    good_files: list[Path] = field(default_factory=list)
    error_files: list[Path] = field(default_factory=list)

    def create_mixed_batch(self) -> tuple[list[Path], list[Path]]:
        """Create batch with both good and error-inducing files.

        Returns:
            Tuple of (good_files, error_files)
        """
        self.good_files = []
        self.error_files = []

        # Good files
        for i in range(8):
            file_path = self.tmp_path / f"good_{i}.txt"
            file_path.write_text(f"Good document content {i} " * 50)
            self.good_files.append(file_path)

        # Error-inducing files
        # Corrupted PDF
        corrupted = self.tmp_path / "corrupted.pdf"
        corrupted.write_bytes(b"%PDF-1.4\n" + b"\x00\xff" * 50)
        self.error_files.append(corrupted)

        # Malformed file
        malformed = self.tmp_path / "malformed.xlsx"
        malformed.write_bytes(b"Not a real XLSX")
        self.error_files.append(malformed)

        return self.good_files, self.error_files

    def get_all_files(self) -> list[Path]:
        """Get all files (good + error-inducing)."""
        return self.good_files + self.error_files


@pytest.fixture
def batch_processing_fixture(
    tmp_path: Path,
    env_vars_fixture: EnvVarsController,
) -> BatchProcessingFixture:
    """
    Provide fixture for batch processing with mixed success/error files.

    Returns:
        BatchProcessingFixture for continue-on-error testing
    """
    return BatchProcessingFixture(
        tmp_path=tmp_path,
        env_controller=env_vars_fixture,
    )


@dataclass
class MemoryProfilerFixture:
    """Fixture for memory profiling tests."""

    # Memory limits from tech-spec Section 5.2
    max_memory_mb: int = 50
    max_memory_bytes: int = 50 * 1024 * 1024

    # Test parameters
    file_counts: list[int] = field(default_factory=lambda: [10, 50, 100, 500])

    def assert_memory_under_limit(self, peak_bytes: int) -> None:
        """Assert memory usage is under limit."""
        peak_mb = peak_bytes / (1024 * 1024)
        assert (
            peak_bytes < self.max_memory_bytes
        ), f"Peak memory {peak_mb:.1f}MB exceeds limit of {self.max_memory_mb}MB"


@pytest.fixture
def memory_profiler_fixture() -> MemoryProfilerFixture:
    """
    Provide memory profiler fixture for AC-5.3-6 testing.

    Returns:
        MemoryProfilerFixture with limits and assertion helpers
    """
    return MemoryProfilerFixture()


# ==============================================================================
# Pytest Markers for Story 5-3
# ==============================================================================


def pytest_configure(config):
    """Register custom markers for Story 5-3 tests."""
    config.addinivalue_line(
        "markers",
        "story_5_3: marks tests as Story 5-3 (Real-Time Progress Indicators)",
    )
    config.addinivalue_line(
        "markers",
        "progress: marks tests related to progress bars (AC-5.3-1, AC-5.3-4, AC-5.3-7)",
    )
    config.addinivalue_line(
        "markers",
        "panels: marks tests related to Rich panels (AC-5.3-2, AC-5.3-3)",
    )
    config.addinivalue_line(
        "markers",
        "no_color: marks tests for NO_COLOR support (AC-5.3-5)",
    )
    config.addinivalue_line(
        "markers",
        "performance: marks performance/memory tests (AC-5.3-6)",
    )
    config.addinivalue_line(
        "markers",
        "verbosity: marks verbosity level tests (AC-5.3-8)",
    )
    config.addinivalue_line(
        "markers",
        "continue_on_error: marks continue-on-error tests (AC-5.3-9)",
    )
