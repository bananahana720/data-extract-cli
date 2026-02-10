"""Exception hierarchy for data extraction pipeline.

This module defines a consistent exception hierarchy for error handling:
- DataExtractError: Base exception for all tool errors
- ProcessingError: Recoverable errors (log, skip file, continue batch)
- CriticalError: Unrecoverable errors (halt processing immediately)
- ConfigurationError: Configuration-related critical errors
- ExtractionError: Document extraction failures (recoverable)
- ValidationError: Data validation failures (recoverable)

Error Handling Strategy:
    ProcessingError: Log warning, quarantine file, continue with remaining batch
    CriticalError: Log error and halt processing immediately (e.g., invalid config)
"""


class DataExtractError(Exception):
    """Base exception for all data extraction tool errors.

    All custom exceptions in the tool inherit from this base class.
    This allows catching all tool-specific errors with a single except clause.

    Example:
        >>> try:
        ...     # Some pipeline operation
        ...     pass
        ... except DataExtractError as e:
        ...     # Catches all tool-specific errors
        ...     print(f"Tool error: {e}")
    """

    pass


class ProcessingError(DataExtractError):
    """Recoverable error during document processing.

    Indicates an error that affects a single file but should not halt
    batch processing. The pipeline should log the error, quarantine
    the problematic file, and continue processing remaining files.

    When to use:
        - Document extraction fails for a single file
        - Data validation fails for a single document
        - OCR quality is below acceptable threshold
        - Entity extraction fails for a document

    Example:
        >>> try:
        ...     process_document(corrupted_pdf)
        ... except ProcessingError as e:
        ...     logger.warning(f"Skipping file: {e}")
        ...     quarantine_file(corrupted_pdf)
        ...     # Continue with next file
    """

    pass


class CriticalError(DataExtractError):
    """Unrecoverable error requiring immediate halt.

    Indicates a critical error that prevents the pipeline from continuing.
    Processing should stop immediately and report the error to the user.

    When to use:
        - Invalid or missing configuration file
        - Database connection failure (if applicable)
        - Insufficient system resources (disk space, memory)
        - Required dependencies missing

    Example:
        >>> if not config_file.exists():
        ...     raise CriticalError(f"Configuration file not found: {config_file}")
    """

    pass


class ConfigurationError(CriticalError):
    """Configuration-related critical error.

    Indicates invalid, missing, or incompatible configuration.
    Extends CriticalError as configuration errors always halt processing.

    When to use:
        - Configuration file missing or unreadable
        - Invalid configuration values (e.g., negative batch size)
        - Required configuration keys missing
        - Configuration version incompatible with tool version

    Example:
        >>> if "batch_size" not in config:
        ...     raise ConfigurationError("Required config key 'batch_size' missing")
        >>> if config["batch_size"] <= 0:
        ...     raise ConfigurationError("batch_size must be positive")
    """

    pass


class ExtractionError(ProcessingError):
    """Document extraction failure (recoverable).

    Indicates failure to extract content from a specific document.
    Extends ProcessingError as extraction failures are file-specific
    and should not halt batch processing.

    When to use:
        - PDF extraction fails (corrupted file, unsupported format)
        - Excel workbook cannot be read
        - PowerPoint slide deck has encoding issues
        - OCR fails for scanned image

    Example:
        >>> try:
        ...     content = extract_pdf(file_path)
        ... except Exception as e:
        ...     raise ExtractionError(f"Failed to extract {file_path}: {e}")
    """

    pass


class ValidationError(ProcessingError):
    """Data validation failure (recoverable).

    Indicates validation failure for extracted data. Extends ProcessingError
    as validation errors are typically file-specific and recoverable.

    When to use:
        - Extracted data fails schema validation
        - Required fields missing from extracted document
        - Data quality below acceptable threshold
        - Entity extraction confidence too low

    Example:
        >>> if chunk.quality_score < 0.5:
        ...     raise ValidationError(f"Chunk quality {chunk.quality_score} below threshold 0.5")
        >>> if not document.text.strip():
        ...     raise ValidationError("Document text is empty")
    """

    pass
