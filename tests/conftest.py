"""
Pytest configuration and shared fixtures for data extraction tests.

This module provides reusable fixtures for testing extractors, processors,
and formatters. Fixtures handle common setup and teardown for tests.

Usage:
    Test files automatically have access to these fixtures:

    def test_my_extractor(sample_content_block):
        # sample_content_block is automatically created
        assert sample_content_block.block_type == ContentType.PARAGRAPH
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Generator, Tuple

import pytest

# Import greenfield core models for fixtures
from data_extract.core.models import (
    ContentBlock,
    ContentType,
    Metadata,
    Position,
    ProcessingResult,
)

# Legacy compatibility - map brownfield concepts to greenfield
DocumentMetadata = Metadata  # Alias for backwards compatibility

# TableMetadata replacement - simple dataclass for table structure in ContentBlock metadata


@dataclass
class TableMetadata:
    """Table metadata for ContentBlock (legacy brownfield compatibility)."""

    num_rows: int
    num_columns: int
    has_header: bool
    header_row: Tuple[str, ...]
    cells: Tuple[Tuple[str, ...], ...]


# ExtractionResult replacement - minimal mock for legacy test fixtures
@dataclass
class ExtractionResult:
    """Legacy brownfield ExtractionResult for test fixtures (greenfield uses Document)."""

    content_blocks: Tuple[ContentBlock, ...]
    document_metadata: Metadata
    success: bool
    errors: Tuple[str, ...]
    warnings: Tuple[str, ...]


# ============================================================================
# ContentBlock Fixtures
# ============================================================================


@pytest.fixture
def sample_content_block() -> ContentBlock:
    """
    Create a basic ContentBlock for testing.

    Returns a paragraph-type content block with sample text.

    Returns:
        ContentBlock with type=PARAGRAPH and sample content
    """
    return ContentBlock(
        block_type=ContentType.PARAGRAPH,
        content="This is a sample paragraph for testing.",
        position=Position(page=1, sequence_index=0),
        metadata={"test": True},
        confidence=0.95,
    )


@pytest.fixture
def sample_heading_block() -> ContentBlock:
    """
    Create a heading ContentBlock for testing.

    Returns:
        ContentBlock with type=HEADING
    """
    return ContentBlock(
        block_type=ContentType.HEADING,
        content="Sample Heading",
        position=Position(page=1, sequence_index=0),
        metadata={"level": 1},
        confidence=1.0,
    )


@pytest.fixture
def sample_table_block() -> ContentBlock:
    """
    Create a table ContentBlock for testing.

    Returns:
        ContentBlock with type=TABLE and associated TableMetadata
    """
    table_meta = TableMetadata(
        num_rows=2,
        num_columns=2,
        has_header=True,
        header_row=("Column 1", "Column 2"),
        cells=(("A", "B"), ("C", "D")),
    )

    return ContentBlock(
        block_type=ContentType.TABLE,
        content="[Table: 2x2]",
        position=Position(page=2, sequence_index=5),
        metadata={"table_metadata": table_meta},
    )


@pytest.fixture
def sample_image_block() -> ContentBlock:
    """
    Create an image ContentBlock for testing.

    Returns:
        ContentBlock with type=IMAGE
    """
    return ContentBlock(
        block_type=ContentType.IMAGE,
        content="[Image: sample.png]",
        position=Position(page=3, sequence_index=10),
        metadata={"image_format": "PNG", "alt_text": "Sample image"},
    )


@pytest.fixture
def sample_content_blocks() -> list[ContentBlock]:
    """
    Create a list of mixed ContentBlocks for testing.

    Returns:
        List containing heading, paragraph, table, and image blocks
    """
    return [
        ContentBlock(
            block_type=ContentType.HEADING,
            content="Introduction",
            position=Position(page=1, sequence_index=0),
        ),
        ContentBlock(
            block_type=ContentType.PARAGRAPH,
            content="This is the first paragraph.",
            position=Position(page=1, sequence_index=1),
        ),
        ContentBlock(
            block_type=ContentType.PARAGRAPH,
            content="This is the second paragraph.",
            position=Position(page=1, sequence_index=2),
        ),
        ContentBlock(
            block_type=ContentType.TABLE,
            content="[Table]",
            position=Position(page=2, sequence_index=3),
        ),
        ContentBlock(
            block_type=ContentType.IMAGE,
            content="[Image]",
            position=Position(page=2, sequence_index=4),
        ),
    ]


# ============================================================================
# ExtractionResult Fixtures
# ============================================================================


@pytest.fixture
def sample_document_metadata(tmp_path: Path) -> DocumentMetadata:
    """
    Create sample DocumentMetadata for testing.

    Args:
        tmp_path: pytest built-in fixture providing temporary directory

    Returns:
        DocumentMetadata with sample values
    """
    test_file = tmp_path / "test_document.txt"
    test_file.write_text("Sample content")

    return DocumentMetadata(
        source_file=test_file,
        file_format="txt",
        file_size_bytes=test_file.stat().st_size,
        title="Test Document",
        author="Test Author",
        page_count=1,
        word_count=50,
    )


@pytest.fixture
def sample_extraction_result(sample_content_blocks, sample_document_metadata) -> ExtractionResult:
    """
    Create a successful ExtractionResult for testing.

    Args:
        sample_content_blocks: List of content blocks
        sample_document_metadata: Document metadata

    Returns:
        ExtractionResult with success=True and sample data
    """
    return ExtractionResult(
        content_blocks=tuple(sample_content_blocks),
        document_metadata=sample_document_metadata,
        success=True,
        errors=(),
        warnings=(),
    )


@pytest.fixture
def failed_extraction_result(sample_document_metadata) -> ExtractionResult:
    """
    Create a failed ExtractionResult for testing error handling.

    Returns:
        ExtractionResult with success=False and error messages
    """
    return ExtractionResult(
        content_blocks=(),
        document_metadata=sample_document_metadata,
        success=False,
        errors=("File is corrupted", "Could not parse content"),
        warnings=("Some metadata missing",),
    )


# ============================================================================
# ProcessingResult Fixtures
# ============================================================================


@pytest.fixture
def sample_processing_result(
    sample_content_blocks, sample_document_metadata, tmp_path: Path
) -> ProcessingResult:
    """
    Create a successful ProcessingResult for testing.

    Returns:
        ProcessingResult with enriched content blocks (greenfield format)
    """
    from data_extract.core.models import DocumentType

    # Create enriched blocks (add processing metadata)
    enriched_blocks = []
    for block in sample_content_blocks:
        enriched_block = ContentBlock(
            block_type=block.block_type,
            content=block.content,
            position=block.position,
            metadata={
                **block.metadata,
                "processed": True,
                "word_count": len(block.content.split()),
            },
        )
        enriched_blocks.append(enriched_block)

    # Greenfield ProcessingResult requires: file_path, document_type, content_blocks, entities, metadata
    return ProcessingResult(
        file_path=sample_document_metadata.source_file,
        document_type=DocumentType.REPORT,
        content_blocks=enriched_blocks,
        entities=[],
        metadata=sample_document_metadata,
    )


# ============================================================================
# Temporary File Fixtures
# ============================================================================


@pytest.fixture
def temp_test_file(tmp_path: Path) -> Generator[Path, None, None]:
    """
    Create a temporary text file for testing.

    This fixture uses pytest's tmp_path fixture and cleans up automatically.

    Args:
        tmp_path: pytest built-in fixture providing temporary directory

    Yields:
        Path to temporary test file

    Usage:
        def test_extractor(temp_test_file):
            result = extractor.extract(temp_test_file)
            assert result.success
    """
    test_file = tmp_path / "test_document.txt"
    test_file.write_text(
        "Sample Document\n\n"
        "This is a test document with multiple paragraphs.\n\n"
        "It contains simple text for extraction testing."
    )

    yield test_file

    # Cleanup happens automatically via tmp_path


@pytest.fixture
def empty_test_file(tmp_path: Path) -> Path:
    """
    Create an empty file for testing edge cases.

    Args:
        tmp_path: pytest built-in fixture

    Returns:
        Path to empty file
    """
    empty_file = tmp_path / "empty.txt"
    empty_file.touch()
    return empty_file


@pytest.fixture
def large_test_file(tmp_path: Path) -> Path:
    """
    Create a large text file for performance testing.

    Args:
        tmp_path: pytest built-in fixture

    Returns:
        Path to large test file (approximately 1MB)
    """
    large_file = tmp_path / "large.txt"
    content = "This is a line of text.\n" * 50000  # ~1MB
    large_file.write_text(content)
    return large_file


@pytest.fixture
def fixture_dir() -> Path:
    """
    Get the path to the fixtures directory.

    Returns:
        Path to tests/fixtures/
    """
    return Path(__file__).parent / "fixtures"


# ============================================================================
# Validation Helper Fixtures
# ============================================================================


@pytest.fixture
def validate_extraction_result():
    """
    Provide a validation helper for ExtractionResult objects.

    Returns:
        Callable that validates ExtractionResult structure

    Usage:
        def test_extractor(validate_extraction_result):
            result = extractor.extract(file_path)
            validate_extraction_result(result)
    """

    def _validate(result: ExtractionResult) -> None:
        """Validate ExtractionResult has required structure."""
        assert isinstance(result, ExtractionResult)
        assert isinstance(result.success, bool)
        assert isinstance(result.content_blocks, tuple)
        assert isinstance(result.errors, tuple)
        assert isinstance(result.warnings, tuple)

        # If successful, should have content
        if result.success:
            assert len(result.content_blocks) > 0 or result.warnings

        # Validate each content block
        for block in result.content_blocks:
            assert isinstance(block, ContentBlock)
            assert isinstance(block.block_type, ContentType)
            assert isinstance(block.content, str)

    return _validate


@pytest.fixture
def validate_processing_result():
    """
    Provide a validation helper for ProcessingResult objects.

    Returns:
        Callable that validates ProcessingResult structure (greenfield format)
    """
    from data_extract.core.models import DocumentType

    def _validate(result: ProcessingResult) -> None:
        """Validate ProcessingResult has required structure (greenfield)."""
        assert isinstance(result, ProcessingResult)
        assert isinstance(result.content_blocks, list)
        assert isinstance(result.document_type, DocumentType)
        assert hasattr(result, "metadata")
        assert hasattr(result, "file_path")

    return _validate


# ============================================================================
# Pytest Configuration
# ============================================================================


def pytest_configure(config):
    """
    Configure pytest with custom markers.

    This allows tests to be marked for selective execution:
    - pytest -m unit       # Run only unit tests
    - pytest -m integration # Run only integration tests
    - pytest -m slow       # Run slow tests
    """
    config.addinivalue_line("markers", "unit: Unit tests (fast)")
    config.addinivalue_line("markers", "integration: Integration tests (slower)")
    config.addinivalue_line("markers", "slow: Slow tests (may take >1 second)")
    config.addinivalue_line("markers", "extraction: Extractor tests")
    config.addinivalue_line("markers", "processing: Processor tests")
    config.addinivalue_line("markers", "formatting: Formatter tests")
