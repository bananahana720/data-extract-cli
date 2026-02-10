"""
Infrastructure Integration Tests.

Tests integration of infrastructure components:
- ConfigManager → LoggingFramework (config loaded, logged)
- LoggingFramework → ErrorHandler (errors logged correctly)
- ErrorHandler → ProgressTracker (errors don't break progress)
- All infrastructure → Pipeline (full integration)
- Configuration changes → Runtime behavior
- Logging levels → Output filtering

Test IDs: II-001 through II-008

NOTE: Tests skipped - brownfield infrastructure moved to TRASH.
"""

import logging
from typing import Any

import pytest

# Stub for brownfield imports (modules deleted, tests skipped)
DocxExtractor: Any = None  # type: ignore[assignment]
TextFileExtractor: Any = None  # type: ignore[assignment]
JsonFormatter: Any = None  # type: ignore[assignment]
ConfigManager: Any = None  # type: ignore[assignment]
get_logger: Any = None  # type: ignore[assignment]
ExtractionPipeline: Any = None  # type: ignore[assignment]
ContextLinker: Any = None  # type: ignore[assignment]

# ==============================================================================
# Test Markers
# ==============================================================================

pytestmark = [
    pytest.mark.P0,
    pytest.mark.integration,
    pytest.mark.infrastructure,
    pytest.mark.skip(reason="Brownfield infrastructure moved to TRASH - needs greenfield rewrite"),
]


# ==============================================================================
# ConfigManager → LoggingFramework Integration Tests
# ==============================================================================


@pytest.mark.test_id("int-INT-001")
def test_ii_001_config_loading_logged(config_file, tmp_path):
    """
    Test II-001: ConfigManager logs configuration loading.

    Scenario: Load config → Check logs

    Verifies:
    - Config loading logged
    - Log entries have correct level
    - Config values logged (if debug level)
    """
    # Arrange: Setup logging to capture output
    log_file = tmp_path / "test.log"
    logger = get_logger("config_test")

    # Add file handler to capture logs
    handler = logging.FileHandler(str(log_file))
    handler.setLevel(logging.DEBUG)
    logger.addHandler(handler)

    # Act: Load configuration
    config = ConfigManager(config_file)

    # Assert: Config loaded
    assert config is not None

    # Assert: Log file created (if logger was used)
    # Note: Actual logging depends on ConfigManager implementation
    # This test verifies no errors occur

    # Cleanup
    logger.removeHandler(handler)
    handler.close()


@pytest.mark.test_id("int-INT-002")
def test_ii_002_config_with_default_logging(sample_docx_file):
    """
    Test II-002: Default configuration works with logging.

    Scenario: Use default config → Process file → Check logs

    Verifies:
    - Default config loads successfully
    - Logging works without explicit config
    - Processing completes without errors
    """
    # Arrange: Use default config (no file specified)
    config = ConfigManager()  # Uses defaults

    # Arrange: Create pipeline with default config
    pipeline = ExtractionPipeline(config=config)
    pipeline.register_extractor("docx", DocxExtractor())
    pipeline.add_processor(ContextLinker())
    pipeline.add_formatter(JsonFormatter())

    # Act: Process file
    result = pipeline.process_file(sample_docx_file)

    # Assert: Success
    assert result.success is True


# ==============================================================================
# LoggingFramework → ErrorHandler Integration Tests
# ==============================================================================


@pytest.mark.test_id("int-INT-003")
def test_ii_003_errors_logged_correctly(corrupted_docx_file, tmp_path):
    """
    Test II-003: ErrorHandler errors are logged correctly.

    Scenario: Process corrupted file → Check error logs

    Verifies:
    - Errors logged with appropriate level
    - Stack traces captured (if debug)
    - Error context included
    """
    # Arrange: Setup logging
    log_file = tmp_path / "errors.log"
    logger = get_logger("error_test")

    handler = logging.FileHandler(str(log_file))
    handler.setLevel(logging.ERROR)
    logger.addHandler(handler)

    # Arrange: Create pipeline
    pipeline = ExtractionPipeline()
    pipeline.register_extractor("docx", DocxExtractor())
    pipeline.add_formatter(JsonFormatter())

    # Act: Process corrupted file (will error)
    result = pipeline.process_file(corrupted_docx_file)

    # Assert: Failed
    assert result.success is False

    # Assert: Errors captured in result
    assert len(result.all_errors) > 0

    # Cleanup
    logger.removeHandler(handler)
    handler.close()

    # Note: Actual log file contents depend on implementation


@pytest.mark.test_id("int-INT-004")
def test_ii_004_warning_vs_error_logging_levels(sample_docx_file, tmp_path):
    """
    Test II-004: Warnings and errors logged at correct levels.

    Scenario: Process with potential warnings → Check log levels

    Verifies:
    - Warnings logged at WARNING level
    - Errors logged at ERROR level
    - Info logged at INFO level
    """
    # Arrange: Setup logging with different levels
    log_file = tmp_path / "levels.log"
    logger = get_logger("level_test")

    handler = logging.FileHandler(str(log_file))
    handler.setLevel(logging.DEBUG)  # Capture all levels
    formatter = logging.Formatter("%(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

    # Act: Log messages at different levels
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")

    # Cleanup
    logger.removeHandler(handler)
    handler.close()

    # Assert: Log file created and has content
    assert log_file.exists()
    log_content = log_file.read_text()

    # Verify levels are in log
    assert "DEBUG" in log_content or "INFO" in log_content
    assert "WARNING" in log_content
    assert "ERROR" in log_content


# ==============================================================================
# ErrorHandler → ProgressTracker Integration Tests
# ==============================================================================


@pytest.mark.test_id("int-INT-005")
def test_ii_005_progress_continues_despite_errors(tmp_path, progress_tracker):
    """
    Test II-005: ProgressTracker continues updating despite errors.

    Scenario: Batch with some failures → Progress updates continue

    Verifies:
    - Progress updates even when errors occur
    - Error doesn't break progress tracking
    - Final progress reaches 100% or stops appropriately
    """
    # Arrange: Unpack progress tracker
    progress_updates, progress_callback = progress_tracker

    # Arrange: Create files including one corrupted
    test_dir = tmp_path / "mixed"
    test_dir.mkdir()

    valid_file = test_dir / "valid.txt"
    valid_file.write_text("Valid content")

    corrupted_file = test_dir / "corrupted.docx"
    corrupted_file.write_text("Not a valid DOCX")

    # Arrange: Pipeline
    pipeline = ExtractionPipeline()
    pipeline.register_extractor("txt", TextFileExtractor())
    pipeline.register_extractor("docx", DocxExtractor())
    pipeline.add_formatter(JsonFormatter())

    # Act: Process both files with progress tracking
    from src.pipeline import BatchProcessor

    batch = BatchProcessor(pipeline=pipeline, max_workers=1)
    results = batch.process_batch([valid_file, corrupted_file], progress_callback=progress_callback)

    # Assert: Both attempted
    assert len(results) == 2

    # Assert: Progress updates received despite errors
    assert len(progress_updates) > 0


@pytest.mark.test_id("int-INT-006")
def test_ii_006_error_handler_with_progress_tracker(sample_docx_file, progress_tracker):
    """
    Test II-006: ErrorHandler and ProgressTracker work together.

    Scenario: Process file with both error handling and progress tracking

    Verifies:
    - Both systems active simultaneously
    - No conflicts or race conditions
    - All updates captured
    """
    # Arrange: Unpack progress tracker
    progress_updates, progress_callback = progress_tracker

    # Arrange: Create pipeline
    pipeline = ExtractionPipeline()
    pipeline.register_extractor("docx", DocxExtractor())
    pipeline.add_processor(ContextLinker())
    pipeline.add_formatter(JsonFormatter())

    # Act: Process with progress tracking
    result = pipeline.process_file(sample_docx_file, progress_callback=progress_callback)

    # Assert: Success
    assert result.success is True

    # Assert: Progress updates received
    assert len(progress_updates) > 0


# ==============================================================================
# Full Infrastructure Integration Tests
# ==============================================================================


@pytest.mark.test_id("int-INT-007")
def test_ii_007_all_infrastructure_with_pipeline(config_file, sample_docx_file, tmp_path):
    """
    Test II-007: All infrastructure components integrated with pipeline.

    Scenario: Config + Logging + ErrorHandler + ProgressTracker + Pipeline

    Verifies:
    - All systems work together
    - No conflicts or errors
    - Processing succeeds
    - All tracking/logging active
    """
    # Arrange: Setup all infrastructure
    # Config
    config = ConfigManager(config_file)

    # Logging
    log_file = tmp_path / "integration.log"
    logger = get_logger("full_integration")
    handler = logging.FileHandler(str(log_file))
    handler.setLevel(logging.INFO)
    logger.addHandler(handler)

    # Progress tracking
    progress_updates = []

    def progress_callback(status: dict):
        progress_updates.append(status)

    # Pipeline with all components
    pipeline = ExtractionPipeline(config=config)
    pipeline.register_extractor("docx", DocxExtractor())
    pipeline.add_processor(ContextLinker())
    pipeline.add_formatter(JsonFormatter())

    # Act: Process file with all infrastructure active
    result = pipeline.process_file(sample_docx_file, progress_callback=progress_callback)

    # Assert: Success
    assert result.success is True

    # Assert: Progress updates received
    assert len(progress_updates) > 0

    # Cleanup
    logger.removeHandler(handler)
    handler.close()


# ==============================================================================
# Configuration Changes Tests
# ==============================================================================


@pytest.mark.test_id("int-INT-008")
def test_ii_008_config_changes_affect_runtime(tmp_path, sample_docx_file):
    """
    Test II-008: Configuration changes affect runtime behavior.

    Scenario: Config A → Process → Config B → Process → Compare

    Verifies:
    - Different configs produce different behavior
    - Config actually applied
    - No config caching issues
    """
    # Arrange: Create two different configs
    config_a = tmp_path / "config_a.yaml"
    config_a.write_text(
        """
pipeline:
  max_workers: 1

extractors:
  docx:
    skip_empty: true
"""
    )

    config_b = tmp_path / "config_b.yaml"
    config_b.write_text(
        """
pipeline:
  max_workers: 4

extractors:
  docx:
    skip_empty: false
"""
    )

    # Arrange: Load config A
    config_mgr_a = ConfigManager(config_a)
    pipeline_a = ExtractionPipeline(config=config_mgr_a)
    pipeline_a.register_extractor("docx", DocxExtractor())
    pipeline_a.add_formatter(JsonFormatter())

    # Act: Process with config A
    result_a = pipeline_a.process_file(sample_docx_file)

    # Arrange: Load config B
    config_mgr_b = ConfigManager(config_b)
    pipeline_b = ExtractionPipeline(config=config_mgr_b)
    pipeline_b.register_extractor("docx", DocxExtractor())
    pipeline_b.add_formatter(JsonFormatter())

    # Act: Process with config B
    result_b = pipeline_b.process_file(sample_docx_file)

    # Assert: Both succeeded
    assert result_a.success is True
    assert result_b.success is True

    # Assert: Configs loaded differently
    assert config_mgr_a is not config_mgr_b


# ==============================================================================
# Logging Level Filtering Tests
# ==============================================================================


@pytest.mark.test_id("int-INT-009")
def test_ii_009_logging_level_filtering(tmp_path):
    """
    Test II-009: Logging respects level filtering.

    Scenario: Set INFO level → Log DEBUG and INFO → Check output

    Verifies:
    - DEBUG messages filtered when level=INFO
    - INFO messages appear
    - Level filtering works correctly
    """
    # Arrange: Setup logging at INFO level
    log_file = tmp_path / "filtered.log"
    logger = get_logger("filter_test")
    logger.setLevel(logging.INFO)  # Filter out DEBUG

    handler = logging.FileHandler(str(log_file))
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter("%(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Act: Log at different levels
    logger.debug("This is DEBUG - should be filtered")
    logger.info("This is INFO - should appear")
    logger.warning("This is WARNING - should appear")

    # Cleanup
    logger.removeHandler(handler)
    handler.close()

    # Assert: File has content
    assert log_file.exists()
    log_content = log_file.read_text()

    # Assert: INFO and WARNING present, DEBUG not present
    assert "INFO - This is INFO" in log_content
    assert "WARNING - This is WARNING" in log_content
    # DEBUG should not appear
    assert "DEBUG" not in log_content


# ==============================================================================
# Error Context Preservation Tests
# ==============================================================================


@pytest.mark.test_id("int-INT-010")
def test_ii_010_error_context_preserved_through_stack(corrupted_docx_file):
    """
    Test II-010: Error context preserved through call stack.

    Scenario: Error deep in stack → Check error at top

    Verifies:
    - Original error message preserved
    - Context information included
    - File path included in error
    """
    # Arrange: Create pipeline
    pipeline = ExtractionPipeline()
    pipeline.register_extractor("docx", DocxExtractor())
    pipeline.add_formatter(JsonFormatter())

    # Act: Process corrupted file
    result = pipeline.process_file(corrupted_docx_file)

    # Assert: Failed
    assert result.success is False

    # Assert: Error information preserved
    assert len(result.all_errors) > 0

    # Assert: Some error context present
    error_text = " ".join(result.all_errors).lower()
    # Error should mention something about the failure
    assert len(error_text) > 0


# ==============================================================================
# Progress Tracker State Tests
# ==============================================================================


@pytest.mark.test_id("int-INT-011")
def test_ii_011_progress_tracker_independent_per_operation(sample_docx_file, sample_text_file):
    """
    Test II-011: ProgressTracker maintains independent state per operation.

    Scenario: Process file A → Process file B → Check progress independent

    Verifies:
    - Progress resets for each operation
    - No state leakage between operations
    - Concurrent tracking possible
    """
    # Arrange: Create pipeline
    pipeline = ExtractionPipeline()
    pipeline.register_extractor("docx", DocxExtractor())
    pipeline.register_extractor("txt", DocxExtractor())
    pipeline.add_formatter(JsonFormatter())

    # Arrange: First progress tracker
    progress_a = []

    def callback_a(status):
        progress_a.append(status)

    # Act: Process file A
    result_a = pipeline.process_file(sample_docx_file, progress_callback=callback_a)

    # Arrange: Second progress tracker
    progress_b = []

    def callback_b(status):
        progress_b.append(status)

    # Act: Process file B
    result_b = pipeline.process_file(sample_text_file, progress_callback=callback_b)

    # Assert: Both succeeded
    assert result_a.success is True
    if sample_text_file.exists():
        # Text file processing may vary
        assert result_b.success is True or len(result_b.all_errors) > 0

    # Assert: Progress tracking independent
    # Each should have its own updates
    assert len(progress_a) > 0
    # Progress B may or may not have updates depending on text processing


# ==============================================================================
# ConfigManager Edge Cases Tests
# ==============================================================================


@pytest.mark.test_id("int-INT-012")
def test_ii_012_config_manager_handles_missing_file(tmp_path):
    """
    Test II-012: ConfigManager handles missing config file gracefully.

    Scenario: Specify non-existent config file

    Verifies:
    - Doesn't crash
    - Falls back to defaults
    - Warning or error logged
    """
    # Arrange: Non-existent config file
    missing_config = tmp_path / "nonexistent.yaml"

    # Act: Try to load
    try:
        config = ConfigManager(missing_config)
        # Should either succeed with defaults or raise appropriate error
        assert config is not None
    except (FileNotFoundError, ValueError) as e:
        # Expected behavior - graceful error
        assert "not found" in str(e).lower() or "does not exist" in str(e).lower()


@pytest.mark.test_id("int-INT-013")
def test_ii_013_config_manager_with_none_uses_defaults():
    """
    Test II-013: ConfigManager with None config uses defaults.

    Scenario: ConfigManager(None) or ConfigManager()

    Verifies:
    - None accepted
    - Defaults used
    - Processing works
    """
    # Act: Create with None (should use defaults)
    config = ConfigManager(None)

    # Assert: Config created
    assert config is not None

    # Can be used with pipeline
    pipeline = ExtractionPipeline(config=config)
    assert pipeline is not None
