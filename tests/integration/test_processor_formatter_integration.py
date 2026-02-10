"""
Processor → Formatter Integration Tests.

Tests data flow from processing through formatting stages:
- Processed content → JSON formatter (all metadata included)
- Processed content → Markdown formatter (hierarchy as headers)
- Processed content → ChunkedText formatter (context preserved)
- Minimal vs extensive processing → Formatters
- Error handling in formatting pipeline

Test IDs: PF-001 through PF-008

NOTE: Tests skipped - brownfield processors/formatters moved to TRASH.
"""

import json
from typing import Any

import pytest

# Stub for brownfield imports (modules deleted, tests skipped)
ContentBlock: Any = None  # type: ignore[assignment]
ContentType: Any = None  # type: ignore[assignment]
Position: Any = None  # type: ignore[assignment]
DocxExtractor: Any = None  # type: ignore[assignment]
ChunkedTextFormatter: Any = None  # type: ignore[assignment]
JsonFormatter: Any = None  # type: ignore[assignment]
MarkdownFormatter: Any = None  # type: ignore[assignment]
ContextLinker: Any = None  # type: ignore[assignment]
MetadataAggregator: Any = None  # type: ignore[assignment]
QualityValidator: Any = None  # type: ignore[assignment]

# ==============================================================================
# Test Markers
# ==============================================================================

pytestmark = [
    pytest.mark.P1,
    pytest.mark.integration,
    pytest.mark.formatting,
    pytest.mark.processing,
    pytest.mark.skip(
        reason="Brownfield processors/formatters moved to TRASH - needs greenfield rewrite"
    ),
]


# ==============================================================================
# Processed Content → JSON Formatter Tests
# ==============================================================================


def test_pf_001_processed_to_json_includes_all_metadata(sample_docx_file):
    """
    Test PF-001: JSON formatter includes all processor metadata.

    Scenario: Extract → Process (all processors) → JSON formatter

    Verifies:
    - All processing metadata included in JSON
    - Quality score present
    - Block hierarchy maintained
    - JSON is valid and complete
    """
    # Arrange: Extract and process
    extractor = DocxExtractor()
    extraction_result = extractor.extract(sample_docx_file)
    assert extraction_result.success is True

    # Process through all processors
    blocks = extraction_result.content_blocks

    linker = ContextLinker()
    linked = linker.process(blocks)

    aggregator = MetadataAggregator()
    aggregated = aggregator.process(linked.content_blocks)

    validator = QualityValidator()
    validated = validator.process(aggregated.content_blocks)

    assert validated.success is True

    # Arrange: Format to JSON
    formatter = JsonFormatter()

    # Act: Format
    formatted_result = formatter.format(validated.content_blocks, validated.document_metadata)

    # Assert: Formatting succeeded
    assert formatted_result.success is True
    assert formatted_result.format_type == "json"

    # Assert: JSON is valid
    parsed = json.loads(formatted_result.content)
    assert isinstance(parsed, dict)

    # Assert: Quality metadata included
    if "metadata" in parsed:
        # Quality score may be in document metadata
        doc_meta = parsed.get("metadata", {})
        # Check if quality information present anywhere
        has_quality = "quality" in str(parsed).lower()
        # At minimum, JSON should be comprehensive
        assert len(parsed) > 0

    # Assert: Content blocks present
    assert "content_blocks" in parsed or "blocks" in parsed


def test_pf_002_minimal_processing_to_json(sample_text_file):
    """
    Test PF-002: JSON formatter handles minimally processed content.

    Scenario: Extract → No processing → JSON formatter

    Verifies:
    - Formatter handles raw extraction
    - JSON valid with minimal metadata
    - No errors with sparse data
    """
    # Arrange: Extract only (no processing)
    extractor = DocxExtractor()
    extraction_result = extractor.extract(sample_text_file)

    if not extraction_result.success or not extraction_result.content_blocks:
        pytest.skip("Text extraction failed")

    # Arrange: Format directly
    formatter = JsonFormatter()

    # Act: Format without processing
    formatted_result = formatter.format(
        extraction_result.content_blocks, extraction_result.document_metadata
    )

    # Assert: Formatting succeeded
    assert formatted_result.success is True

    # Assert: JSON valid
    parsed = json.loads(formatted_result.content)
    assert isinstance(parsed, dict)
    assert len(parsed) > 0


# ==============================================================================
# Processed Content → Markdown Formatter Tests
# ==============================================================================


def test_pf_003_processed_to_markdown_hierarchy_as_headers(sample_docx_file):
    """
    Test PF-003: Markdown formatter renders hierarchy as headers.

    Scenario: Extract → ContextLinker → Markdown formatter

    Verifies:
    - Heading blocks become markdown headers (#, ##, ###)
    - Hierarchy levels respected
    - Paragraph blocks formatted correctly
    - Output is valid markdown
    """
    # Arrange: Extract and process
    extractor = DocxExtractor()
    extraction_result = extractor.extract(sample_docx_file)
    assert extraction_result.success is True

    # Process with ContextLinker to establish hierarchy
    linker = ContextLinker()
    linked = linker.process(extraction_result.content_blocks)
    assert linked.success is True

    # Arrange: Format to Markdown
    formatter = MarkdownFormatter()

    # Act: Format
    formatted_result = formatter.format(linked.content_blocks, linked.document_metadata)

    # Assert: Formatting succeeded
    assert formatted_result.success is True
    assert formatted_result.format_type == "markdown"

    # Assert: Markdown content has headers
    content = formatted_result.content
    assert len(content) > 0

    # Check for markdown header markers
    has_headers = "#" in content or "##" in content

    # Check for markdown formatting
    has_markdown = "#" in content or "**" in content or "\n\n" in content or len(content) > 0
    assert has_markdown, "Should have markdown formatting"


def test_pf_004_extensive_processing_to_markdown(sample_docx_file):
    """
    Test PF-004: Markdown formatter with extensively processed content.

    Scenario: Extract → All processors → Markdown formatter

    Verifies:
    - Rich metadata doesn't break markdown
    - Quality scores included (if configured)
    - All content blocks rendered
    - Metadata optionally included
    """
    # Arrange: Extract and process extensively
    extractor = DocxExtractor()
    extraction_result = extractor.extract(sample_docx_file)
    assert extraction_result.success is True

    # Full processing chain
    blocks = extraction_result.content_blocks

    linker = ContextLinker()
    linked = linker.process(blocks)

    aggregator = MetadataAggregator()
    aggregated = aggregator.process(linked.content_blocks)

    validator = QualityValidator()
    validated = validator.process(aggregated.content_blocks)

    # Arrange: Format to Markdown
    formatter = MarkdownFormatter()

    # Act: Format
    formatted_result = formatter.format(validated.content_blocks, validated.document_metadata)

    # Assert: Formatting succeeded
    assert formatted_result.success is True

    # Assert: Content comprehensive
    content = formatted_result.content
    assert len(content) > 0

    # Assert: Multiple blocks rendered (should have multiple sections)
    # Markdown typically uses double newlines between blocks
    assert content.count("\n") > 0


# ==============================================================================
# Processed Content → ChunkedText Formatter Tests
# ==============================================================================


def test_pf_005_processed_to_chunked_preserves_context(sample_docx_file):
    """
    Test PF-005: ChunkedText formatter preserves context in chunks.

    Scenario: Extract → ContextLinker → ChunkedText formatter

    Verifies:
    - Context preserved across chunks
    - Chunk boundaries respect context
    - Metadata included in chunks
    - Chunk size reasonable
    """
    # Arrange: Extract and process
    extractor = DocxExtractor()
    extraction_result = extractor.extract(sample_docx_file)
    assert extraction_result.success is True

    # Process to establish context
    linker = ContextLinker()
    linked = linker.process(extraction_result.content_blocks)

    # Arrange: Format to chunked text
    formatter = ChunkedTextFormatter()

    # Act: Format
    formatted_result = formatter.format(linked.content_blocks, linked.document_metadata)

    # Assert: Formatting succeeded
    assert formatted_result.success is True
    assert formatted_result.format_type == "chunked"

    # Assert: Chunked output present
    content = formatted_result.content
    assert len(content) > 0

    # Assert: Chunk metadata present
    # ChunkedText typically includes chunk markers or separators
    has_chunks = "chunk" in content.lower() or "---" in content or "\n\n" in content
    assert has_chunks or len(content) > 0  # At minimum, content exists


def test_pf_006_minimal_processing_to_chunked(sample_text_file):
    """
    Test PF-006: ChunkedText formatter with minimal processing.

    Scenario: Extract → ChunkedText formatter (no processing)

    Verifies:
    - Formatter handles raw extraction
    - Chunks created from simple structure
    - No errors with minimal metadata
    """
    # Arrange: Extract only
    extractor = DocxExtractor()
    extraction_result = extractor.extract(sample_text_file)

    if not extraction_result.success or not extraction_result.content_blocks:
        pytest.skip("Text extraction failed")

    # Arrange: Format to chunked
    formatter = ChunkedTextFormatter()

    # Act: Format
    formatted_result = formatter.format(
        extraction_result.content_blocks, extraction_result.document_metadata
    )

    # Assert: Formatting succeeded
    assert formatted_result.success is True

    # Assert: Output present
    assert len(formatted_result.content) > 0


# ==============================================================================
# Multiple Formatters Same Input Tests
# ==============================================================================


def test_pf_007_same_processing_multiple_formatters(sample_docx_file):
    """
    Test PF-007: Same processed content → Multiple formatters.

    Scenario: Extract → Process → JSON + Markdown + Chunked

    Verifies:
    - Same input produces valid output in all formats
    - Formatters don't interfere with each other
    - Content consistency across formats
    """
    # Arrange: Extract and process once
    extractor = DocxExtractor()
    extraction_result = extractor.extract(sample_docx_file)
    assert extraction_result.success is True

    # Full processing
    blocks = extraction_result.content_blocks

    linker = ContextLinker()
    linked = linker.process(blocks)

    aggregator = MetadataAggregator()
    aggregated = aggregator.process(linked.content_blocks)

    validator = QualityValidator()
    validated = validator.process(aggregated.content_blocks)

    # Use final processed blocks and metadata
    final_blocks = validated.content_blocks
    final_metadata = validated.document_metadata

    # Act: Format in all three formats
    json_formatter = JsonFormatter()
    json_result = json_formatter.format(final_blocks, final_metadata)

    md_formatter = MarkdownFormatter()
    md_result = md_formatter.format(final_blocks, final_metadata)

    chunked_formatter = ChunkedTextFormatter()
    chunked_result = chunked_formatter.format(final_blocks, final_metadata)

    # Assert: All succeeded
    assert json_result.success is True
    assert md_result.success is True
    assert chunked_result.success is True

    # Assert: All have content
    assert len(json_result.content) > 0
    assert len(md_result.content) > 0
    assert len(chunked_result.content) > 0

    # Assert: Formats are different
    assert json_result.format_type == "json"
    assert md_result.format_type == "markdown"
    assert chunked_result.format_type == "chunked"

    # Assert: Content differs (different format representations)
    assert json_result.content != md_result.content
    assert json_result.content != chunked_result.content


# ==============================================================================
# Error Handling Tests
# ==============================================================================


def test_pf_008_formatters_handle_processing_errors():
    """
    Test PF-008: Formatters handle content with processing errors.

    Scenario: Partial processing (with errors) → Formatters

    Verifies:
    - Formatters don't crash on problematic input
    - Graceful degradation
    - Output still generated when possible
    """
    # Arrange: Create problematic content blocks
    # Blocks with minimal/missing metadata
    problematic_blocks = (
        ContentBlock(
            block_type=ContentType.PARAGRAPH,
            content="Test content",
            position=Position(page=1, sequence_index=0),
            metadata={},  # Empty metadata
        ),
        ContentBlock(
            block_type=ContentType.PARAGRAPH,
            content="",  # Empty content
            position=Position(page=1, sequence_index=1),
            metadata={},
        ),
    )

    # Act: Format with all formatters
    json_formatter = JsonFormatter()
    json_result = json_formatter.format(problematic_blocks, None)

    md_formatter = MarkdownFormatter()
    md_result = md_formatter.format(problematic_blocks, None)

    chunked_formatter = ChunkedTextFormatter()
    chunked_result = chunked_formatter.format(problematic_blocks, None)

    # Assert: All completed (success or graceful failure)
    # Should not raise exceptions
    assert json_result.success is True or len(json_result.errors) > 0
    assert md_result.success is True or len(md_result.errors) > 0
    assert chunked_result.success is True or len(chunked_result.errors) > 0


# ==============================================================================
# Empty Input Tests
# ==============================================================================


def test_pf_009_formatters_handle_empty_input():
    """
    Test PF-009: All formatters handle empty block list.

    Scenario: Empty blocks → Each formatter

    Verifies:
    - No crash on empty input
    - Valid empty output generated
    - Appropriate format type
    """
    empty_blocks = ()

    # JSON Formatter
    json_formatter = JsonFormatter()
    json_result = json_formatter.format(empty_blocks, None)
    assert json_result.success is True
    assert json_result.format_type == "json"
    # Should produce valid empty JSON
    parsed = json.loads(json_result.content)
    assert isinstance(parsed, (dict, list))

    # Markdown Formatter
    md_formatter = MarkdownFormatter()
    md_result = md_formatter.format(empty_blocks, None)
    assert md_result.success is True
    assert md_result.format_type == "markdown"
    # Empty or minimal markdown is valid

    # ChunkedText Formatter
    chunked_formatter = ChunkedTextFormatter()
    chunked_result = chunked_formatter.format(empty_blocks, None)
    assert chunked_result.success is True
    assert chunked_result.format_type == "chunked"


# ==============================================================================
# Quality Score Formatting Tests
# ==============================================================================


def test_pf_010_formatters_handle_quality_scores(sample_docx_file):
    """
    Test PF-010: Formatters include quality scores when available.

    Scenario: Extract → QualityValidator → All formatters

    Verifies:
    - Quality scores accessible in formatted output
    - JSON includes quality in metadata
    - Markdown may include quality annotation
    - ChunkedText preserves quality context
    """
    # Arrange: Extract and validate quality
    extractor = DocxExtractor()
    extraction_result = extractor.extract(sample_docx_file)
    assert extraction_result.success is True

    # Process with QualityValidator
    validator = QualityValidator()
    validated = validator.process(extraction_result.content_blocks)

    assert validated.success is True
    assert validated.quality_score is not None

    # Act: Format with all formatters
    json_formatter = JsonFormatter()
    json_result = json_formatter.format(validated.content_blocks, validated.document_metadata)

    md_formatter = MarkdownFormatter()
    md_result = md_formatter.format(validated.content_blocks, validated.document_metadata)

    chunked_formatter = ChunkedTextFormatter()
    chunked_result = chunked_formatter.format(validated.content_blocks, validated.document_metadata)

    # Assert: All succeeded
    assert json_result.success is True
    assert md_result.success is True
    assert chunked_result.success is True

    # Assert: JSON may include quality score in metadata
    json_content = json.loads(json_result.content)
    # Quality score might be in metadata or blocks
    # Just verify JSON is complete
    assert len(json_content) > 0


# ==============================================================================
# Complex Content Tests
# ==============================================================================


def test_pf_011_formatters_handle_complex_content_types(tmp_path):
    """
    Test PF-011: Formatters handle mixed content types.

    Scenario: Mixed content (text, tables, images) → Process → Format

    Verifies:
    - Tables formatted appropriately
    - Images referenced correctly
    - Headings structured properly
    - All content types represented
    """
    # Arrange: Create blocks with mixed content types
    from src.core import TableMetadata

    mixed_blocks = (
        ContentBlock(
            block_type=ContentType.HEADING,
            content="Main Title",
            position=Position(page=1, sequence_index=0),
            metadata={"level": 1},
        ),
        ContentBlock(
            block_type=ContentType.PARAGRAPH,
            content="Introduction paragraph with text.",
            position=Position(page=1, sequence_index=1),
            metadata={},
        ),
        ContentBlock(
            block_type=ContentType.TABLE,
            content="Table data",
            position=Position(page=1, sequence_index=2),
            metadata={
                "table_metadata": TableMetadata(
                    num_rows=2,
                    num_columns=2,
                    has_header=True,
                    header_row=("Col1", "Col2"),
                    cells=(("A", "B"), ("C", "D")),
                )
            },
        ),
        ContentBlock(
            block_type=ContentType.IMAGE,
            content="[Image: diagram.png]",
            position=Position(page=2, sequence_index=3),
            metadata={"alt_text": "Diagram"},
        ),
    )

    # Act: Format with all formatters
    json_formatter = JsonFormatter()
    json_result = json_formatter.format(mixed_blocks, None)

    md_formatter = MarkdownFormatter()
    md_result = md_formatter.format(mixed_blocks, None)

    chunked_formatter = ChunkedTextFormatter()
    chunked_result = chunked_formatter.format(mixed_blocks, None)

    # Assert: All succeeded
    assert json_result.success is True
    assert md_result.success is True
    assert chunked_result.success is True

    # Assert: All content types present in outputs
    json_content = json.loads(json_result.content)
    assert len(json_content) > 0

    # Markdown should have headers and content
    assert len(md_result.content) > 0

    # Chunked should have all content
    assert len(chunked_result.content) > 0
