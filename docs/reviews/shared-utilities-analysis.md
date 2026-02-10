# Shared Utilities Analysis

## Summary
- Files scanned: 7 core module files
- Key findings:
  - Protocol-based pipeline architecture for type-safe stage composition
  - Comprehensive exception hierarchy with recoverable vs critical errors
  - Pydantic v2 models for runtime validation (Document, Chunk, Entity, Metadata)
  - Abstract base classes for extractors, processors, formatters
  - spaCy integration for NLP utilities (sentence boundaries)
  - Dual codebase structure (greenfield + brownfield)

## Detailed Analysis

### Core Modules Organization

#### Greenfield Core (`src/data_extract/core/` - 4 files)

**Architecture**: Modern modular pipeline (Epic 1+)

**Files**:
1. `models.py` (360 lines) - Pydantic v2 data models
2. `pipeline.py` (130 lines) - Protocol-based pipeline orchestration
3. `exceptions.py` (145 lines) - Exception hierarchy
4. `__init__.py` - Module exports

**Design Principles**:
- Type safety with Protocol-based composition
- Immutability where appropriate (frozen models)
- Deterministic processing for reproducibility
- Clear separation of concerns

#### Brownfield Core (`src/core/` - 3 files)

**Architecture**: Legacy implementation being consolidated

**Files**:
1. `models.py` - ExtractionResult, ProcessingResult, FormattedOutput (brownfield)
2. `interfaces.py` - BaseExtractor, BaseProcessor, BaseFormatter ABCs
3. `__init__.py` - Module exports

**Status**: Being assessed and migrated to greenfield (Story 1.2-1.4)

#### Shared Utilities (`src/data_extract/utils/` - 2 files)

**Files**:
1. `nlp.py` (92 lines) - spaCy integration for sentence boundaries
2. `__init__.py` - Module exports

**Purpose**: Reusable NLP utilities for Epic 3 (chunking)

### Pipeline Architecture

#### PipelineStage Protocol (`src/data_extract/core/pipeline.py`)

**Protocol Definition**:
```python
class PipelineStage(Protocol, Generic[Input, Output]):
    """Protocol defining contract for all pipeline stages.

    Type Parameters:
        Input: Type of input data accepted by this stage
        Output: Type of output data produced by this stage
    """

    def process(self, input_data: Input, context: ProcessingContext) -> Output:
        """Process input data and return transformed output."""
        ...
```

**Key Features**:
- **Generic Type Parameters**: Compile-time type safety with `Input` and `Output` type variables
- **Protocol-Based**: Duck typing for flexible composition (not inheritance-based)
- **Context Propagation**: ProcessingContext carries config, logger, metrics through pipeline
- **Contract Requirements**:
  1. `process()` method accepts `input_data` of type `Input`
  2. `process()` method accepts `context: ProcessingContext`
  3. `process()` method returns data of type `Output`
  4. Stages should be stateless (all state in ProcessingContext)
  5. Stages should be deterministic (for audit reproducibility)

**Error Handling Contract**:
- `ProcessingError`: Recoverable errors (log, skip file, continue batch)
- `CriticalError`: Unrecoverable errors (halt processing immediately)

#### Pipeline Orchestrator

**Pipeline Class**:
```python
class Pipeline:
    """Pipeline orchestrator that chains multiple stages together.

    Orchestrates execution of multiple pipeline stages by passing output
    of each stage as input to the next stage.
    """

    def __init__(self, stages: List[PipelineStage]) -> None:
        """Initialize pipeline with list of stages."""
        self.stages = stages

    def process(self, initial_input: Any, context: ProcessingContext) -> Any:
        """Execute all pipeline stages in sequence."""
        current_data = initial_input
        for stage in self.stages:
            current_data = stage.process(current_data, context)
        return current_data
```

**Usage Pattern**:
```python
# Define pipeline stages
pipeline = Pipeline([
    ExtractStage(),
    NormalizeStage(),
    ChunkStage(),
    SemanticStage(),
    OutputStage()
])

# Execute pipeline
context = ProcessingContext(config={"chunk_size": 512})
result = pipeline.process(raw_document, context)
```

**Benefits**:
- Type-safe composition (mypy validates stage compatibility)
- Easy testing (each stage independently testable)
- Flexible refactoring (swap stages, add new stages)
- Clear data flow (input → stage1 → stage2 → ... → output)

### Exception Hierarchy

**Exception Structure** (`src/data_extract/core/exceptions.py`):

```
DataExtractError (base)
├── ProcessingError (recoverable)
│   ├── ExtractionError
│   └── ValidationError
└── CriticalError (unrecoverable)
    └── ConfigurationError
```

**Exception Classes** (6 total):

#### 1. DataExtractError (Base)
```python
class DataExtractError(Exception):
    """Base exception for all data extraction tool errors.

    Allows catching all tool-specific errors with single except clause.
    """
```

**When to use**: Never directly - use subclasses

#### 2. ProcessingError (Recoverable)
```python
class ProcessingError(DataExtractError):
    """Recoverable error during document processing.

    Pipeline should log error, quarantine file, continue with remaining files.
    """
```

**When to use**:
- Document extraction fails for a single file
- Data validation fails for a single document
- OCR quality is below acceptable threshold
- Entity extraction fails for a document

**Handling pattern**:
```python
try:
    process_document(file)
except ProcessingError as e:
    logger.warning(f"Skipping file: {e}")
    quarantine_file(file)
    # Continue with next file
```

#### 3. CriticalError (Unrecoverable)
```python
class CriticalError(DataExtractError):
    """Unrecoverable error requiring immediate halt.

    Processing should stop immediately and report error to user.
    """
```

**When to use**:
- Invalid or missing configuration file
- Database connection failure
- Insufficient system resources (disk space, memory)
- Required dependencies missing

**Handling pattern**:
```python
if not config_file.exists():
    raise CriticalError(f"Configuration file not found: {config_file}")
```

#### 4. ConfigurationError (Critical)
```python
class ConfigurationError(CriticalError):
    """Configuration-related critical error.

    Extends CriticalError - configuration errors always halt processing.
    """
```

**When to use**:
- Configuration file missing or unreadable
- Invalid configuration values (e.g., negative batch size)
- Required configuration keys missing
- Configuration version incompatible with tool version

**Example**:
```python
if "batch_size" not in config:
    raise ConfigurationError("Required config key 'batch_size' missing")
if config["batch_size"] <= 0:
    raise ConfigurationError("batch_size must be positive")
```

#### 5. ExtractionError (Processing)
```python
class ExtractionError(ProcessingError):
    """Document extraction failure (recoverable).

    Extends ProcessingError - extraction failures are file-specific.
    """
```

**When to use**:
- PDF extraction fails (corrupted file, unsupported format)
- Excel workbook cannot be read
- PowerPoint slide deck has encoding issues
- OCR fails for scanned image

**Example**:
```python
try:
    content = extract_pdf(file_path)
except Exception as e:
    raise ExtractionError(f"Failed to extract {file_path}: {e}")
```

#### 6. ValidationError (Processing)
```python
class ValidationError(ProcessingError):
    """Data validation failure (recoverable).

    Validation errors are typically file-specific and recoverable.
    """
```

**When to use**:
- Extracted data fails schema validation
- Required fields missing from extracted document
- Data quality below acceptable threshold
- Entity extraction confidence too low

**Example**:
```python
if chunk.quality_score < 0.5:
    raise ValidationError(f"Chunk quality {chunk.quality_score} below threshold 0.5")
if not document.text.strip():
    raise ValidationError("Document text is empty")
```

**Error Handling Strategy**:
- **ProcessingError**: Log warning, quarantine file, continue with remaining batch (ADR-006 continue-on-error)
- **CriticalError**: Log error and halt processing immediately

### Data Models

**Pydantic v2 Models** (`src/data_extract/core/models.py` - 360 lines):

#### Enums (3 types)

**1. EntityType** (6 values):
```python
class EntityType(str, Enum):
    """Audit domain entity types."""
    PROCESS = "process"
    RISK = "risk"
    CONTROL = "control"
    REGULATION = "regulation"
    POLICY = "policy"
    ISSUE = "issue"
```

**2. DocumentType** (4 values):
```python
class DocumentType(str, Enum):
    """Document classification types."""
    REPORT = "report"      # Narrative documents (Word, PDF)
    MATRIX = "matrix"      # Tabular documents (Excel)
    EXPORT = "export"      # System exports (Archer GRC HTML/XML)
    IMAGE = "image"        # Scanned documents or images (OCR)
```

**3. QualityFlag** (4 values):
```python
class QualityFlag(str, Enum):
    """Quality validation flags."""
    LOW_OCR_CONFIDENCE = "low_ocr_confidence"
    MISSING_IMAGES = "missing_images"
    INCOMPLETE_EXTRACTION = "incomplete_extraction"
    COMPLEX_OBJECTS = "complex_objects"
```

#### Core Models (6 models)

**1. Entity**:
```python
class Entity(BaseModel):
    """Domain entity extracted from documents.

    Attributes:
        type: Entity type from EntityType enum
        id: Canonical entity identifier (e.g., 'Risk-123')
        text: Entity text content as it appears in document
        confidence: Confidence score (0.0-1.0) for entity extraction
        location: Character position in document (start and end indices)
    """
    type: EntityType
    id: str
    text: str
    confidence: float  # 0.0-1.0
    location: Dict[str, int]  # {"start": 0, "end": 10}
```

**2. Metadata**:
```python
class Metadata(BaseModel):
    """Provenance and quality tracking metadata.

    Embedded in Document and Chunk models to track processing history,
    quality metrics, and audit trail information.

    Key Attributes:
        source_file: Path to original source file
        file_hash: SHA-256 hash for integrity verification
        processing_timestamp: When processed
        tool_version, config_version: Versioning for reproducibility
        document_type: Classification (report, matrix, export, image)
        quality_scores: Quality metrics dict (e.g., {'ocr_confidence': 0.95})
        quality_flags: List of quality warnings/flags
        ocr_confidence: Per-page OCR confidence scores (page_num -> confidence)
        completeness_ratio: Extraction completeness (0.0-1.0)
        entity_tags: Canonical entity IDs for RAG retrieval filtering
        entity_counts: Count of entities by type (e.g., {'risk': 5, 'control': 3})
        config_snapshot: Full configuration snapshot for reproducibility
        validation_report: Serialized ValidationReport with quality results
    """
    source_file: Path
    file_hash: str  # SHA-256
    processing_timestamp: datetime
    tool_version: str
    config_version: str
    document_type: Optional[Union[DocumentType, str]] = None
    document_subtype: Optional[str] = None
    quality_scores: Dict[str, float] = Field(default_factory=dict)
    ocr_confidence: Dict[int, float] = Field(default_factory=dict)
    completeness_ratio: Optional[float] = None  # 0.0-1.0
    quality_flags: List[str] = Field(default_factory=list)
    entity_tags: List[str] = Field(default_factory=list)
    entity_counts: Dict[str, int] = Field(default_factory=dict)
    config_snapshot: Dict[str, Any] = Field(default_factory=dict)
    validation_report: Dict[str, Any] = Field(default_factory=dict)
```

**3. ValidationReport**:
```python
class ValidationReport(BaseModel):
    """OCR and extraction quality validation report.

    Attributes:
        quarantine_recommended: Whether to quarantine for manual review
        confidence_scores: Per-page OCR confidence (page_num -> confidence)
        quality_flags: List of quality issues (from QualityFlag enum)
        extraction_gaps: Descriptions of extraction gaps
        document_average_confidence: Document-level OCR confidence (0.0-1.0)
        scanned_pdf_detected: Whether document is scanned vs native PDF
        completeness_passed: Whether completeness ratio meets threshold (>=0.90)
        missing_images_count: Count of images without alt text
        complex_objects_count: Count of complex objects (OLE, charts, diagrams)
    """
    quarantine_recommended: bool
    confidence_scores: Dict[int, float] = Field(default_factory=dict)
    quality_flags: List[QualityFlag] = Field(default_factory=list)
    extraction_gaps: List[str] = Field(default_factory=list)
    document_average_confidence: Optional[float] = None  # 0.0-1.0
    scanned_pdf_detected: Optional[bool] = None
    completeness_passed: bool = True
    missing_images_count: int = 0
    complex_objects_count: int = 0
```

**4. Document**:
```python
class Document(BaseModel):
    """Processed document model.

    Type contract: Extract → Normalize stage.

    Attributes:
        id: Unique document identifier
        text: Document text content (raw or normalized)
        entities: List of extracted entities
        metadata: Processing metadata and quality tracking
        structure: Document structure metadata (e.g., sections, pages)
    """
    id: str
    text: str
    entities: List[Entity] = Field(default_factory=list)
    metadata: Metadata
    structure: Dict[str, Any] = Field(default_factory=dict)
```

**5. Chunk**:
```python
class Chunk(BaseModel):
    """Semantic chunk for RAG (Retrieval-Augmented Generation).

    Type contract: Chunk → Semantic stage.

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
        readability_scores: Readability metrics (e.g., flesch_reading_ease)
        metadata: Processing metadata and quality tracking
    """
    id: str  # Format: {source}_{index:03d}
    text: str
    document_id: str
    position_index: int  # >= 0
    token_count: int  # >= 0
    word_count: int  # >= 0
    entities: List[Entity] = Field(default_factory=list)
    section_context: str = ""
    quality_score: float  # 0.0-1.0
    readability_scores: Dict[str, float] = Field(default_factory=dict)
    metadata: Metadata
```

**6. ProcessingContext**:
```python
class ProcessingContext(BaseModel):
    """Shared pipeline state passed through all stages.

    Carries configuration, logger, and metrics through entire pipeline
    to ensure deterministic processing and audit trail.

    Attributes:
        config: Configuration dictionary (CLI > env > YAML > defaults)
        logger: Structured logger instance for audit trail
        metrics: Metrics accumulation dictionary
    """
    model_config = ConfigDict(frozen=False, arbitrary_types_allowed=True)

    config: Dict[str, Any] = Field(default_factory=dict)
    logger: Optional[Any] = Field(default=None)
    metrics: Dict[str, Any] = Field(default_factory=dict)
```

**Pydantic Configuration**:
- `frozen=False` (mutable for pipeline updates)
- `arbitrary_types_allowed=True` (for logger instances)
- Field validation with `ge=0`, `le=1.0` constraints
- Custom validators (e.g., `validate_document_type`)

### Abstract Base Classes

**Brownfield Interfaces** (`src/core/interfaces.py`):

#### BaseExtractor (ABC)

**Contract**:
```python
class BaseExtractor(ABC):
    """Abstract base class for all format-specific extractors.

    Contract:
    - extract() must return ExtractionResult with success flag
    - If extraction fails, return ExtractionResult with success=False and errors
    - Never raise exceptions for file-level failures
    - DO raise exceptions for programming errors
    """

    @abstractmethod
    def extract(self, file_path: Path) -> ExtractionResult:
        """Extract content from file."""
        pass

    @abstractmethod
    def supports_format(self, file_path: Path) -> bool:
        """Check if this extractor can handle the given file."""
        pass

    def supports_streaming(self) -> bool:
        """Whether extractor can process files incrementally."""
        return False

    def validate_file(self, file_path: Path) -> tuple[bool, list[str]]:
        """Pre-extraction validation."""
        # Default implementation checks file existence, not empty
        pass

    def get_format_name(self) -> str:
        """Return human-readable format name."""
        return self.__class__.__name__.replace("Extractor", "")

    def get_supported_extensions(self) -> list[str]:
        """Return list of supported file extensions."""
        return []
```

**Implemented by**: DocxExtractor, PdfExtractor, XlsxExtractor, PptxExtractor, CsvExtractor, TextFileExtractor

#### BaseProcessor (ABC)

**Contract**:
```python
class BaseProcessor(ABC):
    """Abstract base class for content processors.

    Processors enrich extracted content.

    Contract:
    - process() takes ExtractionResult, returns ProcessingResult
    - Processors are composable (output of one is input to next)
    - Processors declare dependencies (which processors must run first)
    """

    @abstractmethod
    def process(self, extraction_result: ExtractionResult) -> ProcessingResult:
        """Process extraction result and return enriched result."""
        pass

    def get_dependencies(self) -> list[str]:
        """Return list of processor names this depends on."""
        return []
```

**Implemented by**: ContextLinker, MetadataAggregator, QualityValidator, ImageAnalyzer

#### BaseFormatter (ABC)

**Contract**:
```python
class BaseFormatter(ABC):
    """Abstract base class for output formatters.

    Formatters convert ProcessingResult to desired output format.

    Contract:
    - format() takes ProcessingResult, returns FormattedOutput
    - Formatters are stateless (thread-safe)
    """

    @abstractmethod
    def format(self, processing_result: ProcessingResult) -> FormattedOutput:
        """Format processing result to output format."""
        pass

    def get_format_name(self) -> str:
        """Return human-readable format name."""
        return self.__class__.__name__.replace("Formatter", "")
```

**Implemented by**: JsonFormatter, MarkdownFormatter, ChunkedTextFormatter

### NLP Utilities

**spaCy Integration** (`src/data_extract/utils/nlp.py` - 92 lines):

#### Sentence Boundary Detection

**Function**:
```python
def get_sentence_boundaries(text: str, nlp: Optional[Language] = None) -> List[int]:
    """Extract sentence boundary positions from text using spaCy.

    Returns character offsets (zero-indexed) where each sentence ends.
    Lazy loads en_core_web_md model if nlp parameter is None.

    Args:
        text: Input text to segment into sentences (non-empty)
        nlp: Optional pre-loaded spaCy Language model

    Returns:
        List of character positions where sentences end
        Example: "Hello. World." returns [6, 13]

    Raises:
        ValueError: If text is empty or whitespace-only
        OSError: If en_core_web_md model is not installed

    NFR Compliance:
        - NFR-P3: Model load <5s, segmentation <100ms per 1000 words
        - NFR-O4: Logs model version on first load
        - NFR-R3: Clear error messages for missing model or invalid input
    """
    # Implementation uses global _nlp_model cache
    # Lazy loads spacy.load("en_core_web_md") on first call
    # Logs model metadata on first load
    # Returns [sent.end_char for sent in doc.sents]
```

**Features**:
- **Lazy Loading**: Model loaded once, cached globally (`_nlp_model`)
- **Model Metadata Logging** (on first load):
  - model_name: "en_core_web_md"
  - version, language, vocab_size
- **Performance**: Model load ~1.2s, processes 4000+ words/second
- **Error Handling**: Clear error messages with installation instructions

**Usage Pattern**:
```python
# Lazy load (first call)
boundaries = get_sentence_boundaries("Dr. Smith visited. This is sentence two.")
# Returns: [18, 42]

# Subsequent calls use cached model
boundaries = get_sentence_boundaries("Hello. World.")
# Returns: [6, 13]

# Or provide pre-loaded model
import spacy
nlp = spacy.load("en_core_web_md")
boundaries = get_sentence_boundaries("Text here.", nlp=nlp)
```

**Model Installation** (Story 2.5.2):
```bash
# Download required language model (43MB, one-time)
python -m spacy download en_core_web_md

# Verify installation
python -m spacy validate

# Test loading
python -c "import spacy; nlp = spacy.load('en_core_web_md'); print(f'Model loaded: {nlp.meta[\"version\"]}')"
```

**CI/CD Integration**: spaCy models automatically cached in CI (transparent to developers).

### Dual Codebase Structure

**Greenfield** (`src/data_extract/`):
- Modern modular architecture (Epic 1+)
- Full type hints, Pydantic v2 models
- Strict mypy compliance
- Protocol-based pipeline
- Target coverage: 80%+

**Brownfield** (`src/(cli|extractors|processors|formatters|core|pipeline|infrastructure)/`):
- Legacy code being assessed (Story 1.2-1.4)
- Excluded from mypy strict checks (pyproject.toml)
- Maintained during migration
- Gradual consolidation into greenfield

**Migration Strategy**:
- Both systems coexist during Epic 1
- Greenfield code references brownfield via adapters
- Tests validate interop (greenfield ↔ brownfield)
- Don't break existing brownfield functionality

## Recommendations

### Code Organization Improvements

1. **Consolidate Core Modules**
   - Merge `src/data_extract/core/models.py` and `src/core/models.py`
   - Single source of truth for data models
   - Avoid duplication between greenfield and brownfield

2. **Expand Utilities Module**
   - Add `src/data_extract/utils/text.py` for text processing utilities
   - Add `src/data_extract/utils/validation.py` for validation helpers
   - Add `src/data_extract/utils/hashing.py` for file hashing utilities
   - Move common functions from extractors to utils

3. **Create Shared Constants Module**
   - Add `src/data_extract/core/constants.py` for magic numbers
   - Examples: DEFAULT_CHUNK_SIZE, MAX_FILE_SIZE_MB, OCR_CONFIDENCE_THRESHOLD
   - Centralize configuration defaults

### Pipeline Architecture Enhancements

1. **Add Pipeline Middleware**
   - Implement middleware pattern for cross-cutting concerns
   - Examples: logging, metrics, error handling, retries
   - Middleware wraps stages transparently

2. **Implement Pipeline Builder**
   - Fluent API for pipeline construction:
     ```python
     pipeline = (PipelineBuilder()
         .add_stage(ExtractStage())
         .add_stage(NormalizeStage())
         .add_stage(ChunkStage())
         .build())
     ```

3. **Add Pipeline Validation**
   - Validate stage compatibility at pipeline construction time
   - Check type compatibility (stage N output = stage N+1 input)
   - Fail fast with clear error messages

4. **Implement Conditional Stages**
   - Add conditional execution based on context:
     ```python
     if context.config.get("enable_ocr", True):
         result = ocr_stage.process(result, context)
     ```

### Exception Handling Improvements

1. **Add Exception Context**
   - Enrich exceptions with context:
     ```python
     raise ExtractionError(
         f"Failed to extract {file_path}",
         file_path=file_path,
         extractor=self.__class__.__name__,
         original_error=str(e)
     )
     ```

2. **Implement Error Codes**
   - Integrate with `error_codes.yaml`
   - Add error code to exceptions:
     ```python
     raise ConfigurationError("batch_size must be positive", code="E403")
     ```

3. **Add Exception Chaining**
   - Use `raise ... from e` pattern consistently
   - Preserve original exception for debugging

4. **Create Exception Utilities**
   - Add `src/data_extract/core/error_utils.py`
   - Functions: `format_exception()`, `get_error_message()`, `is_recoverable()`

### Data Model Enhancements

1. **Add Model Serialization**
   - Implement `to_dict()`, `from_dict()` methods
   - Add `to_json()`, `from_json()` methods
   - Implement `to_yaml()`, `from_yaml()` methods

2. **Add Model Versioning**
   - Include schema version in all models
   - Implement migration logic for schema changes
   - Validate schema version on deserialization

3. **Implement Model Factories**
   - Factory functions for common model creation patterns
   - Examples: `create_empty_document()`, `create_chunk_from_text()`

4. **Add Model Validation Utilities**
   - Create `validate_document()`, `validate_chunk()` functions
   - Comprehensive validation beyond Pydantic (business rules)

### NLP Utilities Expansion

1. **Add Text Processing Functions**
   - `tokenize(text)` - Token extraction
   - `count_tokens(text)` - Token counting
   - `normalize_whitespace(text)` - Whitespace normalization
   - `detect_language(text)` - Language detection

2. **Add Readability Metrics**
   - Integrate textstat library
   - Functions: `flesch_reading_ease()`, `gunning_fog()`, `smog_index()`
   - Add to Chunk quality scoring

3. **Add Entity Linking Utilities**
   - `link_entity_mentions(text, entities)` - Cross-reference linking
   - `normalize_entity_id(id, type)` - ID normalization
   - `extract_entity_context(text, entity)` - Context extraction

### Testing Improvements

1. **Add Property-Based Testing**
   - Use Hypothesis for data model testing
   - Generate random valid/invalid inputs
   - Test invariants (e.g., quality_score always 0.0-1.0)

2. **Add Contract Testing**
   - Verify all extractors implement BaseExtractor contract
   - Verify all processors implement BaseProcessor contract
   - Verify all formatters implement BaseFormatter contract

3. **Add Integration Tests for Core**
   - Test pipeline orchestration with real stages
   - Test exception propagation through pipeline
   - Test context propagation through stages

### Documentation Improvements

1. **Add Architecture Decision Records (ADRs)**
   - ADR: Protocol-based pipeline vs inheritance-based
   - ADR: Pydantic v2 for data models
   - ADR: Exception hierarchy design
   - ADR: Dual codebase migration strategy

2. **Create Developer Guide**
   - How to add new pipeline stage
   - How to add new data model
   - How to add new utility function
   - Testing guidelines for core modules

3. **Add API Reference**
   - Auto-generate from docstrings (Sphinx, mkdocs)
   - Include usage examples for all public APIs
   - Document type signatures clearly

### Performance Optimizations

1. **Profile Core Operations**
   - Profile pipeline orchestration overhead
   - Profile Pydantic model creation/validation
   - Profile spaCy model loading and processing
   - Optimize hot paths

2. **Implement Caching**
   - Cache compiled regex patterns
   - Cache spaCy model globally (already done)
   - Cache entity normalization lookups

3. **Add Performance Benchmarks**
   - Benchmark pipeline stage overhead
   - Benchmark model serialization/deserialization
   - Benchmark sentence boundary detection

### Epic 5 Readiness

**Core Module Requirements**:
- [ ] Consolidate dual codebase (greenfield absorbs brownfield)
- [ ] Finalize data model schema (versioning strategy)
- [ ] Complete exception hierarchy integration with error codes
- [ ] Add pipeline middleware support
- [ ] Expand utility modules (text, validation, hashing)
- [ ] Write comprehensive API documentation
- [ ] Achieve 80%+ test coverage for core modules
