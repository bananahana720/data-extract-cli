# Source Tree Analysis - Data Extraction Tool

**Generated**: 2025-11-07
**Project**: Data Extraction Tool for RAG-Optimized Knowledge Curation
**Version**: v1.0.6
**Purpose**: Comprehensive source code organization reference

---

## Directory Structure Overview

```
data-extraction-tool/
├── bmad/                    # BMad Method framework (workflows, agents, modules)
├── docs/                    # Project documentation
├── examples/                # Working code examples
├── src/                     # Main source code (Python package)
├── tests/                   # Test suite
├── scripts/                 # Utility scripts
├── dist/                    # Distribution packages
├── config/                  # Configuration files
└── [Root config files]      # Project configuration
```

---

## Source Code Structure (`src/`)

### Package Organization

```
src/
├── __init__.py                          # Package initialization
├── cli/                                 # Command-line interface
│   ├── __init__.py
│   ├── main.py                          # CLI entry point
│   └── commands.py                      # CLI command implementations
├── core/                                # Core data models and interfaces
│   ├── __init__.py                      # Public API exports
│   ├── models.py                        # Data structures (ContentBlock, etc.)
│   └── interfaces.py                    # Abstract base classes
├── extractors/                          # Format-specific extractors
│   ├── __init__.py                      # Extractor exports
│   ├── docx_extractor.py                # Word documents (tables + images)
│   ├── pdf_extractor.py                 # PDFs with OCR support
│   ├── pptx_extractor.py                # PowerPoint presentations
│   ├── excel_extractor.py               # Excel workbooks
│   ├── csv_extractor.py                 # CSV/TSV files
│   └── txt_extractor.py                 # Plain text files
├── processors/                          # Content enrichment processors
│   ├── __init__.py                      # Processor exports
│   ├── context_linker.py                # Hierarchy builder
│   ├── metadata_aggregator.py           # Statistics computer
│   └── quality_validator.py             # Quality scorer
├── formatters/                          # Output formatters
│   ├── __init__.py                      # Formatter exports
│   ├── json_formatter.py                # JSON output
│   ├── markdown_formatter.py            # Markdown output
│   └── chunked_text_formatter.py        # Chunked text output
├── pipeline/                            # Pipeline orchestration
│   ├── __init__.py                      # Pipeline exports
│   ├── extraction_pipeline.py           # Main pipeline orchestrator
│   └── batch_processor.py               # Batch processing coordinator
└── infrastructure/                      # Cross-cutting infrastructure
    ├── __init__.py                      # Infrastructure exports
    ├── config_manager.py                # Configuration management
    ├── logging_framework.py             # Structured logging
    ├── error_handler.py                 # Error handling and recovery
    └── progress_tracker.py              # Progress tracking
```

---

## Core Module (`src/core/`)

### `models.py` (692 lines)

**Purpose**: Define all data structures used throughout the pipeline

**Key Classes**:

**1. ContentBlock** (Primary data unit):
```python
@dataclass(frozen=True)
class ContentBlock:
    """Atomic unit of extracted content."""
    block_id: str                    # Unique identifier
    block_type: ContentType          # HEADING, PARAGRAPH, LIST, TABLE, etc.
    content: str                     # Extracted text content
    raw_content: Optional[str]       # Original unprocessed content
    position: Optional[Position]     # Page number + sequence
    parent_id: Optional[str]         # Parent block (for hierarchy)
    related_ids: tuple[str, ...]     # Related blocks
    metadata: dict                   # Extensible metadata
    confidence: Optional[float]      # Extraction confidence (0.0-1.0)
    style: Optional[dict]            # Formatting/style info
```

**2. ContentType** (Enum):
```python
class ContentType(str, Enum):
    """Content block types."""
    HEADING = "heading"
    PARAGRAPH = "paragraph"
    LIST_ITEM = "list_item"
    TABLE = "table"
    IMAGE = "image"
    CODE = "code"
    QUOTE = "quote"
    METADATA = "metadata"
```

**3. Position**:
```python
@dataclass(frozen=True)
class Position:
    """Location within document."""
    page: Optional[int]          # Page number (1-indexed)
    sequence_index: int          # Order within page/document
    line_number: Optional[int]   # Line number (optional)
    column: Optional[int]        # Column number (optional)
```

**4. DocumentMetadata**:
```python
@dataclass(frozen=True)
class DocumentMetadata:
    """Document-level metadata."""
    source_file: Path
    file_size_bytes: int
    title: Optional[str]
    author: Optional[str]
    created_date: Optional[datetime]
    modified_date: Optional[datetime]
    page_count: Optional[int]
    extraction_metadata: dict     # Extractor-specific metadata
```

**5. ExtractionResult** (From extractors):
```python
@dataclass(frozen=True)
class ExtractionResult:
    """Result from extraction stage."""
    content_blocks: tuple[ContentBlock, ...]
    document_metadata: DocumentMetadata
    images: tuple[ImageMetadata, ...] = ()
    tables: tuple[TableMetadata, ...] = ()
    success: bool = True
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
```

**6. ProcessingResult** (From processors):
```python
@dataclass(frozen=True)
class ProcessingResult:
    """Result from processing stage."""
    content_blocks: tuple[ContentBlock, ...]
    document_metadata: DocumentMetadata
    images: tuple[ImageMetadata, ...] = ()
    tables: tuple[TableMetadata, ...] = ()
    processing_stage: ProcessingStage = ProcessingStage.EXTRACTION
    stage_metadata: dict = field(default_factory=dict)
    quality_score: Optional[float] = None
    quality_issues: tuple[str, ...] = ()
    needs_review: bool = False
    success: bool = True
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
```

**7. ProcessingStage** (Enum):
```python
class ProcessingStage(str, Enum):
    """Pipeline stage identifiers."""
    VALIDATION = "validation"
    EXTRACTION = "extraction"
    CONTEXT_LINKING = "context_linking"
    METADATA_AGGREGATION = "metadata_aggregation"
    QUALITY_VALIDATION = "quality_validation"
    FORMATTING = "formatting"
    # Add: SEMANTIC_ANALYSIS = "semantic_analysis"  # For new processor
```

**Integration Note for Semantic Analysis**:
- Add `SEMANTIC_ANALYSIS` to `ProcessingStage` enum
- Semantic metadata goes in `metadata` dict of ContentBlock
- Aggregate stats go in `stage_metadata` of ProcessingResult

### `interfaces.py` (512 lines)

**Purpose**: Define abstract base classes for all pluggable components

**Key Interfaces**:

**1. BaseExtractor** (Lines 26-175):
```python
class BaseExtractor(ABC):
    """Abstract base for format-specific extractors."""

    @abstractmethod
    def extract(self, file_path: Path) -> ExtractionResult:
        """Extract content from file."""

    @abstractmethod
    def supports_format(self, file_path: Path) -> bool:
        """Check if extractor can handle file."""

    def supports_streaming(self) -> bool:
        """Whether extractor can stream large files."""
        return False

    def validate_file(self, file_path: Path) -> tuple[bool, list[str]]:
        """Pre-extraction validation."""
        return True, []
```

**2. BaseProcessor** (Lines 177-280):
```python
class BaseProcessor(ABC):
    """Abstract base for content processors."""

    @abstractmethod
    def get_processor_name(self) -> str:
        """Return unique processor name."""

    @abstractmethod
    def get_dependencies(self) -> list[str]:
        """Return list of processor names this depends on."""

    @abstractmethod
    def is_optional(self) -> bool:
        """Whether this processor is optional."""

    @abstractmethod
    def process(self, extraction_result: ExtractionResult) -> ProcessingResult:
        """Process and enrich content."""
```

**3. BaseFormatter** (Lines 282-350):
```python
class BaseFormatter(ABC):
    """Abstract base for output formatters."""

    @abstractmethod
    def format(self, processing_result: ProcessingResult) -> FormattedOutput:
        """Format processing result to output format."""

    @abstractmethod
    def get_format_type(self) -> str:
        """Return format type identifier."""
```

**4. BasePipeline** (Lines 352-420):
```python
class BasePipeline(ABC):
    """Abstract base for pipeline implementations."""

    @abstractmethod
    def process_file(self, file_path: Path) -> PipelineResult:
        """Process single file through pipeline."""
```

---

## Extractors Module (`src/extractors/`)

### Overview

6 format-specific extractors, all implementing `BaseExtractor` interface.

### `docx_extractor.py` (520 lines)

**Purpose**: Extract content from Word documents (.docx)
**Features**:
- Text extraction from paragraphs
- Table extraction with cell data
- Image extraction (format, dimensions, binary data)
- Heading detection (via style analysis)
- List item detection

**Key Methods**:
- `extract(file_path)`: Main extraction entry point
- `_extract_paragraphs(doc)`: Extract paragraph blocks
- `_extract_tables(doc)`: Extract table blocks
- `_extract_images(doc)`: Extract image metadata

**Configuration**:
```yaml
extractors:
  docx:
    extract_tables: true
    extract_images: true
    preserve_formatting: false
```

**Performance**: 79% test coverage, 51/58 tests passing

### `pdf_extractor.py` (485 lines)

**Purpose**: Extract content from PDFs (.pdf)
**Features**:
- Text extraction with pdfplumber
- Heading detection (font size heuristics)
- Table extraction
- OCR fallback for scanned PDFs (optional)
- Image extraction with base64 encoding

**Key Methods**:
- `extract(file_path)`: Main extraction
- `_extract_with_ocr(file_path)`: OCR extraction path
- `_extract_text_content(pdf)`: Text-based extraction
- `_detect_headings(blocks)`: Heading detection via font analysis

**Configuration**:
```yaml
extractors:
  pdf:
    enable_ocr: true
    poppler_path: "C:/Program Files/poppler/bin"  # Windows
    ocr_language: "eng"
    confidence_threshold: 0.5
```

**Performance**: 81% test coverage, 18 tests passing

### `pptx_extractor.py` (380 lines)

**Purpose**: Extract content from PowerPoint (.pptx)
**Features**:
- Slide title extraction (as HEADING)
- Slide body text extraction
- Speaker notes extraction
- Image extraction with metadata
- Table extraction (placeholder)

**Configuration**:
```yaml
extractors:
  pptx:
    extract_speaker_notes: true
    extract_images: true
```

**Performance**: 82% test coverage, 22 tests passing

### `excel_extractor.py` (420 lines)

**Purpose**: Extract content from Excel workbooks (.xlsx, .xls)
**Features**:
- Multi-sheet extraction
- Table extraction (each sheet as TABLE block)
- Cell value extraction (all types: number, text, formula, date)
- Header detection
- Empty cell handling

**Configuration**:
```yaml
extractors:
  xlsx:
    extract_all_sheets: true
    include_formulas: false
    max_rows: 10000  # Safety limit
```

**Performance**: 82% test coverage, 36 tests passing

### `csv_extractor.py` (410 lines, NEW in v1.0.6)

**Purpose**: Extract content from CSV/TSV files
**Features**:
- Auto-detection: delimiter (comma, tab, semicolon, pipe)
- Auto-detection: encoding (UTF-8, BOM, Latin-1)
- Auto-detection: header presence
- Single TABLE ContentBlock pattern (matches Excel)

**Configuration**:
```yaml
extractors:
  csv:
    auto_detect_delimiter: true
    auto_detect_encoding: true
    max_rows: 100000
```

**Performance**: 88% test coverage, 56/56 tests passing (100%)

### `txt_extractor.py` (245 lines)

**Purpose**: Extract content from plain text files (.txt)
**Features**:
- Encoding detection (UTF-8, Latin-1, etc.)
- Line-by-line extraction (each line as PARAGRAPH)
- Simple structure (no headings, tables, images)

**Configuration**:
```yaml
extractors:
  txt:
    encoding: "utf-8"  # or "auto"
```

**Performance**: >85% test coverage, 38 tests passing

---

## Processors Module (`src/processors/`)

### `context_linker.py` (295 lines)

**Purpose**: Build hierarchical document structure
**Algorithm**: Heading stack with topological ordering
**Output**: Adds `depth`, `document_path`, `parent_id` to metadata

**Key Data Structures**:
```python
heading_stack: dict[int, tuple[str, str]]  # level → (block_id, title)
```

**Example Enrichment**:
```python
# Before
metadata = {}

# After
metadata = {
    "depth": 2,
    "document_path": ["Chapter 1", "Section 1.1"],
}
parent_id = "heading_abc123"
```

**Performance**: 99% test coverage, 17/17 tests passing

### `metadata_aggregator.py` (235 lines)

**Purpose**: Compute statistics and aggregate metadata
**Output**: Adds `word_count`, `char_count` to blocks; document stats to `stage_metadata`

**Key Statistics**:
- Block-level: word_count, char_count, entities (placeholder)
- Document-level: total_words, average_words_per_block, content_type_distribution

**Entity Extraction Placeholder** (lines 210-235):
```python
def _extract_entities(self, text: str) -> list[str]:
    """
    Extract named entities from text.

    Placeholder - would use spaCy:
    import spacy
    nlp = spacy.load("en_core_web_sm")
    doc = nlp(text)
    return [ent.text for ent in doc.ents]
    """
    return []  # Disabled by default
```

**Performance**: 94% test coverage, 17/17 tests passing

### `quality_validator.py` (360 lines)

**Purpose**: Score extraction quality
**Output**: Adds `quality_score`, `quality_issues`, `needs_review` to ProcessingResult

**Quality Dimensions**:
1. Completeness: Headings present, content diversity, empty blocks
2. Consistency: Confidence scores present, metadata complete
3. Readability: Not corrupted, reasonable character distribution

**Overall Score**: Average of 3 dimensions (0-100)

**Performance**: 94% test coverage, 19/19 tests passing

---

## Formatters Module (`src/formatters/`)

### `json_formatter.py` (345 lines)

**Purpose**: Generate JSON output (hierarchical or flat)
**Features**:
- Hierarchical structure (nested by parent_id)
- Flat structure (simple list)
- Pretty-print option
- Unicode support

**Configuration**:
```yaml
formatters:
  json:
    hierarchical: false
    pretty_print: true
    indent: 2
    ensure_ascii: false
```

**Performance**: 91% test coverage, 27 tests passing

### `markdown_formatter.py` (380 lines)

**Purpose**: Generate Markdown output
**Features**:
- Heading hierarchy (# for H1, ## for H2, etc.)
- List formatting (- for bullets, 1. for numbered)
- Table formatting (Markdown tables)
- Image references
- Metadata section (optional)

**Configuration**:
```yaml
formatters:
  markdown:
    include_metadata: true
    include_images: true
    max_heading_level: 6
```

**Performance**: 87% test coverage, 27 tests passing

### `chunked_text_formatter.py` (285 lines)

**Purpose**: Generate token-limited chunks for AI consumption
**Features**:
- Configurable chunk size (default: 1000 tokens)
- Chunk overlap (default: 100 tokens)
- Structure preservation (don't split paragraphs mid-sentence)
- Metadata per chunk

**Configuration**:
```yaml
formatters:
  chunked_text:
    chunk_size: 1000
    chunk_overlap: 100
    preserve_structure: true
```

**Performance**: 98% test coverage, 22 tests passing

---

## Pipeline Module (`src/pipeline/`)

### `extraction_pipeline.py` (612 lines)

**Purpose**: Orchestrate the complete extraction workflow
**Key Responsibilities**:
- Format detection
- Extractor registry
- Processor ordering (topological sort)
- Formatter execution (parallel)
- Error handling at each stage
- Progress reporting

**Key Methods**:
- `process_file(file_path)`: Main entry point
- `detect_format(file_path)`: Detect format from extension
- `_order_processors()`: Topological sort of processors
- `_report_progress(callback, stage, %)`: Progress updates

**Pipeline Stages**:
1. Validation (file exists, format detected)
2. Extraction (format-specific extractor)
3. Processing (ordered processor chain)
4. Formatting (parallel formatters)

**Performance**: >85% test coverage, 107 tests passing

### `batch_processor.py` (425 lines)

**Purpose**: Parallel batch processing of multiple files
**Features**:
- Thread pool execution
- Progress tracking across all files
- Error handling (continue on failure)
- Result aggregation

**Configuration**:
```yaml
batch:
  max_workers: 4
  timeout_per_file: 300  # seconds
```

**Performance**: >85% test coverage, 22 tests passing

---

## Infrastructure Module (`src/infrastructure/`)

### `config_manager.py` (485 lines)

**Purpose**: Centralized configuration management
**Features**:
- YAML/JSON config loading
- Pydantic validation
- Environment variable overrides
- Nested config access (dot notation)
- Thread-safe access

**Usage**:
```python
config = ConfigManager("config.yaml")
value = config.get("processors.semantic_analyzer.confidence_threshold", default=0.7)
```

**Performance**: 94% test coverage, 28 tests passing

### `logging_framework.py` (380 lines)

**Purpose**: Structured JSON logging with correlation IDs
**Features**:
- Structured logging (JSON format)
- Correlation ID tracking (trace requests)
- Performance metrics (timing decorators)
- Log level filtering
- Multiple handlers (console, file, etc.)

**Usage**:
```python
from infrastructure import get_logger, timed

logger = get_logger(__name__)

@timed(logger)
def my_function():
    logger.info("Processing", extra={"block_count": 42})
```

**Performance**: 100% test coverage, 15 tests passing

### `error_handler.py` (520 lines)

**Purpose**: Standardized error handling and recovery
**Features**:
- 50+ error codes
- Recovery actions (RETRY, SKIP, FAIL)
- Plain-language error messages
- Error code validation

**Usage**:
```python
from infrastructure import ErrorHandler, RecoveryAction

handler = ErrorHandler()
recovery = handler.handle_error(
    error_code="EXT_001",
    error_message="File not found",
    context={"file_path": "/path/to/file"}
)

if recovery.action == RecoveryAction.FAIL:
    # Handle fatal error
    pass
```

**Performance**: 94% test coverage, 26 tests passing

### `progress_tracker.py` (380 lines)

**Purpose**: Real-time progress tracking with ETA
**Features**:
- Multi-stage tracking
- ETA calculation
- Rich formatting (terminal progress bars)
- Thread-safe (uses RLock)

**Usage**:
```python
from infrastructure import ProgressTracker

tracker = ProgressTracker(total_items=100)
tracker.start_stage("processing")

for i in range(100):
    tracker.update(1)  # Increment by 1

tracker.complete_stage()
status = tracker.get_status()
```

**Performance**: >90% test coverage, 28 tests passing

**Note**: Critical fix in v1.0.3 - Changed from Lock to RLock to prevent deadlock

---

## CLI Module (`src/cli/`)

### `main.py` (285 lines)

**Purpose**: CLI entry point and command routing
**Framework**: Click (command-line framework)

**Commands**:
- `extract`: Extract single file
- `batch`: Process multiple files
- `version`: Show version info
- `config`: Show configuration

**Entry Point**:
```python
# pyproject.toml
[project.scripts]
data-extract = "src.cli.main:cli"
```

### `commands.py` (520 lines)

**Purpose**: CLI command implementations
**Features**:
- Rich terminal UI (progress bars, tables)
- Error reporting
- File validation
- Output path handling

**Example Usage**:
```bash
# Extract single file
data-extract extract document.pdf --output output.json

# Batch processing
data-extract batch input_folder/ --format markdown

# Show version
data-extract version --verbose
```

**Performance**: ~60% test coverage, 61 tests passing

---

## Test Suite (`tests/`)

### Test Organization

```
tests/
├── __init__.py
├── test_core/                       # Core model tests
│   ├── test_models.py
│   └── test_interfaces.py
├── test_extractors/                 # Extractor tests
│   ├── test_docx_extractor.py
│   ├── test_pdf_extractor.py
│   ├── test_pptx_extractor.py
│   ├── test_excel_extractor.py
│   ├── test_csv_extractor.py
│   └── test_txt_extractor.py
├── test_processors/                 # Processor tests
│   ├── test_context_linker.py
│   ├── test_metadata_aggregator.py
│   └── test_quality_validator.py
├── test_formatters/                 # Formatter tests
│   ├── test_json_formatter.py
│   ├── test_markdown_formatter.py
│   └── test_chunked_text_formatter.py
├── test_pipeline/                   # Pipeline tests
│   ├── test_extraction_pipeline.py
│   └── test_batch_processor.py
├── test_infrastructure/             # Infrastructure tests
│   ├── test_config_manager.py
│   ├── test_logging_framework.py
│   ├── test_error_handler.py
│   └── test_progress_tracker.py
├── test_cli/                        # CLI tests
│   ├── test_main.py
│   └── test_commands.py
├── integration/                     # Integration tests
│   └── test_end_to_end.py
├── fixtures/                        # Test fixtures
│   ├── sample.docx
│   ├── sample.pdf
│   ├── sample.pptx
│   ├── sample.xlsx
│   ├── sample.csv
│   └── sample.txt
└── conftest.py                      # Pytest configuration
```

### Test Metrics (v1.0.6)

- **Total Tests**: 1,016
- **Passing**: 840 (82.7%)
- **Coverage**: 92%+ overall
- **Test Infrastructure**: pytest, pytest-cov, pytest-mock

**Test Categories**:
- Unit tests: 800+
- Integration tests: 70+
- Edge case tests: 80+
- Performance tests: 23 (deferred)

---

## Documentation (`docs/`)

### Comprehensive Documentation (115+ files)

```
docs/
├── architecture/                    # Architecture documentation
│   ├── FOUNDATION.md
│   ├── GETTING_STARTED.md
│   └── QUICK_REFERENCE.md
├── guides/                          # Developer guides
│   ├── INFRASTRUCTURE_GUIDE.md
│   ├── CONFIG_GUIDE.md
│   ├── LOGGING_GUIDE.md
│   └── ERROR_HANDLING_GUIDE.md
├── reports/                         # Development reports
│   ├── WAVE1_COMPLETION_REPORT.md
│   ├── WAVE2_COMPLETION_REPORT.md
│   ├── WAVE3_COMPLETION_REPORT.md
│   ├── WAVE4_COMPLETION_REPORT.md
│   └── adr-assessment/              # ADR compliance reports
├── planning/                        # Planning documents
│   └── v1_0_6-planning/
│       └── testing-remediation/
├── bmm-project-overview.md          # NEW: BMM project overview
├── bmm-pipeline-integration-guide.md # NEW: Pipeline integration guide
├── bmm-processor-chain-analysis.md  # NEW: Processor chain analysis
├── USER_GUIDE.md                    # End-user documentation
├── QUICKSTART.md                    # Quick start guide
└── index.md                         # Documentation index
```

---

## Configuration Files

### `pyproject.toml` (Build configuration)

**Purpose**: Python package configuration (PEP 518)

**Key Sections**:
- `[project]`: Package metadata (name, version, dependencies)
- `[project.scripts]`: CLI entry points
- `[tool.pytest]`: Pytest configuration
- `[tool.black]`: Code formatting
- `[tool.ruff]`: Linting
- `[tool.mypy]`: Type checking

### `config.yaml.example` (Runtime configuration template)

**Purpose**: Example runtime configuration for users

**Sections**:
- `extractors`: Extractor-specific config
- `processors`: Processor-specific config
- `formatters`: Formatter-specific config
- `pipeline`: Pipeline settings
- `logging`: Logging configuration

---

## Integration Points for Semantic Analysis

### Where to Add Code

**1. New Processor**:
```
src/processors/semantic_analyzer.py  ← CREATE NEW FILE
```

**2. ProcessingStage Enum**:
```
src/core/models.py  ← ADD ENUM VALUE
# Add: SEMANTIC_ANALYSIS = "semantic_analysis"
```

**3. Processor Registration**:
```
src/pipeline/__init__.py  ← ADD IMPORT + EXPORT
from processors import SemanticAnalyzer
__all__ = [..., "SemanticAnalyzer"]
```

**4. Configuration**:
```
config.yaml  ← ADD CONFIG SECTION
processors:
  semantic_analyzer:
    enabled: true
    ...
```

**5. Tests**:
```
tests/test_processors/test_semantic_analyzer.py  ← CREATE TEST FILE
```

---

## Summary: File Count and Lines of Code

| Directory | Files | Approx. Lines | Purpose |
|-----------|-------|---------------|---------|
| `src/core/` | 3 | 1,200 | Data models and interfaces |
| `src/extractors/` | 7 | 2,900 | Format-specific extraction |
| `src/processors/` | 4 | 890 | Content enrichment |
| `src/formatters/` | 4 | 1,010 | Output generation |
| `src/pipeline/` | 3 | 1,040 | Pipeline orchestration |
| `src/infrastructure/` | 5 | 1,765 | Cross-cutting services |
| `src/cli/` | 3 | 805 | Command-line interface |
| `tests/` | 50+ | 8,000+ | Test suite |
| `docs/` | 115+ | 50,000+ | Documentation |
| **Total** | **190+** | **67,000+** | **Complete codebase** |

---

**Document Status**: ✅ Complete | **Generated**: 2025-11-07 | **For**: BMM document-project workflow
