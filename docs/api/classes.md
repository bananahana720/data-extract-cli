# API Classes Documentation

## Module: `cli.progress_display`

### Class: `SingleFileProgress`

Progress display for single file extraction.

Shows stage-based progress with spinner, progress bar, and ETA.

Attributes:
    file_path: Path to file being processed
    console: Rich Console instance
    verbose: Show detailed stage information
    quiet: Suppress all output

#### Methods:
- **`__init__(self: Any, file_path: Path, console: Optional[Console], verbose: bool, quiet: bool)`**
-   Initialize single file progress display.
-
-   Args:
-       file_path: Path to file being processed
-       console: Optional Rich Console instance
-       verbose: Show detailed progress information
-       quiet: Suppress all output
- **`__enter__(self: Any)`**
-   Enter context manager.
- **`__exit__(self: Any, exc_type: Any, exc_val: Any, exc_tb: Any)`**
-   Exit context manager.
- **`update(self: Any, status: Dict[str, Any]) -> None`**
-   Update progress display with status information.
-
-   Thread-safe: Can be called from worker threads.
-
-   Args:
-       status: Status dict from progress callback with keys:
-           - stage: Current pipeline stage
-           - percentage: Completion percentage (0-100)
-           - message: Optional status message
- **`complete(self: Any, success: bool = True) -> None`**
-   Mark progress as complete.
-
-   Args:
-       success: Whether operation succeeded

### Class: `BatchProgress`

Progress display for batch file processing.

Shows table with per-file status, progress, and overall batch progress.

Attributes:
    file_paths: List of files being processed
    console: Rich Console instance
    verbose: Show detailed information
    quiet: Suppress all output

#### Methods:
- **`__init__(self: Any, file_paths: List[Path], console: Optional[Console], verbose: bool, quiet: bool)`**
-   Initialize batch progress display.
-
-   Args:
-       file_paths: List of file paths being processed
-       console: Optional Rich Console instance
-       verbose: Show detailed progress information
-       quiet: Suppress all output
- **`__enter__(self: Any)`**
-   Enter context manager.
- **`__exit__(self: Any, exc_type: Any, exc_val: Any, exc_tb: Any)`**
-   Exit context manager.
- **`update(self: Any, status: Dict[str, Any]) -> None`**
-   Update progress display with status information.
-
-   Thread-safe: Can be called from worker threads in batch processing.
-
-   Args:
-       status: Status dict from progress callback with keys:
-           - current_file: Name of current file (optional)
-           - batch_percentage: Overall batch percentage (optional)
-           - stage: Current stage for file (optional)
-           - percentage: File progress percentage (optional)
-           - items_processed: Number of files completed (optional)
- **`mark_file_complete(self: Any, file_path: Path, success: bool = True) -> None`**
-   Mark a specific file as complete.
-
-   Thread-safe: Can be called from worker threads.
-
-   Args:
-       file_path: Path to file that completed
-       success: Whether file processed successfully
- **`mark_file_failed(self: Any, file_path: Path, error: str) -> None`**
-   Mark a specific file as failed.
-
-   Thread-safe: Can be called from worker threads.
-
-   Args:
-       file_path: Path to file that failed
-       error: Optional error message
- **`get_summary_table(self: Any) -> Table`**
-   Create summary table for batch progress.
-
-   Returns:
-       Rich Table with per-file status

## Module: `core.interfaces`

### Class: `BaseExtractor`
**Inherits from:** ABC

Abstract base class for all format-specific extractors.

Each file format (DOCX, PDF, PPTX, etc.) implements this interface.
The pipeline uses these extractors without knowing format-specific details.

Contract:
- extract() must return ExtractionResult with success flag
- If extraction fails, return ExtractionResult with success=False and errors
- Never raise exceptions for file-level failures (network issues, corrupted files)
- DO raise exceptions for programming errors (bugs, invalid arguments)

#### Methods:
- **`__init__(self: Any, config: Optional[dict])`**
-   Initialize extractor with optional configuration.
-
-   Args:
-       config: Format-specific configuration options
- **`extract(self: Any, file_path: Path) -> ExtractionResult`**
-   Decorators: abstractmethod
-   Extract content from file.
-
-   This is the core method every extractor must implement.
-
-   Args:
-       file_path: Path to file to extract
-
-   Returns:
-       ExtractionResult with content blocks and metadata
-
-   Note:
-       - If extraction fails, return ExtractionResult with success=False
-       - Populate errors tuple with descriptive error messages
-       - Partial extraction is acceptable (return what you can)
- **`supports_format(self: Any, file_path: Path) -> bool`**
-   Decorators: abstractmethod
-   Check if this extractor can handle the given file.
-
-   Args:
-       file_path: Path to file to check
-
-   Returns:
-       True if this extractor can handle the file
- **`supports_streaming(self: Any) -> bool`**
-   Whether this extractor can process files incrementally.
-
-   Streaming extractors can handle very large files without loading
-   entire file into memory. Not all formats support this.
-
-   Returns:
-       True if streaming is supported
- **`validate_file(self: Any, file_path: Path) -> tuple[bool, list[str]]`**
-   Pre-extraction validation.
-
-   Optional hook for format-specific validation before extraction.
-   This can catch issues early and provide better error messages.
-
-   Args:
-       file_path: Path to file to validate
-
-   Returns:
-       Tuple of (is_valid, error_messages)
- **`get_format_name(self: Any) -> str`**
-   Return human-readable format name.
-
-   Returns:
-       Format name (e.g., "Microsoft Word", "PDF", "PowerPoint")
- **`get_supported_extensions(self: Any) -> list[str]`**
-   Return list of supported file extensions.
-
-   Returns:
-       List of extensions (e.g., [".docx", ".doc"])

### Class: `BaseProcessor`
**Inherits from:** ABC

Abstract base class for content processors.

Processors enrich extracted content. Examples:
- Context linking (create document tree)
- Metadata aggregation (compute statistics)
- Image analysis (detect image types)
- Quality validation (score extraction quality)

Contract:
- process() takes ExtractionResult, returns ProcessingResult
- Processors are composable (output of one is input to next)
- Processors declare dependencies (which processors must run first)
- Failed processing returns ProcessingResult with success=False

#### Methods:
- **`__init__(self: Any, config: Optional[dict])`**
-   Initialize processor with optional configuration.
-
-   Args:
-       config: Processor-specific configuration options
- **`process(self: Any, extraction_result: ExtractionResult) -> ProcessingResult`**
-   Decorators: abstractmethod
-   Process extracted content.
-
-   Args:
-       extraction_result: Result from extraction stage
-
-   Returns:
-       ProcessingResult with enriched content
-
-   Note:
-       - If processing fails, return ProcessingResult with success=False
-       - Partial processing is acceptable (return what you can)
-       - Preserve original content_blocks, add enrichments to metadata
- **`get_dependencies(self: Any) -> list[str]`**
-   Return list of processors that must run before this one.
-
-   This enables the pipeline to order processors correctly.
-   Use processor class names (e.g., ["ContextLinker", "MetadataAggregator"]).
-
-   Returns:
-       List of processor class names
- **`get_processor_name(self: Any) -> str`**
-   Return human-readable processor name.
-
-   Returns:
-       Processor name
- **`is_optional(self: Any) -> bool`**
-   Whether this processor can be skipped if it fails.
-
-   Optional processors don't block the pipeline if they fail.
-
-   Returns:
-       True if processor is optional

### Class: `BaseFormatter`
**Inherits from:** ABC

Abstract base class for output formatters.

Formatters convert processed content to AI-ready formats.
Examples: JSON, Markdown, chunked text, etc.

Contract:
- format() takes ProcessingResult, returns FormattedOutput
- Formatters are independent (can run in parallel)
- Failed formatting returns FormattedOutput with success=False

#### Methods:
- **`__init__(self: Any, config: Optional[dict])`**
-   Initialize formatter with optional configuration.
-
-   Args:
-       config: Formatter-specific configuration options
- **`format(self: Any, processing_result: ProcessingResult) -> FormattedOutput`**
-   Decorators: abstractmethod
-   Convert processed content to target format.
-
-   Args:
-       processing_result: Result from processing stage
-
-   Returns:
-       FormattedOutput with formatted content
-
-   Note:
-       - If formatting fails, return FormattedOutput with success=False
-       - Include additional files (images, metadata) in additional_files
- **`get_format_type(self: Any) -> str`**
-   Decorators: abstractmethod
-   Return format type identifier.
-
-   This is used for file extensions and format selection.
-
-   Returns:
-       Format type (e.g., "json", "markdown", "chunked")
- **`supports_streaming(self: Any) -> bool`**
-   Whether this formatter can write output incrementally.
-
-   Streaming formatters can handle very large documents without loading
-   entire output into memory.
-
-   Returns:
-       True if streaming is supported
- **`get_file_extension(self: Any) -> str`**
-   Return appropriate file extension for this format.
-
-   Returns:
-       File extension (e.g., ".json", ".md")
- **`get_formatter_name(self: Any) -> str`**
-   Return human-readable formatter name.
-
-   Returns:
-       Formatter name

### Class: `BasePipeline`
**Inherits from:** ABC

Abstract base class for extraction pipelines.

Pipelines orchestrate the extraction workflow:
1. Detect file format
2. Extract content
3. Process content (multiple stages)
4. Format output
5. Export results

Contract:
- process_file() takes file path, returns PipelineResult
- Pipeline manages error propagation and recovery
- Pipeline tracks progress and metrics

#### Methods:
- **`process_file(self: Any, file_path: Path) -> 'PipelineResult'`**
-   Decorators: abstractmethod
-   Process a single file through the complete pipeline.
-
-   Args:
-       file_path: Path to file to process
-
-   Returns:
-       PipelineResult with results from all stages
- **`register_extractor(self: Any, format_type: str, extractor: BaseExtractor) -> None`**
-   Decorators: abstractmethod
-   Register a format-specific extractor.
-
-   Args:
-       format_type: Format identifier (e.g., "docx", "pdf")
-       extractor: Extractor instance
- **`add_processor(self: Any, processor: BaseProcessor) -> None`**
-   Decorators: abstractmethod
-   Add a processor to the pipeline.
-
-   Processors are automatically ordered based on dependencies.
-
-   Args:
-       processor: Processor instance
- **`add_formatter(self: Any, formatter: BaseFormatter) -> None`**
-   Decorators: abstractmethod
-   Add an output formatter to the pipeline.
-
-   Multiple formatters can be added to generate multiple output formats.
-
-   Args:
-       formatter: Formatter instance

## Module: `core.models`

### Class: `ContentType`
**Inherits from:** str, Enum

Types of content blocks in extracted documents.

### Class: `ProcessingStage`
**Inherits from:** str, Enum

Stages in the extraction pipeline.

### Class: `Position`

Location information for content within a document.

#### Methods:
- **`__repr__(self: Any) -> str`**

#### Attributes:
- `page`: `Optional[int]`
- `slide`: `Optional[int]`
- `sheet`: `Optional[str]`
- `x`: `Optional[float]`
- `y`: `Optional[float]`
- `width`: `Optional[float]`
- `height`: `Optional[float]`
- `sequence_index`: `Optional[int]`

### Class: `ContentBlock`

A single unit of extracted content.

This is the atomic unit - everything is composed of ContentBlocks.
Immutable to prevent accidental modification during processing.

#### Methods:
- **`__repr__(self: Any) -> str`**

#### Attributes:
- `block_id`: `UUID`
- `block_type`: `ContentType`
- `content`: `str`
- `raw_content`: `Optional[str]`
- `position`: `Optional[Position]`
- `parent_id`: `Optional[UUID]`
- `related_ids`: `tuple[UUID, Ellipsis]`
- `metadata`: `dict[str, Any]`
- `confidence`: `Optional[float]`
- `style`: `dict[str, Any]`

### Class: `ImageMetadata`

Metadata for extracted images.

#### Attributes:
- `image_id`: `UUID`
- `file_path`: `Optional[Path]`
- `format`: `Optional[str]`
- `width`: `Optional[int]`
- `height`: `Optional[int]`
- `color_mode`: `Optional[str]`
- `dpi`: `Optional[int]`
- `alt_text`: `Optional[str]`
- `caption`: `Optional[str]`
- `image_type`: `Optional[str]`
- `content_hash`: `Optional[str]`
- `is_low_quality`: `bool`
- `quality_issues`: `tuple[str, Ellipsis]`

### Class: `TableMetadata`

Metadata for extracted tables.

#### Attributes:
- `table_id`: `UUID`
- `num_rows`: `int`
- `num_columns`: `int`
- `has_header`: `bool`
- `header_row`: `Optional[tuple[str, Ellipsis]]`
- `cells`: `tuple[tuple[str, Ellipsis], Ellipsis]`
- `merged_cells`: `tuple[tuple[int, int, int, int], Ellipsis]`

### Class: `DocumentMetadata`

Document-level metadata extracted or computed.

#### Attributes:
- `source_file`: `Path`
- `file_format`: `str`
- `file_size_bytes`: `int`
- `file_hash`: `Optional[str]`
- `title`: `Optional[str]`
- `author`: `Optional[str]`
- `created_date`: `Optional[datetime]`
- `modified_date`: `Optional[datetime]`
- `subject`: `Optional[str]`
- `keywords`: `tuple[str, Ellipsis]`
- `page_count`: `Optional[int]`
- `word_count`: `Optional[int]`
- `character_count`: `Optional[int]`
- `image_count`: `int`
- `table_count`: `int`
- `language`: `Optional[str]`
- `content_summary`: `Optional[str]`
- `extracted_at`: `datetime`
- `extractor_version`: `Optional[str]`
- `extraction_duration_seconds`: `Optional[float]`

### Class: `ExtractionResult`

Result of extraction stage.

This is what extractors produce - raw content blocks without enrichment.

#### Methods:
- **`__len__(self: Any) -> int`**
-   Number of content blocks.
- **`__repr__(self: Any) -> str`**

#### Attributes:
- `content_blocks`: `tuple[ContentBlock, Ellipsis]`
- `document_metadata`: `DocumentMetadata`
- `images`: `tuple[ImageMetadata, Ellipsis]`
- `tables`: `tuple[TableMetadata, Ellipsis]`
- `success`: `bool`
- `errors`: `tuple[str, Ellipsis]`
- `warnings`: `tuple[str, Ellipsis]`

### Class: `ProcessingResult`

Result of processing stage.

Processing stages take ExtractionResult and enrich it.
This includes context linking, metadata aggregation, quality validation.

#### Attributes:
- `content_blocks`: `tuple[ContentBlock, Ellipsis]`
- `document_metadata`: `DocumentMetadata`
- `images`: `tuple[ImageMetadata, Ellipsis]`
- `tables`: `tuple[TableMetadata, Ellipsis]`
- `processing_stage`: `ProcessingStage`
- `stage_metadata`: `dict[str, Any]`
- `quality_score`: `Optional[float]`
- `quality_issues`: `tuple[str, Ellipsis]`
- `needs_review`: `bool`
- `success`: `bool`
- `errors`: `tuple[str, Ellipsis]`
- `warnings`: `tuple[str, Ellipsis]`

### Class: `FormattedOutput`

Result of formatting stage.

This is what formatters produce - ready for export.

#### Attributes:
- `content`: `str`
- `format_type`: `str`
- `source_document`: `Path`
- `generated_at`: `datetime`
- `additional_files`: `tuple[Path, Ellipsis]`
- `success`: `bool`
- `errors`: `tuple[str, Ellipsis]`
- `warnings`: `tuple[str, Ellipsis]`

### Class: `PipelineResult`

Complete result of running the extraction pipeline.

This is the final output that includes all stages.

#### Methods:
- **`__repr__(self: Any) -> str`**

#### Attributes:
- `source_file`: `Path`
- `extraction_result`: `Optional[ExtractionResult]`
- `processing_result`: `Optional[ProcessingResult]`
- `formatted_outputs`: `tuple[FormattedOutput, Ellipsis]`
- `success`: `bool`
- `failed_stage`: `Optional[ProcessingStage]`
- `started_at`: `datetime`
- `completed_at`: `Optional[datetime]`
- `duration_seconds`: `Optional[float]`
- `all_errors`: `tuple[str, Ellipsis]`
- `all_warnings`: `tuple[str, Ellipsis]`

## Module: `data_extract.chunk.engine`

### Class: `ChunkingConfig`

Configuration for ChunkingEngine (Story 3.3).

Attributes:
    chunk_size: Target chunk size in tokens (128-2048, default 512)
    overlap_pct: Overlap percentage as float (0.0-0.5, default 0.15)
    entity_aware: Enable entity-aware chunking (default False)
    quality_enrichment: Enable quality metadata enrichment (default True)

Example:
    >>> config = ChunkingConfig(chunk_size=1024, overlap_pct=0.25)
    >>> engine = ChunkingEngine(config)

#### Attributes:
- `chunk_size`: `int`
- `overlap_pct`: `float`
- `entity_aware`: `bool`
- `quality_enrichment`: `bool`

### Class: `ChunkingEngine`

Semantic boundary-aware chunking engine for RAG workflows.

Chunks documents at semantic boundaries (sentences, sections) with configurable
size and overlap. Ensures no mid-sentence splits for coherent LLM context.

Design Patterns:
    - Dependency Injection: Accepts SentenceSegmenter for testability
    - Streaming Generator: Yields chunks one at a time (memory-efficient)
    - Deterministic Processing: Same input always produces identical chunks
    - Immutable Output: Chunks are Pydantic models (validation + serialization)
    - PipelineStage Protocol: Implements process(Document, Context) -> List[Chunk]

Attributes:
    segmenter: SentenceSegmenter instance for sentence boundary detection
    chunk_size: Target chunk size in tokens (default: 512)
    overlap_pct: Overlap percentage as float 0.0-0.5 (default: 0.15)
    overlap_tokens: Calculated overlap in tokens (chunk_size * overlap_pct)

Example:
    >>> from src.data_extract.chunk.sentence_segmenter import SentenceSegmenter
    >>> segmenter = SentenceSegmenter()
    >>> engine = ChunkingEngine(segmenter=segmenter, chunk_size=512, overlap_pct=0.15)
    >>> chunks = engine.process(document, context)
    >>> print(f"Generated {len(chunks)} chunks")
    Generated 42 chunks

NFR Compliance:
    - NFR-P3: Chunks 10,000-word document in <2 seconds
    - NFR-P4: 100% deterministic (same input → same chunks)

#### Methods:
- **`__init__(self: Any, config: Optional[ChunkingConfig], segmenter: Optional[Any], chunk_size: Optional[int], overlap_pct: Optional[float], entity_aware: Optional[bool], entity_preserver: Optional[EntityPreserver], quality_enrichment: Optional[bool])`**
-   Initialize chunking engine with configuration.
-
-   Supports two initialization patterns:
-   1. New pattern (Story 3.3): ChunkingEngine(config=ChunkingConfig(...))
-   2. Legacy pattern (Stories 3.1-3.2): ChunkingEngine(segmenter, chunk_size=512, ...)
-
-   Args:
-       config: ChunkingConfig instance (new pattern, Story 3.3). If provided, overrides
-           individual parameters.
-       segmenter: SentenceSegmenter instance for sentence boundary detection.
-           If None, creates default SentenceSegmenter.
-       chunk_size: Target chunk size in tokens. Range: 128-2048. Default: 512.
-       overlap_pct: Overlap percentage as float. Range: 0.0-0.5. Default: 0.15.
-       entity_aware: Enable entity-aware chunking (Story 3.2). Default: False.
-       entity_preserver: EntityPreserver instance. If None and entity_aware=True,
-           creates default EntityPreserver.
-       quality_enrichment: Enable quality metadata enrichment (Story 3.3). Default: True.
-
-   Raises:
-       ValueError: If chunk_size < 1 or overlap_pct < 0.0 or overlap_pct > 1.0
-
-   Example:
-       >>> # New pattern (Story 3.3)
-       >>> config = ChunkingConfig(chunk_size=1024, quality_enrichment=True)
-       >>> engine = ChunkingEngine(config)
-       >>> # Legacy pattern (backward compatibility)
-       >>> engine = ChunkingEngine(segmenter, chunk_size=512, overlap_pct=0.15)
- **`chunk(self: Any, result: ProcessingResult) -> Iterator[Chunk]`**
-   Chunk ProcessingResult and yield enriched chunks (Story 3.3 integration).
-
-   New unified entry point for Story 3.3. Accepts ProcessingResult from Epic 2,
-   extracts normalized text, performs chunking, and enriches with quality metadata.
-
-   Args:
-       result: ProcessingResult from Epic 2 normalize stage
-
-   Yields:
-       Chunk objects with quality-enriched metadata
-
-   Raises:
-       ProcessingError: For recoverable errors (empty doc, segmentation failures)
-
-   Example:
-       >>> config = ChunkingConfig(chunk_size=512, quality_enrichment=True)
-       >>> engine = ChunkingEngine(config)
-       >>> chunks = list(engine.chunk(processing_result))
-       >>> chunks[0].metadata.quality.overall
-       0.93
- **`process(self: Any, document: Document, context: ProcessingContext) -> List[Chunk]`**
-   Process document and return chunks (implements PipelineStage protocol).
-
-   This is the main entry point implementing the PipelineStage[Document, List[Chunk]]
-   protocol. Converts the generator output to a list for compatibility.
-
-   Args:
-       document: Normalized document from Epic 2
-       context: Processing context (config, logger, metrics)
-
-   Returns:
-       List of Chunk objects with metadata
-
-   Raises:
-       ProcessingError: For recoverable errors (empty doc, segmentation failures)
-
-   Example:
-       >>> engine = ChunkingEngine(segmenter, chunk_size=512)
-       >>> chunks = engine.process(document, context)
-       >>> print(f"Generated {len(chunks)} chunks")
- **`chunk_document(self: Any, document: Document, context: ProcessingContext) -> Iterator[Chunk]`**
-   Chunk document at semantic boundaries with configurable size and overlap.
-
-   Implements semantic chunking algorithm:
-   1. Extract sentences using spaCy sentence boundaries
-   2. Build chunks respecting sentence boundaries (no mid-sentence splits)
-   3. Apply sliding window with configured overlap
-   4. Detect and preserve section boundaries when possible
-   5. (Story 3.2) Analyze entity boundaries for entity-aware chunking
-   6. Handle edge cases (very long sentences, micro-sentences, empty docs)
-
-   Args:
-       document: Normalized document from Epic 2 (with text, entities, metadata)
-       context: Processing context (config, logger, metrics)
-
-   Yields:
-       Chunk: Semantic chunks with metadata, entities, and quality scores
-
-   Raises:
-       ProcessingError: For recoverable errors (empty doc, sentence segmentation failures)
-
-   Edge Cases (AC-3.1-6):
-       - Very Long Sentences (>chunk_size): Entire sentence becomes single chunk, warning logged
-       - Micro-Sentences (<10 chars): Combined with adjacent until chunk_size reached
-       - Short Sections (<chunk_size): Section becomes single chunk, no artificial splitting
-       - Empty Documents: Returns empty iterator (no chunks), logs info
-       - No Punctuation: spaCy statistical model handles (no fallback needed)
-
-   Example:
-       >>> engine = ChunkingEngine(chunk_size=512, overlap_pct=0.15)
-       >>> chunks = list(engine.chunk_document(document, context))
-       >>> print(f"Generated {len(chunks)} chunks")
-       Generated 42 chunks
- **`_build_section_hierarchy(self: Any, document: Document, sentences: List[str]) -> Dict[int, str]`**
-   Build section hierarchy map (sentence_idx -> breadcrumb).
-
-   Args:
-       document: Document with structure metadata
-       sentences: List of sentences from document text
-
-   Returns:
-       Dict mapping sentence index to section breadcrumb string
-       (e.g., {0: "Introduction", 5: "Risk Assessment > Controls"})
- **`_detect_section_boundaries(self: Any, document: Document, sentences: List[str]) -> List[int]`**
-   Detect section boundaries from document structure.
-
-   **IMPLEMENTED: AC-3.1-2 completion in Story 3.2**
-
-   Detects section markers from multiple sources:
-   1. ContentBlocks with block_type="heading" from document.structure
-   2. Page break markers from document.structure
-   3. Regex patterns for markdown/numbered headings in text
-
-   Args:
-       document: Document with structure metadata and text
-       sentences: Pre-segmented sentences from document.text (avoids redundant segmentation)
-
-   Returns:
-       List of sentence indices where sections begin (sorted, deterministic)
-
-   Example:
-       >>> # Document with 2 headings
-       >>> section_indices = engine._detect_section_boundaries(document, sentences)
-       >>> section_indices
-       [0, 5]  # Sections start at sentence 0 and 5
- **`_generate_chunks(self: Any, sentences: List[str], section_markers: List[int], entity_refs: List[EntityReference], all_relationships: List[Tuple[str, str, str]], section_hierarchy: Dict[int, str], document: Document, context: ProcessingContext) -> Iterator[Tuple[str, Dict[str, Any]]]`**
-   Generate chunks using sliding window with sentence boundaries.
-
-   Implements chunking algorithm with edge case handling:
-   - Respects sentence boundaries (no mid-sentence splits)
-   - Applies sliding window with overlap
-   - (Story 3.2) Respects entity boundaries when entity_aware=True
-   - (Story 3.2) Populates section context breadcrumbs (AC-3.2-7)
-   - Handles very long sentences (>chunk_size)
-   - Combines micro-sentences (<10 chars)
-   - Preserves section boundaries when possible
-
-   Args:
-       sentences: List of sentence texts
-       section_markers: Sentence indices marking section boundaries
-       entity_refs: List of EntityReference objects (from EntityPreserver)
-       all_relationships: All detected relationships from EntityPreserver
-       section_hierarchy: Map of sentence index to section breadcrumb
-       document: Source document
-       context: Processing context
-
-   Yields:
-       Tuple of (chunk_text, chunk_metadata dict)
- **`_find_nearest_gap(self: Any, boundary_pos: int, entity_gaps: List[int], sentence_positions: List[int]) -> Optional[int]`**
-   Find nearest entity gap to proposed chunk boundary.
-
-   Args:
-       boundary_pos: Proposed chunk boundary position
-       entity_gaps: List of safe gap positions from EntityPreserver
-       sentence_positions: List of sentence start positions
-
-   Returns:
-       Position of nearest gap, or None if no suitable gap found
- **`_build_chunk_metadata(self: Any, chunk_text: str, chunk_start_pos: int, chunk_end_pos: int, entity_refs: List[EntityReference], all_relationships: List[Tuple[str, str, str]], section_context: str) -> Dict[str, Any]`**
-   Build chunk metadata including entity tags, relationships, and section context.
-
-   Args:
-       chunk_text: Chunk text content
-       chunk_start_pos: Character position where chunk starts
-       chunk_end_pos: Character position where chunk ends
-       entity_refs: All entity references from document
-       all_relationships: All detected relationships from EntityPreserver
-       section_context: Section breadcrumb for this chunk position
-
-   Returns:
-       Dict with section_context, entity_tags, entity_relationships
- **`_resolve_document_metadata(self: Any, result: ProcessingResult) -> Metadata`**
-   Resolve metadata object from ProcessingResult (new or brownfield).
- **`_resolve_source_path(self: Any, result: ProcessingResult, metadata: Any) -> Optional[Path]`**
-   Resolve source file path from ProcessingResult or metadata.
- **`_resolve_document_id(self: Any, result: ProcessingResult, source_path: Optional[Path]) -> str`**
-   Determine identifier for document namespace.
- **`_resolve_source_hash(self: Any, metadata: Any) -> str`**
-   Extract file hash from metadata when available.
- **`_resolve_document_type(self: Any, result: ProcessingResult, metadata: Any) -> str`**
-   Resolve document type string.
- **`_resolve_completeness_ratio(self: Any, metadata: Any) -> float`**
-   Resolve completeness ratio from metadata.
- **`_build_metadata_from_legacy(self: Any, result: ProcessingResult, legacy_metadata: Any, source_path: Optional[Path]) -> Metadata`**
-   Build Metadata object from legacy DocumentMetadata structures.
- **`_extract_ocr_confidence(self: Any, result: ProcessingResult, metadata: Any) -> float`**
-   Extract average OCR confidence from ProcessingResult metadata.
-
-   Args:
-       result: ProcessingResult with metadata containing OCR confidence
-
-   Returns:
-       Average OCR confidence (0.0-1.0), defaults to 1.0 if not available
- **`_extract_chunk_entities(self: Any, chunk_text: str, document_entities: List[Entity], chunk_index: int) -> List[Entity]`**
-   Extract entities that appear in this chunk.
-
-   Args:
-       chunk_text: Chunk text to search
-       document_entities: All entities from parent document
-       chunk_index: Position of this chunk in document
-
-   Returns:
-       List of entities found in chunk text
- **`_create_chunk_metadata(self: Any, document: Document, chunk_id: str, position_index: int, token_count: int, word_count: int, context: ProcessingContext, chunk_metadata: Dict[str, Any]) -> Union[Metadata, ChunkMetadata]`**
-   Create metadata for chunk with provenance tracking.
-
-   Args:
-       document: Parent document
-       chunk_id: Unique chunk identifier
-       position_index: Chunk position in document
-       token_count: Number of tokens in chunk
-       word_count: Number of words in chunk
-       context: Processing context
-       chunk_metadata: Dict with entity_tags, entity_relationships, section_context
-
-   Returns:
-       ChunkMetadata if entity_aware enabled, otherwise Metadata (backward compatibility)

## Module: `data_extract.chunk.entity_preserver`

### Class: `EntityReference`

Immutable reference to entity mention within chunk.

Tracks entity position, type, and context for chunk metadata enrichment.
Supports JSON serialization for output formats.

Attributes:
    entity_type: Entity type as string (e.g., "RISK", "CONTROL", "POLICY")
    entity_id: Canonical entity identifier (e.g., "RISK-2024-001")
    start_pos: Character offset where entity starts in text
    end_pos: Character offset where entity ends in text
    is_partial: True if entity split across chunk boundary
    context_snippet: ±20 chars around entity for context

Example:
    >>> ref = EntityReference(
    ...     entity_type="RISK",
    ...     entity_id="RISK-001",
    ...     start_pos=100,
    ...     end_pos=120,
    ...     is_partial=False,
    ...     context_snippet="...Data breach risk..."
    ... )
    >>> ref.to_dict()
    {'entity_type': 'RISK', 'entity_id': 'RISK-001', ...}

#### Methods:
- **`to_dict(self: Any) -> Dict[str, Any]`**
-   Convert to JSON-serializable dictionary.
-
-   Returns:
-       Dict with all EntityReference fields

#### Attributes:
- `entity_type`: `str`
- `entity_id`: `str`
- `start_pos`: `int`
- `end_pos`: `int`
- `is_partial`: `bool`
- `context_snippet`: `str`

### Class: `EntityPreserver`

Analyzes entity boundaries to preserve complete entity definitions in chunks.

Implements entity-aware chunking logic:
1. analyze_entities(): Build EntityReference map from Epic 2 entities
2. find_entity_gaps(): Identify safe split zones between entities
3. detect_entity_relationships(): Find relationship patterns (e.g., "mitigated by")

Design:
    - Deterministic processing (entities sorted by start_pos)
    - Streaming-compatible (no buffering entire document)
    - Graceful degradation (handles overlapping entities, missing data)

Example:
    >>> preserver = EntityPreserver()
    >>> entities = [Entity(type="RISK", id="RISK-001", ...)]
    >>> entity_refs = preserver.analyze_entities(text, entities)
    >>> gaps = preserver.find_entity_gaps(entity_refs, text)
    >>> relationships = preserver.detect_entity_relationships(text, entity_refs)

#### Methods:
- **`__init__(self: Any) -> None`**
-   Initialize EntityPreserver.
- **`analyze_entities(self: Any, text: str, entities: List[Entity]) -> List[EntityReference]`**
-   Analyze entity boundaries and build EntityReference map.
-
-   Extracts entity positions, types, and context snippets for chunk metadata.
-   Sorts entities by start position for deterministic processing (AC-3.2-8).
-
-   Args:
-       text: Full document text
-       entities: Entity list from Epic 2 ProcessingResult
-
-   Returns:
-       List of EntityReference objects sorted by start_pos
-
-   Example:
-       >>> entities = [
-       ...     Entity(type=EntityType.RISK, id="RISK-001", text="Data breach",
-       ...            confidence=0.95, location={"start": 100, "end": 120})
-       ... ]
-       >>> entity_refs = preserver.analyze_entities(text, entities)
-       >>> len(entity_refs)
-       1
- **`find_entity_gaps(self: Any, entities: List[EntityReference], text: str) -> List[int]`**
-   Identify character positions between entities (safe split zones).
-
-   Analyzes entity positions to find gaps where chunk boundaries can be placed
-   without splitting entity definitions. Returns character offsets in text.
-
-   **Integration**: Called by ChunkingEngine._generate_chunks() during entity-aware
-   boundary adjustment (line 677). When a chunk reaches target size, the engine
-   searches for the nearest entity gap within ±20% of chunk_size to adjust the
-   boundary, preventing entity splits (AC-3.2-1, AC-3.2-4).
-
-   Args:
-       entities: Sorted list of EntityReference objects
-       text: Full document text
-
-   Returns:
-       List of character offsets suitable for chunk boundaries
-
-   Example:
-       >>> # Entity 1 at 100-120, Entity 2 at 200-220
-       >>> gaps = preserver.find_entity_gaps(entity_refs, text)
-       >>> # Returns positions between 120 and 200
- **`detect_entity_relationships(self: Any, text: str, entities: List[EntityReference]) -> List[Tuple[str, str, str]]`**
-   Detect entity relationship patterns in text.
-
-   Searches for relationship keywords connecting entity pairs
-   (e.g., "RISK-001 mitigated by CTRL-042"). Returns relationship triples.
-
-   Args:
-       text: Full document text
-       entities: List of EntityReference objects
-
-   Returns:
-       List of (entity1_id, relation_type, entity2_id) triples
-
-   Example:
-       >>> # Text: "RISK-001 mitigated by CTRL-042"
-       >>> relationships = preserver.detect_entity_relationships(text, entity_refs)
-       >>> relationships[0]
-       ('RISK-001', 'mitigated_by', 'CTRL-042')

## Module: `data_extract.chunk.metadata_enricher`

### Class: `MetadataEnricher`

Enriches chunks with comprehensive metadata and quality scores.

Calculates quality metrics using textstat for readability, lexical overlap
for coherence, and source metadata for OCR/completeness. Generates quality
flags for targeted manual review.

Designed for dependency injection (textstat_library parameter) to enable
testing with mocked readability calculations.

Example:
    >>> enricher = MetadataEnricher()
    >>> chunk = Chunk(id="test_001", text="Sample text.", ...)
    >>> source_metadata = {
    ...     "ocr_confidence": 0.99,
    ...     "completeness": 0.95,
    ...     "source_hash": "abc123",
    ...     "document_type": "report"
    ... }
    >>> enriched = enricher.enrich_chunk(chunk, source_metadata)
    >>> enriched.metadata.quality.overall
    0.93

#### Methods:
- **`__init__(self: Any, textstat_library: Any = textstat) -> None`**
-   Initialize enricher with textstat library.
-
-   Args:
-       textstat_library: Textstat module for readability metrics (default: textstat).
-           Used for dependency injection in tests.
- **`enrich_chunk(self: Any, chunk: Chunk, source_metadata: Dict[str, Any]) -> Chunk`**
-   Enrich chunk with quality metadata and scores.
-
-   Main entry point for metadata enrichment. Calculates all quality metrics,
-   creates QualityScore object, and returns new Chunk with enriched metadata.
-   Maintains immutability (frozen dataclasses).
-
-   Args:
-       chunk: Basic chunk from ChunkingEngine
-       source_metadata: Source document metadata from ProcessingResult
-           Expected fields: ocr_confidence, completeness, source_hash, document_type
-
-   Returns:
-       New Chunk instance with enriched ChunkMetadata including QualityScore
-
-   Example:
-       >>> enricher = MetadataEnricher()
-       >>> chunk = Chunk(id="test", text="Clean text.", ...)
-       >>> source_meta = {"ocr_confidence": 0.99, "completeness": 0.98, ...}
-       >>> enriched = enricher.enrich_chunk(chunk, source_meta)
-       >>> enriched.metadata.quality.is_high_quality()
-       True
- **`_calculate_readability(self: Any, text: str) -> Tuple[float, float]`**
-   Calculate readability scores using textstat library.
-
-   Uses Flesch-Kincaid Grade Level and Gunning Fog Index. Handles edge
-   cases (empty text, very short text) gracefully.
-
-   Args:
-       text: Text to analyze
-
-   Returns:
-       Tuple of (flesch_kincaid_score, gunning_fog_score)
-       Returns (0.0, 0.0) for empty text.
-
-   Example:
-       >>> enricher = MetadataEnricher()
-       >>> fk, gf = enricher._calculate_readability("Simple text. Easy read.")
-       >>> fk < 8.0  # Low grade level
-       True
- **`_calculate_coherence(self: Any, text: str) -> float`**
-   Calculate coherence using sentence-to-sentence lexical overlap heuristic.
-
-   Simple lexical overlap: For each adjacent sentence pair, calculate
-   intersection ∩ / union ∪ of words. Average across all pairs.
-
-   This is a temporary heuristic for Epic 3. Will be replaced with
-   TF-IDF cosine similarity in Epic 4.
-
-   Args:
-       text: Text to analyze
-
-   Returns:
-       Coherence score (0.0-1.0)
-       1.0 for single sentence (no comparison needed)
-       0.0 for empty text
-
-   Example:
-       >>> enricher = MetadataEnricher()
-       >>> # High overlap (repeated words)
-       >>> coherence = enricher._calculate_coherence(
-       ...     "The cat sat. The cat ran. The cat jumped."
-       ... )
-       >>> coherence > 0.5
-       True
- **`_calculate_overall_quality(self: Any, quality_components: Dict[str, float]) -> float`**
-   Calculate overall quality as weighted composite score.
-
-   Weights:
-       - OCR confidence: 40% (foundation metric)
-       - Completeness: 30% (entity preservation critical)
-       - Coherence: 20% (semantic flow)
-       - Readability: 10% (normalized, low priority for technical docs)
-
-   Args:
-       quality_components: Dict with ocr_confidence, completeness, coherence,
-           readability_normalized (all 0.0-1.0)
-
-   Returns:
-       Overall quality score (0.0-1.0)
-
-   Example:
-       >>> enricher = MetadataEnricher()
-       >>> overall = enricher._calculate_overall_quality({
-       ...     "ocr_confidence": 0.95,
-       ...     "completeness": 0.90,
-       ...     "coherence": 0.80,
-       ...     "readability_normalized": 0.85
-       ... })
-       >>> 0.85 <= overall <= 0.95
-       True
- **`_detect_quality_flags(self: Any, quality: QualityScore, text: str) -> List[str]`**
-   Detect specific quality issues and generate flags.
-
-   Flag detection logic:
-       - low_ocr: OCR confidence < 0.95
-       - incomplete_extraction: Completeness < 0.90
-       - high_complexity: Flesch-Kincaid grade level > 15.0
-       - gibberish: >30% non-alphabetic characters
-
-   Args:
-       quality: QualityScore with calculated metrics
-       text: Original text for gibberish detection
-
-   Returns:
-       List of applicable quality flags (empty if no issues)
-
-   Example:
-       >>> enricher = MetadataEnricher()
-       >>> quality = QualityScore(
-       ...     readability_flesch_kincaid=18.0,  # High complexity
-       ...     ocr_confidence=0.87,  # Low OCR
-       ...     completeness=0.85,  # Incomplete
-       ...     ...
-       ... )
-       >>> flags = enricher._detect_quality_flags(quality, "Normal text")
-       >>> "low_ocr" in flags and "incomplete_extraction" in flags
-       True
- **`_calculate_word_token_counts(self: Any, text: str) -> Tuple[int, int]`**
-   Calculate word count and token count.
-
-   Word count: Whitespace split (simple, fast)
-   Token count: len(text) / 4 heuristic (OpenAI approximation)
-
-   Args:
-       text: Text to count
-
-   Returns:
-       Tuple of (word_count, token_count)
-
-   Example:
-       >>> enricher = MetadataEnricher()
-       >>> words, tokens = enricher._calculate_word_token_counts("Hello world test")
-       >>> words
-       3
-       >>> tokens
-       3

## Module: `data_extract.chunk.models`

### Class: `ChunkMetadata`

Chunk-level metadata for entity-aware chunking and quality scoring (Stories 3.2-3.3).

Extends document-level Metadata with chunk-specific fields for
entity tracking, section context, relationship preservation, and quality metrics.
Immutability enforced per ADR-001 to prevent pipeline state corruption.

Story 3.2 fields: entity_tags, section_context, entity_relationships
Story 3.3 fields: quality, source_hash, document_type, word_count, token_count,
                  created_at, processing_version

Attributes:
    entity_tags: List of EntityReference objects for entities in chunk (AC-3.3-3)
    section_context: Section breadcrumb showing chunk location (AC-3.3-2)
    entity_relationships: Relationship triples within chunk (entity1_id, relation_type, entity2_id)
    source_metadata: Original document metadata for provenance tracking
    quality: Composite quality metrics (readability, OCR, completeness, coherence) (AC-3.3-4, AC-3.3-5)
    source_hash: SHA-256 hash of original source file for immutability verification (AC-3.3-1)
    document_type: Document classification from Epic 2 (report, matrix, export, image) (AC-3.3-1)
    word_count: Number of words in chunk (whitespace split) (AC-3.3-7)
    token_count: Estimated token count (len/4 heuristic) for LLM billing (AC-3.3-7)
    created_at: Processing timestamp for audit trail (AC-3.3-1)
    processing_version: Tool version for reproducibility (AC-3.3-1)

Example:
    >>> chunk_meta = ChunkMetadata(
    ...     entity_tags=[
    ...         EntityReference(
    ...             entity_type="RISK",
    ...             entity_id="RISK-001",
    ...             start_pos=100,
    ...             end_pos=120,
    ...             is_partial=False,
    ...             context_snippet="...Data breach risk..."
    ...         )
    ...     ],
    ...     section_context="Risk Assessment > Identified Risks",
    ...     entity_relationships=[("RISK-001", "mitigated_by", "CTRL-042")],
    ...     source_metadata=document.metadata,
    ...     quality=QualityScore(
    ...         readability_flesch_kincaid=8.5,
    ...         readability_gunning_fog=10.2,
    ...         ocr_confidence=0.99,
    ...         completeness=0.95,
    ...         coherence=0.88,
    ...         overall=0.93,
    ...         flags=[]
    ...     ),
    ...     source_hash="a3b2c1...",
    ...     document_type="report",
    ...     word_count=150,
    ...     token_count=200,
    ...     created_at=datetime.now(),
    ...     processing_version="1.0.0"
    ... )
    >>> chunk_meta.to_dict()
    {'entity_tags': [...], 'section_context': '...', 'quality': {...}, ...}

#### Methods:
- **`to_dict(self: Any) -> Dict[str, Any]`**
-   Convert to JSON-serializable dictionary.
-
-   AC-3.4-3: Fields never null - use empty string/array/dict for missing data.
-
-   Returns:
-       Dict with all ChunkMetadata fields JSON-serializable (Story 3.2 + 3.3 + 3.4 fields)

#### Attributes:
- `entity_tags`: `List[EntityReference]`
- `section_context`: `str`
- `entity_relationships`: `List[Tuple[str, str, str]]`
- `source_metadata`: `Optional[Metadata]`
- `quality`: `Optional[QualityScore]`
- `source_hash`: `Optional[str]`
- `document_type`: `Optional[str]`
- `word_count`: `int`
- `token_count`: `int`
- `created_at`: `Optional[datetime]`
- `processing_version`: `str`
- `source_file`: `Optional[Path]`
- `config_snapshot`: `Dict[str, Any]`

## Module: `data_extract.chunk.quality`

### Class: `QualityScore`

Quality metrics for a text chunk.

Immutable quality score combining readability, OCR confidence, completeness,
coherence, and specific quality issue flags. Designed for RAG chunk filtering
and prioritization workflows.

Immutability enforced per ADR-001 to prevent pipeline state corruption.

Attributes:
    readability_flesch_kincaid: Flesch-Kincaid Grade Level (0.0-30.0).
        Lower is more readable. Grade 8 = 8th grade reading level.
    readability_gunning_fog: Gunning Fog Index (0.0-30.0).
        Lower is more readable. Measures years of education needed.
    ocr_confidence: OCR accuracy confidence (0.0-1.0).
        Propagated from Epic 2 source metadata. 1.0 = perfect OCR.
    completeness: Entity preservation rate (0.0-1.0).
        Calculated from Story 3.2 entity analysis. 1.0 = all entities intact.
    coherence: Sentence-to-sentence semantic overlap (0.0-1.0).
        Simple lexical overlap heuristic. 1.0 = high coherence.
    overall: Weighted composite quality score (0.0-1.0).
        Weighted average: OCR (40%), completeness (30%), coherence (20%), readability (10%).
        1.0 = perfect quality, 0.0 = unusable.
    flags: Quality issue flags for targeted review.
        Possible values: 'low_ocr', 'incomplete_extraction', 'high_complexity', 'gibberish'.
        Empty list if no issues detected.

Example:
    >>> quality = QualityScore(
    ...     readability_flesch_kincaid=8.5,
    ...     readability_gunning_fog=10.2,
    ...     ocr_confidence=0.99,
    ...     completeness=0.95,
    ...     coherence=0.88,
    ...     overall=0.93,
    ...     flags=[]
    ... )
    >>> quality.is_high_quality()
    True
    >>> quality.to_dict()
    {'readability_flesch_kincaid': 8.5, 'readability_gunning_fog': 10.2, ...}

Raises:
    ValueError: If scores outside valid ranges (quality 0.0-1.0, readability 0.0-30.0).

#### Methods:
- **`__post_init__(self: Any) -> None`**
-   Validate score ranges after initialization.
-
-   Ensures all quality scores in 0.0-1.0 range and readability scores in 0.0-30.0 range.
-
-   Raises:
-       ValueError: If any score outside valid range.
- **`to_dict(self: Any) -> Dict[str, Any]`**
-   Convert to JSON-serializable dictionary.
-
-   Returns:
-       Dict with all QualityScore fields in JSON-compatible format.
-
-   Example:
-       >>> quality = QualityScore(..., flags=["low_ocr"])
-       >>> quality.to_dict()
-       {'readability_flesch_kincaid': 12.3, 'flags': ['low_ocr'], ...}
- **`is_high_quality(self: Any) -> bool`**
-   Check if chunk meets high-quality threshold.
-
-   Uses overall score >= 0.75 threshold for RAG chunk filtering.
-
-   Returns:
-       True if overall quality >= 0.75, False otherwise.
-
-   Example:
-       >>> high_quality_chunk = QualityScore(..., overall=0.92, ...)
-       >>> high_quality_chunk.is_high_quality()
-       True
-       >>> low_quality_chunk = QualityScore(..., overall=0.68, ...)
-       >>> low_quality_chunk.is_high_quality()
-       False

#### Attributes:
- `readability_flesch_kincaid`: `float`
- `readability_gunning_fog`: `float`
- `ocr_confidence`: `float`
- `completeness`: `float`
- `coherence`: `float`
- `overall`: `float`
- `flags`: `List[str]`

## Module: `data_extract.chunk.sentence_segmenter`

### Class: `SentenceSegmenter`

Sentence segmentation using spaCy for semantic chunking.

Wraps get_sentence_boundaries() utility to provide a clean interface
for dependency injection in ChunkingEngine.

Example:
    >>> segmenter = SentenceSegmenter()
    >>> sentences = segmenter.segment("First sentence. Second sentence.")
    >>> print(sentences)
    ['First sentence.', 'Second sentence.']

#### Methods:
- **`segment(self: Any, text: str) -> List[str]`**
-   Segment text into sentences using spaCy.
-
-   Args:
-       text: Input text to segment
-
-   Returns:
-       List of sentence strings
-
-   Raises:
-       ValueError: If text is empty or whitespace-only
-       OSError: If en_core_web_md model is not installed

## Module: `data_extract.core.exceptions`

### Class: `DataExtractError`
**Inherits from:** Exception

Base exception for all data extraction tool errors.

All custom exceptions in the tool inherit from this base class.
This allows catching all tool-specific errors with a single except clause.

Example:
    >>> try:
    ...     # Some pipeline operation
    ...     pass
    ... except DataExtractError as e:
    ...     # Catches all tool-specific errors
    ...     print(f"Tool error: {e}")

### Class: `ProcessingError`
**Inherits from:** DataExtractError

Recoverable error during document processing.

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

### Class: `CriticalError`
**Inherits from:** DataExtractError

Unrecoverable error requiring immediate halt.

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

### Class: `ConfigurationError`
**Inherits from:** CriticalError

Configuration-related critical error.

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

### Class: `ExtractionError`
**Inherits from:** ProcessingError

Document extraction failure (recoverable).

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

### Class: `ValidationError`
**Inherits from:** ProcessingError

Data validation failure (recoverable).

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

## Module: `data_extract.core.models`

### Class: `ContentType`
**Inherits from:** str, Enum

Content block types for document structure.

Intentional subset of brownfield ContentType for greenfield architecture.
Includes essential types for Epic 3 chunking and future expansion.

Note: UNKNOWN added for graceful degradation when content type cannot
be determined. Prevents extraction failures on unrecognized content.

Future expansion candidates (from brownfield): QUOTE, CHART, LIST_ITEM,
TABLE_CELL, METADATA, FOOTNOTE, COMMENT, HYPERLINK.

### Class: `Position`
**Inherits from:** BaseModel

Position information for content blocks.

#### Attributes:
- `page`: `int`
- `sequence_index`: `int`

### Class: `ContentBlock`
**Inherits from:** BaseModel

Content block representing a structural element in a document.

#### Attributes:
- `block_type`: `ContentType`
- `content`: `str`
- `position`: `Position`
- `metadata`: `Dict[str, Any]`

### Class: `EntityType`
**Inherits from:** str, Enum

Audit domain entity types.

Six entity types recognized in audit documents for consistent
naming and cross-reference resolution.

Values:
    PROCESS: Business or operational processes
    RISK: Identified risks or risk factors
    CONTROL: Control measures or procedures
    REGULATION: Regulatory requirements or standards
    POLICY: Organizational policies or guidelines
    ISSUE: Identified issues, findings, or audit observations

### Class: `DocumentType`
**Inherits from:** str, Enum

Document classification types for schema standardization.

Four document types for applying type-specific transformations and
schema standardization across different source formats.

Values:
    REPORT: Narrative documents (Word, PDF) with sections and headings
    MATRIX: Tabular documents (Excel) like control matrices or risk registers
    EXPORT: System exports (Archer GRC HTML/XML) with structured fields
    IMAGE: Scanned documents or images requiring OCR processing

### Class: `QualityFlag`
**Inherits from:** str, Enum

Quality validation flags for OCR and extraction issues.

Quality flags used by validation pipeline to mark documents
requiring manual review or quarantine.

Values:
    LOW_OCR_CONFIDENCE: OCR confidence score below threshold (default 95%)
    MISSING_IMAGES: Referenced images not found or failed to extract
    INCOMPLETE_EXTRACTION: Extraction incomplete or partially failed
    COMPLEX_OBJECTS: Complex objects (OLE, charts, diagrams) that can't be extracted

### Class: `Entity`
**Inherits from:** BaseModel

Domain entity extracted from documents.

Represents entities from the audit domain: risk, control, policy,
process, regulation, issue. Used by Document and Chunk models.

Attributes:
    type: Entity type from EntityType enum
    id: Canonical entity identifier (e.g., 'Risk-123')
    text: Entity text content as it appears in document
    confidence: Confidence score (0.0-1.0) for entity extraction
    location: Character position in document (start and end indices)

#### Attributes:
- `type`: `EntityType`
- `id`: `str`
- `text`: `str`
- `confidence`: `float`
- `location`: `Dict[str, int]`

### Class: `Metadata`
**Inherits from:** BaseModel

Provenance and quality tracking metadata.

Embedded in Document and Chunk models to track processing history,
quality metrics, and audit trail information.

Note: frozen=True ensures metadata immutability. Metadata should be
created once during processing and never modified. This prevents
pipeline state corruption and ensures audit trail integrity.

Attributes:
    source_file: Path to original source file
    file_hash: SHA-256 hash of source file for integrity verification
    processing_timestamp: When the document/chunk was processed
    tool_version: Version of the data extraction tool
    config_version: Version of the configuration used
    document_type: Document classification (report, matrix, export, image)
    document_subtype: Document subtype (e.g., Archer module variations)
    quality_scores: Quality metrics dict (e.g., {'ocr_confidence': 0.95})
    quality_flags: List of quality warnings/flags (string values from QualityFlag enum)
    ocr_confidence: Per-page OCR confidence scores (page_num -> confidence 0.0-1.0)
    completeness_ratio: Extraction completeness ratio (0.0-1.0, extracted/total elements)
    entity_tags: List of canonical entity IDs for RAG retrieval filtering
    entity_counts: Count of entities by type (e.g., {'risk': 5, 'control': 3})
    config_snapshot: Full configuration snapshot for reproducibility (all processing settings)
    validation_report: Serialized ValidationReport with quality validation results

#### Methods:
- **`validate_document_type(cls: Any, v: Any) -> Optional[Union[DocumentType, str]]`**
-   Decorators: field_validator('document_type', mode='before'), classmethod
-   Validate and optionally convert document_type.
-
-   Accepts DocumentType enum, string, or None for backwards compatibility.
-
-   Args:
-       v: Value to validate
-
-   Returns:
-       DocumentType enum, string (for legacy support), or None

#### Attributes:
- `source_file`: `Path`
- `file_hash`: `str`
- `processing_timestamp`: `datetime`
- `tool_version`: `str`
- `config_version`: `str`
- `document_type`: `Optional[Union[DocumentType, str]]`
- `document_subtype`: `Optional[str]`
- `quality_scores`: `Dict[str, float]`
- `ocr_confidence`: `Dict[int, float]`
- `completeness_ratio`: `Optional[float]`
- `quality_flags`: `List[str]`
- `entity_tags`: `List[str]`
- `entity_counts`: `Dict[str, int]`
- `entity_relationships`: `List[Tuple[str, str, str]]`
- `section_context`: `Optional[str]`
- `config_snapshot`: `Dict[str, Any]`
- `validation_report`: `Dict[str, Any]`

### Class: `ValidationReport`
**Inherits from:** BaseModel

OCR and extraction quality validation report.

Generated by QualityValidator to assess OCR confidence and extraction
completeness. Used to determine quarantine recommendations.

Attributes:
    quarantine_recommended: Whether document should be quarantined for manual review
    confidence_scores: Per-page OCR confidence scores (page_num -> confidence 0.0-1.0)
    quality_flags: List of quality issues detected (from QualityFlag enum)
    extraction_gaps: Descriptions of detected extraction gaps or issues
    document_average_confidence: Document-level average OCR confidence (0.0-1.0)
    scanned_pdf_detected: Whether document was detected as scanned (vs native PDF)
    completeness_passed: Whether completeness ratio meets threshold (>=0.90 default)
    missing_images_count: Count of images without alt text detected
    complex_objects_count: Count of complex objects (OLE, charts, diagrams) detected

#### Attributes:
- `quarantine_recommended`: `bool`
- `confidence_scores`: `Dict[int, float]`
- `quality_flags`: `List[QualityFlag]`
- `extraction_gaps`: `List[str]`
- `document_average_confidence`: `Optional[float]`
- `scanned_pdf_detected`: `Optional[bool]`
- `completeness_passed`: `bool`
- `missing_images_count`: `int`
- `complex_objects_count`: `int`

### Class: `Document`
**Inherits from:** BaseModel

Processed document model.

Type contract: Extract → Normalize stage.
Represents a document after extraction with raw/cleaned text,
extracted entities, and processing metadata.

Attributes:
    id: Unique document identifier
    text: Document text content (raw or normalized)
    entities: List of extracted entities
    metadata: Processing metadata and quality tracking
    structure: Document structure metadata (e.g., sections, pages)

#### Attributes:
- `id`: `str`
- `text`: `str`
- `entities`: `List[Entity]`
- `metadata`: `Metadata`
- `structure`: `Dict[str, Any]`

### Class: `Chunk`
**Inherits from:** BaseModel

Semantic chunk for RAG (Retrieval-Augmented Generation).

Type contract: Chunk → Semantic stage.
Represents a semantically coherent chunk with quality scoring,
readability metrics, and full provenance tracking.

Attributes:
    id: Unique chunk identifier (format: {source}_{index:03d})
    text: Chunk text content
    document_id: Reference to parent document
    position_index: Position in original document (0-based)
    token_count: Number of tokens in chunk
    word_count: Number of words in chunk
    entities: List of entities in this chunk
    section_context: Section/heading context for this chunk
    quality_score: Overall quality score (0.0-1.0)
    readability_scores: Readability metrics dict (e.g., flesch_reading_ease)
    metadata: Processing metadata and quality tracking (Metadata or ChunkMetadata for entity-aware chunks)

#### Methods:
- **`to_dict(self: Any) -> Dict[str, Any]`**
-   Convert chunk to dictionary (Pydantic v2 compatibility wrapper).
-
-   Returns:
-       Dict representation of chunk with all fields JSON-serializable

#### Attributes:
- `id`: `str`
- `text`: `str`
- `document_id`: `str`
- `position_index`: `int`
- `token_count`: `int`
- `word_count`: `int`
- `entities`: `List[Entity]`
- `section_context`: `str`
- `quality_score`: `float`
- `readability_scores`: `Dict[str, float]`
- `metadata`: `Union[Metadata, Any]`

### Class: `ProcessingResult`
**Inherits from:** BaseModel

Output from Epic 2 normalization stage (Story 3.3 integration).

Represents normalized document content ready for chunking. Contains
extracted content blocks, entities, and quality metadata from Epic 2.

Attributes:
    file_path: Path to source document
    document_type: Classification from Epic 2 (report, matrix, export, image)
    content_blocks: Normalized content blocks (text, tables, images)
    entities: Extracted entities from document
    metadata: Document-level metadata (OCR confidence, completeness, etc.)

Example:
    >>> result = ProcessingResult(
    ...     file_path=Path("/docs/report.pdf"),
    ...     document_type=DocumentType.REPORT,
    ...     content_blocks=[ContentBlock(...)],
    ...     entities=[],
    ...     metadata=Metadata(ocr_confidence=0.99, completeness=0.98)
    ... )

#### Attributes:
- `file_path`: `Path`
- `document_type`: `DocumentType`
- `content_blocks`: `List[ContentBlock]`
- `entities`: `List[Entity]`
- `metadata`: `Metadata`

### Class: `ProcessingContext`
**Inherits from:** BaseModel

Shared pipeline state passed through all stages.

Carries configuration, logger, and metrics through the entire
pipeline to ensure deterministic processing and audit trail.

Attributes:
    config: Configuration dictionary (three-tier precedence: CLI > env > YAML > defaults)
    logger: Structured logger instance for audit trail
    metrics: Metrics accumulation dictionary

#### Attributes:
- `config`: `Dict[str, Any]`
- `logger`: `Optional[Any]`
- `metrics`: `Dict[str, Any]`

## Module: `data_extract.core.pipeline`

### Class: `PipelineStage`
**Inherits from:** Protocol, Generic[Input, Output]

Protocol defining the contract for all pipeline stages.

All pipeline stages must implement this protocol to ensure consistent
interfaces and enable type-safe pipeline orchestration.

Type Parameters:
    Input: Type of input data accepted by this stage
    Output: Type of output data produced by this stage

Example:
    >>> class MyStage:
    ...     def process(self, input_data: str, context: ProcessingContext) -> int:
    ...         return len(input_data)
    ...
    >>> # MyStage implements PipelineStage[str, int]

Contract Requirements:
    1. process() method must accept input_data of type Input
    2. process() method must accept context: ProcessingContext
    3. process() method must return data of type Output
    4. Stages should be stateless - all state in ProcessingContext
    5. Stages should be deterministic for audit reproducibility

#### Methods:
- **`process(self: Any, input_data: Input, context: ProcessingContext) -> Output`**
-   Process input data and return transformed output.
-
-   Args:
-       input_data: Input data to process (type defined by Input type parameter)
-       context: Shared processing context (config, logger, metrics)
-
-   Returns:
-       Processed output data (type defined by Output type parameter)
-
-   Raises:
-       ProcessingError: For recoverable errors (log, skip file, continue batch)
-       CriticalError: For unrecoverable errors (halt processing immediately)

### Class: `Pipeline`

Pipeline orchestrator that chains multiple stages together.

Orchestrates execution of multiple pipeline stages by passing the output
of each stage as input to the next stage. Ensures ProcessingContext is
propagated through all stages.

Attributes:
    stages: List of pipeline stages to execute in sequence

Example:
    >>> # Define mock stages
    >>> class StringToInt:
    ...     def process(self, data: str, context: ProcessingContext) -> int:
    ...         return len(data)
    ...
    >>> class IntToFloat:
    ...     def process(self, data: int, context: ProcessingContext) -> float:
    ...         return float(data) * 1.5
    ...
    >>> # Create and run pipeline
    >>> pipeline = Pipeline([StringToInt(), IntToFloat()])
    >>> context = ProcessingContext()
    >>> result = pipeline.process("hello", context)
    >>> print(result)  # 7.5 (len("hello") = 5, 5 * 1.5 = 7.5)

#### Methods:
- **`__init__(self: Any, stages: List[PipelineStage]) -> None`**
-   Initialize pipeline with list of stages.
-
-   Args:
-       stages: List of pipeline stages to execute in sequence.
-              Each stage's output type must match next stage's input type.
- **`process(self: Any, initial_input: Any, context: ProcessingContext) -> Any`**
-   Execute all pipeline stages in sequence.
-
-   Chains stages by passing output of stage N as input to stage N+1.
-   ProcessingContext is passed to all stages for config, logging, and metrics.
-
-   Args:
-       initial_input: Input data for first pipeline stage
-       context: Shared processing context (config, logger, metrics)
-
-   Returns:
-       Output from the final pipeline stage
-
-   Raises:
-       ProcessingError: If a recoverable error occurs in any stage
-       CriticalError: If an unrecoverable error occurs in any stage
-
-   Example:
-       >>> pipeline = Pipeline([ExtractStage(), NormalizeStage(), ChunkStage()])
-       >>> context = ProcessingContext(config={"chunk_size": 512})
-       >>> chunks = pipeline.process(raw_document, context)

## Module: `data_extract.extract.adapter`

### Class: `PipelineStage`
**Inherits from:** Protocol[TInput, TOutput]

Protocol for pipeline stages in greenfield architecture.

All pipeline stages must implement this protocol to ensure type-safe
composition and compatibility with the greenfield pipeline runner.

Type Parameters:
    TInput: Input type (e.g., Path for extractors)
    TOutput: Output type (e.g., Document for extractors)

#### Methods:
- **`process(self: Any, input_data: TInput) -> TOutput`**
-   Process input and return output.
-
-   Args:
-       input_data: Input to process (type specified by TInput)
-
-   Returns:
-       Processed output (type specified by TOutput)
-
-   Raises:
-       FileNotFoundError: If input file doesn't exist
-       ValidationError: If output model fails Pydantic validation
-       RuntimeError: If processing fails critically

### Class: `ExtractorAdapter`

Base adapter for wrapping brownfield extractors.

Converts brownfield ExtractionResult to greenfield Document model.
Provides common utilities for all format-specific adapters.

Attributes:
    extractor: Brownfield extractor instance (e.g., PdfExtractor)
    format_name: Human-readable format name (e.g., "PDF", "DOCX")

#### Methods:
- **`__init__(self: Any, extractor: Any, format_name: str) -> None`**
-   Initialize adapter with brownfield extractor.
-
-   Args:
-       extractor: Brownfield extractor instance with extract(Path) method
-       format_name: Human-readable format name for metadata
- **`process(self: Any, input_data: Path) -> Document`**
-   Extract and convert file to greenfield Document.
-
-   Implements PipelineStage protocol. Delegates extraction to brownfield
-   extractor, then converts result to greenfield Document model.
-
-   Args:
-       input_data: Path to file to extract
-
-   Returns:
-       Document: Greenfield document model with full metadata
-
-   Raises:
-       FileNotFoundError: If input file doesn't exist
-       ValidationError: If Document model validation fails
-       RuntimeError: If extraction fails critically
- **`_convert_to_document(self: Any, result: BrownfieldExtractionResult, source_file: Path) -> Document`**
-   Convert brownfield ExtractionResult to greenfield Document.
-
-   Core conversion logic called by process(). Handles model transformation,
-   metadata mapping, and validation report generation.
-
-   Args:
-       result: Brownfield extraction result
-       source_file: Path to source file
-
-   Returns:
-       Document: Greenfield document model
- **`_generate_document_id(self: Any, source_file: Path) -> str`**
-   Generate unique document identifier.
-
-   Uses filename stem plus timestamp to ensure uniqueness across
-   multiple processing runs of same file.
-
-   Args:
-       source_file: Path to source file
-
-   Returns:
-       Unique document identifier (format: filename_uuid)
- **`_concatenate_content_blocks(self: Any, result: BrownfieldExtractionResult) -> str`**
-   Concatenate content blocks into document text.
-
-   Preserves block order using sequence_index from Position metadata.
-   Joins blocks with double newlines for readability.
-
-   Args:
-       result: Brownfield extraction result
-
-   Returns:
-       Concatenated text from all content blocks
- **`_convert_metadata(self: Any, result: BrownfieldExtractionResult, source_file: Path) -> Metadata`**
-   Convert brownfield metadata to greenfield Metadata model.
-
-   Maps document-level metadata, quality scores, OCR confidence,
-   and generates validation report.
-
-   Args:
-       result: Brownfield extraction result
-       source_file: Path to source file
-
-   Returns:
-       Greenfield Metadata model
- **`_compute_file_hash(self: Any, file_path: Path) -> str`**
-   Compute SHA-256 hash of file for integrity verification.
-
-   Args:
-       file_path: Path to file
-
-   Returns:
-       SHA-256 hash as hex string
- **`_extract_ocr_confidence(self: Any, result: BrownfieldExtractionResult) -> Dict[int, float]`**
-   Extract per-page OCR confidence scores from content blocks.
-
-   Aggregates confidence scores by page number from ContentBlock metadata.
-
-   Args:
-       result: Brownfield extraction result
-
-   Returns:
-       Dict mapping page number to average confidence score (0.0-1.0)
- **`_generate_validation_report(self: Any, result: BrownfieldExtractionResult, ocr_confidence: Dict[int, float]) -> ValidationReport`**
-   Generate validation report from extraction result.
-
-   Assesses quality, detects issues, and makes quarantine recommendation.
-
-   Args:
-       result: Brownfield extraction result
-       ocr_confidence: Per-page OCR confidence scores
-
-   Returns:
-       ValidationReport with quality assessment
- **`_extract_structure_metadata(self: Any, result: BrownfieldExtractionResult) -> Dict[str, Any]`**
-   Extract document structure metadata from extraction result.
-
-   Preserves page counts, word counts, image/table counts, and other
-   structural information for downstream stages.
-
-   Args:
-       result: Brownfield extraction result
-
-   Returns:
-       Dict with structure metadata

## Module: `data_extract.extract.csv`

### Class: `CsvExtractorAdapter`
**Inherits from:** ExtractorAdapter

Adapter for CSV extraction using brownfield CSVExtractor.

Wraps src.extractors.csv_extractor.CSVExtractor and converts brownfield
ExtractionResult to greenfield Document model.

Features:
- Header detection
- Delimiter auto-detection
- Encoding handling
- Table structure preservation

Example:
    >>> adapter = CsvExtractorAdapter()
    >>> document = adapter.process(Path("data.csv"))
    >>> print(document.structure["table_count"])
    1

#### Methods:
- **`__init__(self: Any) -> None`**
-   Initialize CSV adapter with brownfield extractor.

## Module: `data_extract.extract.docx`

### Class: `DocxExtractorAdapter`
**Inherits from:** ExtractorAdapter

Adapter for DOCX extraction using brownfield DocxExtractor.

Wraps src.extractors.docx_extractor.DocxExtractor and converts brownfield
ExtractionResult to greenfield Document model.

Features:
- Heading hierarchy preservation
- Table structure extraction
- Comments and tracked changes
- Style metadata

Example:
    >>> adapter = DocxExtractorAdapter()
    >>> document = adapter.process(Path("document.docx"))
    >>> print(document.structure["table_count"])
    5

#### Methods:
- **`__init__(self: Any) -> None`**
-   Initialize DOCX adapter with brownfield extractor.

## Module: `data_extract.extract.excel`

### Class: `ExcelExtractorAdapter`
**Inherits from:** ExtractorAdapter

Adapter for Excel extraction using brownfield ExcelExtractor.

Wraps src.extractors.excel_extractor.ExcelExtractor and converts brownfield
ExtractionResult to greenfield Document model.

Features:
- Multi-sheet workbook support
- Table structure preservation
- Formula extraction
- Cell metadata

Example:
    >>> adapter = ExcelExtractorAdapter()
    >>> document = adapter.process(Path("workbook.xlsx"))
    >>> print(document.structure["table_count"])
    3

#### Methods:
- **`__init__(self: Any) -> None`**
-   Initialize Excel adapter with brownfield extractor.

## Module: `data_extract.extract.pdf`

### Class: `PdfExtractorAdapter`
**Inherits from:** ExtractorAdapter

Adapter for PDF extraction using brownfield PdfExtractor.

Wraps src.extractors.pdf_extractor.PdfExtractor and converts brownfield
ExtractionResult to greenfield Document model.

Features:
- Native text extraction + OCR fallback
- Per-page OCR confidence tracking
- Table and image metadata preservation
- Scanned PDF detection

Example:
    >>> adapter = PdfExtractorAdapter()
    >>> document = adapter.process(Path("document.pdf"))
    >>> print(document.metadata.ocr_confidence)
    {1: 0.98, 2: 0.95, 3: 0.92}

#### Methods:
- **`__init__(self: Any) -> None`**
-   Initialize PDF adapter with brownfield extractor.
- **`_generate_validation_report(self: Any, result: BrownfieldExtractionResult, ocr_confidence: Dict[int, float]) -> ValidationReport`**
-   Override to add PDF-specific validation logic.
-
-   Extends base validation with scanned PDF detection.
-
-   Args:
-       result: Brownfield extraction result
-       ocr_confidence: Per-page OCR confidence scores
-
-   Returns:
-       ValidationReport with PDF-specific validation

## Module: `data_extract.extract.pptx`

### Class: `PptxExtractorAdapter`
**Inherits from:** ExtractorAdapter

Adapter for PPTX extraction using brownfield PptxExtractor.

Wraps src.extractors.pptx_extractor.PptxExtractor and converts brownfield
ExtractionResult to greenfield Document model.

Features:
- Slide order preservation
- Speaker notes extraction
- Image and chart metadata
- Layout information

Example:
    >>> adapter = PptxExtractorAdapter()
    >>> document = adapter.process(Path("presentation.pptx"))
    >>> print(document.structure["page_count"])  # slide count
    25

#### Methods:
- **`__init__(self: Any) -> None`**
-   Initialize PPTX adapter with brownfield extractor.

## Module: `data_extract.extract.txt`

### Class: `TxtExtractorAdapter`
**Inherits from:** ExtractorAdapter

Adapter for text file extraction using brownfield TextFileExtractor.

Wraps src.extractors.txt_extractor.TextFileExtractor and converts brownfield
ExtractionResult to greenfield Document model.

Features:
- Encoding detection
- Line break preservation
- Paragraph detection

Example:
    >>> adapter = TxtExtractorAdapter()
    >>> document = adapter.process(Path("document.txt"))
    >>> print(len(document.text))
    5000

#### Methods:
- **`__init__(self: Any) -> None`**
-   Initialize TXT adapter with brownfield extractor.

## Module: `data_extract.normalize.cleaning`

### Class: `CleaningResult`
**Inherits from:** BaseModel

Audit log of text cleaning transformations (AC-2.1.7).

Captures all cleaning decisions for audit trail and debugging.

Attributes:
    original_length: Length of text before cleaning
    cleaned_length: Length of text after cleaning
    artifacts_removed: Count of OCR artifacts removed
    headers_footers_removed: Count of headers/footers removed
    whitespace_normalized: Whether whitespace was normalized
    transformations: List of transformation log entries

#### Attributes:
- `original_length`: `int`
- `cleaned_length`: `int`
- `artifacts_removed`: `int`
- `headers_footers_removed`: `int`
- `whitespace_normalized`: `bool`
- `transformations`: `List[Dict[str, Any]]`

### Class: `TextCleaner`

Text cleaning engine for normalization pipeline.

Implements AC-2.1.1 through AC-2.1.5:
- OCR artifact removal (AC-2.1.1)
- Whitespace normalization (AC-2.1.2)
- Header/footer removal (AC-2.1.3, AC-2.1.4)
- Formatting preservation (AC-2.1.5)

Design:
- Deterministic: Same input + config → same output (AC-2.1.6)
- Auditable: All transformations logged in CleaningResult (AC-2.1.7)
- Modular: Each cleaning stage is separate method

#### Methods:
- **`__init__(self: Any, config: NormalizationConfig)`**
-   Initialize TextCleaner with configuration.
-
-   Args:
-       config: Normalization configuration
- **`_load_cleaning_patterns(self: Any) -> None`**
-   Load cleaning patterns from YAML configuration file.
-
-   Loads OCR artifact patterns and header/footer patterns.
-   Patterns are compiled into regex objects for performance.
- **`clean_text(self: Any, text: str, doc_type: Optional[str]) -> Tuple[str, CleaningResult]`**
-   Clean text through all configured stages.
-
-   Main entry point for text cleaning. Applies transformations
-   in deterministic order: OCR artifacts → whitespace → headers/footers.
-
-   Args:
-       text: Raw extracted text
-       doc_type: Document type for type-specific rules (optional)
-
-   Returns:
-       Tuple of (cleaned_text, cleaning_result_audit_log)
-
-   Examples:
-       >>> cleaner = TextCleaner(config)
-       >>> cleaned, result = cleaner.clean_text("Text with ^^^^^ noise")
-       >>> assert "^^^^^" not in cleaned
-       >>> assert result.artifacts_removed > 0
- **`remove_ocr_artifacts(self: Any, text: str) -> Tuple[str, int]`**
-   Remove OCR artifacts from text (AC-2.1.1).
-
-   Detects and removes:
-   - Garbled characters (^^^^^, ■■■■, ~~~)
-   - Repeated symbols (long underscores, dashes)
-   - Random character sequences
-   - Control characters
-
-   Args:
-       text: Text to clean
-
-   Returns:
-       Tuple of (cleaned_text, artifacts_removed_count)
-
-   Examples:
-       >>> cleaned, count = cleaner.remove_ocr_artifacts("Text ^^^^^ noise")
-       >>> assert "^^^^^" not in cleaned
-       >>> assert count == 1
- **`normalize_whitespace(self: Any, text: str) -> Tuple[str, bool]`**
-   Normalize whitespace while preserving formatting (AC-2.1.2, AC-2.1.5).
-
-   Normalization rules:
-   - Multiple spaces → single space (within lines)
-   - Multiple newlines → max 2 newlines (preserve paragraph breaks)
-   - Tabs normalized to spaces
-   - Leading/trailing whitespace trimmed per block
-
-   Preserves:
-   - Paragraph breaks (double newlines)
-   - Intentional indentation (code blocks, lists)
-   - Markdown formatting
-
-   Args:
-       text: Text to normalize
-
-   Returns:
-       Tuple of (normalized_text, was_normalized)
-
-   Examples:
-       >>> normalized, changed = cleaner.normalize_whitespace("Text   with\n\n\n\nspaces")
-       >>> assert "  " not in normalized  # Multiple spaces removed
-       >>> assert "\n\n" in normalized  # Paragraph breaks preserved
- **`detect_headers_footers(self: Any, pages: List[str]) -> Tuple[Optional[str], Optional[str]]`**
-   Detect repeated headers/footers across pages (AC-2.1.4).
-
-   Multi-page repetition analysis:
-   - Extracts top 10% of each page (potential header)
-   - Extracts bottom 10% of each page (potential footer)
-   - Finds common substrings across >= header_repetition_threshold pages
-   - Returns most common patterns
-
-   Args:
-       pages: List of page texts (one per page)
-
-   Returns:
-       Tuple of (header_pattern, footer_pattern) or (None, None)
-
-   Algorithm:
-   - Extract top/bottom regions from each page
-   - Find longest common substring across pages
-   - Require threshold minimum (default: 3 pages)
-   - Return patterns if found, else None
-
-   Examples:
-       >>> pages = ["Page 1\nContent", "Page 2\nContent", "Page 3\nContent"]
-       >>> header, footer = cleaner.detect_headers_footers(pages)
-       >>> assert "Page" in header  # Repeated header detected
- **`_find_common_pattern(self: Any, regions: List[str]) -> Optional[str]`**
-   Find common substring across regions.
-
-   Args:
-       regions: List of text regions
-
-   Returns:
-       Common pattern if found, else None
- **`remove_headers_footers(self: Any, pages: List[str], header: Optional[str], footer: Optional[str]) -> List[str]`**
-   Remove detected headers/footers from pages (AC-2.1.3).
-
-   Args:
-       pages: List of page texts
-       header: Header pattern to remove
-       footer: Footer pattern to remove
-
-   Returns:
-       List of cleaned pages
-
-   Examples:
-       >>> pages = ["Header\nContent\nFooter"] * 3
-       >>> cleaned = cleaner.remove_headers_footers(pages, "Header", "Footer")
-       >>> assert all("Header" not in p for p in cleaned)

## Module: `data_extract.normalize.config`

### Class: `NormalizationConfig`
**Inherits from:** BaseModel

Configuration for text normalization pipeline.

Defines settings for text cleaning, artifact removal, whitespace
normalization, header/footer detection, and entity normalization.

Attributes:
    remove_ocr_artifacts: Enable OCR artifact removal (AC-2.1.1)
    remove_headers_footers: Enable header/footer removal (AC-2.1.3)
    normalize_whitespace: Enable whitespace normalization (AC-2.1.2)
    header_repetition_threshold: Min pages for header/footer detection (AC-2.1.4)
    whitespace_max_consecutive_newlines: Max consecutive newlines (AC-2.1.2)
    ocr_artifact_patterns_file: Path to OCR artifact patterns YAML
    header_footer_patterns_file: Path to header/footer patterns YAML
    enable_entity_normalization: Enable entity recognition and normalization (AC-2.2.1)
    entity_patterns_file: Path to entity patterns YAML (AC-2.2.7)
    entity_dictionary_file: Path to entity dictionary YAML (AC-2.2.3)
    entity_context_window: Context window size for entity disambiguation (AC-2.2.1)
    ocr_confidence_threshold: Minimum OCR confidence threshold (AC-2.4.2)
    ocr_preprocessing_enabled: Enable image preprocessing before OCR (AC-2.4.3)
    quarantine_low_confidence: Enable quarantine for low confidence (AC-2.4.5)

#### Methods:
- **`validate_file_paths(cls: Any, v: Optional[Path]) -> Optional[Path]`**
-   Decorators: field_validator('ocr_artifact_patterns_file', 'header_footer_patterns_file', 'entity_patterns_file', 'entity_dictionary_file', 'schema_templates_file'), classmethod
-   Validate that configuration file paths exist if specified.
-
-   Args:
-       v: Path to validate
-
-   Returns:
-       Validated path or None
-
-   Raises:
-       ValueError: If path is specified but does not exist

#### Attributes:
- `remove_ocr_artifacts`: `bool`
- `remove_headers_footers`: `bool`
- `normalize_whitespace`: `bool`
- `header_repetition_threshold`: `int`
- `whitespace_max_consecutive_newlines`: `int`
- `ocr_artifact_patterns_file`: `Optional[Path]`
- `header_footer_patterns_file`: `Optional[Path]`
- `enable_entity_normalization`: `bool`
- `entity_patterns_file`: `Optional[Path]`
- `entity_dictionary_file`: `Optional[Path]`
- `entity_context_window`: `int`
- `enable_schema_standardization`: `bool`
- `schema_templates_file`: `Optional[Path]`
- `ocr_confidence_threshold`: `float`
- `ocr_preprocessing_enabled`: `bool`
- `quarantine_low_confidence`: `bool`
- `completeness_threshold`: `float`
- `tool_version`: `str`

## Module: `data_extract.normalize.entities`

### Class: `EntityNormalizer`

Entity recognizer and normalizer for audit documents.

Recognizes and normalizes audit domain entities using configurable
patterns and dictionaries. Implements PipelineStage protocol.

Attributes:
    patterns: Compiled entity patterns by type
    dictionary: Abbreviation expansion dictionary
    config: Normalization configuration settings
    logger: Structured logger for audit trail

Example:
    >>> from pathlib import Path
    >>> normalizer = EntityNormalizer(
    ...     patterns_file=Path("config/normalize/entity_patterns.yaml"),
    ...     dictionary_file=Path("config/normalize/entity_dictionary.yaml")
    ... )
    >>> document = Document(...)
    >>> normalized_doc = normalizer.process(document, context)

#### Methods:
- **`__init__(self: Any, patterns_file: Optional[Path], dictionary_file: Optional[Path], context_window: int = 5, logger: Optional[Any])`**
-   Initialize EntityNormalizer with configuration files.
-
-   Args:
-       patterns_file: Path to entity patterns YAML (AC-2.2.7)
-       dictionary_file: Path to entity dictionary YAML (AC-2.2.3)
-       context_window: Words before/after for disambiguation (AC-2.2.1)
-       logger: Structured logger for audit trail
-
-   Raises:
-       FileNotFoundError: If required configuration files not found
-       ValueError: If patterns fail validation
- **`_load_patterns(self: Any, patterns_file: Path) -> Dict[EntityType, List[Dict[str, Any]]]`**
-   Load and compile entity recognition patterns from YAML.
-
-   Args:
-       patterns_file: Path to entity_patterns.yaml
-
-   Returns:
-       Dictionary mapping entity types to compiled pattern lists
-
-   Raises:
-       FileNotFoundError: If patterns file not found
-       ValueError: If pattern compilation fails
- **`_load_dictionary(self: Any, dictionary_file: Path) -> Dict[str, Dict[str, Any]]`**
-   Load abbreviation expansion dictionary from YAML.
-
-   Args:
-       dictionary_file: Path to entity_dictionary.yaml
-
-   Returns:
-       Dictionary mapping abbreviations to expansion info
-
-   Raises:
-       FileNotFoundError: If dictionary file not found
- **`recognize_entity_type(self: Any, mention: str, context_words: List[str]) -> Optional[Tuple[EntityType, float]]`**
-   Classify entity mention by type using pattern matching.
-
-   Args:
-       mention: Entity text to classify
-       context_words: Surrounding words for disambiguation (AC-2.2.1)
-
-   Returns:
-       Tuple of (EntityType, confidence) or None if no match
-
-   Example:
-       >>> normalizer.recognize_entity_type("Risk #123", ["identified", "operational"])
-       (EntityType.RISK, 0.95)
- **`standardize_entity_id(self: Any, entity_mention: str, entity_type: EntityType) -> str`**
-   Normalize entity ID format to canonical form.
-
-   Converts various ID formats to standard "EntityType-NNN" format (AC-2.2.2).
-
-   Args:
-       entity_mention: Raw entity text (e.g., "Risk #123", "risk 456")
-       entity_type: Type of entity
-
-   Returns:
-       Canonical entity ID (e.g., "Risk-123")
-
-   Example:
-       >>> normalizer.standardize_entity_id("Risk #123", EntityType.RISK)
-       "Risk-123"
-       >>> normalizer.standardize_entity_id("CONTROL_456", EntityType.CONTROL)
-       "Control-456"
- **`normalize_capitalization(self: Any, text: str, entity_type: EntityType) -> str`**
-   Apply consistent capitalization to entity type names.
-
-   Args:
-       text: Text containing entity mention
-       entity_type: Type of entity
-
-   Returns:
-       Text with normalized capitalization (AC-2.2.4)
-
-   Example:
-       >>> normalizer.normalize_capitalization("RISK assessment", EntityType.RISK)
-       "Risk assessment"
- **`expand_abbreviations(self: Any, text: str, context_window: int = 5) -> Tuple[str, List[Dict[str, Any]]]`**
-   Expand abbreviations using dictionary with context awareness.
-
-   Args:
-       text: Input text with abbreviations
-       context_window: Words before/after for context checking (AC-2.2.3)
-
-   Returns:
-       Tuple of (expanded_text, expansion_log) for audit trail
-
-   Example:
-       >>> normalizer.expand_abbreviations("GRC framework review")
-       ("Governance, Risk, and Compliance framework review", [...])
- **`resolve_cross_references(self: Any, entities: List[Entity]) -> List[Entity]`**
-   Link entity mentions to canonical IDs and build entity graph.
-
-   Handles partial matches and entity relationship preservation (AC-2.2.5).
-
-   Args:
-       entities: List of recognized entities
-
-   Returns:
-       List of entities with resolved canonical IDs
-
-   Example:
-       >>> entities = [Entity(...), Entity(...)]
-       >>> resolved = normalizer.resolve_cross_references(entities)
- **`process(self: Any, document: Document, context: ProcessingContext) -> Document`**
-   Process document to recognize and normalize entities.
-
-   Main pipeline method implementing PipelineStage protocol.
-
-   Args:
-       document: Input document with text
-       context: Processing context with config and logger
-
-   Returns:
-       Document with recognized entities and enriched metadata (AC-2.2.6)
-
-   Example:
-       >>> document = Document(id="doc1", text="Risk #123 identified...", ...)
-       >>> normalized = normalizer.process(document, context)
-       >>> len(normalized.entities)  # Entities recognized
-       1

## Module: `data_extract.normalize.metadata`

### Class: `MetadataEnricher`

Metadata enrichment orchestrator for Story 2.6.

Coordinates all metadata enrichment operations:
- File hashing (SHA-256)
- Entity aggregation (tags and counts)
- Quality score aggregation (OCR, completeness, readability)
- Configuration snapshot serialization
- Timestamp and tool version recording

Integrates as Step 8 in the Normalizer pipeline after QualityValidator (Step 7).

Examples:
    >>> from pathlib import Path
    >>> enricher = MetadataEnricher()
    >>> enriched_metadata = enricher.enrich_metadata(
    ...     source_file=Path("document.pdf"),
    ...     entities=entity_list,
    ...     validation_report=validation_report,
    ...     config=normalization_config,
    ... )

Story: 2.6 - Metadata Enrichment Framework
AC: All (2.6.1-2.6.8)

#### Methods:
- **`enrich_metadata(self: Any, source_file: Path, entities: List[Entity], validation_report: ValidationReport, config: NormalizationConfig, readability_scores: Dict[str, float] | None) -> Metadata`**
-   Enrich metadata with all processing information.
-
-   Main entry point for metadata enrichment. Aggregates all metadata from
-   processing pipeline and creates enriched Metadata object for audit trail.
-
-   Args:
-       source_file: Path to source document file
-       entities: List of entities extracted from document
-       validation_report: ValidationReport from Story 2.5
-       config: NormalizationConfig with processing settings
-       readability_scores: Optional readability metrics dict
-
-   Returns:
-       Enriched Metadata object with all fields populated
-
-   Raises:
-       ProcessingError: If file hashing fails (continue-on-error pattern)
-
-   Examples:
-       >>> enricher = MetadataEnricher()
-       >>> metadata = enricher.enrich_metadata(
-       ...     source_file=Path("audit.pdf"),
-       ...     entities=[...],
-       ...     validation_report=report,
-       ...     config=config,
-       ... )
-       >>> assert metadata.file_hash  # SHA-256 hash
-       >>> assert metadata.entity_tags  # Entity IDs
-       >>> assert metadata.config_snapshot  # Full config
-
-   Story: 2.6 - Metadata Enrichment Framework
-   AC: All (2.6.1-2.6.8)

## Module: `data_extract.normalize.normalizer`

### Class: `Normalizer`

Main normalization orchestrator (Story 2.1 + 2.2 + 2.3 + 2.4 + 2.5 + 2.6).

Implements PipelineStage[Document, Document] protocol for integration
with the modular pipeline architecture from Epic 1.

Orchestrates:
- Text cleaning via TextCleaner (Story 2.1)
- Entity normalization via EntityNormalizer (Story 2.2)
- Schema standardization via SchemaStandardizer (Story 2.3)
- OCR quality validation via QualityValidator (Story 2.4)
- Completeness validation via QualityValidator (Story 2.5)
- Metadata enrichment via MetadataEnricher (Story 2.6)
- Metadata enrichment with cleaning and entity metrics
- Error handling (ProcessingError, CriticalError)
- Structured logging via structlog

Type Contract: Document (raw text) → Document (cleaned text + entities + standardized schema + validated OCR)

Design:
- Stateless: All state in ProcessingContext
- Deterministic: Same input + config → same output
- Auditable: All cleaning and entity decisions logged

Example:
    >>> config = NormalizationConfig()
    >>> normalizer = Normalizer(config)
    >>> context = ProcessingContext(config={}, logger=logger)
    >>> processed_doc = normalizer.process(raw_doc, context)

#### Methods:
- **`__init__(self: Any, config: NormalizationConfig)`**
-   Initialize Normalizer with configuration.
-
-   Args:
-       config: Normalization configuration
- **`process(self: Any, document: Document, context: ProcessingContext) -> Document`**
-   Normalize document through all stages (PipelineStage protocol).
-
-   Main pipeline method that cleans document text, enriches metadata,
-   and logs cleaning metrics.
-
-   Args:
-       document: Document with raw text from extraction stage
-       context: Processing context (config, logger, metrics)
-
-   Returns:
-       Document with cleaned text and enriched metadata
-
-   Raises:
-       ProcessingError: For recoverable errors (malformed text, etc.)
-       CriticalError: For fatal errors (invalid config, missing dependencies)
-
-   Pipeline Flow:
-       1. Extract text from document
-       2. Clean text using TextCleaner
-       3. Aggregate CleaningResults
-       4. Update document metadata
-       5. Log metrics to context.logger
-       6. Return normalized document
-
-   Example:
-       >>> doc = Document(
-       ...     id="doc1",
-       ...     text="Text ^^^^^ with noise",
-       ...     metadata=metadata,
-       ... )
-       >>> cleaned = normalizer.process(doc, context)
-       >>> assert "^^^^^" not in cleaned.text

### Class: `NormalizerFactory`

Factory for creating Normalizer instances with different configurations.

Provides convenience methods for common normalization scenarios.

Example:
    >>> # Default normalizer
    >>> normalizer = NormalizerFactory.create_default()
    >>>
    >>> # Custom normalizer
    >>> config = NormalizationConfig(remove_ocr_artifacts=False)
    >>> normalizer = NormalizerFactory.create(config)

#### Methods:
- **`create_default() -> Normalizer`**
-   Decorators: staticmethod
-   Create normalizer with default configuration.
-
-   Returns:
-       Normalizer with default NormalizationConfig
-
-   Example:
-       >>> normalizer = NormalizerFactory.create_default()
-       >>> assert normalizer.config.remove_ocr_artifacts is True
- **`create(config: NormalizationConfig) -> Normalizer`**
-   Decorators: staticmethod
-   Create normalizer with custom configuration.
-
-   Args:
-       config: Custom normalization configuration
-
-   Returns:
-       Normalizer with provided configuration
-
-   Example:
-       >>> config = NormalizationConfig(remove_headers_footers=False)
-       >>> normalizer = NormalizerFactory.create(config)
-       >>> assert normalizer.config.remove_headers_footers is False
- **`create_from_yaml(yaml_path: str) -> Normalizer`**
-   Decorators: staticmethod
-   Create normalizer from YAML configuration file.
-
-   Args:
-       yaml_path: Path to YAML configuration file
-
-   Returns:
-       Normalizer with configuration loaded from YAML
-
-   Example:
-       >>> normalizer = NormalizerFactory.create_from_yaml(
-       ...     "config/normalize/cleaning_rules.yaml"
-       ... )

## Module: `data_extract.normalize.schema`

### Class: `SchemaStandardizer`
**Inherits from:** PipelineStage[Document, Document]

Schema standardizer for document type detection and transformation.

Implements PipelineStage protocol to detect document types (REPORT, MATRIX,
EXPORT, IMAGE) with >95% accuracy and apply type-specific schema transformations.

Attributes:
    logger: Structured logger for audit trail
    schema_templates: Field mapping templates loaded from YAML config
    enable_standardization: Flag to enable/disable schema standardization

#### Methods:
- **`__init__(self: Any, schema_templates: Optional[Dict[str, Any]], schema_templates_file: Optional[Path], enable_standardization: bool = True, logger: Optional[Any]) -> None`**
-   Initialize schema standardizer.
-
-   Args:
-       schema_templates: Field mapping templates for standardization (dict)
-       schema_templates_file: Path to schema_templates.yaml file
-       enable_standardization: Enable/disable schema standardization
-       logger: Structured logger instance
- **`standardize_field_names(self: Any, fields: Dict[str, Any], doc_type: DocumentType, doc_subtype: Optional[str]) -> Dict[str, Any]`**
-   Standardize field names using configured mappings.
-
-   Args:
-       fields: Dictionary of source fields to standardize
-       doc_type: Document type (REPORT, MATRIX, EXPORT, IMAGE)
-       doc_subtype: Document subtype (e.g., Archer module name)
-
-   Returns:
-       Dictionary with standardized field names
- **`_get_field_mapping(self: Any, doc_type: DocumentType, doc_subtype: Optional[str]) -> Dict[str, Any]`**
-   Get field mapping for document type and subtype.
-
-   Args:
-       doc_type: Document type
-       doc_subtype: Document subtype (optional)
-
-   Returns:
-       Field mapping dictionary
- **`process(self: Any, document: Document, context: ProcessingContext) -> Document`**
-   Apply schema standardization to document.
-
-   Detects document type and applies type-specific transformations to ensure
-   consistent schema across all document sources.
-
-   Args:
-       document: Document to standardize
-       context: Processing context with config and metrics
-
-   Returns:
-       Document with standardized schema and updated metadata
-
-   Raises:
-       ProcessingError: If schema detection fails (graceful degradation)
- **`detect_document_type(self: Any, document: Document) -> Tuple[DocumentType, float]`**
-   Detect document type using structure analysis.
-
-   Analyzes document structure (sections, tables, fields, OCR metadata) to
-   determine document type with >95% accuracy.
-
-   Args:
-       document: Document to classify
-
-   Returns:
-       Tuple of (DocumentType, confidence_score)
- **`_detect_archer_export(self: Any, text: str, structure: Dict[str, Any]) -> bool`**
-   Detect Archer GRC export patterns.
-
-   Args:
-       text: Document text content
-       structure: Document structure metadata
-
-   Returns:
-       True if Archer export patterns detected
- **`standardize_schema(self: Any, document: Document, doc_type: DocumentType) -> Document`**
-   Apply type-specific schema transformation.
-
-   Args:
-       document: Document to transform
-       doc_type: Detected document type
-
-   Returns:
-       Document with standardized schema
- **`_transform_report(self: Any, document: Document) -> Document`**
-   Transform REPORT document schema.
-
-   Extracts sections, headings, and narrative flow.
-
-   Args:
-       document: Document to transform
-
-   Returns:
-       Document with REPORT schema
- **`_transform_matrix(self: Any, document: Document) -> Document`**
-   Transform MATRIX document schema.
-
-   Preserves table structure (rows, columns, headers).
-
-   Args:
-       document: Document to transform
-
-   Returns:
-       Document with MATRIX schema
- **`_transform_export(self: Any, document: Document) -> Document`**
-   Transform EXPORT document schema.
-
-   Parses Archer-specific field schemas and hyperlinks, applies field name standardization.
-
-   Args:
-       document: Document to transform
-
-   Returns:
-       Document with EXPORT schema
- **`_transform_image(self: Any, document: Document) -> Document`**
-   Transform IMAGE document schema.
-
-   Validates OCR metadata presence.
-
-   Args:
-       document: Document to transform
-
-   Returns:
-       Document with IMAGE schema
- **`parse_archer_export(self: Any, document: Document) -> Dict[str, Any]`**
-   Parse Archer GRC HTML/XML export.
-
-   Extracts Archer-specific field schemas and hyperlinks representing
-   entity relationships.
-
-   Args:
-       document: Document with Archer export content
-
-   Returns:
-       Dictionary with parsed Archer fields and relationships
- **`preserve_excel_structure(self: Any, document: Document) -> Document`**
-   Preserve Excel table structure.
-
-   Extracts rows, columns, and headers from tables and ensures they're
-   preserved in a structured format for control matrices and risk registers.
-
-   Args:
-       document: Document with Excel table content
-
-   Returns:
-       Document with preserved table structure

## Module: `data_extract.normalize.validation`

### Class: `QualityValidator`
**Inherits from:** PipelineStage[Document, Document]

OCR quality validator with confidence scoring and completeness validation.

Implements PipelineStage protocol to calculate OCR confidence scores, apply
image preprocessing, detect extraction gaps, and quarantine low-quality extractions.

Attributes:
    logger: Structured logger for audit trail
    ocr_confidence_threshold: Minimum confidence threshold (default 0.95)
    ocr_preprocessing_enabled: Enable OCR preprocessing (default True)
    quarantine_low_confidence: Enable quarantine for low confidence (default True)
    completeness_threshold: Minimum completeness ratio threshold (default 0.90, Story 2.5)

#### Methods:
- **`__init__(self: Any, ocr_confidence_threshold: float = 0.95, ocr_preprocessing_enabled: bool = True, quarantine_low_confidence: bool = True, completeness_threshold: float = 0.9, logger: Optional[Any]) -> None`**
-   Initialize quality validator.
-
-   Args:
-       ocr_confidence_threshold: Minimum confidence threshold (0.0-1.0)
-       ocr_preprocessing_enabled: Enable image preprocessing for OCR
-       quarantine_low_confidence: Enable quarantine mechanism
-       completeness_threshold: Minimum completeness ratio threshold (0.0-1.0, Story 2.5)
-       logger: Structured logger instance
- **`validate_ocr_confidence(self: Any, image_path: Path, preprocess: bool = True) -> tuple[float, Dict[str, Any]]`**
-   Calculate OCR confidence score for an image.
-
-   Uses pytesseract.image_to_data() to extract word-level confidence scores
-   and calculates page-level average confidence.
-
-   Args:
-       image_path: Path to image file
-       preprocess: Whether to apply preprocessing before OCR
-
-   Returns:
-       Tuple of (confidence_score, ocr_data_dict)
-       - confidence_score: Average confidence (0.0-1.0)
-       - ocr_data_dict: Full OCR data from pytesseract
-
-   Raises:
-       ProcessingError: If pytesseract fails or image cannot be loaded
- **`_calculate_raw_confidence(self: Any, image: Any) -> float`**
-   Calculate raw OCR confidence for an image.
-
-   Helper method for preprocessing confidence comparison.
-
-   Args:
-       image: PIL Image object
-
-   Returns:
-       Average confidence score (0.0-1.0)
- **`preprocess_image_for_ocr(self: Any, image: Any) -> Any`**
-   Preprocess image for improved OCR accuracy.
-
-   Applies deskew, denoise, and contrast enhancement to improve OCR quality.
-
-   Args:
-       image: PIL Image object to preprocess
-
-   Returns:
-       Preprocessed PIL Image object
- **`calculate_document_average_confidence(self: Any, confidence_scores: Dict[int, float]) -> Optional[float]`**
-   Calculate document-level average confidence from per-page scores.
-
-   Args:
-       confidence_scores: Dictionary of page_num -> confidence score
-
-   Returns:
-       Average confidence across all pages, or None if no scores
- **`check_confidence_threshold(self: Any, confidence_scores: Dict[int, float]) -> tuple[bool, List[int]]`**
-   Check if any pages are below confidence threshold.
-
-   Args:
-       confidence_scores: Dictionary of page_num -> confidence score
-
-   Returns:
-       Tuple of (quarantine_recommended, pages_below_threshold)
-       - quarantine_recommended: True if any page below threshold
-       - pages_below_threshold: List of page numbers below threshold
- **`create_validation_report(self: Any, confidence_scores: Dict[int, float], pages_below_threshold: List[int], scanned_pdf_detected: Optional[bool]) -> ValidationReport`**
-   Create validation report for OCR quality assessment.
-
-   Args:
-       confidence_scores: Per-page OCR confidence scores
-       pages_below_threshold: List of page numbers below threshold
-       scanned_pdf_detected: Whether document was detected as scanned PDF
-
-   Returns:
-       ValidationReport with quarantine recommendation and quality flags
- **`detect_scanned_pdf(self: Any, document: Document) -> bool`**
-   Detect if document is a scanned PDF vs. native PDF.
-
-   Uses heuristics to determine if a PDF was scanned (images + OCR) or
-   contains native digital text. Analyzes document structure and metadata
-   for indicators of scanning.
-
-   Heuristic rules:
-   - If document_type is 'image' → scanned
-   - If >50% of structure indicates image-based content → scanned
-   - If OCR confidence scores are present in metadata → scanned
-   - If document has rich font/structure metadata → native
-
-   Args:
-       document: Document to analyze
-
-   Returns:
-       True if scanned PDF detected, False if native or indeterminate
- **`quarantine_document(self: Any, document: Document, validation_report: ValidationReport, output_dir: Path) -> Path`**
-   Quarantine low-confidence document with audit log.
-
-   Creates quarantine directory structure and writes audit log with file hash,
-   confidence scores, quality flags, and timestamp.
-
-   Args:
-       document: Document to quarantine
-       validation_report: Validation report with quality assessment
-       output_dir: Base output directory for quarantine files
-
-   Returns:
-       Path to quarantine directory where document should be moved
-
-   Raises:
-       ProcessingError: If quarantine directory creation fails
- **`detect_missing_images(self: Any, document: Document) -> List[Dict[str, Any]]`**
-   Detect images without alt text in document structure (Story 2.5 - AC 2.5.1).
-
-   Analyzes ContentBlocks in document.structure for block_type='image' with
-   missing or empty alt text. Extracts page number and section context from
-   ContentBlock metadata.
-
-   Args:
-       document: Document with structure containing ContentBlocks
-
-   Returns:
-       List of extraction gaps with location details:
-       [{"gap_type": "missing_image", "location": {"page": N, "section": "..."},
-         "description": "...", "severity": "warning"}]
- **`detect_complex_objects(self: Any, document: Document) -> List[Dict[str, Any]]`**
-   Detect complex objects that can't be extracted (Story 2.5 - AC 2.5.2).
-
-   Detects ContentBlocks with block_type in ['ole_object', 'chart', 'diagram', 'drawing'].
-   Extracts object metadata: object_type, object_id, page, section.
-
-   Args:
-       document: Document with structure containing ContentBlocks
-
-   Returns:
-       List of extraction gaps with object details and suggested action
- **`calculate_completeness_ratio(self: Any, document: Document) -> float`**
-   Calculate extraction completeness ratio (Story 2.5 - AC 2.5.3).
-
-   Counts total elements from source document metadata (all ContentBlocks including skipped).
-   Counts successfully extracted elements (ContentBlocks with non-empty content).
-   Calculates ratio: extracted / total with division-by-zero handling.
-
-   Args:
-       document: Document with structure containing ContentBlocks
-
-   Returns:
-       Completeness ratio (0.0-1.0)
- **`log_extraction_gap(self: Any, gap_type: str, location: Dict[str, Any], description: str, severity: str, suggested_action: Optional[str]) -> Dict[str, Any]`**
-   Helper method for structured gap logging (Story 2.5 - AC 2.5.4, 2.5.6).
-
-   Creates structured gap log entry with JSON output for audit trail.
-
-   Args:
-       gap_type: Type of gap (e.g., 'missing_image', 'complex_object')
-       location: Location dict with page, section, etc.
-       description: Human-readable description of the gap
-       severity: Severity level ('info', 'warning', 'error')
-       suggested_action: Optional suggested action for remediation
-
-   Returns:
-       Gap dictionary for ValidationReport.extraction_gaps list
- **`process(self: Any, document: Document, context: ProcessingContext) -> Document`**
-   Apply quality validation to document (OCR + completeness).
-
-   Orchestrates full validation workflow:
-   1. Detect if document is scanned PDF (if OCR available)
-   2. Calculate OCR confidence scores (if scanned and OCR available)
-   3. Check confidence thresholds (if OCR available)
-   4. Detect completeness issues (missing images, complex objects)
-   5. Calculate completeness ratio
-   6. Create validation report
-   7. Populate document metadata
-   8. Quarantine if needed
-
-   Args:
-       document: Document to validate
-       context: Processing context with config, logger, metrics
-
-   Returns:
-       Document with enriched metadata (ocr_confidence, quality_flags, completeness_ratio)
-
-   Raises:
-       ProcessingError: If validation fails critically

## Module: `data_extract.output.formatters.base`

### Class: `FormattingResult`

Result of formatting operation.

#### Methods:
- **`__post_init__(self: Any)`**

#### Attributes:
- `output_path`: `Path`
- `chunk_count`: `int`
- `total_size`: `int`
- `metadata`: `dict`
- `format_type`: `str`
- `duration_seconds`: `float`
- `errors`: `list`

### Class: `BaseFormatter`
**Inherits from:** ABC

Base class for all output formatters.

#### Methods:
- **`format_chunks(self: Any, chunks: List[Any], output_path: Path) -> FormattingResult`**
-   Decorators: abstractmethod
-   Format chunks and write to output path.
-
-   Args:
-       chunks: List of chunks to format
-       output_path: Path to write output
-       **kwargs: Additional formatter-specific options
-
-   Returns:
-       FormattingResult with details of operation

## Module: `data_extract.output.formatters.csv_formatter`

### Class: `CsvFormatter`
**Inherits from:** BaseFormatter

Formats chunks as CSV output.

#### Methods:
- **`__init__(self: Any, max_text_length: Optional[int], validate: bool = True)`**
-   Initialize CSV formatter.
-
-   Args:
-       max_text_length: Maximum text length before truncation
-       validate: Whether to validate output
- **`format_chunks(self: Any, chunks: List[Any], output_path: Path) -> FormattingResult`**
-   Format chunks as CSV and write to file.
-
-   Args:
-       chunks: List of chunks to format
-       output_path: Path to write CSV file
-       **kwargs: Additional options
-
-   Returns:
-       FormattingResult with operation details

## Module: `data_extract.output.formatters.json_formatter`

### Class: `JsonFormatter`
**Inherits from:** BaseFormatter

Formats chunks as JSON output.

#### Methods:
- **`__init__(self: Any, validate: bool = True)`**
-   Initialize JSON formatter.
-
-   Args:
-       validate: Whether to validate output against schema
- **`format_chunks(self: Any, chunks: List[Any], output_path: Path) -> FormattingResult`**
-   Format chunks as JSON and write to file.
-
-   Args:
-       chunks: List of chunks to format
-       output_path: Path to write JSON file
-       **kwargs: Additional options
-
-   Returns:
-       FormattingResult with operation details

## Module: `data_extract.output.formatters.txt_formatter`

### Class: `TxtFormatter`
**Inherits from:** BaseFormatter

Formats chunks as plain text output.

#### Methods:
- **`__init__(self: Any, include_metadata: bool, delimiter: str = ━━━ CHUNK {{n}} ━━━)`**
-   Initialize text formatter.
-
-   Args:
-       include_metadata: Whether to include metadata headers
-       delimiter: Delimiter between chunks
- **`format_chunks(self: Any, chunks: List[Any], output_path: Path) -> FormattingResult`**
-   Format chunks as plain text and write to file.
-
-   Args:
-       chunks: List of chunks to format
-       output_path: Path to write text file
-       **kwargs: Additional options
-
-   Returns:
-       FormattingResult with operation details

## Module: `data_extract.output.organization`

### Class: `OrganizationStrategy`
**Inherits from:** Enum

Strategies for organizing output files.

### Class: `OrganizationResult`

Result of organizing output files.

#### Attributes:
- `strategy`: `OrganizationStrategy`
- `output_dir`: `Path`
- `files_created`: `List[Path]`
- `manifest_path`: `Optional[Path]`
- `metadata`: `Dict[str, Any]`

### Class: `Organizer`

Organizes output files according to strategy.

#### Methods:
- **`__init__(self: Any)`**
-   Initialize the organizer.
- **`organize(self: Any, chunks: List[Any], output_dir: Path, strategy: OrganizationStrategy, format_type: str = txt) -> OrganizationResult`**
-   Organize chunks into files according to strategy.
-
-   Args:
-       chunks: List of chunks to organize
-       output_dir: Base output directory
-       strategy: Organization strategy to use
-       format_type: Output format type (txt, json, csv)
-       **kwargs: Additional formatter options
-
-   Returns:
-       OrganizationResult with details of created files

## Module: `data_extract.output.validation.csv_parser`

### Class: `CsvParserValidator`

Validates CSV files can be parsed by multiple engines.

#### Methods:
- **`__init__(self: Any)`**
-   Initialize CSV parser validator.
- **`validate(self: Any, csv_path: Path) -> Dict[str, Any]`**
-   Validate CSV file with multiple parsers.
-
-   Args:
-       csv_path: Path to CSV file to validate
-
-   Returns:
-       Dictionary with validation results

## Module: `data_extract.output.writer`

### Class: `OutputWriter`

Main entry point for writing formatted output.

#### Methods:
- **`__init__(self: Any)`**
-   Initialize output writer.
- **`write(self: Any, chunks: List[Any], output_path: Path, format_type: str = txt, per_chunk: bool, organize: bool, strategy: Optional[OrganizationStrategy]) -> Any`**
-   Write chunks to output with specified format and organization.
-
-   Args:
-       chunks: List of chunks to write
-       output_path: Output file or directory path
-       format_type: Output format (json, txt, csv)
-       per_chunk: Write each chunk to separate file
-       organize: Enable output organization
-       strategy: Organization strategy if organize is True
-       **kwargs: Additional formatter options
-
-   Returns:
-       FormattingResult or OrganizationResult

## Module: `extractors.csv_extractor`

### Class: `CSVExtractor`
**Inherits from:** BaseExtractor

Extracts content from CSV/TSV files.

Supports CSV and TSV files with automatic detection of:
- Delimiter (comma, tab, semicolon, pipe)
- Encoding (UTF-8, Latin-1, CP1252, etc.)
- Header row presence

Design Notes:
- Single TABLE ContentBlock per CSV file
- Full grid structure stored in TableMetadata
- All cells stored as strings (no type conversion)
- Malformed rows normalized to consistent length
- Configuration overrides available for all auto-detection

Configuration:
    delimiter (str): CSV delimiter (default: auto-detect)
    encoding (str): File encoding (default: auto-detect)
    has_header (bool): First row is header (default: auto-detect)
    max_rows (int): Maximum rows to extract (default: None)
    skip_rows (int): Number of rows to skip at start (default: 0)
    quotechar (str): Quote character for fields (default: '"')
    strict (bool): Strict parsing mode (default: False)

Example:
    >>> extractor = CSVExtractor()
    >>> result = extractor.extract(Path("data.csv"))
    >>> if result.success:
    ...     table = result.tables[0]
    ...     print(f"Rows: {table.num_rows}, Columns: {table.num_columns}")

#### Methods:
- **`__init__(self: Any, config: Optional[Union[dict, object]])`**
-   Initialize CSV extractor with optional configuration.
-
-   Args:
-       config: Configuration options (dict or ConfigManager):
-           - delimiter: CSV delimiter (default: auto-detect)
-           - encoding: File encoding (default: auto-detect)
-           - has_header: First row is header (default: auto-detect)
-           - max_rows: Maximum rows to extract (default: None)
-           - skip_rows: Number of rows to skip (default: 0)
-           - quotechar: Quote character (default: '"')
-           - strict: Strict parsing mode (default: False)
- **`supports_format(self: Any, file_path: Path) -> bool`**
-   Check if file is a CSV or TSV file.
-
-   Args:
-       file_path: Path to check
-
-   Returns:
-       True if file has .csv or .tsv extension
- **`get_supported_extensions(self: Any) -> list[str]`**
-   Return supported file extensions.
- **`get_format_name(self: Any) -> str`**
-   Return human-readable format name.
- **`extract(self: Any, file_path: Path) -> ExtractionResult`**
-   Extract content from CSV file.
-
-   Strategy:
-   1. Validate file exists and is accessible
-   2. Detect encoding (or use configured)
-   3. Detect delimiter (or use configured)
-   4. Read all rows using csv.reader
-   5. Skip rows if configured
-   6. Detect header row (or use configured)
-   7. Normalize row lengths
-   8. Apply max_rows limit if configured
-   9. Create TableMetadata with full grid
-   10. Create single TABLE ContentBlock
-   11. Generate document metadata
-   12. Return structured result
-
-   Args:
-       file_path: Path to CSV file
-
-   Returns:
-       ExtractionResult with single TABLE ContentBlock and metadata
- **`_detect_encoding(self: Any, file_path: Path) -> str`**
-   Detect file encoding with UTF-8 → chardet → Latin-1 cascade.
-
-   Algorithm:
-   1. Try UTF-8 (most common)
-   2. Check for UTF-8 BOM
-   3. Use chardet on first 100KB if available
-   4. Fallback to Latin-1 (always works)
-
-   Args:
-       file_path: Path to CSV file
-
-   Returns:
-       Detected encoding name
- **`_detect_delimiter(self: Any, file_path: Path, encoding: str) -> str`**
-   Detect CSV delimiter using csv.Sniffer with fallback.
-
-   Algorithm:
-   1. Read first 8KB of file
-   2. Try csv.Sniffer.sniff()
-   3. If fails, count delimiter candidates
-   4. Return most common valid delimiter
-   5. Default to comma if all fail
-
-   Args:
-       file_path: Path to CSV file
-       encoding: File encoding to use
-
-   Returns:
-       Detected delimiter: ",", "  ", ";", "|"
- **`_detect_header(self: Any, rows: List[List[str]]) -> bool`**
-   Detect header presence using multi-check heuristic.
-
-   Algorithm:
-   1. Check if first row has different data types than second row
-   2. Check if first row values are unique
-   3. Check if first row has longer strings (typical header pattern)
-   4. Combine checks with weighted scoring
-
-   Target accuracy: ≥95%
-
-   Args:
-       rows: List of rows (list of lists)
-
-   Returns:
-       True if header detected
- **`_is_numeric(self: Any, value: str) -> bool`**
-   Check if string value is numeric.
-
-   Args:
-       value: String to check
-
-   Returns:
-       True if value is numeric
- **`_normalize_row(self: Any, row: List[str], expected_columns: int) -> List[str]`**
-   Normalize row length by padding or truncating.
-
-   Args:
-       row: Input row
-       expected_columns: Target column count
-
-   Returns:
-       Row with exactly expected_columns elements
- **`_read_csv_file(self: Any, file_path: Path, encoding: str, delimiter: str) -> List[List[str]]`**
-   Read CSV file and return rows.
-
-   Args:
-       file_path: Path to CSV file
-       encoding: File encoding
-       delimiter: CSV delimiter
-
-   Returns:
-       List of rows (each row is a list of strings)
- **`_extract_document_metadata(self: Any, file_path: Path, table_metadata: TableMetadata) -> DocumentMetadata`**
-   Extract document-level metadata from CSV file.
-
-   Args:
-       file_path: Path to file
-       table_metadata: Table metadata for statistics
-
-   Returns:
-       DocumentMetadata with available properties
- **`_compute_file_hash(self: Any, file_path: Path) -> str`**
-   Compute SHA256 hash of file for deduplication.
-
-   Args:
-       file_path: Path to file
-
-   Returns:
-       Hex string of SHA256 hash

## Module: `extractors.docx_extractor`

### Class: `DocxExtractor`
**Inherits from:** BaseExtractor

Extracts text content from Microsoft Word (.docx) files.

This is a SPIKE implementation focused on paragraph extraction.
Uses python-docx library for document parsing.

Design Notes:
- Only extracts text paragraphs in this version
- Detects headings based on style names
- Handles basic errors gracefully
- Returns partial results on non-fatal errors

Example:
    >>> extractor = DocxExtractor()
    >>> result = extractor.extract(Path("document.docx"))
    >>> if result.success:
    ...     for block in result.content_blocks:
    ...         print(block.content)

#### Methods:
- **`__init__(self: Any, config: Optional[Union[dict, object]])`**
-   Initialize DOCX extractor with optional configuration.
-
-   Args:
-       config: Configuration options (dict or ConfigManager):
-           - max_paragraph_length: Max characters per paragraph (default: None)
-           - skip_empty: Skip empty paragraphs (default: True)
-           - extract_styles: Include style information (default: True)
- **`supports_format(self: Any, file_path: Path) -> bool`**
-   Check if file is a DOCX file.
-
-   Args:
-       file_path: Path to check
-
-   Returns:
-       True if file has .docx extension
- **`get_supported_extensions(self: Any) -> list[str]`**
-   Return supported file extensions.
- **`get_format_name(self: Any) -> str`**
-   Return human-readable format name.
- **`extract(self: Any, file_path: Path) -> ExtractionResult`**
-   Extract content from DOCX file.
-
-   Strategy:
-   1. Validate file exists and is accessible
-   2. Open document with python-docx
-   3. Extract paragraphs sequentially
-   4. Detect content types (heading vs paragraph)
-   5. Generate document metadata
-   6. Return structured result
-
-   Args:
-       file_path: Path to DOCX file
-
-   Returns:
-       ExtractionResult with content blocks and metadata
-
-   Note:
-       - Returns success=False for file-level errors
-       - Returns partial results if some paragraphs fail
-       - Logs warnings for recoverable issues
- **`_detect_content_type(self: Any, paragraph: Any) -> ContentType`**
-   Detect content type based on paragraph style.
-
-   Uses Word's built-in style names to classify content.
-
-   Args:
-       paragraph: python-docx Paragraph object
-
-   Returns:
-       ContentType enum value
- **`_extract_document_metadata(self: Any, file_path: Path, doc: Document) -> DocumentMetadata`**
-   Extract document-level metadata from DOCX file.
-
-   Extracts both file system metadata and embedded document properties.
-
-   Args:
-       file_path: Path to file
-       doc: python-docx Document object
-
-   Returns:
-       DocumentMetadata with available properties
- **`_compute_file_hash(self: Any, file_path: Path) -> str`**
-   Compute SHA256 hash of file for deduplication.
-
-   Args:
-       file_path: Path to file
-
-   Returns:
-       Hex string of SHA256 hash
- **`_extract_table(self: Any, table: Any, table_idx: int) -> TableMetadata`**
-   Extract table data from a python-docx Table object.
-
-   Args:
-       table: python-docx Table object
-       table_idx: Index of table in document
-
-   Returns:
-       TableMetadata with table structure and content

## Module: `extractors.excel_extractor`

### Class: `ExcelExtractor`
**Inherits from:** BaseExtractor

Extracts content from Microsoft Excel workbooks.

Supports multi-sheet extraction with cell values, formulas, and structure
preservation. Uses openpyxl for Excel file parsing.

Design Notes:
- Extracts all sheets by default
- Each sheet becomes a TABLE ContentBlock
- Cell data stored in TableMetadata
- Formulas preserved in metadata
- Charts detected and metadata extracted

Example:
    >>> extractor = ExcelExtractor()
    >>> result = extractor.extract(Path("workbook.xlsx"))
    >>> if result.success:
    ...     for block in result.content_blocks:
    ...         print(f"Sheet: {block.position.sheet}")

#### Methods:
- **`__init__(self: Any, config: Optional[Union[dict, object]])`**
-   Initialize Excel extractor with optional configuration.
-
-   Args:
-       config: Configuration options (dict or ConfigManager):
-           - max_rows: Maximum rows to extract per sheet (default: None)
-           - max_columns: Maximum columns per sheet (default: None)
-           - include_formulas: Extract formula strings (default: True)
-           - include_charts: Extract chart metadata (default: True)
-           - skip_empty_cells: Skip empty cells (default: False)
- **`supports_format(self: Any, file_path: Path) -> bool`**
-   Check if file is an Excel file.
-
-   Args:
-       file_path: Path to check
-
-   Returns:
-       True if file has .xlsx or .xls extension
- **`get_supported_extensions(self: Any) -> list[str]`**
-   Return supported file extensions.
- **`get_format_name(self: Any) -> str`**
-   Return human-readable format name.
- **`extract(self: Any, file_path: Path) -> ExtractionResult`**
-   Extract content from Excel workbook.
-
-   Strategy:
-   1. Validate file exists and is accessible
-   2. Open workbook with openpyxl
-   3. Extract each sheet sequentially
-   4. Create TableMetadata for each sheet
-   5. Extract cell values and formulas
-   6. Detect charts if enabled
-   7. Generate document metadata
-   8. Return structured result
-
-   Args:
-       file_path: Path to Excel file
-
-   Returns:
-       ExtractionResult with content blocks and metadata
- **`_extract_sheet(self: Any, worksheet: Any, sheet_name: str, sheet_index: int, worksheet_values: Any) -> tuple[list[ContentBlock], Optional[TableMetadata]]`**
-   Extract content from a single worksheet.
-
-   Args:
-       worksheet: openpyxl Worksheet object (with formulas)
-       sheet_name: Name of the sheet
-       sheet_index: Index of sheet in workbook
-       worksheet_values: Optional worksheet with calculated values
-
-   Returns:
-       Tuple of (content_blocks, table_metadata)
- **`_extract_document_metadata(self: Any, file_path: Path, workbook: Any) -> DocumentMetadata`**
-   Extract document-level metadata from Excel file.
-
-   Args:
-       file_path: Path to file
-       workbook: openpyxl Workbook object
-
-   Returns:
-       DocumentMetadata with available properties
- **`_compute_file_hash(self: Any, file_path: Path) -> str`**
-   Compute SHA256 hash of file for deduplication.
-
-   Args:
-       file_path: Path to file
-
-   Returns:
-       Hex string of SHA256 hash

## Module: `extractors.pdf_extractor`

### Class: `PdfExtractor`
**Inherits from:** BaseExtractor

Extracts content from PDF files.

Uses pypdf for native text extraction and pytesseract for OCR fallback
when PDFs contain scanned images instead of native text.

Example:
    >>> extractor = PdfExtractor()
    >>> result = extractor.extract(Path("document.pdf"))
    >>> if result.success:
    ...     for block in result.content_blocks:
    ...         print(f"Page {block.position.page}: {block.content}")

#### Methods:
- **`__init__(self: Any, config: Optional[Union[dict, object]])`**
-   Initialize PDF extractor with optional configuration.
-
-   Args:
-       config: Configuration options (dict or ConfigManager):
-           - use_ocr: Enable OCR fallback (default: True)
-           - tesseract_cmd: Path to tesseract executable (default: None)
-           - poppler_path: Path to poppler bin directory (default: None)
-           - ocr_dpi: DPI for OCR image conversion (default: 300)
-           - ocr_lang: Language for OCR (default: "eng")
-           - extract_images: Extract image metadata (default: True)
-           - extract_tables: Extract table structures (default: True)
-           - min_text_threshold: Min chars to consider native text (default: 10)
- **`_get_config_value(self: Any, config_dict: Any, key: Any, default: Any)`**
-   Helper to handle False values correctly.
- **`supports_format(self: Any, file_path: Path) -> bool`**
-   Check if file is a PDF file.
-
-   Args:
-       file_path: Path to check
-
-   Returns:
-       True if file has .pdf extension
- **`get_supported_extensions(self: Any) -> list[str]`**
-   Return supported file extensions.
- **`get_format_name(self: Any) -> str`**
-   Return human-readable format name.
- **`extract(self: Any, file_path: Path) -> ExtractionResult`**
-   Extract content from PDF file.
-
-   Strategy:
-   1. Validate file exists and is accessible
-   2. Try native text extraction with pypdf
-   3. If text is minimal, fall back to OCR
-   4. Extract tables if configured
-   5. Extract image metadata if configured
-   6. Generate document metadata
-   7. Return structured result
-
-   Args:
-       file_path: Path to PDF file
-
-   Returns:
-       ExtractionResult with content blocks and metadata
-
-   Note:
-       - Returns success=False for file-level errors
-       - Returns partial results if some pages fail
-       - Uses OCR fallback automatically if native text is insufficient
- **`_needs_ocr(self: Any, file_path: Path) -> bool`**
-   Determine if PDF requires OCR (is image-based).
-
-   Args:
-       file_path: Path to PDF file
-
-   Returns:
-       True if OCR is needed
- **`_extract_with_ocr(self: Any, file_path: Path) -> List[ContentBlock]`**
-   Extract text using OCR (pytesseract).
-
-   Args:
-       file_path: Path to PDF file
-
-   Returns:
-       List of ContentBlock with OCR-extracted text
- **`_extract_tables(self: Any, file_path: Path) -> List[TableMetadata]`**
-   Extract tables from PDF using pdfplumber.
-
-   Args:
-       file_path: Path to PDF file
-
-   Returns:
-       List of TableMetadata
- **`_extract_image_metadata(self: Any, reader: 'PdfReader', file_path: Path) -> List[ImageMetadata]`**
-   Extract image metadata from PDF.
-
-   Args:
-       reader: PdfReader instance
-       file_path: Path to PDF file
-
-   Returns:
-       List of ImageMetadata
- **`_extract_document_metadata(self: Any, file_path: Path, reader: 'PdfReader') -> DocumentMetadata`**
-   Extract document-level metadata from PDF file.
-
-   Args:
-       file_path: Path to file
-       reader: PdfReader instance
-
-   Returns:
-       DocumentMetadata with available properties
- **`_compute_file_hash(self: Any, file_path: Path) -> str`**
-   Compute SHA256 hash of file for deduplication.
-
-   Args:
-       file_path: Path to file
-
-   Returns:
-       Hex string of SHA256 hash
- **`_is_likely_heading(self: Any, line: str, next_line: Optional[str]) -> tuple[bool, int]`**
-   Heuristic to determine if a line of text is likely a heading.
-
-   PDFs don't have explicit style information, so we use heuristics:
-   - Short lines (< 80 chars)
-   - Title Case or ALL CAPS patterns
-   - Common heading patterns (Section N:, Chapter N, etc.)
-   - Not ending with sentence punctuation
-   - Standalone (surrounded by blank lines or followed by normal text)
-
-   Args:
-       line: Text line to evaluate
-       next_line: Optional next line for context
-
-   Returns:
-       Tuple of (is_heading, level) where level is 1-3
- **`_split_text_into_blocks(self: Any, text: str, page_num: int, sequence_index: int) -> tuple[List[ContentBlock], int]`**
-   Split page text into content blocks with heading detection.
-
-   Args:
-       text: Raw page text
-       page_num: Page number
-       sequence_index: Starting sequence index
-
-   Returns:
-       Tuple of (list of ContentBlocks, next sequence_index)

## Module: `extractors.pptx_extractor`

### Class: `PptxExtractor`
**Inherits from:** BaseExtractor

Extracts content from Microsoft PowerPoint (.pptx) files.

Extracts:
- Slide titles and body text
- Speaker notes
- Slide sequence and positioning
- Presentation metadata

Example:
    >>> extractor = PptxExtractor()
    >>> result = extractor.extract(Path("presentation.pptx"))
    >>> if result.success:
    ...     for block in result.content_blocks:
    ...         print(f"Slide {block.position.slide}: {block.content}")

#### Methods:
- **`__init__(self: Any, config: Optional[Union[dict, object]])`**
-   Initialize PPTX extractor with optional configuration.
-
-   Args:
-       config: Configuration options (dict or ConfigManager):
-           - extract_notes: Extract speaker notes (default: True)
-           - extract_images: Extract image metadata (default: True)
-           - skip_empty_slides: Skip slides with no content (default: False)
- **`supports_format(self: Any, file_path: Path) -> bool`**
-   Check if file is a PPTX file.
-
-   Args:
-       file_path: Path to check
-
-   Returns:
-       True if file has .pptx extension
- **`get_supported_extensions(self: Any) -> list[str]`**
-   Return supported file extensions.
- **`get_format_name(self: Any) -> str`**
-   Return human-readable format name.
- **`extract(self: Any, file_path: Path) -> ExtractionResult`**
-   Extract content from PPTX file.
-
-   Strategy:
-   1. Validate file exists and is accessible
-   2. Open presentation with python-pptx
-   3. Iterate through slides
-   4. Extract text from shapes (title, body)
-   5. Extract speaker notes if configured
-   6. Generate presentation metadata
-   7. Return structured result
-
-   Args:
-       file_path: Path to PPTX file
-
-   Returns:
-       ExtractionResult with content blocks and metadata
-
-   Note:
-       - Returns success=False for file-level errors
-       - Returns partial results if some slides fail
-       - Logs warnings for recoverable issues
- **`_detect_shape_type(self: Any, shape: Any, slide: Any) -> ContentType`**
-   Detect content type based on shape properties.
-
-   Heuristic:
-   - Shapes in title placeholders → HEADING
-   - Other text shapes → PARAGRAPH
-
-   Args:
-       shape: python-pptx Shape object
-       slide: python-pptx Slide object
-
-   Returns:
-       ContentType enum value
- **`_extract_presentation_metadata(self: Any, file_path: Path, prs: Presentation) -> DocumentMetadata`**
-   Extract presentation-level metadata from PPTX file.
-
-   Extracts both file system metadata and embedded document properties.
-
-   Args:
-       file_path: Path to file
-       prs: python-pptx Presentation object
-
-   Returns:
-       DocumentMetadata with available properties
- **`_compute_file_hash(self: Any, file_path: Path) -> str`**
-   Compute SHA256 hash of file for deduplication.
-
-   Args:
-       file_path: Path to file
-
-   Returns:
-       Hex string of SHA256 hash
- **`_extract_image_metadata(self: Any, prs: Presentation) -> list[ImageMetadata]`**
-   Extract image metadata from presentation slides.
-
-   Strategy:
-   1. Iterate through all slides
-   2. Find shapes that are pictures
-   3. Extract image properties (dimensions, format)
-   4. Create ImageMetadata objects
-
-   Args:
-       prs: python-pptx Presentation object
-
-   Returns:
-       List of ImageMetadata objects

## Module: `extractors.txt_extractor`

### Class: `TextFileExtractor`
**Inherits from:** BaseExtractor

Simple extractor for plain text files.

Demonstrates:
- How to implement BaseExtractor interface
- How to create ContentBlock objects
- How to populate ExtractionResult
- Error handling patterns

#### Methods:
- **`supports_format(self: Any, file_path: Path) -> bool`**
-   Check if file is a text file.
- **`get_supported_extensions(self: Any) -> list[str]`**
-   Supported file extensions.
- **`extract(self: Any, file_path: Path) -> ExtractionResult`**
-   Extract content from text file.
-
-   Strategy:
-   1. Validate file
-   2. Read content
-   3. Split into paragraphs
-   4. Create ContentBlock for each paragraph
-   5. Generate metadata
-   6. Return ExtractionResult

## Module: `formatters.chunked_text_formatter`

### Class: `ChunkedTextFormatter`
**Inherits from:** BaseFormatter

Format ProcessingResult as token-limited text chunks.

Configuration Options:
    token_limit (int): Maximum tokens per chunk (default: 8000)
    include_context_headers (bool): Include section context in chunks (default: True)
    chunk_overlap (int): Number of tokens to overlap between chunks (default: 0)
    output_dir (Path): Directory for chunk files (default: current directory)

Example:
    >>> formatter = ChunkedTextFormatter(config={"token_limit": 4000})
    >>> result = formatter.format(processing_result)
    >>> print(f"Created {1 + len(result.additional_files)} chunks")

#### Methods:
- **`__init__(self: Any, config: dict | None)`**
-   Initialize chunked text formatter.
-
-   Args:
-       config: Configuration options
- **`format(self: Any, processing_result: ProcessingResult) -> FormattedOutput`**
-   Convert ProcessingResult to chunked text format.
-
-   Args:
-       processing_result: Result from processing stage
-
-   Returns:
-       FormattedOutput with first chunk as content, rest as additional_files
- **`get_format_type(self: Any) -> str`**
-   Return format type identifier.
-
-   Returns:
-       "chunked"
- **`get_file_extension(self: Any) -> str`**
-   Return file extension for chunked text.
-
-   Returns:
-       ".txt"
- **`_estimate_tokens(self: Any, text: str) -> int`**
-   Estimate token count for text.
-
-   Uses simple heuristic: word_count * 1.3
-
-   Args:
-       text: Text to estimate
-
-   Returns:
-       Estimated token count
- **`_build_context_map(self: Any, blocks: tuple[ContentBlock, Ellipsis]) -> dict[Any, list[ContentBlock]]`**
-   Build map of block_id to parent heading chain.
-
-   Args:
-       blocks: Content blocks
-
-   Returns:
-       Dictionary mapping block_id to list of parent headings
- **`_convert_blocks_to_text(self: Any, blocks: tuple[ContentBlock, Ellipsis], context_map: dict[Any, list[ContentBlock]]) -> list[dict[str, Any]]`**
-   Convert blocks to text with metadata.
-
-   Args:
-       blocks: Content blocks
-       context_map: Block to context mapping
-
-   Returns:
-       List of text blocks with metadata
- **`_block_to_text(self: Any, block: ContentBlock) -> str`**
-   Convert a content block to plain text.
-
-   Args:
-       block: Block to convert
-
-   Returns:
-       Text representation
- **`_split_into_chunks(self: Any, text_blocks: list[dict[str, Any]], metadata: DocumentMetadata) -> list[str]`**
-   Split text blocks into token-limited chunks.
-
-   Args:
-       text_blocks: Text blocks with metadata
-       metadata: Document metadata
-
-   Returns:
-       List of chunk strings
- **`_build_chunk_text(self: Any, blocks: list[dict[str, Any]], chunk_number: int, metadata: DocumentMetadata, context: list[ContentBlock]) -> str`**
-   Build text for a single chunk.
-
-   Args:
-       blocks: Text blocks in this chunk
-       chunk_number: Chunk number (1-indexed)
-       metadata: Document metadata
-       context: Current heading context
-
-   Returns:
-       Formatted chunk text
- **`_generate_chunk_filename(self: Any, source_file: Path, chunk_number: int) -> Path`**
-   Generate filename for chunk file.
-
-   Args:
-       source_file: Original source file
-       chunk_number: Chunk number (1-indexed)
-
-   Returns:
-       Path for chunk file

## Module: `formatters.json_formatter`

### Class: `JsonFormatter`
**Inherits from:** BaseFormatter

Format ProcessingResult as hierarchical JSON.

Configuration Options:
    hierarchical (bool): Build nested structure based on parent_id (default: False)
    pretty_print (bool): Pretty-print JSON with indentation (default: True)
    indent (int): Number of spaces for indentation (default: 2)
    ensure_ascii (bool): Escape non-ASCII characters (default: False)

Example:
    >>> formatter = JsonFormatter(config={"pretty_print": True, "indent": 4})
    >>> result = formatter.format(processing_result)
    >>> print(result.content)  # Pretty JSON output

#### Methods:
- **`__init__(self: Any, config: dict | None)`**
-   Initialize JSON formatter.
-
-   Args:
-       config: Configuration options
- **`format(self: Any, processing_result: ProcessingResult) -> FormattedOutput`**
-   Convert ProcessingResult to JSON format.
-
-   Args:
-       processing_result: Result from processing stage
-
-   Returns:
-       FormattedOutput with JSON content
- **`get_format_type(self: Any) -> str`**
-   Return format type identifier.
-
-   Returns:
-       "json"
- **`_build_json_structure(self: Any, processing_result: ProcessingResult) -> dict[str, Any]`**
-   Build JSON data structure from ProcessingResult.
-
-   Args:
-       processing_result: Result to convert
-
-   Returns:
-       Dictionary ready for JSON serialization
- **`_build_hierarchical_blocks(self: Any, blocks: tuple[ContentBlock, Ellipsis]) -> list[dict[str, Any]]`**
-   Build hierarchical block structure based on parent_id.
-
-   Args:
-       blocks: Flat tuple of content blocks
-
-   Returns:
-       List of blocks with children nested
- **`_serialize_block_with_children(self: Any, block: ContentBlock, children_map: dict[UUID | None, list[ContentBlock]]) -> dict[str, Any]`**
-   Serialize a block with its children nested.
-
-   Args:
-       block: Block to serialize
-       children_map: Mapping of parent_id to children
-
-   Returns:
-       Dictionary with nested children
- **`_serialize_content_block(self: Any, block: ContentBlock) -> dict[str, Any]`**
-   Serialize a ContentBlock to dictionary.
-
-   Args:
-       block: Block to serialize
-
-   Returns:
-       Dictionary representation
- **`_serialize_position(self: Any, position: Position) -> dict[str, Any]`**
-   Serialize Position to dictionary.
-
-   Args:
-       position: Position to serialize
-
-   Returns:
-       Dictionary representation
- **`_serialize_document_metadata(self: Any, metadata: DocumentMetadata) -> dict[str, Any]`**
-   Serialize DocumentMetadata to dictionary.
-
-   Args:
-       metadata: Metadata to serialize
-
-   Returns:
-       Dictionary representation
- **`_serialize_table_metadata(self: Any, table: Any) -> dict[str, Any]`**
-   Serialize TableMetadata to dictionary.
-
-   Args:
-       table: TableMetadata to serialize
-
-   Returns:
-       Dictionary representation
- **`_serialize_image_metadata(self: Any, image: Any) -> dict[str, Any]`**
-   Serialize ImageMetadata to dictionary.
-
-   Args:
-       image: ImageMetadata to serialize
-
-   Returns:
-       Dictionary representation
- **`_json_serializer(self: Any, obj: Any) -> Any`**
-   Custom JSON serializer for non-standard types.
-
-   Args:
-       obj: Object to serialize
-
-   Returns:
-       Serializable representation
-
-   Raises:
-       TypeError: If object type is not supported

## Module: `formatters.markdown_formatter`

### Class: `MarkdownFormatter`
**Inherits from:** BaseFormatter

Format ProcessingResult as human-readable Markdown.

Configuration Options:
    include_frontmatter (bool): Include YAML frontmatter (default: True)
    heading_offset (int): Offset for heading levels, 0-based (default: 0)
    include_metadata (bool): Include technical metadata comments (default: False)
    include_position_info (bool): Include page/position comments (default: False)

Example:
    >>> formatter = MarkdownFormatter(config={"heading_offset": 1})
    >>> result = formatter.format(processing_result)
    >>> print(result.content)  # Clean markdown output

#### Methods:
- **`__init__(self: Any, config: dict | None)`**
-   Initialize Markdown formatter.
-
-   Args:
-       config: Configuration options
- **`format(self: Any, processing_result: ProcessingResult) -> FormattedOutput`**
-   Convert ProcessingResult to Markdown format.
-
-   Args:
-       processing_result: Result from processing stage
-
-   Returns:
-       FormattedOutput with Markdown content
- **`get_format_type(self: Any) -> str`**
-   Return format type identifier.
-
-   Returns:
-       "markdown"
- **`get_file_extension(self: Any) -> str`**
-   Return file extension for markdown.
-
-   Returns:
-       ".markdown"
- **`_build_frontmatter(self: Any, metadata: DocumentMetadata) -> str`**
-   Build YAML frontmatter from document metadata.
-
-   Args:
-       metadata: Document metadata
-
-   Returns:
-       YAML frontmatter string or empty if no useful metadata
- **`_convert_blocks_to_markdown(self: Any, blocks: tuple[ContentBlock, Ellipsis]) -> str`**
-   Convert content blocks to markdown.
-
-   Args:
-       blocks: Content blocks to convert
-
-   Returns:
-       Markdown string
- **`_convert_block(self: Any, block: ContentBlock) -> str`**
-   Convert a single content block to markdown.
-
-   Args:
-       block: Block to convert
-
-   Returns:
-       Markdown string
- **`_convert_heading(self: Any, block: ContentBlock) -> str`**
-   Convert heading block to markdown heading.
-
-   Args:
-       block: Heading block
-
-   Returns:
-       Markdown heading
- **`_convert_paragraph(self: Any, block: ContentBlock) -> str`**
-   Convert paragraph block to markdown.
-
-   Args:
-       block: Paragraph block
-
-   Returns:
-       Paragraph text
- **`_convert_list_item(self: Any, block: ContentBlock) -> str`**
-   Convert list item to markdown list.
-
-   Args:
-       block: List item block
-
-   Returns:
-       Markdown list item
- **`_convert_quote(self: Any, block: ContentBlock) -> str`**
-   Convert quote block to markdown blockquote.
-
-   Args:
-       block: Quote block
-
-   Returns:
-       Markdown blockquote
- **`_convert_code(self: Any, block: ContentBlock) -> str`**
-   Convert code block to fenced code block.
-
-   Args:
-       block: Code block
-
-   Returns:
-       Markdown fenced code block
- **`_convert_table(self: Any, block: ContentBlock) -> str`**
-   Convert table block to markdown table.
-
-   Args:
-       block: Table block
-
-   Returns:
-       Markdown table or reference
- **`_convert_image(self: Any, block: ContentBlock) -> str`**
-   Convert image block to markdown image reference.
-
-   Args:
-       block: Image block
-
-   Returns:
-       Markdown image syntax

## Module: `infrastructure.config_manager`

### Class: `ConfigurationError`
**Inherits from:** Exception

Raised when configuration loading or validation fails.

### Class: `ConfigManager`

Thread-safe configuration manager with validation and env var support.

This class provides centralized configuration management for the data
extraction tool. It supports loading from YAML/JSON files, validating
against pydantic schemas, and overriding values with environment variables.

Attributes:
    config_file: Path to configuration file
    env_prefix: Prefix for environment variable overrides
    schema: Optional pydantic model for validation

Thread Safety:
    All public methods are thread-safe. Internal state is protected
    by a reentrant lock.

#### Methods:
- **`__init__(self: Any, config_file: Optional[Union[str, Path, dict]], schema: Optional[Type[BaseModel]], defaults: Optional[dict], env_prefix: Optional[str])`**
-   Initialize configuration manager.
-
-   Args:
-       config_file: Path to YAML or JSON configuration file, or dict for testing.
-                   If None, defaults to './config.yaml' in current working directory.
-       schema: Optional pydantic model for validation
-       defaults: Default configuration values
-       env_prefix: Prefix for environment variable overrides (e.g., "DATA_EXTRACTOR")
-
-   Raises:
-       ConfigurationError: If file cannot be loaded or validation fails
-
-   Example:
-       >>> # With explicit path
-       >>> config = ConfigManager(
-       ...     "config.yaml",
-       ...     schema=AppConfig,
-       ...     defaults={"logging": {"level": "INFO"}},
-       ...     env_prefix="DATA_EXTRACTOR"
-       ... )
-       >>> # With default path (./config.yaml)
-       >>> config = ConfigManager()
-       >>> # With dict (for testing)
-       >>> config = ConfigManager({"key": "value"})
- **`_load_file(self: Any) -> dict`**
-   Load configuration from file.
-
-   Returns:
-       Configuration dict from file, or empty dict if file doesn't exist
-
-   Raises:
-       ConfigurationError: If file exists but cannot be parsed
- **`_load_env_vars(self: Any) -> dict`**
-   Load configuration overrides from environment variables.
-
-   Environment variables are converted to nested dict keys using underscores:
-   DATA_EXTRACTOR_LOGGING_LEVEL -> logging.level
-
-   For keys with underscores (like skip_empty), tries multiple split patterns
-   to find the best match against existing config structure.
-
-   Returns:
-       Configuration dict from environment variables
- **`_split_env_var_path(self: Any, path: str) -> list[str]`**
-   Split environment variable path intelligently.
-
-   Tries to match against existing configuration structure to handle
-   keys that contain underscores (like skip_empty).
-
-   Args:
-       path: Lowercase env var path (e.g., "extractors_docx_skip_empty")
-
-   Returns:
-       List of path components
- **`_path_exists_in_config(self: Any, parts: list[str]) -> bool`**
-   Check if a path exists in the current configuration.
- **`_coerce_type(self: Any, value: str) -> Union[str, int, float, bool]`**
-   Coerce string value to appropriate Python type.
-
-   Args:
-       value: String value from environment variable
-
-   Returns:
-       Coerced value (str, int, float, or bool)
- **`_merge_configs(self: Any) -> dict`**
-   Merge multiple configuration dicts with later configs taking precedence.
-
-   Args:
-       *configs: Variable number of configuration dicts
-
-   Returns:
-       Merged configuration dict
- **`_deep_merge(self: Any, base: dict, override: dict) -> dict`**
-   Deep merge two dicts, with override taking precedence.
-
-   Args:
-       base: Base configuration dict
-       override: Override configuration dict
-
-   Returns:
-       Merged dict
- **`_validate(self: Any) -> None`**
-   Validate configuration against pydantic schema.
-
-   Raises:
-       ConfigurationError: If validation fails
- **`_navigate_path(self: Any, path: str) -> tuple[dict, list[str]]`**
-   Navigate to a configuration path.
-
-   Args:
-       path: Dot-separated path (e.g., "extractors.docx.skip_empty")
-
-   Returns:
-       Tuple of (current_dict, remaining_parts)
- **`get(self: Any, path: str, default: Any) -> Any`**
-   Get configuration value by dot-separated path.
-
-   Args:
-       path: Dot-separated configuration path (e.g., "logging.level")
-       default: Default value if path not found (default: None)
-
-   Returns:
-       Configuration value
-
-   Raises:
-       ConfigurationError: If path not found and no default provided
-
-   Example:
-       >>> config.get("logging.level")
-       'INFO'
-       >>> config.get("missing.key", default="fallback")
-       'fallback'
- **`get_section(self: Any, path: str, default: Optional[dict]) -> dict`**
-   Get configuration section as dict.
-
-   Args:
-       path: Dot-separated path to section
-       default: Default dict if section not found
-
-   Returns:
-       Configuration section as dict
-
-   Example:
-       >>> config.get_section("extractors.docx")
-       {'max_paragraph_length': 1000, 'skip_empty': True}
- **`has(self: Any, path: str) -> bool`**
-   Check if configuration key exists.
-
-   Args:
-       path: Dot-separated configuration path
-
-   Returns:
-       True if key exists, False otherwise
-
-   Example:
-       >>> config.has("logging.level")
-       True
-       >>> config.has("nonexistent.key")
-       False
- **`get_all(self: Any) -> dict`**
-   Get complete configuration as dict.
-
-   Returns:
-       Copy of entire configuration dict
-
-   Example:
-       >>> all_config = config.get_all()
-       >>> print(all_config.keys())
-       dict_keys(['extractors', 'logging', 'general'])
- **`reload(self: Any) -> None`**
-   Reload configuration from file.
-
-   This re-reads the configuration file and re-applies environment
-   variable overrides. Useful for picking up configuration changes
-   without restarting the application.
-
-   Raises:
-       ConfigurationError: If reload fails
-
-   Example:
-       >>> config.reload()
- **`__repr__(self: Any) -> str`**
-   String representation of ConfigManager.

## Module: `infrastructure.error_handler`

### Class: `RecoveryAction`
**Inherits from:** str, Enum

Recovery actions for different error types.

### Class: `DataExtractionError`
**Inherits from:** Exception

Base exception for all data extraction errors.

All errors in the system inherit from this class, providing:
- Standardized error codes
- User-friendly and technical messages
- Recovery information
- Context propagation
- Original exception chaining

Attributes:
    error_code: Error code (E001-E999) for documentation
    message: User-friendly message for non-technical users
    technical_message: Technical message with details for developers
    category: Error category (ValidationError, ExtractionError, etc.)
    recoverable: Whether error can be recovered from
    suggested_action: What user should do to resolve
    context: Additional context information
    original_exception: Original exception if wrapping another error

#### Methods:
- **`__str__(self: Any) -> str`**
-   Return user-friendly message.
- **`__repr__(self: Any) -> str`**
-   Return detailed representation for debugging.

#### Attributes:
- `error_code`: `str`
- `message`: `str`
- `technical_message`: `Optional[str]`
- `category`: `str`
- `recoverable`: `bool`
- `suggested_action`: `str`
- `context`: `dict[str, Any]`
- `original_exception`: `Optional[Exception]`

### Class: `ValidationError`
**Inherits from:** DataExtractionError

Errors during input validation (E001-E099).

#### Methods:
- **`__init__(self: Any)`**

### Class: `ExtractionError`
**Inherits from:** DataExtractionError

Errors during content extraction (E100-E199).

#### Methods:
- **`__init__(self: Any)`**

### Class: `ProcessingError`
**Inherits from:** DataExtractionError

Errors during content processing (E200-E299).

#### Methods:
- **`__init__(self: Any)`**

### Class: `FormattingError`
**Inherits from:** DataExtractionError

Errors during output formatting (E300-E399).

#### Methods:
- **`__init__(self: Any)`**

### Class: `ConfigError`
**Inherits from:** DataExtractionError

Errors in configuration (E400-E499).

#### Methods:
- **`__init__(self: Any)`**

### Class: `ResourceError`
**Inherits from:** DataExtractionError

Resource errors - memory, disk, timeout (E500-E599).

#### Methods:
- **`__init__(self: Any)`**

### Class: `ExternalServiceError`
**Inherits from:** DataExtractionError

Errors from external services like OCR (E600-E699).

#### Methods:
- **`__init__(self: Any)`**

### Class: `PipelineError`
**Inherits from:** DataExtractionError

Pipeline orchestration errors (E700-E799).

#### Methods:
- **`__init__(self: Any)`**

### Class: `UnknownError`
**Inherits from:** DataExtractionError

Unknown or unexpected errors (E900-E999).

#### Methods:
- **`__init__(self: Any)`**

### Class: `ErrorHandler`

Central error handling system.

Responsibilities:
- Load error code registry from YAML
- Create typed exceptions from error codes
- Determine recovery actions
- Implement retry with backoff
- Format errors for users and developers
- Log errors appropriately

Example:
    >>> handler = ErrorHandler()
    >>> error = handler.create_error("E001", file_path="/docs/report.docx")
    >>> print(handler.format_for_user(error))
    >>> if error.recoverable:
    >>>     handler.retry_with_backoff(operation)

#### Methods:
- **`__init__(self: Any, error_codes_path: Optional[Path])`**
-   Initialize error handler.
-
-   Args:
-       error_codes_path: Path to error_codes.yaml (defaults to package location)
- **`_load_error_codes(self: Any, path: Path) -> dict[str, dict]`**
-   Load error code registry from YAML file.
-
-   Args:
-       path: Path to error_codes.yaml
-
-   Returns:
-       Dictionary mapping error codes to error information
- **`get_error_info(self: Any, error_code: str) -> dict[str, Any]`**
-   Get error information for a specific error code.
-
-   Args:
-       error_code: Error code (e.g., "E001")
-
-   Returns:
-       Dictionary with error information (category, message, etc.)
- **`create_error(self: Any, error_code: str, original_exception: Optional[Exception], custom_message: Optional[str]) -> DataExtractionError`**
-   Create a typed exception from an error code.
-
-   Args:
-       error_code: Error code (e.g., "E001")
-       original_exception: Original exception if wrapping
-       custom_message: Override default message
-       **context: Context variables for message formatting
-
-   Returns:
-       Typed exception (ValidationError, ExtractionError, etc.)
-
-   Example:
-       >>> error = handler.create_error(
-       >>>     "E001",
-       >>>     file_path="/docs/report.docx",
-       >>>     user="auditor"
-       >>> )
- **`_format_message(self: Any, template: str, context: dict[str, Any]) -> str`**
-   Format message template with context variables.
-
-   Args:
-       template: Message template with {placeholders}
-       context: Context variables for substitution
-
-   Returns:
-       Formatted message
- **`get_recovery_action(self: Any, error_code: str) -> RecoveryAction`**
-   Determine recovery action for an error code.
-
-   Args:
-       error_code: Error code (e.g., "E001")
-
-   Returns:
-       RecoveryAction (RETRY, SKIP, or ABORT)
-
-   Logic:
-   - Recoverable errors with transient nature → RETRY (E104, E600, E601)
-   - Recoverable errors that can be skipped → SKIP (E105, E203)
-   - Non-recoverable errors → ABORT
- **`retry_with_backoff(self: Any, operation: Callable[[], T], max_retries: int = 3, initial_delay: float = 1.0, backoff_factor: float = 2.0) -> T`**
-   Retry an operation with exponential backoff.
-
-   Args:
-       operation: Callable to retry
-       max_retries: Maximum number of retry attempts
-       initial_delay: Initial delay in seconds
-       backoff_factor: Multiplier for each retry (exponential backoff)
-
-   Returns:
-       Result from operation
-
-   Raises:
-       Exception: If all retries exhausted
-
-   Example:
-       >>> result = handler.retry_with_backoff(
-       >>>     lambda: extract_file(path),
-       >>>     max_retries=3,
-       >>>     initial_delay=1.0
-       >>> )
- **`format_for_user(self: Any, error: DataExtractionError) -> str`**
-   Format error for non-technical users.
-
-   Provides:
-   - User-friendly message
-   - Suggested action
-   - No technical jargon or stack traces
-
-   Args:
-       error: Error to format
-
-   Returns:
-       User-friendly error message
-
-   Example:
-       >>> print(handler.format_for_user(error))
-       The file you specified could not be found. Please check
-       the file path and try again.
- **`format_for_developer(self: Any, error: DataExtractionError) -> str`**
-   Format error for developers with debug information.
-
-   Provides:
-   - Error code
-   - Technical message
-   - Context information
-   - Original exception details
-   - Stack trace if available
-
-   Args:
-       error: Error to format
-
-   Returns:
-       Detailed error message for debugging
-
-   Example:
-       >>> print(handler.format_for_developer(error))
-       [E001] File not found: /docs/report.docx
-       Context: user=auditor, operation=extraction
-       Original: FileNotFoundError: No such file
- **`log_error(self: Any, error: DataExtractionError, level: int = logging.ERROR) -> None`**
-   Log error appropriately based on severity.
-
-   Args:
-       error: Error to log
-       level: Logging level (default: ERROR)
-
-   Logs:
-   - Error code and category
-   - Technical message
-   - Context information
-   - Original exception if present

## Module: `infrastructure.logging_framework`

### Class: `JSONFormatter`
**Inherits from:** logging.Formatter

Custom formatter that outputs JSON structured logs.

Includes standard fields plus any extra fields from log records.

#### Methods:
- **`format(self: Any, record: logging.LogRecord) -> str`**
-   Format log record as JSON.

## Module: `infrastructure.progress_tracker`

### Class: `ProgressTracker`

Thread-safe progress tracker for long-running operations.

Tracks:
- Items processed / total items
- Percentage completion
- Elapsed time
- Estimated time remaining (ETA)
- Throughput (items/second)
- Current item being processed
- Cancellation status

Attributes:
    total_items: Total number of items to process
    items_processed: Number of items processed so far
    percentage: Completion percentage (0.0-100.0)
    current_item: Description of current item being processed
    description: Operation description
    callback: Callback function called on updates
    cancelled: Whether operation has been cancelled

#### Methods:
- **`__post_init__(self: Any)`**
-   Initialize progress tracker.
- **`percentage(self: Any) -> float`**
-   Decorators: property
-   Get completion percentage.
-
-   Returns:
-       Percentage complete (0.0-100.0)
- **`update(self: Any, items_processed: int, current_item: Optional[str]) -> None`**
-   Update progress with new item count.
-
-   Args:
-       items_processed: Total items processed so far
-       current_item: Description of current item (optional)
-
-   Thread-safe: Yes
- **`increment(self: Any, n: int = 1, current_item: Optional[str]) -> None`**
-   Increment progress by n items.
-
-   Args:
-       n: Number of items to increment by (default: 1)
-       current_item: Description of current item (optional)
-
-   Thread-safe: Yes
- **`get_elapsed_time(self: Any) -> float`**
-   Get elapsed time since tracker started.
-
-   Returns:
-       Elapsed time in seconds
-
-   Thread-safe: Yes
- **`get_throughput(self: Any) -> Optional[float]`**
-   Calculate items processed per second.
-
-   Returns:
-       Items per second, or None if no time elapsed
-
-   Thread-safe: Yes
- **`get_eta(self: Any) -> Optional[float]`**
-   Estimate time remaining in seconds.
-
-   Returns:
-       Estimated seconds remaining, or None if cannot estimate
-
-   Thread-safe: Yes
- **`format_eta(self: Any) -> str`**
-   Format ETA as human-readable string.
-
-   Returns:
-       ETA string (e.g., "2 minutes 30 seconds")
-
-   Thread-safe: Yes
- **`format_throughput(self: Any) -> str`**
-   Format throughput as human-readable string.
-
-   Returns:
-       Throughput string (e.g., "42.5 items/sec")
-
-   Thread-safe: Yes
- **`add_callback(self: Any, callback: Callable[[dict[str, Any]], None]) -> None`**
-   Add a progress callback.
-
-   Args:
-       callback: Function to call on progress updates
-
-   Thread-safe: Yes
- **`remove_callback(self: Any, callback: Callable[[dict[str, Any]], None]) -> None`**
-   Remove a progress callback.
-
-   Args:
-       callback: Function to remove
-
-   Thread-safe: Yes
- **`cancel(self: Any) -> None`**
-   Cancel the operation.
-
-   Thread-safe: Yes
- **`is_cancelled(self: Any) -> bool`**
-   Check if operation has been cancelled.
-
-   Returns:
-       True if cancelled
-
-   Thread-safe: Yes
- **`is_complete(self: Any) -> bool`**
-   Check if operation is complete.
-
-   Returns:
-       True if all items processed
-
-   Thread-safe: Yes
- **`reset(self: Any) -> None`**
-   Reset progress tracker to initial state.
-
-   Thread-safe: Yes
- **`update_description(self: Any, description: str) -> None`**
-   Update operation description.
-
-   Args:
-       description: New description
-
-   Thread-safe: Yes
- **`get_status(self: Any) -> dict[str, Any]`**
-   Get complete status dictionary.
-
-   Returns:
-       Dictionary with all progress information
-
-   Thread-safe: Yes
- **`_notify_callbacks(self: Any) -> None`**
-   Notify all registered callbacks of progress update.
-
-   Handles callback errors gracefully without stopping progress tracking.
- **`__enter__(self: Any)`**
-   Enter context manager.
- **`__exit__(self: Any, exc_type: Any, exc_val: Any, exc_tb: Any)`**
-   Exit context manager, marking as complete.

#### Attributes:
- `total_items`: `int`
- `description`: `str`
- `callback`: `Optional[Callable[[dict[str, Any]], None]]`

## Module: `pipeline.batch_processor`

### Class: `BatchProcessor`

Parallel batch processor for multiple files.

This class coordinates parallel processing of multiple files using
a thread pool, providing progress tracking and result aggregation.

Attributes:
    pipeline: ExtractionPipeline instance to use for processing
    max_workers: Maximum number of concurrent worker threads
    timeout_per_file: Optional timeout in seconds per file
    logger: Structured logger instance
    error_handler: Error handling component

Thread Safety:
    This class is thread-safe. The pipeline instances should also
    be thread-safe or use separate instances per thread.

#### Methods:
- **`__init__(self: Any, pipeline: Optional[ExtractionPipeline], max_workers: Optional[int], config: Optional[Dict[str, Any]])`**
-   Initialize batch processor.
-
-   Args:
-       pipeline: Optional ExtractionPipeline instance. Creates default if None.
-       max_workers: Maximum concurrent workers. Defaults to CPU count.
-       config: Optional configuration dict with keys:
-           - max_workers: Worker count override
-           - timeout_per_file: Timeout per file in seconds
-
-   Raises:
-       ValueError: If max_workers is <= 0
-
-   Example:
-       >>> batch = BatchProcessor(max_workers=4)
-       >>> batch = BatchProcessor(config={'max_workers': 8, 'timeout_per_file': 300})
- **`process_batch(self: Any, file_paths: List[Path], progress_callback: Optional[Callable[[Dict[str, Any]], None]]) -> List[PipelineResult]`**
-   Process multiple files in parallel.
-
-   This method processes all files concurrently using a thread pool,
-   tracking progress and collecting results.
-
-   Args:
-       file_paths: List of file paths to process
-       progress_callback: Optional callback for progress updates
-
-   Returns:
-       List of PipelineResult in same order as input files
-
-   Example:
-       >>> files = [Path("doc1.docx"), Path("doc2.pdf")]
-       >>> results = batch.process_batch(files)
-       >>> for result in results:
-       >>>     if result.success:
-       >>>         print(f"Success: {result.source_file}")
-       >>>     else:
-       >>>         print(f"Failed: {result.source_file}")
- **`_process_single_file(self: Any, file_path: Path, tracker: ProgressTracker) -> PipelineResult`**
-   Process a single file within the batch.
-
-   This is called by worker threads. It wraps pipeline processing
-   with error handling.
-
-   Args:
-       file_path: Path to file to process
-       tracker: Progress tracker instance
-
-   Returns:
-       PipelineResult for this file
- **`get_summary(self: Any, results: List[PipelineResult]) -> Dict[str, Any]`**
-   Get summary statistics for batch results.
-
-   Args:
-       results: List of pipeline results
-
-   Returns:
-       Dictionary with summary statistics:
-           - total_files: Total number of files processed
-           - successful: Number of successful files
-           - failed: Number of failed files
-           - success_rate: Fraction of successful files (0.0-1.0)
-           - failed_stages: Count of failures by stage
-
-   Example:
-       >>> summary = batch.get_summary(results)
-       >>> print(f"Success rate: {summary['success_rate']:.1%}")
- **`get_failed_results(self: Any, results: List[PipelineResult]) -> List[PipelineResult]`**
-   Extract failed results from batch.
-
-   Args:
-       results: List of pipeline results
-
-   Returns:
-       List of failed results only
-
-   Example:
-       >>> failed = batch.get_failed_results(results)
-       >>> for result in failed:
-       >>>     print(f"Failed: {result.source_file} - {result.all_errors}")
- **`get_successful_results(self: Any, results: List[PipelineResult]) -> List[PipelineResult]`**
-   Extract successful results from batch.
-
-   Args:
-       results: List of pipeline results
-
-   Returns:
-       List of successful results only
-
-   Example:
-       >>> successful = batch.get_successful_results(results)
-       >>> print(f"Processed {len(successful)} files successfully")

## Module: `pipeline.extraction_pipeline`

### Class: `ExtractionPipeline`
**Inherits from:** BasePipeline

Main pipeline orchestrator for document extraction.

This class coordinates the entire extraction workflow from file input
to formatted output, integrating extractors, processors, and formatters.

Attributes:
    config: Configuration manager instance
    error_handler: Error handling component
    logger: Structured logger instance

Thread Safety:
    This class is not thread-safe. Create separate instances for
    concurrent processing or use BatchProcessor.

#### Methods:
- **`__init__(self: Any, config: Optional[ConfigManager])`**
-   Initialize extraction pipeline.
-
-   Args:
-       config: Optional ConfigManager instance. If None, creates default.
- **`_create_default_config(self: Any) -> ConfigManager`**
-   Create default configuration.
-
-   Returns:
-       ConfigManager with default settings
- **`detect_format(self: Any, file_path: Path) -> Optional[str]`**
-   Detect file format from extension.
-
-   Args:
-       file_path: Path to file
-
-   Returns:
-       Format identifier (e.g., 'docx', 'pdf') or None if unknown
- **`register_extractor(self: Any, format_type: str, extractor: BaseExtractor) -> None`**
-   Register a format-specific extractor.
-
-   Args:
-       format_type: Format identifier (e.g., "docx", "pdf")
-       extractor: Extractor instance
-
-   Example:
-       >>> pipeline.register_extractor("docx", DocxExtractor())
- **`get_extractor(self: Any, format_type: str) -> Optional[BaseExtractor]`**
-   Get registered extractor for format.
-
-   Args:
-       format_type: Format identifier
-
-   Returns:
-       Extractor instance or None if not registered
- **`add_processor(self: Any, processor: BaseProcessor) -> None`**
-   Add a processor to the pipeline.
-
-   Processors are automatically ordered based on dependencies.
-
-   Args:
-       processor: Processor instance
-
-   Example:
-       >>> pipeline.add_processor(ContextLinker())
-       >>> pipeline.add_processor(MetadataAggregator())
- **`add_formatter(self: Any, formatter: BaseFormatter) -> None`**
-   Add an output formatter to the pipeline.
-
-   Multiple formatters can be added to generate multiple output formats.
-
-   Args:
-       formatter: Formatter instance
-
-   Example:
-       >>> pipeline.add_formatter(JsonFormatter())
-       >>> pipeline.add_formatter(MarkdownFormatter())
- **`_order_processors(self: Any) -> list[BaseProcessor]`**
-   Order processors based on dependencies using topological sort.
-
-   Returns:
-       Ordered list of processors
-
-   Raises:
-       ValueError: If circular dependency detected
- **`_report_progress(self: Any, callback: Optional[Callable[[dict[str, Any]], None]], stage: str, percentage: float, message: Optional[str]) -> None`**
-   Report progress to callback if provided.
-
-   Args:
-       callback: Progress callback function
-       stage: Current pipeline stage
-       percentage: Completion percentage (0-100)
-       message: Optional progress message
- **`process_file(self: Any, file_path: Path, progress_callback: Optional[Callable[[dict[str, Any]], None]]) -> PipelineResult`**
-   Decorators: timed(get_logger(__name__))
-   Process a single file through the complete pipeline.
-
-   This is the main entry point for file processing. It coordinates:
-   1. Validation
-   2. Extraction
-   3. Processing (all processors in dependency order)
-   4. Formatting (all formatters in parallel)
-
-   Args:
-       file_path: Path to file to process
-       progress_callback: Optional callback for progress updates
-
-   Returns:
-       PipelineResult with results from all stages
-
-   Example:
-       >>> result = pipeline.process_file(Path("document.docx"))
-       >>> if result.success:
-       >>>     print(f"Success! Generated {len(result.formatted_outputs)} outputs")
-       >>> else:
-       >>>     print(f"Failed at {result.failed_stage}: {result.all_errors}")

## Module: `processors.context_linker`

### Class: `ContextLinker`
**Inherits from:** BaseProcessor

Build hierarchical document structure from flat content blocks.

This processor enriches content blocks with:
- parent_id: Links to parent heading (if any)
- depth: Nesting depth in document hierarchy
- document_path: List of heading titles from root to this block

Algorithm:
1. Maintain heading stack (tracks current heading at each level)
2. For each block:
   - If heading: Update stack at that level, clear deeper levels
   - If content: Link to most recent heading
3. Compute depth based on hierarchy position
4. Generate document path by walking up parent chain

Configuration:
- max_depth (int): Maximum nesting depth to track (default: 10)
- include_path (bool): Include document_path in metadata (default: True)

#### Methods:
- **`get_processor_name(self: Any) -> str`**
-   Return processor name.
- **`is_optional(self: Any) -> bool`**
-   ContextLinker is required for downstream processors.
- **`get_dependencies(self: Any) -> list[str]`**
-   ContextLinker has no dependencies - runs first.
- **`process(self: Any, extraction_result: ExtractionResult) -> ProcessingResult`**
-   Process extracted content to build document hierarchy.
-
-   Args:
-       extraction_result: Raw extraction result
-
-   Returns:
-       ProcessingResult with enriched content blocks
-
-   Processing Steps:
-   1. Handle empty input gracefully
-   2. Build heading stack while processing blocks
-   3. Enrich each block with hierarchy metadata
-   4. Compute statistics for stage_metadata
- **`_find_parent_heading(self: Any, heading_stack: dict, current_level: int) -> Optional`**
-   Find parent heading for a heading block.
-
-   Parent is the most recent heading at a higher level.
-   If no higher-level heading exists, returns None (root-level).
-
-   Args:
-       heading_stack: Current heading stack
-       current_level: Level of current heading
-
-   Returns:
-       Block ID of parent heading, or None if root
- **`_find_current_parent(self: Any, heading_stack: dict) -> Optional`**
-   Find parent heading for a content block.
-
-   Parent is the most recent heading at any level.
-
-   Args:
-       heading_stack: Current heading stack
-
-   Returns:
-       Block ID of parent heading, or None if no headings
- **`_compute_depth(self: Any, heading_stack: dict) -> int`**
-   Compute depth for a content block.
-
-   Depth is one level deeper than the current heading level.
-
-   Args:
-       heading_stack: Current heading stack
-
-   Returns:
-       Depth value (0 if no headings, else level of deepest heading + 1)
- **`_build_document_path(self: Any, heading_stack: dict, current_level: int) -> list[str]`**
-   Build document path for a heading block.
-
-   Path includes all ancestor headings but not the current heading itself.
-
-   Args:
-       heading_stack: Current heading stack
-       current_level: Level of current heading
-
-   Returns:
-       List of heading titles from root to parent
- **`_build_full_document_path(self: Any, heading_stack: dict) -> list[str]`**
-   Build complete document path for a content block.
-
-   Path includes all ancestor headings.
-
-   Args:
-       heading_stack: Current heading stack
-
-   Returns:
-       List of heading titles from root to current parent

## Module: `processors.metadata_aggregator`

### Class: `MetadataAggregator`
**Inherits from:** BaseProcessor

Compute statistics and extract entities from content.

This processor enriches content blocks with:
- word_count: Number of words in block
- char_count: Number of characters in block
- entities: List of extracted entities (optional)

And adds to stage_metadata:
- total_words: Sum of all words
- total_characters: Sum of all characters
- average_words_per_block: Mean word count
- min_words_per_block: Minimum word count
- max_words_per_block: Maximum word count
- content_type_distribution: Count by content type
- unique_content_types: Number of unique types
- summary: High-level document summary

Configuration:
- enable_entities (bool): Enable entity extraction (default: False)
- summary_max_headings (int): Max headings in summary (default: 5)

#### Methods:
- **`get_processor_name(self: Any) -> str`**
-   Return processor name.
- **`is_optional(self: Any) -> bool`**
-   MetadataAggregator is optional - enrichment, not critical.
- **`get_dependencies(self: Any) -> list[str]`**
-   Can run independently or after ContextLinker.
- **`process(self: Any, extraction_result: ExtractionResult) -> ProcessingResult`**
-   Process extracted content to compute statistics.
-
-   Args:
-       extraction_result: Raw extraction result
-
-   Returns:
-       ProcessingResult with enriched metadata
-
-   Processing Steps:
-   1. Handle empty input
-   2. Compute block-level statistics (word counts, char counts)
-   3. Extract entities if configured
-   4. Aggregate document-level statistics
-   5. Generate summary
- **`_count_words(self: Any, text: str) -> int`**
-   Count words in text.
-
-   Simple whitespace-based word counting.
-
-   Args:
-       text: Text to count words in
-
-   Returns:
-       Number of words
- **`_extract_entities(self: Any, text: str) -> list[str]`**
-   Extract named entities from text.
-
-   This is a placeholder for entity extraction. In production,
-   this would use spaCy or another NLP library.
-
-   Args:
-       text: Text to extract entities from
-
-   Returns:
-       List of entity strings (empty for now)
-
-   Note:
-       Actual implementation would use:
-       ```python
-       import spacy
-       nlp = spacy.load("en_core_web_sm")
-       doc = nlp(text)
-       return [ent.text for ent in doc.ents]
-       ```

## Module: `processors.quality_validator`

### Class: `QualityValidator`
**Inherits from:** BaseProcessor

Validate extraction quality and compute quality scores.

This processor:
- Computes quality score (0-100) based on multiple dimensions
- Identifies specific quality issues
- Sets needs_review flag for low-quality extractions
- Provides detailed quality metrics in stage_metadata

Quality Dimensions:
1. Completeness (0-100):
   - Presence of headings
   - Content type diversity
   - Document structure

2. Consistency (0-100):
   - Confidence scores present
   - Metadata completeness
   - Block structure validity

3. Readability (0-100):
   - Text appears readable
   - Not corrupted or garbled
   - Reasonable character distributions

Overall Score:
    Average of all dimension scores

Configuration:
- needs_review_threshold (float): Score below which needs_review=True (default: 60.0)
- empty_block_penalty (float): Penalty per empty block (default: 5.0)
- low_confidence_threshold (float): Threshold for low confidence warning (default: 0.5)

#### Methods:
- **`get_processor_name(self: Any) -> str`**
-   Return processor name.
- **`is_optional(self: Any) -> bool`**
-   QualityValidator is optional - informational only.
- **`get_dependencies(self: Any) -> list[str]`**
-   Can benefit from MetadataAggregator but not required.
- **`process(self: Any, extraction_result: ExtractionResult) -> ProcessingResult`**
-   Process extracted content to validate quality.
-
-   Args:
-       extraction_result: Raw extraction result
-
-   Returns:
-       ProcessingResult with quality score and issues
-
-   Processing Steps:
-   1. Check for empty input (low score)
-   2. Compute completeness score
-   3. Compute consistency score
-   4. Compute readability score
-   5. Calculate overall quality score
-   6. Identify specific issues
-   7. Determine if review needed
- **`_compute_completeness(self: Any, blocks: tuple[ContentBlock, Ellipsis]) -> tuple[float, dict]`**
-   Compute completeness score.
-
-   Checks for:
-   - Presence of headings (structure)
-   - Content type diversity
-   - Empty blocks (penalty)
-
-   Args:
-       blocks: Content blocks to analyze
-
-   Returns:
-       Tuple of (score, analysis_data)
- **`_compute_consistency(self: Any, blocks: tuple[ContentBlock, Ellipsis]) -> tuple[float, dict]`**
-   Compute consistency score.
-
-   Checks for:
-   - Confidence scores present
-   - Confidence scores reasonable
-   - Metadata completeness
-
-   Args:
-       blocks: Content blocks to analyze
-
-   Returns:
-       Tuple of (score, analysis_data)
- **`_compute_readability(self: Any, blocks: tuple[ContentBlock, Ellipsis]) -> tuple[float, dict]`**
-   Compute readability score.
-
-   Checks for:
-   - Excessive special characters (corruption)
-   - Very long words (potential gibberish)
-   - Readable character distribution
-
-   Args:
-       blocks: Content blocks to analyze
-
-   Returns:
-       Tuple of (score, analysis_data)
- **`_special_char_ratio(self: Any, text: str) -> float`**
-   Calculate ratio of special characters to total characters.
-
-   Args:
-       text: Text to analyze
-
-   Returns:
-       Ratio (0.0 to 1.0)
- **`_has_abnormal_words(self: Any, text: str) -> bool`**
-   Check for abnormally long words (potential corruption).
-
-   Args:
-       text: Text to analyze
-
-   Returns:
-       True if abnormal words found
