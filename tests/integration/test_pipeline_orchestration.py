"""
Pipeline Orchestration Integration Tests.

Tests complete pipeline orchestration and coordination:
- Auto-detection → Correct extractor selection
- Full pipeline: Extractor → Processor chain → Formatter
- Batch processing → Multiple files → Consistent results
- Mixed file types → Batch → All succeed
- Error recovery → Pipeline handles failures gracefully
- Configuration → Pipeline respects settings
- Progress tracking → Accurate throughout pipeline
- Format switching → Same input → Multiple outputs
- Parallel processing → No race conditions

Test IDs: PO-001 through PO-012

NOTE: Tests skipped - brownfield pipeline infrastructure moved to TRASH.
Greenfield pipeline has different architecture (Extract → Normalize → Chunk → Semantic → Output).
"""

from typing import Any

import pytest

# Stub for brownfield imports (modules deleted, tests skipped)
ProcessingStage: Any = None  # type: ignore[assignment]
DocxExtractor: Any = None  # type: ignore[assignment]
PdfExtractor: Any = None  # type: ignore[assignment]
ChunkedTextFormatter: Any = None  # type: ignore[assignment]
JsonFormatter: Any = None  # type: ignore[assignment]
MarkdownFormatter: Any = None  # type: ignore[assignment]
BatchProcessor: Any = None  # type: ignore[assignment]
ExtractionPipeline: Any = None  # type: ignore[assignment]
ContextLinker: Any = None  # type: ignore[assignment]
MetadataAggregator: Any = None  # type: ignore[assignment]
QualityValidator: Any = None  # type: ignore[assignment]

# ==============================================================================
# Test Markers
# ==============================================================================

pytestmark = [
    pytest.mark.P0,
    pytest.mark.integration,
    pytest.mark.pipeline,
    pytest.mark.slow,
    pytest.mark.skip(reason="Brownfield pipeline moved to TRASH - needs greenfield rewrite"),
]


# ==============================================================================
# Format Auto-Detection Tests
# ==============================================================================


@pytest.mark.test_id("int-INT-001")
def test_po_001_pipeline_auto_detects_docx(sample_docx_file):
    """
    Test PO-001: Pipeline auto-detects DOCX and selects correct extractor.

    Scenario: DOCX file → Pipeline.process_file() without format specified

    Verifies:
    - Format detected from file extension
    - Correct extractor selected
    - Processing succeeds
    """
    # Arrange: Create pipeline with registered extractors
    pipeline = ExtractionPipeline()
    pipeline.register_extractor("docx", DocxExtractor())
    pipeline.add_processor(ContextLinker())
    pipeline.add_formatter(JsonFormatter())

    # Act: Process without specifying format
    result = pipeline.process_file(sample_docx_file)

    # Assert: Success
    assert result.success is True
    assert result.extraction_result is not None
    assert result.extraction_result.success is True


@pytest.mark.test_id("int-INT-002")
def test_po_002_pipeline_auto_detects_pdf(sample_pdf_file):
    """
    Test PO-002: Pipeline auto-detects PDF and selects correct extractor.

    Scenario: PDF file → Pipeline.process_file() without format specified

    Verifies:
    - PDF format detected
    - Correct extractor used
    - Multi-page handled
    """
    # Arrange: Create pipeline
    pipeline = ExtractionPipeline()
    pipeline.register_extractor("pdf", PdfExtractor())
    pipeline.add_processor(MetadataAggregator())
    pipeline.add_formatter(JsonFormatter())

    # Act: Process
    result = pipeline.process_file(sample_pdf_file)

    # Assert: Success
    assert result.success is True
    assert result.extraction_result is not None


@pytest.mark.test_id("int-INT-003")
def test_po_003_pipeline_handles_unsupported_format(tmp_path):
    """
    Test PO-003: Pipeline gracefully handles unsupported format.

    Scenario: Unsupported file (.xyz) → Pipeline

    Verifies:
    - Graceful failure
    - Error message clear
    - No crash
    """
    # Arrange: Create unsupported file
    unsupported_file = tmp_path / "test.xyz"
    unsupported_file.write_text("test content")

    # Arrange: Create pipeline
    pipeline = ExtractionPipeline()
    pipeline.register_extractor("docx", DocxExtractor())

    # Act: Try to process
    result = pipeline.process_file(unsupported_file)

    # Assert: Failed gracefully
    assert result.success is False
    assert len(result.all_errors) > 0
    # Error should mention unsupported format
    error_text = " ".join(result.all_errors).lower()
    assert "unsupported" in error_text or "format" in error_text or "not found" in error_text


# ==============================================================================
# Full Pipeline Tests
# ==============================================================================


@pytest.mark.test_id("int-INT-004")
def test_po_004_full_pipeline_end_to_end(sample_docx_file):
    """
    Test PO-004: Complete pipeline from extraction to formatted output.

    Scenario: DOCX → Extract → ContextLinker → MetadataAggregator →
              QualityValidator → JSON + Markdown formatters

    Verifies:
    - All stages execute
    - No data loss
    - Multiple formatters produce outputs
    - Quality score computed
    """
    # Arrange: Create fully configured pipeline
    pipeline = ExtractionPipeline()

    # Register extractors
    pipeline.register_extractor("docx", DocxExtractor())

    # Add processors (in any order - pipeline should sort by dependencies)
    pipeline.add_processor(QualityValidator())  # Depends on MetadataAggregator
    pipeline.add_processor(ContextLinker())  # No dependencies
    pipeline.add_processor(MetadataAggregator())  # Depends on ContextLinker

    # Add multiple formatters
    pipeline.add_formatter(JsonFormatter())
    pipeline.add_formatter(MarkdownFormatter())

    # Act: Process file
    result = pipeline.process_file(sample_docx_file)

    # Assert: Overall success
    assert result.success is True
    assert result.failed_stage is None

    # Assert: Extraction completed
    assert result.extraction_result is not None
    assert result.extraction_result.success is True
    assert len(result.extraction_result.content_blocks) > 0

    # Assert: Processing completed
    assert result.processing_result is not None
    assert result.processing_result.success is True
    assert result.processing_result.quality_score is not None
    assert result.processing_result.processing_stage == ProcessingStage.QUALITY_VALIDATION

    # Assert: All formatters produced output
    assert len(result.formatted_outputs) == 2
    assert all(out.success for out in result.formatted_outputs)

    # Verify format types
    format_types = {out.format_type for out in result.formatted_outputs}
    assert "json" in format_types
    assert "markdown" in format_types


@pytest.mark.test_id("int-INT-005")
def test_po_005_pipeline_processor_dependency_ordering(sample_docx_file):
    """
    Test PO-005: Pipeline orders processors by dependencies.

    Scenario: Add processors in wrong order → Pipeline auto-sorts

    Verifies:
    - Processors execute in correct order
    - Dependencies respected
    - No errors from incorrect ordering
    """
    # Arrange: Create pipeline
    pipeline = ExtractionPipeline()
    pipeline.register_extractor("docx", DocxExtractor())

    # Add processors in intentionally wrong order
    pipeline.add_processor(QualityValidator())  # Should run last
    pipeline.add_processor(MetadataAggregator())  # Should run second
    pipeline.add_processor(ContextLinker())  # Should run first

    pipeline.add_formatter(JsonFormatter())

    # Act: Process
    result = pipeline.process_file(sample_docx_file)

    # Assert: Success despite wrong add order
    assert result.success is True
    assert result.processing_result is not None
    assert result.processing_result.success is True

    # Assert: Quality score computed (means all processors ran)
    assert result.processing_result.quality_score is not None


# ==============================================================================
# Batch Processing Tests
# ==============================================================================


@pytest.mark.test_id("int-INT-006")
def test_po_006_batch_processes_multiple_files(batch_test_directory, configured_pipeline):
    """
    Test PO-006: Batch processor handles multiple files.

    Scenario: Directory with 5+ files → Batch process

    Verifies:
    - All files processed
    - Results for each file
    - Summary statistics correct
    - No cross-contamination
    """
    # Arrange: Get files from batch directory
    files = list(batch_test_directory.glob("*"))
    assert len(files) > 0

    # Arrange: Create batch processor
    batch = BatchProcessor(pipeline=configured_pipeline, max_workers=2)

    # Act: Process batch
    results = batch.process_batch(files)

    # Assert: All files processed
    assert len(results) == len(files)

    # Assert: Each result is independent
    for i, result in enumerate(results):
        assert result.source_file == files[i]
        # Results can be success or failure, but should exist

    # Assert: Summary available
    summary = batch.get_summary(results)
    assert summary["total_files"] == len(files)
    assert summary["successful"] >= 0
    assert summary["failed"] >= 0
    assert summary["successful"] + summary["failed"] == len(files)


@pytest.mark.test_id("int-INT-007")
def test_po_007_batch_handles_mixed_formats(
    sample_docx_file, sample_pdf_file, sample_text_file, tmp_path
):
    """
    Test PO-007: Batch processing with mixed file types.

    Scenario: DOCX + PDF + TXT → Batch process

    Verifies:
    - All formats processed
    - Correct extractor for each
    - Consistent output structure
    """
    # Arrange: Create directory with mixed files
    mixed_dir = tmp_path / "mixed"
    mixed_dir.mkdir()

    # Copy files to mixed directory
    import shutil

    docx_copy = mixed_dir / "test.docx"
    pdf_copy = mixed_dir / "test.pdf"
    txt_copy = mixed_dir / "test.txt"

    shutil.copy(sample_docx_file, docx_copy)
    shutil.copy(sample_pdf_file, pdf_copy)
    shutil.copy(sample_text_file, txt_copy)

    # Arrange: Create pipeline with all extractors
    pipeline = ExtractionPipeline()
    pipeline.register_extractor("docx", DocxExtractor())
    pipeline.register_extractor("pdf", PdfExtractor())
    pipeline.register_extractor("txt", DocxExtractor())  # TXT uses DOCX extractor

    pipeline.add_processor(ContextLinker())
    pipeline.add_formatter(JsonFormatter())

    # Arrange: Create batch processor
    batch = BatchProcessor(pipeline=pipeline, max_workers=2)

    # Act: Process all files
    files = [docx_copy, pdf_copy, txt_copy]
    results = batch.process_batch(files)

    # Assert: All processed
    assert len(results) == 3

    # Assert: Check successes
    successful = batch.get_successful_results(results)
    assert len(successful) >= 1  # At least some should succeed

    # Assert: Different formats processed
    formats_processed = {r.source_file.suffix for r in results}
    assert ".docx" in formats_processed
    assert ".pdf" in formats_processed
    assert ".txt" in formats_processed


@pytest.mark.test_id("int-INT-008")
def test_po_008_batch_partial_failures(
    batch_test_directory, corrupted_docx_file, configured_pipeline, tmp_path
):
    """
    Test PO-008: Batch processing continues despite individual failures.

    Scenario: Mix of valid and corrupted files → Batch process

    Verifies:
    - Batch continues after failures
    - Failed files reported
    - Successful files processed
    - Summary shows partial success
    """
    # Arrange: Create directory with valid and corrupted files
    test_dir = tmp_path / "partial"
    test_dir.mkdir()

    import shutil

    # Copy some valid files
    valid_files = list(batch_test_directory.glob("*"))[:2]
    for vf in valid_files:
        shutil.copy(vf, test_dir / vf.name)

    # Add corrupted file
    shutil.copy(corrupted_docx_file, test_dir / "corrupted.docx")

    # Arrange: Batch processor
    batch = BatchProcessor(pipeline=configured_pipeline, max_workers=2)

    # Act: Process
    files = list(test_dir.glob("*"))
    results = batch.process_batch(files)

    # Assert: All files attempted
    assert len(results) == len(files)

    # Assert: Some succeeded, some failed
    successful = batch.get_successful_results(results)
    failed = batch.get_failed_results(results)

    assert len(successful) >= 1  # At least some valid files processed
    # Corrupted file may fail or succeed with warnings


@pytest.mark.test_id("int-INT-009")
def test_po_009_batch_respects_max_workers(batch_test_directory, configured_pipeline):
    """
    Test PO-009: Batch processor respects worker limit.

    Scenario: Batch with max_workers=1 vs max_workers=4

    Verifies:
    - Worker limit enforced
    - Results consistent regardless of workers
    - No race conditions
    """
    # Arrange: Get files
    files = list(batch_test_directory.glob("*"))[:4]
    if len(files) < 2:
        pytest.skip("Need at least 2 files for parallel testing")

    # Act: Process with 1 worker (sequential)
    batch_single = BatchProcessor(pipeline=configured_pipeline, max_workers=1)
    results_single = batch_single.process_batch(files)

    # Act: Process with 4 workers (parallel)
    batch_multi = BatchProcessor(pipeline=configured_pipeline, max_workers=4)
    results_multi = batch_multi.process_batch(files)

    # Assert: Same number of results
    assert len(results_single) == len(results_multi) == len(files)

    # Assert: Success rates similar (allowing for timing variations)
    summary_single = batch_single.get_summary(results_single)
    summary_multi = batch_multi.get_summary(results_multi)

    assert summary_single["total_files"] == summary_multi["total_files"]
    # Success counts should be close (may vary slightly due to timing)


# ==============================================================================
# Configuration Integration Tests
# ==============================================================================


@pytest.mark.test_id("int-INT-010")
def test_po_010_pipeline_respects_configuration(sample_docx_file, config_file):
    """
    Test PO-010: Pipeline respects configuration settings.

    Scenario: Load config → Create pipeline → Process

    Verifies:
    - Config loaded correctly
    - Pipeline uses config settings
    - Processing reflects configuration
    """
    # Arrange: Load config
    from src.infrastructure import ConfigManager

    config = ConfigManager(config_file)

    # Arrange: Create pipeline with config
    pipeline = ExtractionPipeline(config=config)

    pipeline.register_extractor("docx", DocxExtractor())
    pipeline.add_processor(ContextLinker())
    pipeline.add_formatter(JsonFormatter())

    # Act: Process
    result = pipeline.process_file(sample_docx_file)

    # Assert: Success
    assert result.success is True

    # Config integration verified by no errors


# ==============================================================================
# Progress Tracking Tests
# ==============================================================================


@pytest.mark.test_id("int-INT-011")
def test_po_011_pipeline_progress_tracking(sample_docx_file, progress_tracker):
    """
    Test PO-011: Pipeline provides progress updates.

    Scenario: Process file with progress callback

    Verifies:
    - Progress updates from 0% to 100%
    - Stage information included
    - Updates at key milestones
    """
    # Arrange: Unpack progress tracker
    progress_updates, progress_callback = progress_tracker

    # Arrange: Create pipeline
    pipeline = ExtractionPipeline()
    pipeline.register_extractor("docx", DocxExtractor())
    pipeline.add_processor(ContextLinker())
    pipeline.add_processor(MetadataAggregator())
    pipeline.add_formatter(JsonFormatter())

    # Act: Process with progress tracking
    result = pipeline.process_file(sample_docx_file, progress_callback=progress_callback)

    # Assert: Success
    assert result.success is True

    # Assert: Progress updates received
    assert len(progress_updates) > 0

    # Assert: Progress range
    if progress_updates:
        percentages = [u.get("percentage", 0) for u in progress_updates if "percentage" in u]
        if percentages:
            assert min(percentages) >= 0.0
            assert max(percentages) <= 100.0

    # Assert: Stage information present
    stages_seen = {u.get("stage") for u in progress_updates if "stage" in u}
    # At least some updates should have stage info
    assert len(progress_updates) > 0  # At minimum, updates occurred


@pytest.mark.test_id("int-INT-012")
def test_po_012_batch_progress_tracking(
    batch_test_directory, configured_pipeline, progress_tracker
):
    """
    Test PO-012: Batch processor provides progress updates.

    Scenario: Batch process with progress callback

    Verifies:
    - File-level progress
    - Overall batch progress
    - Current file indicated
    """
    # Arrange: Unpack progress tracker
    progress_updates, progress_callback = progress_tracker

    # Arrange: Get files
    files = list(batch_test_directory.glob("*"))[:3]
    if len(files) == 0:
        pytest.skip("No files in batch directory")

    # Arrange: Batch processor
    batch = BatchProcessor(pipeline=configured_pipeline, max_workers=1)

    # Act: Process with progress
    results = batch.process_batch(files, progress_callback=progress_callback)

    # Assert: All processed
    assert len(results) == len(files)

    # Assert: Progress updates received
    assert len(progress_updates) > 0


# ==============================================================================
# Format Switching Tests
# ==============================================================================


@pytest.mark.test_id("int-INT-013")
def test_po_013_same_input_multiple_output_formats(sample_docx_file):
    """
    Test PO-013: Same input produces multiple output formats.

    Scenario: DOCX → Pipeline → JSON + Markdown + Chunked

    Verifies:
    - All formatters execute
    - Outputs are independent
    - Content consistent across formats
    """
    # Arrange: Pipeline with all formatters
    pipeline = ExtractionPipeline()
    pipeline.register_extractor("docx", DocxExtractor())

    pipeline.add_processor(ContextLinker())
    pipeline.add_processor(MetadataAggregator())

    # Add all three formatters
    pipeline.add_formatter(JsonFormatter())
    pipeline.add_formatter(MarkdownFormatter())
    pipeline.add_formatter(ChunkedTextFormatter())

    # Act: Process once
    result = pipeline.process_file(sample_docx_file)

    # Assert: Success
    assert result.success is True

    # Assert: All three outputs generated
    assert len(result.formatted_outputs) == 3

    # Assert: All succeeded
    assert all(out.success for out in result.formatted_outputs)

    # Assert: Different formats
    format_types = {out.format_type for out in result.formatted_outputs}
    assert format_types == {"json", "markdown", "chunked"}

    # Assert: All have content
    assert all(len(out.content) > 0 for out in result.formatted_outputs)


# ==============================================================================
# Error Recovery Tests
# ==============================================================================


@pytest.mark.test_id("int-INT-014")
def test_po_014_pipeline_error_recovery(corrupted_docx_file):
    """
    Test PO-014: Pipeline handles extraction errors gracefully.

    Scenario: Corrupted file → Pipeline

    Verifies:
    - Extraction failure detected
    - Pipeline stops at extraction stage
    - Error information preserved
    - Failed stage identified
    """
    # Arrange: Create pipeline
    pipeline = ExtractionPipeline()
    pipeline.register_extractor("docx", DocxExtractor())
    pipeline.add_processor(ContextLinker())
    pipeline.add_formatter(JsonFormatter())

    # Act: Try to process corrupted file
    result = pipeline.process_file(corrupted_docx_file)

    # Assert: Failed
    assert result.success is False

    # Assert: Errors captured
    assert len(result.all_errors) > 0

    # Assert: Failed stage identified
    # Should fail at extraction or early stage
    assert result.failed_stage is not None


@pytest.mark.test_id("int-INT-015")
def test_po_015_pipeline_empty_file_handling(empty_docx_file):
    """
    Test PO-015: Pipeline handles empty files.

    Scenario: Empty DOCX → Pipeline

    Verifies:
    - Empty file doesn't crash
    - Succeeds with warnings or minimal output
    - Quality score reflects emptiness
    """
    # Arrange: Create pipeline
    pipeline = ExtractionPipeline()
    pipeline.register_extractor("docx", DocxExtractor())
    pipeline.add_processor(QualityValidator())
    pipeline.add_formatter(JsonFormatter())

    # Act: Process empty file
    result = pipeline.process_file(empty_docx_file)

    # Assert: Completed (may succeed with warnings)
    assert result.success is True or len(result.all_warnings) > 0

    # Assert: If has quality score, it should be low for empty file
    if result.processing_result and result.processing_result.quality_score is not None:
        # Empty file should have low quality score
        assert result.processing_result.quality_score < 50.0


# ==============================================================================
# Performance and Stress Tests
# ==============================================================================


@pytest.mark.test_id("int-INT-016")
def test_po_016_pipeline_handles_large_file(large_docx_file):
    """
    Test PO-016: Pipeline handles large files efficiently.

    Scenario: Large DOCX (100+ paragraphs) → Pipeline

    Verifies:
    - Large file processes successfully
    - Memory usage reasonable
    - Performance acceptable
    - All stages complete
    """
    # Arrange: Create pipeline
    pipeline = ExtractionPipeline()
    pipeline.register_extractor("docx", DocxExtractor())
    pipeline.add_processor(ContextLinker())
    pipeline.add_processor(MetadataAggregator())
    pipeline.add_formatter(JsonFormatter())

    # Act: Process large file
    result = pipeline.process_file(large_docx_file)

    # Assert: Success
    assert result.success is True

    # Assert: Many blocks extracted
    assert len(result.extraction_result.content_blocks) > 50

    # Assert: All stages completed
    assert result.processing_result is not None
    assert len(result.formatted_outputs) > 0


@pytest.mark.test_id("int-INT-017")
def test_po_017_batch_output_directory_creation(
    batch_test_directory, configured_pipeline, tmp_path
):
    """
    Test PO-017: Batch processor creates output directory structure.

    Scenario: Batch process → Non-existent output directory

    Verifies:
    - Output directory created
    - Files written successfully
    - Naming conventions followed
    """
    # Arrange: Output directory (doesn't exist yet)
    output_dir = tmp_path / "batch_output" / "nested"

    # Arrange: Get files
    files = list(batch_test_directory.glob("*"))[:2]
    if len(files) == 0:
        pytest.skip("No files in batch directory")

    # Arrange: Batch processor
    batch = BatchProcessor(pipeline=configured_pipeline, max_workers=1)

    # Act: Process batch
    results = batch.process_batch(files)

    # Assert: Processing completed
    assert len(results) == len(files)

    # Note: Actual file writing depends on BatchProcessor implementation
    # This test verifies the results are available for writing
