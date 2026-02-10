# API Functions Documentation

## Module: `cli.commands`

**`create_pipeline(config_path: Optional[Path])`**
  Create and configure extraction pipeline.

  Args:
      config_path: Optional path to configuration file

  Returns:
      Tuple of (ExtractionPipeline, config) - pipeline and loaded config

**`add_formatters(pipeline: ExtractionPipeline, format_type: str, config: Any) -> None`**
  Add formatters to pipeline based on format type.

  Args:
      pipeline: Pipeline to add formatters to
      format_type: Format type ('json', 'markdown', 'chunked', 'all')
      config: Optional configuration (ConfigManager or dict)

**`write_outputs(result: Any, output_path: Path, format_type: str) -> None`**
  Write formatted outputs to files with proper UTF-8 encoding.

  Handles Unicode characters safely to prevent encoding errors on Windows.

  Args:
      result: PipelineResult with formatted outputs
      output_path: Base output path
      format_type: Format type for naming

**`get_extension_for_format(format_type: str) -> str`**
  Get file extension for format type.

  Args:
      format_type: Format type name

  Returns:
      File extension including dot

**`format_user_error(error_msg: str, suggestion: Optional[str]) -> str`**
  Format error message for non-technical users.

  Args:
      error_msg: Technical error message
      suggestion: Optional suggestion for fixing

  Returns:
      User-friendly error message

**`extract_command(ctx: Any, file_path: Path, output: Optional[Path], format: str, force: bool)`**
  Decorators: click.command(), click.argument('file_path', type=click.Path(exists=True, path_type=Path)), click.option('--output', '-o', type=click.Path(path_type=Path), help='Output file or directory path'), click.option('--format', '-f', type=click.Choice(['json', 'markdown', 'chunked', 'all'], case_sensitive=False), default='json', help='Output format (default: json)'), click.option('--force', is_flag=True, help='Overwrite existing files without asking'), click.pass_context
  Extract content from a single file.

  Processes the specified file and generates output in the requested format.

  Examples:

      Extract to JSON:
      $ data-extract extract document.docx --format json

      Extract to Markdown with custom output:
      $ data-extract extract report.pdf --output result.md --format markdown

      Extract to all formats:
      $ data-extract extract presentation.pptx --format all

**`batch_command(ctx: Any, paths: tuple, output: Path, pattern: Optional[str], format: str, workers: int)`**
  Decorators: click.command(), click.argument('paths', nargs=-1, type=click.Path(exists=True, path_type=Path)), click.option('--output', '-o', type=click.Path(path_type=Path), required=True, help='Output directory path'), click.option('--pattern', '-p', type=str, help='Glob pattern to filter files (e.g., "*.pdf")'), click.option('--format', '-f', type=click.Choice(['json', 'markdown', 'chunked', 'all'], case_sensitive=False), default='json', help='Output format (default: json)'), click.option('--workers', '-w', type=int, default=4, help='Number of parallel workers (default: 4)'), click.pass_context
  Process multiple files in batch.

  Processes all files in specified directories or file list, using parallel
  workers for faster processing.

  Examples:

      Process all files in directory:
      $ data-extract batch ./documents/ --output ./results/

      Process only PDF files:
      $ data-extract batch ./documents/ --pattern "*.pdf" --output ./results/

      Process with custom worker count:
      $ data-extract batch ./documents/ --output ./results/ --workers 8

**`version_command(verbose: bool)`**
  Decorators: click.command(), click.option('--verbose', '-v', is_flag=True, help='Show detailed version information')
  Show version information.

  Displays the version number and optionally detailed component information.

  Examples:

      Show version:
      $ data-extract version

      Show detailed version info:
      $ data-extract version --verbose

**`config_command()`**
  Decorators: click.group()
  Configuration management commands.

  Manage and validate configuration files.

**`config_show(ctx: Any)`**
  Decorators: config_command.command(name='show'), click.pass_context
  Show current configuration.

**`config_validate(ctx: Any)`**
  Decorators: config_command.command(name='validate'), click.pass_context
  Validate configuration file.

**`config_path_command(ctx: Any)`**
  Decorators: config_command.command(name='path'), click.pass_context
  Show configuration file path.

## Module: `cli.main`

**`cli(ctx: Any, config: Optional[Path], verbose: bool, quiet: bool)`**
  Decorators: click.group(), click.option('--config', '-c', type=click.Path(exists=False, path_type=Path), help='Path to configuration file'), click.option('--verbose', '-v', is_flag=True, help='Show detailed output'), click.option('--quiet', '-q', is_flag=True, help='Suppress progress output'), click.pass_context
  Data Extraction Tool - Extract content from documents for AI processing.

  This tool helps you extract content from Word documents, PDFs, PowerPoint
  presentations, and Excel workbooks into AI-friendly formats.

  Examples:

      Extract a single file to JSON:
      $ data-extract extract document.docx --format json

      Process multiple files:
      $ data-extract batch ./documents/ --format json

      Show version information:
      $ data-extract version

**`version_short(ctx: Any)`**
  Decorators: cli.command(name='-V', hidden=True), click.pass_context
  Show version (short flag).

**`main()`**
  Entry point for console script.

## Module: `cli.progress_display`

**`_create_safe_console() -> Console`**
  Create a Console instance with safe encoding for Windows.

  Ensures UTF-8 encoding is used to prevent 'charmap' codec errors
  when displaying Unicode characters (e.g., from PDF icons or special fonts).

  Args:
      **kwargs: Additional Console constructor arguments

  Returns:
      Configured Console instance

**`create_progress_display(file_path: Optional[Path], file_paths: Optional[List[Path]], console: Optional[Console], verbose: bool, quiet: bool)`**
  Decorators: contextmanager
  Context manager factory for progress displays.

  Creates SingleFileProgress or BatchProgress based on arguments.

  Args:
      file_path: Single file path (creates SingleFileProgress)
      file_paths: List of file paths (creates BatchProgress)
      console: Optional Rich Console instance
      verbose: Show detailed information
      quiet: Suppress all output

  Yields:
      Progress display instance (SingleFileProgress or BatchProgress)

  Raises:
      ValueError: If neither file_path nor file_paths provided

  Example:
      >>> # Single file
      >>> with create_progress_display(file_path=Path("doc.docx")) as progress:
      >>>     def callback(status):
      >>>         progress.update(status)
      >>>     result = pipeline.process_file(file_path, progress_callback=callback)
      >>>
      >>> # Batch
      >>> with create_progress_display(file_paths=files) as progress:
      >>>     def callback(status):
      >>>         progress.update(status)
      >>>     results = batch.process_batch(files, progress_callback=callback)

## Module: `data_extract.chunk.__init__`

**`__getattr__(name: str) -> Any`**
  Lazily import attributes to avoid mandatory heavy dependencies.

## Module: `data_extract.cli`

**`app() -> None`**
  Decorators: click.group(), click.version_option(version='0.1.0')
  Data Extraction Tool - Enterprise document processing for RAG workflows.

  Minimal CLI for Story 3.5 - Full implementation in Epic 5.

**`process(input_file: Path, format_type: str, output_path: Path, per_chunk: bool, include_metadata: bool, organize: bool, strategy: Optional[str], delimiter: str) -> None`**
  Decorators: app.command(), click.argument('input_file', type=click.Path(exists=True, path_type=Path)), click.option('--format', 'format_type', type=click.Choice(['json', 'txt', 'csv'], case_sensitive=False), default='txt', help='Output format (default: txt)'), click.option('--output', 'output_path', type=click.Path(path_type=Path), required=True, help='Output file or directory path'), click.option('--per-chunk', is_flag=True, default=False, help='Write each chunk to separate file (TXT only)'), click.option('--include-metadata', is_flag=True, default=False, help='Include metadata headers in output (TXT only)'), click.option('--organize', is_flag=True, default=False, help='Enable output organization (requires --strategy)'), click.option('--strategy', type=click.Choice(['by_document', 'by_entity', 'flat'], case_sensitive=False), default=None, help='Organization strategy (requires --organize)'), click.option('--delimiter', type=str, default='━━━ CHUNK {{n}} ━━━', help='Custom chunk delimiter (TXT only, use {{n}} for chunk number)')
  Process a document and generate formatted output.

  Example usage:

      
      # Concatenated TXT output
      data-extract process input.pdf --format txt --output chunks.txt

      
      # Per-chunk TXT files with metadata
      data-extract process input.pdf --format txt --output output/ --per-chunk --include-metadata

      
      # Organized output with BY_DOCUMENT strategy
      data-extract process input.pdf --format txt --output output/ --per-chunk --organize --strategy by_document

      
      # JSON output
      data-extract process input.pdf --format json --output output.json

      
      # CSV output
      data-extract process input.pdf --format csv --output output.csv

  Note: This is a minimal implementation for Story 3.6 UAT validation.
  Full pipeline integration will be completed in Epic 5.

**`_create_demo_chunks(input_file: Path) -> list`**
  Create demo chunks for UAT validation.

  NOTE: This is a temporary helper for Story 3.5 demonstration.
  Epic 5 will replace with full extraction → normalize → chunk pipeline.

  Args:
      input_file: Input file path (used for metadata only)

  Returns:
      List of demo Chunk objects with realistic metadata

**`version() -> None`**
  Decorators: app.command()
  Display version information.

## Module: `data_extract.extract.__init__`

**`get_extractor(file_path: Path) -> ExtractorAdapter`**
  Get appropriate extractor adapter for file.

  Auto-detects file format from extension and returns the corresponding
  adapter instance. Factory pattern ensures single entry point for all
  extraction operations.

  Args:
      file_path: Path to file to extract

  Returns:
      ExtractorAdapter: Adapter instance for the file format

  Raises:
      ValueError: If file extension is not supported

  Example:
      >>> adapter = get_extractor(Path("report.pdf"))
      >>> isinstance(adapter, PdfExtractorAdapter)
      True

      >>> adapter = get_extractor(Path("data.xlsx"))
      >>> isinstance(adapter, ExcelExtractorAdapter)
      True

**`is_supported(file_path: Path) -> bool`**
  Check if file format is supported.

  Args:
      file_path: Path to file

  Returns:
      True if file format is supported, False otherwise

  Example:
      >>> is_supported(Path("document.pdf"))
      True
      >>> is_supported(Path("video.mp4"))
      False

## Module: `data_extract.normalize.config`

**`validate_entity_patterns(patterns_file: Path) -> List[str]`**
  Validate entity patterns YAML file and return validation errors.

  Checks that:
  - All 6 entity types have patterns defined
  - All regex patterns compile successfully
  - Required fields (pattern, description, priority) are present
  - Priority values are positive integers

  Args:
      patterns_file: Path to entity_patterns.yaml file

  Returns:
      List of validation error messages (empty if valid)

  Example:
      >>> errors = validate_entity_patterns(Path("config/normalize/entity_patterns.yaml"))
      >>> if errors:
      ...     print("Validation errors:", errors)

**`load_config(yaml_path: Optional[Path], env_vars: Optional[Dict[str, Any]], cli_flags: Optional[Dict[str, Any]]) -> NormalizationConfig`**
  Load normalization configuration with cascade precedence.

  Configuration cascade (highest to lowest precedence):
  1. CLI flags (cli_flags parameter)
  2. Environment variables (DATA_EXTRACT_NORMALIZE_* prefix)
  3. YAML configuration file (yaml_path parameter)
  4. Hardcoded defaults (NormalizationConfig defaults)

  Args:
      yaml_path: Path to YAML configuration file (optional)
      env_vars: Environment variables dict (defaults to os.environ)
      cli_flags: CLI flags dict (highest precedence)

  Returns:
      NormalizationConfig: Merged configuration with cascade precedence

  Raises:
      ValueError: If YAML file is invalid or file paths don't exist

  Examples:
      >>> # Load with defaults only
      >>> config = load_config()

      >>> # Load with YAML file
      >>> config = load_config(yaml_path=Path("config/normalize/cleaning_rules.yaml"))

      >>> # Load with CLI overrides
      >>> config = load_config(
      ...     yaml_path=Path("config/normalize/cleaning_rules.yaml"),
      ...     cli_flags={"remove_ocr_artifacts": False}
      ... )

## Module: `data_extract.normalize.metadata`

**`calculate_file_hash(file_path: Path, chunk_size: int = 8192) -> str`**
  Calculate SHA-256 hash of a file using chunked reading.

  Uses chunked reading (default 8KB chunks) for memory efficiency with large files.
  Ensures deterministic hashing for audit trail integrity.

  Args:
      file_path: Path to file to hash
      chunk_size: Size of chunks to read (default 8192 bytes = 8KB)

  Returns:
      SHA-256 hash as 64-character hexadecimal string

  Raises:
      ProcessingError: If file cannot be read (missing, permission denied, I/O error)

  Examples:
      >>> file_hash = calculate_file_hash(Path("document.pdf"))
      >>> assert len(file_hash) == 64  # SHA-256 produces 64 hex characters
      >>> # Same file always produces same hash (determinism)
      >>> hash1 = calculate_file_hash(Path("document.pdf"))
      >>> hash2 = calculate_file_hash(Path("document.pdf"))
      >>> assert hash1 == hash2

  Story: 2.6 - Metadata Enrichment Framework
  AC: 2.6.1 (file hash), 2.6.8 (audit trail)

**`aggregate_entity_tags(entities: List[Entity]) -> Tuple[List[str], Dict[str, int]]`**
  Aggregate entity tags and counts by entity type.

  Extracts entity type and ID from Entity objects, formats as "EntityType-ID"
  (e.g., "Risk-123", "Control-456"), and counts entities by EntityType.

  Args:
      entities: List of Entity objects to aggregate

  Returns:
      Tuple of (entity_tags, entity_counts):
          - entity_tags: List of formatted entity IDs (e.g., ["Risk-123", "Control-456"])
          - entity_counts: Dict mapping entity type to count (e.g., {"risk": 2, "control": 1})

  Examples:
      >>> entities = [
      ...     Entity(type=EntityType.RISK, id="Risk-123", text="...", confidence=0.9, location={}),
      ...     Entity(type=EntityType.CONTROL, id="Control-456", text="...", confidence=0.9, location={}),
      ... ]
      >>> tags, counts = aggregate_entity_tags(entities)
      >>> assert tags == ["Risk-123", "Control-456"]
      >>> assert counts == {"risk": 1, "control": 1}

  Story: 2.6 - Metadata Enrichment Framework
  AC: 2.6.4 (entity tags)

**`aggregate_quality_scores(validation_report: ValidationReport, readability_scores: Dict[str, float] | None) -> Tuple[Dict[str, float], List[str]]`**
  Aggregate quality scores from validation report and readability metrics.

  Collects OCR confidence, completeness ratio, and optional readability scores
  into a unified quality_scores dict. Also aggregates quality_flags from validation.

  Args:
      validation_report: ValidationReport from Story 2.5 with quality metrics
      readability_scores: Optional dict of readability metrics (e.g., flesch_reading_ease)

  Returns:
      Tuple of (quality_scores, quality_flags):
          - quality_scores: Dict with ocr_confidence, completeness_ratio, readability metrics
          - quality_flags: List of quality flag strings from ValidationReport

  Examples:
      >>> report = ValidationReport(
      ...     quarantine_recommended=False,
      ...     document_average_confidence=0.95,
      ...     completeness_passed=True,
      ...     quality_flags=[],
      ... )
      >>> scores, flags = aggregate_quality_scores(report)
      >>> assert scores["ocr_confidence"] == 0.95

  Story: 2.6 - Metadata Enrichment Framework
  AC: 2.6.5 (quality scores aggregation)

**`serialize_config_snapshot(config: NormalizationConfig) -> Dict[str, Any]`**
  Serialize NormalizationConfig to dict for reproducibility.

  Converts Pydantic config model to JSON-serializable dict using model_dump().
  Includes all configuration fields for full reproducibility.

  Args:
      config: NormalizationConfig instance to serialize

  Returns:
      Dict with all configuration fields (JSON-serializable)

  Examples:
      >>> from src.data_extract.normalize.config import NormalizationConfig
      >>> config = NormalizationConfig(
      ...     tool_version="2.0.0",
      ...     ocr_confidence_threshold=0.95,
      ...     completeness_threshold=0.90,
      ... )
      >>> snapshot = serialize_config_snapshot(config)
      >>> assert snapshot["tool_version"] == "2.0.0"
      >>> assert snapshot["ocr_confidence_threshold"] == 0.95

  Story: 2.6 - Metadata Enrichment Framework
  AC: 2.6.6 (configuration snapshot for reproducibility)

## Module: `data_extract.output.utils`

**`clean_text_artifacts(text: str) -> str`**
  Remove markdown and formatting artifacts from text.

  Args:
      text: Text to clean

  Returns:
      Cleaned text without artifacts

**`truncate_text(text: str, max_length: int) -> str`**
  Truncate text to maximum length with ellipsis.

  Args:
      text: Text to truncate
      max_length: Maximum length

  Returns:
      Truncated text with ellipsis if needed

**`normalize_path(path: Any) -> str`**
  Normalize path to string format.

  Args:
      path: Path object or string

  Returns:
      Normalized path string

## Module: `data_extract.output.validation.csv_parser`

**`validate_csv_structure(csv_path: Path) -> bool`**
  Quick validation of CSV structure.

  Args:
      csv_path: Path to CSV file

  Returns:
      True if CSV structure is valid

## Module: `data_extract.utils.nlp`

**`get_sentence_boundaries(text: str, nlp: Optional[Language]) -> List[int]`**
  Extract sentence boundary positions from text using spaCy.

  Returns character offsets (zero-indexed) where each sentence ends.
  Lazy loads en_core_web_md model if nlp parameter is None.

  Args:
      text: Input text to segment into sentences. Must be non-empty.
      nlp: Optional pre-loaded spaCy Language model. If None, lazy loads
          en_core_web_md and caches for subsequent calls.

  Returns:
      List of character positions (zero-indexed) where sentences end.
      For example, "Hello. World." returns [6, 13].

  Raises:
      ValueError: If text is empty or whitespace-only.
      OSError: If en_core_web_md model is not installed.

  Example:
      >>> boundaries = get_sentence_boundaries("Dr. Smith visited. This is sentence two.")
      >>> print(boundaries)
      [18, 42]

      >>> # With pre-loaded model
      >>> import spacy
      >>> nlp = spacy.load("en_core_web_md")
      >>> boundaries = get_sentence_boundaries("Hello. World.", nlp=nlp)
      >>> print(boundaries)
      [6, 13]

  NFR Compliance:
      - NFR-P3: Model load <5s, segmentation <100ms per 1000 words
      - NFR-O4: Logs model version on first load
      - NFR-R3: Clear error messages for missing model or invalid input

## Module: `extractors.txt_extractor`

**`main()`**
  Example usage of the TextFileExtractor.

## Module: `infrastructure.logging_framework`

**`get_logger(name: str, level: int = logging.INFO, json_format: bool = True, file_path: Optional[Path], console: bool, max_bytes: int = 10 * 1024 * 1024, backup_count: int = 5) -> logging.Logger`**
  Get or create a logger with specified configuration.

  Loggers are cached - calling with same name returns same instance.

  Args:
      name: Logger name (typically __name__)
      level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
      json_format: Use JSON structured logging (default: True)
      file_path: Optional file path for file logging
      console: Enable console logging (default: False)
      max_bytes: Max bytes per log file before rotation (default: 10MB)
      backup_count: Number of backup log files to keep (default: 5)

  Returns:
      Configured logger instance

  Example:
      >>> logger = get_logger(__name__)
      >>> logger.info("Processing file", file="document.docx", size=1024)

**`correlation_context(correlation_id: str)`**
  Decorators: contextmanager
  Context manager for setting correlation ID for request tracking.

  The correlation ID is automatically included in all log messages
  within the context. Uses context variables for thread-safety.

  Args:
      correlation_id: Unique identifier for this request/operation

  Example:
      >>> logger = get_logger(__name__)
      >>> with correlation_context("req-12345"):
      >>>     logger.info("Processing request")  # Includes correlation_id
      >>>     process_file()

**`timer(logger: logging.Logger, operation: str, level: int = logging.INFO)`**
  Decorators: contextmanager
  Context manager for timing operations.

  Automatically logs duration when context exits.

  Args:
      logger: Logger instance to use
      operation: Name of operation being timed
      level: Log level (default: INFO)

  Example:
      >>> with timer(logger, "file_extraction"):
      >>>     extract_content(file_path)
      # Logs: {"operation": "file_extraction", "duration_seconds": 1.234, ...}

**`timed(logger: logging.Logger, level: int = logging.INFO) -> Callable`**
  Decorator for timing functions.

  Automatically logs function duration.

  Args:
      logger: Logger instance to use
      level: Log level (default: INFO)

  Returns:
      Decorated function

  Example:
      >>> @timed(logger)
      >>> def extract_document(path):
      >>>     # ... extraction logic ...
      >>>     return result
      # Logs: {"function": "extract_document", "duration_seconds": 2.345, ...}

**`configure_from_yaml(config_path: Path, logger_name: str) -> logging.Logger`**
  Configure logger from YAML configuration file.

  Args:
      config_path: Path to YAML configuration file
      logger_name: Name for the logger

  Returns:
      Configured logger instance

  Configuration format:
      logging:
        version: 1
        level: DEBUG
        format: json
        handlers:
          file:
            enabled: true
            path: logs/app.log
            max_bytes: 10485760
            backup_count: 5
          console:
            enabled: true

  Example:
      >>> logger = configure_from_yaml(Path("log_config.yaml"), __name__)
      >>> logger.info("Logger configured from YAML")
