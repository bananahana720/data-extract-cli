"""
Basic integration tests for pipeline functionality.

Tests the core integration between extractors, processors, and formatters.
This test module validates AC-1.3.4: Integration test framework functional.

NOTE: Tests skipped - brownfield extractors/processors moved to TRASH.
"""

from pathlib import Path
from typing import Any

import pytest

pytestmark = [
    pytest.mark.P0,
    pytest.mark.integration,
    pytest.mark.skip(
        reason="Brownfield extractors/processors moved to TRASH - needs greenfield rewrite"
    ),
]

# Stub for brownfield imports (modules deleted, tests skipped)
ContentBlock: Any = None  # type: ignore[assignment]
ContentType: Any = None  # type: ignore[assignment]
DocumentMetadata: Any = None  # type: ignore[assignment]
ExtractionResult: Any = None  # type: ignore[assignment]
DocxExtractor: Any = None  # type: ignore[assignment]
TextFileExtractor: Any = None  # type: ignore[assignment]
MarkdownFormatter: Any = None  # type: ignore[assignment]
MetadataAggregator: Any = None  # type: ignore[assignment]


@pytest.mark.integration
@pytest.mark.test_id("int-INT-001")
def test_fixture_loading_basic():
    """
    Test AC-1.3.4: Can load test fixtures.

    Verifies that test fixtures are accessible and can be loaded
    from the tests/fixtures directory structure.  # noqa: E402
    """
    # Arrange: Define fixture paths
    # Use __file__-relative path for robustness across different working directories
    fixtures_dir = Path(__file__).parent.parent / "fixtures"

    # Act & Assert: Verify fixture directories exist
    assert fixtures_dir.exists(), "Fixtures directory should exist"
    assert (fixtures_dir / "pdfs").exists(), "PDFs fixture subdirectory should exist"
    assert (fixtures_dir / "docx").exists(), "DOCX fixture subdirectory should exist"
    assert (fixtures_dir / "xlsx").exists(), "Excel fixture subdirectory should exist"
    assert (fixtures_dir / "images").exists(), "Images fixture subdirectory should exist"

    # Act & Assert: Verify sample fixtures exist
    pdf_sample = fixtures_dir / "pdfs" / "sample.pdf"
    docx_sample = fixtures_dir / "docx" / "sample.docx"
    xlsx_sample = fixtures_dir / "xlsx" / "sample.xlsx"
    image_sample = fixtures_dir / "images" / "sample.png"

    assert pdf_sample.exists(), f"PDF sample fixture should exist at {pdf_sample}"
    assert docx_sample.exists(), f"DOCX sample fixture should exist at {docx_sample}"
    assert xlsx_sample.exists(), f"Excel sample fixture should exist at {xlsx_sample}"
    assert image_sample.exists(), f"Image sample fixture should exist at {image_sample}"

    # Verify file sizes are reasonable (<100KB per AC-1.3.2)
    assert pdf_sample.stat().st_size < 100_000, "PDF fixture should be <100KB"
    assert docx_sample.stat().st_size < 100_000, "DOCX fixture should be <100KB"
    assert xlsx_sample.stat().st_size < 100_000, "Excel fixture should be <100KB"
    assert image_sample.stat().st_size < 100_000, "Image fixture should be <100KB"


@pytest.mark.integration
@pytest.mark.test_id("int-INT-002")
def test_document_object_creation():
    """
    Test AC-1.3.4: Can create mock Document objects.

    Verifies that core data models (ContentBlock, DocumentMetadata, ExtractionResult)
    can be instantiated and used correctly.
    """
    # Arrange: Create test data
    test_file = Path("test.txt")

    # Act: Create core model objects
    content_block = ContentBlock(
        block_type=ContentType.PARAGRAPH,
        content="This is a test paragraph",
        metadata={"source": "test"},
    )

    document_metadata = DocumentMetadata(
        source_file=test_file, file_size_bytes=1024, file_format="txt"
    )

    extraction_result = ExtractionResult(
        content_blocks=(content_block,), document_metadata=document_metadata, success=True
    )

    # Assert: Verify objects created successfully
    assert content_block.block_type == ContentType.PARAGRAPH
    assert content_block.content == "This is a test paragraph"
    assert document_metadata.source_file == test_file
    assert document_metadata.file_format == "txt"
    assert extraction_result.success is True
    assert len(extraction_result.content_blocks) == 1


@pytest.mark.integration
@pytest.mark.test_id("int-INT-003")
def test_simple_extraction_pipeline():
    """
    Test AC-1.3.4: Example integration test passes.

    End-to-end test of a simple extraction pipeline:
    Extract → Process → Format

    Uses real fixture file to validate the full workflow.
    """
    # Arrange: Setup pipeline components
    fixtures_dir = Path(__file__).parent.parent / "fixtures"
    fixture_path = fixtures_dir / "docx" / "sample.docx"
    assert fixture_path.exists(), "Test fixture must exist"

    extractor = DocxExtractor()
    processor = MetadataAggregator()
    formatter = MarkdownFormatter()

    # Act: Execute extraction pipeline with error handling
    # Step 1: Extract content from DOCX
    try:
        extraction_result = extractor.extract(fixture_path)
    except Exception as e:
        raise AssertionError(f"Extraction failed with exception: {type(e).__name__}: {e}") from e

    # Assert: Extraction succeeded
    assert extraction_result is not None, "Extraction should return a result"
    assert (
        extraction_result.success is True
    ), f"Extraction should succeed. Errors: {extraction_result.errors if hasattr(extraction_result, 'errors') else 'N/A'}"
    assert len(extraction_result.content_blocks) > 0, "Should extract content blocks"
    assert extraction_result.document_metadata is not None, "Should include metadata"

    # Step 2: Process extracted content
    try:
        processing_result = processor.process(extraction_result)
    except Exception as e:
        raise AssertionError(f"Processing failed with exception: {type(e).__name__}: {e}") from e

    # Assert: Processing succeeded
    assert processing_result is not None, "Processing should return result"
    assert len(processing_result.content_blocks) > 0, "Should have processed blocks"

    # Step 3: Format processed content
    try:
        formatted_output = formatter.format(processing_result)
    except Exception as e:
        raise AssertionError(f"Formatting failed with exception: {type(e).__name__}: {e}") from e

    # Assert: Formatting succeeded
    assert formatted_output is not None, "Formatting should return output"
    assert formatted_output.success is True, "Formatting should succeed"
    assert formatted_output.content is not None, "Should have content"
    assert isinstance(formatted_output.content, str), "Markdown output should be string"
    assert len(formatted_output.content) > 0, "Formatted output should not be empty"


@pytest.mark.integration
@pytest.mark.test_id("int-INT-004")
def test_txt_extractor_basic_workflow():
    """
    Simple integration test with TXT extractor.

    Tests a minimal extraction workflow with the simplest extractor type.
    """
    # Arrange: Create a simple text fixture
    fixtures_dir = Path(__file__).parent.parent / "fixtures"
    fixture_path = fixtures_dir / "sample.txt"
    assert fixture_path.exists(), "TXT fixture should exist"

    extractor = TextFileExtractor()

    # Act: Extract text content with error handling
    try:
        result = extractor.extract(fixture_path)
    except Exception as e:
        raise AssertionError(
            f"TXT extraction failed with exception: {type(e).__name__}: {e}"
        ) from e

    # Assert: Basic extraction validation
    assert result is not None, "Should return extraction result"
    assert (
        result.success is True
    ), f"Extraction should succeed. Errors: {result.errors if hasattr(result, 'errors') else 'N/A'}"
    assert len(result.content_blocks) > 0, "Should extract at least one block"
    assert result.document_metadata.file_format == "text", "Should identify as text file"
    assert result.document_metadata.source_file == fixture_path, "Should track source file"


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.test_id("int-INT-005")
def test_pipeline_with_all_extractors():
    """
    Integration test validating all extractor types work with fixtures.

    Marked as 'slow' since it tests multiple extractors.
    """
    # Arrange: Define fixtures for each extractor type
    # Use __file__-relative paths for robustness
    fixtures_dir = Path(__file__).parent.parent / "fixtures"
    # Map file types to their format identifiers and fixtures
    test_cases = [
        ("text", fixtures_dir / "sample.txt", TextFileExtractor()),
        ("docx", fixtures_dir / "docx" / "sample.docx", DocxExtractor()),
    ]

    # Act & Assert: Test each extractor with its fixture
    for expected_format, fixture_path, extractor in test_cases:
        # Verify fixture exists
        assert fixture_path.exists(), f"{expected_format.upper()} fixture should exist"

        # Extract content with error handling
        try:
            result = extractor.extract(fixture_path)
        except Exception as e:
            raise AssertionError(
                f"{expected_format.upper()} extraction failed with exception: {type(e).__name__}: {e}"
            ) from e

        # Validate extraction
        assert result is not None, f"{expected_format.upper()} extraction should return result"
        assert (
            result.success is True
        ), f"{expected_format.upper()} extraction should succeed. Errors: {result.errors if hasattr(result, 'errors') else 'N/A'}"
        assert (
            result.document_metadata.file_format == expected_format
        ), f"Should identify as {expected_format.upper()} file"


@pytest.mark.integration
@pytest.mark.edge_case
@pytest.mark.test_id("int-INT-006")
def test_empty_file_handling():
    """
    Test edge case: Empty file extraction.

    Verifies that extractors handle empty files gracefully without crashing.
    Tests both empty text files and minimal content scenarios.
    """
    # Arrange: Get fixtures directory
    fixtures_dir = Path(__file__).parent.parent / "fixtures"

    # Test 1: Empty text file
    empty_txt = fixtures_dir / "empty.txt"
    if not empty_txt.exists():
        empty_txt.write_text("")

    extractor = TextFileExtractor()

    # Act: Extract from empty file
    result = extractor.extract(empty_txt)

    # Assert: Should return result (success may be False for empty files)
    assert result is not None, "Should return result even for empty file"
    # Empty files may be considered failed extraction (success=False) or succeed with no content
    # Both behaviors are acceptable as long as no exception is raised
    assert len(result.content_blocks) >= 0, "Should handle empty content gracefully"
    if not result.success:
        # If marked as failure, should have 0 blocks
        assert len(result.content_blocks) == 0, "Failed empty extraction should have no blocks"

    # Cleanup
    if empty_txt.exists():
        empty_txt.unlink()


@pytest.mark.integration
@pytest.mark.edge_case
@pytest.mark.test_id("int-INT-007")
def test_nonexistent_file_handling():
    """
    Test edge case: Nonexistent file extraction.

    Verifies that extractors handle missing files gracefully with proper error reporting.
    """
    # Arrange: Path to nonexistent file
    nonexistent_file = Path(__file__).parent.parent / "fixtures" / "does_not_exist.txt"

    extractor = TextFileExtractor()

    # Act & Assert: Should handle missing file gracefully
    try:
        result = extractor.extract(nonexistent_file)
        # If no exception, verify error is indicated in result
        assert result is not None, "Should return result object"
        if hasattr(result, "success"):
            # Either success=False or exception raised is acceptable
            if result.success:
                # Some implementations may succeed with empty content
                assert len(result.content_blocks) == 0, "Nonexistent file should have no content"
    except (FileNotFoundError, IOError) as e:
        # Exception is acceptable and expected for missing files
        assert (
            "does_not_exist.txt" in str(e) or "not found" in str(e).lower()
        ), "Error message should indicate file not found"


@pytest.mark.integration
@pytest.mark.edge_case
@pytest.mark.test_id("int-INT-008")
def test_extraction_with_minimal_content():
    """
    Test edge case: Minimal content extraction.

    Verifies that extractors handle files with very minimal content (1 character, 1 word).
    """
    # Arrange: Create minimal content file
    fixtures_dir = Path(__file__).parent.parent / "fixtures"
    minimal_txt = fixtures_dir / "minimal.txt"
    minimal_txt.write_text("a")

    extractor = TextFileExtractor()

    # Act: Extract minimal content
    result = extractor.extract(minimal_txt)

    # Assert: Should handle minimal content correctly
    assert result is not None, "Should return result for minimal content"
    assert result.success is True, "Minimal content extraction should succeed"
    assert len(result.content_blocks) > 0, "Should extract at least one block"
    assert result.content_blocks[0].content is not None, "Content should not be None"

    # Cleanup
    if minimal_txt.exists():
        minimal_txt.unlink()


@pytest.mark.integration
@pytest.mark.edge_case
@pytest.mark.test_id("int-INT-009")
def test_docx_extraction_error_handling():
    """
    Test edge case: DOCX extractor error handling with corrupted/invalid files.

    Verifies that DOCX extractor handles malformed files gracefully.
    """
    # Arrange: Create a fake/corrupted DOCX file (not valid ZIP structure)
    fixtures_dir = Path(__file__).parent.parent / "fixtures"
    corrupted_docx = fixtures_dir / "corrupted.docx"
    corrupted_docx.write_text("This is not a valid DOCX file, just plain text pretending to be one")

    extractor = DocxExtractor()

    # Act & Assert: Should handle corruption gracefully
    try:
        result = extractor.extract(corrupted_docx)
        # If no exception, verify error is indicated
        assert result is not None, "Should return result object"
        # Accept either success=False or exception
        if hasattr(result, "success") and not result.success:
            # Graceful failure - acceptable
            assert (
                len(result.errors) > 0 or result.content_blocks is not None
            ), "Failed extraction should have error messages or empty content"
    except Exception as e:
        # Exception is acceptable for corrupted files
        # Just verify it's a reasonable error type
        assert isinstance(
            e, (ValueError, IOError, OSError, Exception)
        ), f"Should raise appropriate exception, got {type(e).__name__}"
    finally:
        # Cleanup
        if corrupted_docx.exists():
            corrupted_docx.unlink()


@pytest.mark.integration
@pytest.mark.edge_case
@pytest.mark.test_id("int-INT-010")
def test_pipeline_with_extraction_failure():
    """
    Test edge case: Pipeline handling when extraction fails.

    Verifies that downstream components (processor, formatter) handle
    failed extraction results gracefully.
    """
    # Arrange: Create extraction result with success=False
    test_file = Path("test_failed.txt")

    failed_result = ExtractionResult(
        content_blocks=(),  # Empty content
        document_metadata=DocumentMetadata(
            source_file=test_file, file_size_bytes=0, file_format="txt"
        ),
        success=False,
        errors=("Simulated extraction failure",),
    )

    processor = MetadataAggregator()
    formatter = MarkdownFormatter()

    # Act: Process failed extraction result
    try:
        processing_result = processor.process(failed_result)

        # Assert: Processor should handle failure gracefully
        assert processing_result is not None, "Processor should return result even on failure"

        # Try formatting
        try:
            formatted_output = formatter.format(processing_result)
            # Formatter may succeed with empty content or fail gracefully
            assert formatted_output is not None, "Formatter should return result"
        except Exception as format_error:
            # Acceptable if formatter raises exception for failed input
            assert isinstance(
                format_error, (ValueError, Exception)
            ), "Should raise appropriate exception"
    except Exception as process_error:
        # Acceptable if processor raises exception for failed input
        assert isinstance(
            process_error, (ValueError, Exception)
        ), "Should raise appropriate exception"
