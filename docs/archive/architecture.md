# Architecture

## Executive Summary

This architecture defines the technical blueprint for transforming data-extraction-tool from a brownfield foundation into a production-ready **knowledge quality gateway for enterprise Gen AI**. The architecture emphasizes **modularity** (pipeline-composable processing), **determinism** (audit trail compliance), **quality** (validation at every stage), and **usability** (professional CLI experience). All decisions optimize for batch processing efficiency, classical NLP methods (no transformers), and Python 3.12 enterprise constraints.

**Architectural Philosophy:** Build a streaming, memory-efficient pipeline where each stage (extract → normalize → chunk → analyze → output) is independent, testable, and replaceable. Prioritize clarity and maintainability for learning semantic analysis concepts while delivering production-quality results.

## Project Initialization

This is a **brownfield project** with existing extraction capabilities. The architecture builds on this foundation:

### Existing Foundation (Assessed)
- Document extraction infrastructure (PyMuPDF, python-docx, pytesseract)
- Basic text processing and structure preservation
- Initial output generation

### New Architecture Integration
Rather than a fresh starter template, we'll refactor existing code into the new modular pipeline architecture defined below. Story 1.2 (Brownfield Assessment) will map existing code to new structure.

### Development Setup
```bash
# Python 3.12 virtual environment
python3.12 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install with pinned dependencies
pip install -e ".[dev]"

# Pre-commit hooks for code quality
pre-commit install
```

## Decision Summary

| Category | Decision | Version | Affects Epics | Rationale |
| -------- | -------- | ------- | ------------- | --------- |
| CLI Framework | Typer | 0.12.x (latest) | Epic 5 (CLI UX) | Modern, type-safe, less boilerplate than Click. Built on Click for compatibility. Auto-generates help text. |
| Terminal UI | Rich | 13.x (latest) | Epic 5 (Progress) | Beautiful progress bars, tables, syntax highlighting. Industry standard for modern Python CLI. |
| Project Structure | src/ layout with pipeline modules | N/A | Epic 1 (Foundation) | Clear separation: src/data_extract/{extract, normalize, chunk, semantic, output}. Follows modern Python packaging. |
| Dependency Management | pyproject.toml + pip | Python 3.12 | Epic 1 (Foundation) | PEP 621 standard. Pin all versions for reproducibility (audit requirement). |
| NLP Core | spaCy | 3.7.x (latest) | Epics 2, 3 (NLP) | Production-ready, fast, excellent sentence segmentation. Use en_core_web_md model. |
| Text Vectorization | scikit-learn | 1.5.x (latest) | Epic 4 (Semantic) | TF-IDF, LSA, cosine similarity. Industry standard for classical NLP. No transformer dependencies. |
| Topic Modeling | gensim | 4.3.x (latest) | Epic 4 (Semantic) | Word2Vec, LDA. Complements scikit-learn for advanced semantic analysis. |
| Document Extraction | PyMuPDF (fitz) | 1.24.x (latest) | Epic 1, 2 | Fast PDF processing. Better than PyPDF2. Handles both native and scanned PDFs. |
| Word Documents | python-docx | 1.1.x (latest) | Epic 1, 2 | Standard for .docx. Extracts text, tables, comments, tracked changes. |
| OCR Engine | pytesseract | 0.3.x (latest) | Epic 2 (Quality) | Tesseract wrapper. Confidence scoring. Preprocessing with Pillow for quality. |
| Data Models | Pydantic | 2.x (latest) | All Epics | Type-safe data validation. Better than dataclasses for config and API contracts. Schema validation. |
| Configuration | PyYAML + env vars | 6.0.x (latest) | Epic 5 (Config) | YAML for user config. Env vars for overrides. CLI flags highest precedence. |
| Testing Framework | pytest | 8.x (latest) | Epic 1 (Foundation) | Industry standard. Plugin ecosystem (pytest-cov, pytest-xdist for parallel). |
| Code Quality | ruff + mypy + black | Latest | Epic 1 (Foundation) | Ruff: fast linter. Mypy: type checking. Black: formatting. Pre-commit hooks enforce. |
| Progress Feedback | rich.progress | 13.x (latest) | Epic 5 (Progress) | Integrated with Rich. Real-time progress bars, elapsed/remaining time, file counts. |
| Logging | Python logging + structlog | 3.11+ / 24.x | All Epics | Structured logging for audit trail. JSON output option. Configurable levels. |
| Quality Metrics | textstat | 0.7.x (latest) | Epic 2, 4 | Readability scores (Flesch-Kincaid, Gunning Fog, SMOG). Lexical diversity. |
| Parallelization | concurrent.futures | Python stdlib | Epic 5 (Batch) | ThreadPoolExecutor for I/O-bound tasks. ProcessPoolExecutor for CPU-bound. Simpler than multiprocessing. |
| Metadata Format | JSON with schema | Python stdlib | Epic 3 (Output) | JSON for structured metadata. Include processing config, version, timestamps for audit trail. |
| Caching Strategy | SHA-256 file hashing | Python stdlib | Epic 5 (Incremental) | Detect file changes for incremental processing. Manifest file tracks processed files. |
| Error Handling | Continue-on-error + quarantine | N/A | Epic 5 (Batch) | Catch errors per file, continue batch, quarantine failures, detailed logs. No silent failures. |

## Project Structure

```
data-extraction-tool/
├── pyproject.toml              # PEP 621 project config, dependencies, entry points
├── README.md                   # Setup instructions, quick start
├── .gitignore                  # Exclude venv, __pycache__, outputs, .env
├── .pre-commit-config.yaml     # ruff, mypy, black hooks
│
├── src/
│   └── data_extract/           # Main package
│       ├── __init__.py         # Package version, exports
│       ├── __main__.py         # Entry point for python -m data_extract
│       ├── cli.py              # Typer CLI app definition, command routing
│       │
│       ├── core/               # Core data models and interfaces
│       │   ├── __init__.py
│       │   ├── models.py       # Pydantic: Document, Chunk, Metadata, Config
│       │   ├── pipeline.py     # Pipeline interface/protocol, stage contracts
│       │   └── exceptions.py   # Custom exception hierarchy
│       │
│       ├── extract/            # Stage 1: Document extraction
│       │   ├── __init__.py
│       │   ├── extractor.py    # Main extraction orchestrator
│       │   ├── pdf.py          # PyMuPDF: PDF extraction
│       │   ├── docx.py         # python-docx: Word extraction
│       │   ├── xlsx.py         # openpyxl: Excel extraction
│       │   ├── image.py        # pytesseract: Image OCR
│       │   └── archer.py       # HTML/XML: Archer export parsing
│       │
│       ├── normalize/          # Stage 2: Text normalization
│       │   ├── __init__.py
│       │   ├── normalizer.py   # Main normalization orchestrator
│       │   ├── cleaning.py     # Artifact removal, whitespace normalization
│       │   ├── entities.py     # Entity normalization (6 audit types)
│       │   ├── schema.py       # Schema standardization across doc types
│       │   └── validation.py   # Completeness validation, quality checks
│       │
│       ├── chunk/              # Stage 3: Intelligent chunking
│       │   ├── __init__.py
│       │   ├── chunker.py      # Main chunking orchestrator
│       │   ├── semantic.py     # Semantic boundary-aware chunking (spaCy)
│       │   ├── entity_aware.py # Entity-aware chunking logic
│       │   └── metadata.py     # Chunk metadata enrichment
│       │
│       ├── semantic/           # Stage 4: Semantic analysis
│       │   ├── __init__.py
│       │   ├── analyzer.py     # Main semantic analysis orchestrator
│       │   ├── tfidf.py        # TF-IDF vectorization (scikit-learn)
│       │   ├── similarity.py   # Cosine similarity, document matching
│       │   ├── lsa.py          # Latent Semantic Analysis (TruncatedSVD)
│       │   └── quality.py      # Quality metrics (textstat)
│       │
│       ├── output/             # Stage 5: Output formatting
│       │   ├── __init__.py
│       │   ├── writer.py       # Main output orchestrator
│       │   ├── json_writer.py  # JSON format with metadata
│       │   ├── txt_writer.py   # Plain text format for LLM upload
│       │   ├── csv_writer.py   # CSV tabular format
│       │   └── organizer.py    # Output organization strategies
│       │
│       ├── config/             # Configuration management
│       │   ├── __init__.py
│       │   ├── loader.py       # Load from YAML, env vars, CLI flags
│       │   ├── presets.py      # Named presets (chatgpt, knowledge-graph, etc.)
│       │   └── defaults.yaml   # Default configuration values
│       │
│       └── utils/              # Shared utilities
│           ├── __init__.py
│           ├── logging.py      # Structured logging setup (structlog)
│           ├── progress.py     # Rich progress bar helpers
│           ├── cache.py        # File hashing, manifest management
│           └── errors.py       # Error handling, quarantine logic
│
├── tests/                      # Mirror src/ structure
│   ├── __init__.py
│   ├── conftest.py             # pytest fixtures, test configuration
│   ├── fixtures/               # Sample files for testing
│   │   ├── pdfs/
│   │   ├── docx/
│   │   ├── xlsx/
│   │   ├── images/
│   │   └── archer/
│   ├── unit/                   # Unit tests (fast, isolated)
│   │   ├── test_extract/
│   │   ├── test_normalize/
│   │   ├── test_chunk/
│   │   ├── test_semantic/
│   │   └── test_output/
│   ├── integration/            # Integration tests (full pipeline)
│   │   ├── test_pipeline_basic.py
│   │   ├── test_batch_processing.py
│   │   └── test_determinism.py
│   └── performance/            # Performance benchmarks
│       └── test_throughput.py
│
├── docs/                       # Project documentation
│   ├── architecture.md         # This file
│   ├── PRD.md                  # Product requirements
│   ├── epics.md                # Epic breakdown
│   └── brownfield-assessment.md # Brownfield codebase analysis
│
├── config/                     # Configuration templates
│   └── config.example.yaml     # Example configuration file
│
└── scripts/                    # Development/deployment scripts
    ├── setup.sh                # Development environment setup
    └── verify_install.py       # Verify installation and dependencies
```

## Epic to Architecture Mapping

| Epic | Primary Components | Integration Points | Key Patterns |
|------|-------------------|-------------------|--------------|
| **Epic 1: Foundation** | `core/`, `pyproject.toml`, `tests/` | All other epics depend on foundation | Pipeline pattern, Pydantic models, pytest framework |
| **Epic 2: Normalization** | `normalize/` (cleaning, entities, schema, validation) | Receives from `extract/`, feeds to `chunk/` | Strategy pattern for cleaning rules, Entity registry |
| **Epic 3: Chunking** | `chunk/` (engine, models, sentence_segmenter) | Uses spaCy from Story 2.5.2, feeds to `output/` | Semantic boundary-aware chunking, Generator-based streaming |
| **Epic 4: Semantic Analysis** | `semantic/` (tfidf, similarity, lsa, quality) | Works on chunks from `chunk/`, uses scikit-learn/gensim | Vectorization pipeline, Similarity matrix |
| **Epic 5: CLI UX** | `cli.py`, `config/`, `utils/progress.py`, `utils/errors.py` | Orchestrates all pipeline stages | Command pattern, Configuration cascade, Rich UI |

### Epic-Specific Architecture Notes

**Epic 1 (Foundation):**
- Defines `Pipeline` protocol in `core/pipeline.py` with contracts: `process(input) → output`
- All stages implement pipeline interface for composability
- `core/models.py` defines shared data structures used across all stages

**Epic 2 (Normalization):**
- Six entity types (processes, risks, controls, regulations, policies, issues) handled in `normalize/entities.py`
- Entity registry pattern with configurable dictionaries for domain-specific terms
- Validation produces quality scores stored in metadata for downstream filtering

**Epic 3 (Chunking):**
- **ChunkingEngine** respects sentence boundaries (never splits mid-sentence)
- Uses **SentenceSegmenter** (Story 2.5.2) with spaCy `en_core_web_md` model
- Generator-based streaming for constant memory usage (not batch-loading)
- **Chunk data model** (frozen dataclass): text, metadata, position, token_count, source_block_id
- Configuration: chunk_size (128-2048 tokens), overlap_pct (0.0-0.5)
- Metadata includes: source_file, position_index, token_count, word_count, source_block_id
- Performance: ~3s for 10k words, 255 MB memory (linear scaling validated)

**Epic 4 (Semantic Analysis):**
- TF-IDF vectors stored as scipy sparse matrices for memory efficiency
- LSA components configurable (default: 100-300), explained variance tracked
- Similarity uses cosine similarity on vectors, cached for performance

**Epic 5 (CLI UX):**
- Typer app in `cli.py` with sub-commands: `process`, `similarity`, `validate`, `config`, `info`
- Configuration cascade: CLI flags → ENV vars → YAML file → defaults
- Rich progress shows: [████████░░] 65% (13/20) | Current: file.pdf | 2m 34s elapsed

## Technology Stack Details

### Core Technologies

**Python 3.12** (Enterprise Requirement)
- Type hints with PEP 695 syntax (Python 3.12+ type parameter syntax)
- Pattern matching for document type detection
- Improved error messages for debugging
- Performance improvements over 3.11

**CLI & Terminal UI:**
- **Typer 0.12.x**: Command routing, type-safe CLI, auto-help generation
- **Rich 13.x**: Progress bars, tables, syntax highlighting, terminal formatting
- Integration: Typer for commands, Rich for output presentation

**NLP & Document Processing:**
- **spaCy 3.7.x**: Sentence segmentation, tokenization, named entity recognition (NER)
  - Model: `en_core_web_md` (50MB, includes word vectors)
  - Used for: Semantic chunking, entity detection
- **scikit-learn 1.5.x**: TF-IDF vectorization, LSA (TruncatedSVD), cosine similarity
  - Classical ML algorithms only (no deep learning)
- **gensim 4.3.x**: Word2Vec, FastText, LDA topic modeling
  - Advanced semantic analysis (post-MVP)
- **textstat 0.7.x**: Readability metrics (Flesch-Kincaid, Gunning Fog, SMOG)

**Document Extraction:**
- **PyMuPDF (fitz) 1.24.x**: PDF text/image extraction, fast, handles complex PDFs
- **python-docx 1.1.x**: Word document parsing (text, tables, comments, tracked changes)
- **openpyxl 3.1.x**: Excel reading/writing, table extraction
- **pytesseract 0.3.x**: OCR wrapper for Tesseract engine
  - Requires system Tesseract installation
- **Pillow 10.x**: Image preprocessing for OCR (deskew, denoise, contrast)
- **BeautifulSoup4 4.12.x**: HTML/XML parsing for Archer exports

**Data & Configuration:**
- **Pydantic 2.x**: Data validation, settings management, JSON schema generation
  - Replaces dataclasses for type-safe models with validation
- **PyYAML 6.0.x**: YAML configuration file parsing
- **python-dotenv 1.0.x**: Environment variable loading from .env files

**Development & Quality:**
- **pytest 8.x**: Test framework
  - **pytest-cov**: Coverage reporting
  - **pytest-xdist**: Parallel test execution
- **ruff 0.6.x**: Fast Python linter (replaces flake8, isort, etc.)
- **mypy 1.11.x**: Static type checking
- **black 24.x**: Code formatting (opinionated)
- **pre-commit 3.x**: Git hooks for quality enforcement

**Logging & Monitoring:**
- **structlog 24.x**: Structured logging with JSON output
  - Integrates with Python's logging module
  - Audit trail compliance (timestamps, processing decisions)

### Integration Points

**CLI → Pipeline Orchestration:**
```python
# cli.py routes commands to pipeline stages
@app.command()
def process(input_path: Path, output: Path = "./processed"):
    pipeline = Pipeline([
        Extractor(),
        Normalizer(),
        Chunker(),
        Analyzer(),
        Writer()
    ])
    results = pipeline.process(input_path)
```

**Extract → Normalize:**
- `Extractor` returns `Document` objects with raw text + metadata
- `Normalizer` receives `Document`, applies cleaning, returns normalized `Document`
- Data contract: `Document(text: str, metadata: Metadata, entities: List[Entity])`

**Normalize → Chunk:**
- `Normalizer` returns validated `Document` with entity tags
- `Chunker` uses entity information to determine optimal split points
- Data contract: `List[Chunk]` where each chunk has source document reference

**Chunk → Semantic:**
- `Chunker` produces `List[Chunk]` with text + metadata
- `Analyzer` vectorizes chunks (TF-IDF), computes similarity matrix
- Data contract: `SemanticAnalysis(vectors, similarity_matrix, quality_scores)`

**Semantic → Output:**
- All stages feed results to `Writer`
- `Writer` generates JSON, TXT, CSV from unified data structures
- Data contract: `ProcessingResult(documents, chunks, analysis, metadata)`

**Configuration Flow:**
```
CLI flags → Environment variables → YAML config → Hardcoded defaults
(Highest precedence)                              (Lowest precedence)
```

### Dependency Installation

**pyproject.toml dependencies:**
```toml
[project]
dependencies = [
    "typer[all]>=0.12.0,<0.13",
    "rich>=13.0.0,<14.0",
    "spacy>=3.7.0,<3.8",
    "scikit-learn>=1.5.0,<1.6",
    "gensim>=4.3.0,<4.4",
    "textstat>=0.7.0,<0.8",
    "pymupdf>=1.24.0,<1.25",
    "python-docx>=1.1.0,<1.2",
    "openpyxl>=3.1.0,<3.2",
    "pytesseract>=0.3.0,<0.4",
    "Pillow>=10.0.0,<11.0",
    "beautifulsoup4>=4.12.0,<5.0",
    "pydantic>=2.0.0,<3.0",
    "PyYAML>=6.0.0,<7.0",
    "python-dotenv>=1.0.0,<2.0",
    "structlog>=24.0.0,<25.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0,<9.0",
    "pytest-cov>=5.0.0,<6.0",
    "pytest-xdist>=3.6.0,<4.0",
    "ruff>=0.6.0,<0.7",
    "mypy>=1.11.0,<2.0",
    "black>=24.0.0,<25.0",
    "pre-commit>=3.0.0,<4.0",
]

[project.scripts]
data-extract = "data_extract.cli:app"
```

**External Dependencies (System-Level):**
- Tesseract OCR engine (for pytesseract)
  - Install: `apt-get install tesseract-ocr` (Linux) or `brew install tesseract` (Mac)
  - Windows: Download installer from https://github.com/UB-Mannheim/tesseract/wiki
- spaCy language model: `python -m spacy download en_core_web_md`

## Implementation Patterns

These patterns ensure consistent implementation across all AI agents:

### Pipeline Stage Pattern
**MUST use for all processing stages** (extract, normalize, chunk, semantic, output)

**Implementation:** `src/data_extract/core/pipeline.py` (Story 1.4)

```python
from typing import Protocol, Generic, TypeVar, List, Any
from data_extract.core.models import ProcessingContext

Input = TypeVar('Input', contravariant=True)
Output = TypeVar('Output', covariant=True)

class PipelineStage(Protocol, Generic[Input, Output]):
    """All pipeline stages implement this interface"""

    def process(self, input_data: Input, context: ProcessingContext) -> Output:
        """
        Process input and return output.

        Args:
            input_data: Data from previous stage
            context: Shared processing context (config, logger, metrics)

        Returns:
            Processed output for next stage

        Raises:
            ProcessingError: On recoverable errors (logged, continue batch)
            CriticalError: On unrecoverable errors (halt processing)
        """
        ...

class Pipeline:
    """Pipeline orchestrator that chains multiple stages"""

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

**Example: All stages follow this pattern**
```python
class Normalizer(PipelineStage[Document, Document]):
    def process(self, document: Document, context: ProcessingContext) -> Document:
        # Apply cleaning rules
        cleaned_text = self._clean_text(document.text)
        # Normalize entities
        entities = self._normalize_entities(document.entities)
        # Return normalized document
        return Document(text=cleaned_text, entities=entities, metadata=document.metadata)
```

### Error Handling Pattern
**MUST use for all file processing operations**

**Implementation:** `src/data_extract/core/exceptions.py` (Story 1.4)

```python
# In batch processing loop
for file_path in files:
    try:
        result = process_file(file_path)
        successful_results.append(result)
    except ProcessingError as e:
        # Recoverable error - log, quarantine, continue
        logger.warning(f"Processing failed: {file_path}", error=str(e))
        quarantine_file(file_path, error=e)
        failed_files.append((file_path, e))
        continue  # CRITICAL: Continue processing other files
    except CriticalError as e:
        # Unrecoverable error - halt immediately
        logger.error(f"Critical failure: {file_path}", error=str(e))
        raise

# After loop: Report summary of successes and failures
report_summary(successful_results, failed_files)
```

**Exception Hierarchy:**
```python
class DataExtractError(Exception):
    """Base exception for all tool errors"""

class ProcessingError(DataExtractError):
    """Recoverable error - continue batch processing"""

class CriticalError(DataExtractError):
    """Unrecoverable error - halt processing"""

class ConfigurationError(CriticalError):
    """Invalid configuration - cannot proceed"""

class ExtractionError(ProcessingError):
    """File extraction failed - skip file, continue batch"""

class ValidationError(ProcessingError):
    """Quality validation failed - flag file, continue"""
```

### Logging Pattern
**MUST use structured logging for audit trail**

```python
import structlog

logger = structlog.get_logger()

# Log with context (automatically includes timestamps, levels)
logger.info("processing_started",
            file=file_path,
            file_hash=file_hash,
            config_version=config.version)

logger.debug("chunk_created",
             chunk_id=chunk.id,
             chunk_size=len(chunk.text),
             entity_count=len(chunk.entities),
             quality_score=chunk.quality_score)

logger.warning("quality_threshold_failed",
               file=file_path,
               ocr_confidence=0.87,
               threshold=0.95,
               action="quarantined")
```

### Configuration Cascade Pattern
**MUST implement three-tier precedence**

```python
def load_config() -> Config:
    # 1. Load defaults (hardcoded in code)
    config = DEFAULT_CONFIG.copy()

    # 2. Overlay YAML file config (if exists)
    if yaml_config_exists():
        yaml_config = load_yaml_config()
        config.update(yaml_config)

    # 3. Overlay environment variables (DATA_EXTRACT_*)
    env_config = load_from_env_vars()
    config.update(env_config)

    # 4. CLI flags applied last (highest precedence)
    # (Handled by Typer when function is called)

    return Config(**config)  # Pydantic validates
```

**Environment Variable Naming:**
- Prefix: `DATA_EXTRACT_`
- Example: `DATA_EXTRACT_CHUNK_SIZE=512`
- Example: `DATA_EXTRACT_OUTPUT_DIR=/path/to/output`

## Consistency Rules

### Naming Conventions

**Files and Modules:**
- Python files: `lowercase_with_underscores.py`
- Classes: `PascalCase` (e.g., `DocumentExtractor`, `SemanticChunker`)
- Functions/methods: `lowercase_with_underscores` (e.g., `process_batch`, `calculate_similarity`)
- Constants: `UPPERCASE_WITH_UNDERSCORES` (e.g., `DEFAULT_CHUNK_SIZE`, `MAX_FILE_SIZE`)
- Private methods: `_leading_underscore` (e.g., `_clean_text`, `_validate_chunk`)

**Variables:**
- Local variables: `lowercase_with_underscores`
- Type variables: `PascalCase` (e.g., `Input`, `Output`, `T`)
- Pydantic models: `PascalCase` (e.g., `Document`, `Chunk`, `Metadata`)

**CLI Commands:**
- Main commands: single words lowercase (e.g., `process`, `similarity`, `validate`)
- Sub-commands: hyphenated lowercase (e.g., `config-show`, `config-init`)
- Flags: full words with hyphens (e.g., `--chunk-size`, `--output-dir`, `--no-validate`)

**Output Files:**
- JSON: `{source_filename}_chunks.json`
- TXT chunks: `{source_filename}_chunk_{001}.txt`
- CSV index: `{batch_name}_chunk_index.csv`
- Logs: `processing_{YYYY-MM-DD-HH-MM-SS}.log`
- Manifest: `.processing_manifest.json` (hidden file)

### Code Organization

**Module Structure:**
```python
# Standard import order (enforced by ruff)
# 1. Standard library imports
import json
import logging
from pathlib import Path
from typing import List, Optional

# 2. Third-party imports
import spacy
from pydantic import BaseModel
from rich.progress import Progress

# 3. Local application imports
from data_extract.core.models import Document, Chunk
from data_extract.core.pipeline import PipelineStage
from data_extract.utils.logging import get_logger
```

**Function Organization:**
```python
class Normalizer(PipelineStage):
    # 1. Class docstring
    """Normalizes extracted text for RAG optimization."""

    # 2. Class-level constants
    DEFAULT_ENTITY_TYPES = ["process", "risk", "control", "regulation", "policy", "issue"]

    # 3. __init__ and setup methods
    def __init__(self, config: NormalizerConfig):
        self.config = config
        self.logger = get_logger(__name__)

    # 4. Public interface methods
    def process(self, document: Document, context: ProcessingContext) -> Document:
        """Main processing method (implements PipelineStage)."""
        ...

    # 5. Private helper methods (alphabetical)
    def _clean_text(self, text: str) -> str:
        ...

    def _normalize_entities(self, entities: List[Entity]) -> List[Entity]:
        ...

    def _validate_output(self, document: Document) -> bool:
        ...
```

**Testing Organization:**
```python
# tests/unit/test_normalize/test_cleaning.py
import pytest
from data_extract.normalize.cleaning import TextCleaner

class TestTextCleaner:
    """Test suite for TextCleaner class"""

    @pytest.fixture
    def cleaner(self):
        return TextCleaner()

    def test_removes_ocr_artifacts(self, cleaner):
        """Should remove common OCR artifacts like ^^^^"""
        ...

    def test_normalizes_whitespace(self, cleaner):
        """Should collapse multiple spaces to single space"""
        ...

    def test_preserves_intentional_formatting(self, cleaner):
        """Should keep lists and emphasis intact"""
        ...
```

### Error Handling

**Always Catch Specific Exceptions:**
```python
# GOOD: Specific exception handling
try:
    document = extract_pdf(file_path)
except FileNotFoundError as e:
    logger.error("file_not_found", file=file_path)
    raise ProcessingError(f"File not found: {file_path}") from e
except PermissionError as e:
    logger.error("permission_denied", file=file_path)
    raise ProcessingError(f"Permission denied: {file_path}") from e

# BAD: Bare except
try:
    document = extract_pdf(file_path)
except:  # NEVER DO THIS
    pass
```

**Provide Actionable Error Messages:**
```python
# GOOD: Actionable error message
raise ConfigurationError(
    f"Invalid chunk size: {chunk_size}. "
    f"Must be between 128 and 2048 tokens. "
    f"Update config file or use --chunk-size flag."
)

# BAD: Vague error message
raise ConfigurationError("Invalid config")
```

**No Silent Failures:**
```python
# GOOD: Flag issues, don't skip silently
if ocr_confidence < threshold:
    logger.warning("low_ocr_confidence",
                   file=file_path,
                   confidence=ocr_confidence,
                   threshold=threshold)
    metadata["quality_flags"].append("low_ocr_confidence")
    # Continue processing, but flag the issue

# BAD: Silent skip
if ocr_confidence < threshold:
    return None  # NEVER RETURN NONE SILENTLY
```

### Logging Strategy

**Structured Logging Levels:**
- **DEBUG**: Detailed information for diagnosing problems (chunk boundaries, entity matches, config values)
- **INFO**: Confirmation of expected behavior (processing started/completed, files processed, chunks created)
- **WARNING**: Unexpected but recoverable (low OCR confidence, quality threshold not met, file skipped)
- **ERROR**: Serious problems (file processing failed, invalid configuration, missing dependencies)
- **CRITICAL**: System-level failures (database corruption, out of disk space, Python version mismatch)

**What to Log:**
```python
# START of operations (with context)
logger.info("batch_processing_started",
            input_dir=input_dir,
            file_count=len(files),
            config_version=config.version)

# DECISIONS made during processing
logger.debug("chunk_split_decision",
             reason="sentence_boundary",
             position=char_index,
             chunk_size=current_size)

# QUALITY issues (with threshold values)
logger.warning("quality_threshold_failed",
               metric="ocr_confidence",
               value=0.87,
               threshold=0.95,
               action="flagged_for_review")

# END of operations (with results)
logger.info("batch_processing_completed",
            successful=len(successful),
            failed=len(failed),
            duration_seconds=elapsed_time)
```

**Structured Format (JSON for audit trail):**
```json
{
  "timestamp": "2025-11-09T14:23:45.123Z",
  "level": "info",
  "event": "processing_completed",
  "file": "audit-report-2024.pdf",
  "file_hash": "sha256:abc123...",
  "chunks_created": 47,
  "quality_score": 0.96,
  "config_version": "1.0.0",
  "processing_time_ms": 2340
}
```

## Data Architecture

### Core Data Models (Pydantic)

**Implementation:** `src/data_extract/core/models.py` (Story 1.4)

```python
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path

class Entity(BaseModel):
    """Domain entity (risk, control, policy, etc.)"""
    model_config = ConfigDict(frozen=False)

    type: str = Field(..., description="Entity type (e.g., risk, control, policy)")
    id: str = Field(..., description="Unique entity identifier")
    text: str = Field(..., description="Entity text content")
    confidence: float = Field(..., ge=0.0, le=1.0,
                             description="Confidence score (0.0-1.0)")

class Metadata(BaseModel):
    """Metadata attached to documents and chunks"""
    model_config = ConfigDict(frozen=False)

    source_file: Path = Field(..., description="Path to original source file")
    file_hash: str = Field(..., description="SHA-256 hash for integrity")
    processing_timestamp: datetime = Field(..., description="Processing timestamp")
    tool_version: str = Field(..., description="Tool version")
    config_version: str = Field(..., description="Config version")
    document_type: str = Field(..., description="Document type (pdf, docx, xlsx)")
    quality_scores: Dict[str, float] = Field(default_factory=dict,
                                             description="Quality metrics")
    quality_flags: List[str] = Field(default_factory=list,
                                     description="Quality warnings")

class Document(BaseModel):
    """Represents a processed document"""
    model_config = ConfigDict(frozen=False)

    id: str = Field(..., description="Unique document identifier")
    text: str = Field(..., description="Document text content")
    entities: List[Entity] = Field(default_factory=list,
                                   description="Extracted entities")
    metadata: Metadata = Field(..., description="Processing metadata")
    structure: Dict[str, Any] = Field(default_factory=dict,
                                      description="Document structure")

class Chunk(BaseModel):
    """Represents a semantic chunk for RAG"""
    model_config = ConfigDict(frozen=False)

    id: str = Field(..., description="Chunk ID (format: {source}_{index:03d})")
    text: str = Field(..., description="Chunk text content")
    document_id: str = Field(..., description="Parent document reference")
    position_index: int = Field(..., ge=0, description="Position in document")
    token_count: int = Field(..., ge=0, description="Token count")
    word_count: int = Field(..., ge=0, description="Word count")
    entities: List[Entity] = Field(default_factory=list,
                                   description="Entities in chunk")
    section_context: str = Field(default="", description="Section/heading context")
    quality_score: float = Field(..., ge=0.0, le=1.0,
                                 description="Quality score (0.0-1.0)")
    readability_scores: Dict[str, float] = Field(default_factory=dict,
                                                 description="Readability metrics")
    metadata: Metadata = Field(..., description="Processing metadata")

class ProcessingContext(BaseModel):
    """Shared pipeline state (Story 1.4)"""
    model_config = ConfigDict(frozen=False, arbitrary_types_allowed=True)

    config: Dict[str, Any] = Field(default_factory=dict,
                                   description="Configuration (CLI > env > YAML)")
    logger: Optional[Any] = Field(default=None,
                                 description="Structured logger instance")
    metrics: Dict[str, Any] = Field(default_factory=dict,
                                    description="Metrics accumulation")
```

**Type Contracts Between Pipeline Stages:**
- Extract → Normalize: `Document` (with raw text)
- Normalize → Chunk: `ProcessingResult` (with cleaned content blocks)
- Chunk → Semantic: `Iterator[Chunk]` or `List[Chunk]` (with metadata)
- Semantic → Output: `ProcessingResult` (with analysis results)

### ChunkingEngine Component Design (Epic 3)

**Implementation:** `src/data_extract/chunk/` (Story 3.1)

**Core Components:**

```python
from dataclasses import dataclass
from typing import Iterator

@dataclass(frozen=True)
class Chunk:
    """Immutable chunk for RAG workflows"""
    text: str                    # Chunk text content
    metadata: ChunkMetadata      # Source, position, quality
    position_index: int          # Sequential position in document
    token_count: int             # Estimated token count (GPT tokenizer)
    word_count: int              # Actual word count
    source_block_id: str         # Reference to source ContentBlock

@dataclass(frozen=True)
class ChunkMetadata:
    """Chunk-level metadata"""
    source_file: str             # Original document path
    chunk_id: str                # Unique identifier (source_position)
    source_block_id: str         # Parent ContentBlock ID

@dataclass
class ChunkingConfig:
    """Chunking configuration"""
    chunk_size: int = 512        # Target tokens (128-2048 range)
    overlap_pct: float = 0.15    # Overlap percentage (0.0-0.5 range)

class ChunkingEngine:
    """Semantic boundary-aware chunking engine"""

    def __init__(self, config: ChunkingConfig):
        self.config = config
        self.segmenter = SentenceSegmenter()  # Lazy-loaded spaCy

    def chunk(self, result: ProcessingResult) -> Iterator[Chunk]:
        """
        Generator that yields chunks respecting sentence boundaries.

        Memory-efficient: Streams chunks without buffering entire document.
        Deterministic: Same input always produces same chunks.
        """
        for block in result.content_blocks:
            if block.block_type != ContentBlockType.TEXT:
                continue  # Only chunk text blocks

            # Segment into sentences (spaCy)
            sentences = self.segmenter.segment(block.text)

            # Build chunks respecting sentence boundaries
            current_chunk = []
            current_tokens = 0

            for sentence in sentences:
                sentence_tokens = self._estimate_tokens(sentence)

                # Yield chunk if adding sentence would exceed size
                if current_tokens + sentence_tokens > self.config.chunk_size:
                    if current_chunk:  # Yield accumulated sentences
                        yield self._build_chunk(current_chunk, block)
                        # Apply overlap (keep last N% of tokens)
                        current_chunk = self._apply_overlap(current_chunk)
                        current_tokens = sum(self._estimate_tokens(s) for s in current_chunk)

                # Add sentence to current chunk
                current_chunk.append(sentence)
                current_tokens += sentence_tokens

            # Yield final chunk
            if current_chunk:
                yield self._build_chunk(current_chunk, block)
```

**Key Design Decisions:**

1. **Generator-Based Streaming** (ADR-005):
   - Returns `Iterator[Chunk]` instead of `List[Chunk]`
   - Constant memory usage (doesn't buffer all chunks)
   - Enables progressive output writing

2. **Sentence Boundary Respect** (ADR-011):
   - Never splits mid-sentence (preserves semantic units)
   - Long sentences (>chunk_size) become single chunks
   - Uses spaCy for accurate boundary detection

3. **Immutable Chunks**:
   - Frozen dataclasses prevent mutations
   - Deterministic output (same input → same chunks)
   - Safe for parallel processing

4. **Configurable Overlap**:
   - Overlap preserves context across chunk boundaries
   - Range: 0% (no overlap) to 50% (max recommended)
   - Default: 15% balances context vs. redundancy

**Epic 3 Pipeline Integration:**

```
Epic 2 Output (ProcessingResult)
    ↓
    └─→ ContentBlock[] (text blocks from extraction/normalization)
         ↓
    ChunkingEngine.chunk(result) → Iterator[Chunk]
         ↓
         ├─→ SentenceSegmenter (spaCy en_core_web_md)
         │    └─→ Sentence boundaries detected
         ↓
         ├─→ Chunk Assembly (respecting boundaries)
         │    ├─→ Accumulate sentences until ~chunk_size
         │    ├─→ Apply overlap (keep last N% tokens)
         │    └─→ Yield chunk (generator pattern)
         ↓
    Output Stage (Epic 3 Story 3.4+)
         ├─→ JSON writer (structured metadata)
         ├─→ TXT writer (individual chunk files)
         └─→ CSV writer (chunk index)
```

**Performance Characteristics:**

| Metric | Baseline | NFR Target | Status |
|--------|----------|------------|--------|
| 10k-word latency | 3.0s | <4.0s | ✅ 75% of threshold |
| Memory (10k words) | 255 MB | <500 MB | ✅ 51% of limit |
| Batch memory | ≤7.8 MB variance | <100 MB | ✅ Constant |
| Scaling | 0.19s per 1k words | Linear | ✅ Validated |

See `docs/performance-baselines-epic-3.md` for detailed benchmarks.

### JSON Output Format (Story 3.4)

**Decision:** Emit a single JSON document per processed file with the shape:

```json
{
  "metadata": {
    "processing_version": "1.0.0-epic3",
    "processing_timestamp": "2025-11-15T04:30:56Z",
    "configuration": {"chunk_size": 512, "overlap_pct": 0.15, "entity_aware": false, "quality_enrichment": true},
    "source_documents": [".../test_document.txt"],
    "chunk_count": 123
  },
  "chunks": [
    {
      "chunk_id": "acme_report_chunk_000",
      "text": "...",
      "metadata": {...ChunkMetadata serialization...},
      "entities": [...EntityReference...],
      "quality": {...QualityScore...}
    }
  ]
}
```

**Rationale**
- Single document JSON is human readable, diff-friendly, and immediately parsable by `json.load()`, pandas (`pd.json_normalize(chunks)`), jq, Node.js, and downstream vector-database importers.
- JSON Schema Draft 7 validation (`src/data_extract/output/schemas/data-extract-chunk.schema.json`) enforces structure, score ranges, enums, and string patterns. Validation is enabled by default and can be disabled per formatter instance.
- Metadata header captures reproducibility details (tool version, timestamp, chunking configuration, source file list, chunk count) and is required for audit trails.

**Implementation Notes**
- Formatter protocol + dataclasses live in `src/data_extract/output/formatters/base.py`; `JsonFormatter` is in `.../json_formatter.py`.
- Schema reference for consumers documented in `docs/json-schema-reference.md`.
- Brownfield compatibility: `data_extract.chunk.engine` normalizes metadata emanating from both `data_extract.core` Pydantic objects and the legacy `src.core` dataclasses so JsonFormatter always receives a canonical `Metadata`.
- Validation/compatibility tests: `tests/unit/test_output/test_json_schema.py`, `tests/unit/test_output/test_json_formatter.py`, `tests/integration/test_output/test_json_output_pipeline.py`, and `tests/integration/test_output/test_json_compatibility.py`.
- Performance baselines (<1 second per document) tracked in `tests/performance/test_json_performance.py` with summary metrics published in `docs/performance-baselines-epic-3.md`.
### Entity Relationships

**Six Audit Entity Types** (Domain-Specific):
1. **Process** → Business processes under audit
2. **Risk** → Identified risks (can relate to multiple processes)
3. **Control** → Security controls (mitigate risks)
4. **Regulation** → Regulatory frameworks (SOX, GDPR, etc.)
5. **Policy** → Corporate policies (implement regulations)
6. **Issue** → Audit findings (gaps in controls)

**Relationships Preserved:**
- Risk → Control: "Risk X mitigated by Control Y"
- Process → Risk: "Process A has Risk B"
- Regulation → Policy: "Policy implements Regulation"
- Control → Issue: "Control C has finding Issue D"

### Storage & Persistence

**File-Based (No Database):**
- **Processing manifest**: `.processing_manifest.json` (tracks processed files)
- **Configuration**: `~/.data-extract/config.yaml` or project-local
- **Logs**: `~/.data-extract/logs/` or configured location
- **Cache**: TF-IDF vectors, LSA models saved as joblib files
- **Outputs**: JSON, TXT, CSV in configured output directory

**Caching Strategy:**
```python
# File hash as cache key
file_hash = hashlib.sha256(file_path.read_bytes()).hexdigest()

# Manifest tracks: {file_hash: {output_path, timestamp, config_hash}}
if file_hash in manifest and config_hash == manifest[file_hash]["config_hash"]:
    return load_from_cache(manifest[file_hash]["output_path"])
```

## Security Architecture

### On-Premise Processing (Enterprise Requirement)
- **NO external API calls** (no OpenAI, Anthropic, etc.)
- **NO cloud dependencies** (no AWS, Azure, GCP services)
- **NO network transmission of data** (all processing local)
- **NO telemetry or usage tracking**

### Data Handling
- **Sensitive document processing**: Assume all inputs are confidential audit documents
- **Temporary file cleanup**: Delete temp files after processing (configurable retention)
- **File permissions**: Output files inherit source file permissions (or configurable)
- **No data in logs**: Log file paths and hashes, NOT content

### Input Validation
- **File type validation**: Check magic bytes, not just extensions
- **File size limits**: Configurable max file size (default: 100MB per file)
- **Path traversal prevention**: Validate all file paths (reject ../ patterns)
- **Safe extraction**: Prevent zip bombs, XML bombs in document parsing

### Dependency Security
- **Pinned versions**: All dependencies pinned in pyproject.toml for reproducibility
- **No transformer models**: Comply with enterprise IT restriction
- **Trusted sources**: All packages from official PyPI
- **Regular updates**: Security patches via Dependabot or manual review

## Performance Considerations

### Target Performance (NFR-P1)
- **100 mixed files in <10 minutes** (sustained throughput: ~10 files/min)
- **Individual file processing**: <5 seconds (excluding OCR)
- **OCR processing**: <10 seconds per scanned page
- **Similarity matrix**: <5 minutes for 1,000 documents

### Memory Efficiency (NFR-P2)
- **Max memory footprint**: 2GB during batch processing
- **Streaming architecture**: Process files one at a time, release memory after each
- **Sparse matrices**: Use scipy sparse matrices for TF-IDF vectors (memory efficient)
- **Chunked processing**: Don't load entire document corpus into RAM

### Optimization Strategies
- **Parallel processing**: Use `concurrent.futures` for I/O-bound tasks (file reading)
  - ThreadPoolExecutor for I/O (default: 4 workers)
  - ProcessPoolExecutor for CPU-bound (semantic analysis) if needed
- **Lazy loading**: Don't load spaCy model until first use
- **Vectorizer caching**: Fit TF-IDF vectorizer once, reuse for all documents
- **Progressive output**: Write chunks incrementally, don't buffer all in memory

### Bottleneck Analysis
- **Slowest operations**:
  1. OCR (pytesseract) - 10s per page
  2. spaCy sentence segmentation - ~0.5s per document
  3. TF-IDF vectorization - ~1s per 100 documents
- **Optimization priority**: OCR preprocessing (quality/speed tradeoff)

## Deployment Architecture

### Local Development
```
Developer Workstation
├── Python 3.12 virtual environment
├── Source code (git repository)
├── Test fixtures (sample audit documents)
└── Local output directory
```

### Enterprise Deployment (Future)
```
Enterprise Workstation (F100 Environment)
├── Python 3.12 (IT-approved)
├── Tesseract OCR (system-installed)
├── Tool installed via pip (internal PyPI mirror or wheel file)
├── Configuration in user home directory (~/.data-extract/)
├── Shared output location (network drive)
└── Logs (local or network share)
```

### Packaging & Distribution
- **Development**: `pip install -e ".[dev]"` from source
- **User install**: `pip install data-extraction-tool` (future: internal PyPI)
- **Wheel distribution**: Build wheel for air-gapped systems (`pip wheel .`)
- **Dependencies bundled**: Optional vendoring for restricted networks

## Development Environment

### Prerequisites

**Required:**
- Python 3.12.x (enterprise requirement - must be exact version)
- Git (for version control)
- Tesseract OCR engine 5.x (system-level dependency)

**Recommended:**
- VS Code or PyCharm (Python IDE)
- Windows Terminal or iTerm2 (modern terminal for Rich UI)
- 16GB RAM (for processing large batches)
- SSD (faster file I/O)

### Setup Commands

```bash
# Clone repository
git clone <repository-url>
cd data-extraction-tool

# Create Python 3.12 virtual environment
python3.12 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Verify Python version
python --version  # Should show Python 3.12.x

# Install dependencies (development mode with dev tools)
pip install -e ".[dev]"

# Download spaCy language model
python -m spacy download en_core_web_md

# Install pre-commit hooks (enforces code quality)
pre-commit install

# Verify installation
python -m data_extract --help

# Run tests to verify setup
pytest tests/ -v

# Check code quality
ruff check src/
mypy src/
black --check src/
```

### IDE Configuration (VS Code)

**`.vscode/settings.json`:**
```json
{
  "python.defaultInterpreterPath": "./venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": ["tests/"]
}
```

## Architecture Decision Records (ADRs)

### ADR-001: Choose Typer Over Click for CLI Framework
**Status**: Accepted
**Context**: Need modern CLI framework with type safety and minimal boilerplate
**Decision**: Use Typer (built on Click) for CLI instead of raw Click or argparse
**Consequences**:
- ✅ Auto-generated help text from type hints
- ✅ Less boilerplate than Click
- ✅ Compatible with Click (can mix if needed)
- ❌ Slightly less mature than Click (but well-maintained)

### ADR-002: Use Pydantic Over Dataclasses
**Status**: Accepted
**Context**: Need type-safe data models with validation
**Decision**: Use Pydantic v2 for all data models (Document, Chunk, Config)
**Consequences**:
- ✅ Runtime validation prevents bugs
- ✅ JSON schema generation (for documentation)
- ✅ Better error messages than dataclasses
- ❌ Slight performance overhead vs dataclasses (acceptable tradeoff)

### ADR-003: File-Based Storage (No Database)
**Status**: Accepted
**Context**: CLI tool needs persistence for caching and configuration
**Decision**: Use file-based storage (JSON manifest, YAML config) instead of database
**Consequences**:
- ✅ Simple, no database dependency
- ✅ Human-readable (can edit YAML config)
- ✅ Git-friendly (config is version-controllable)
- ❌ Not suitable for very large scale (>10k documents) - acceptable for audit use case

### ADR-004: Classical NLP Only (No Transformers)
**Status**: Accepted (Enterprise Constraint)
**Context**: Enterprise IT policy prohibits transformer-based models
**Decision**: Use classical NLP (TF-IDF, LSA, Word2Vec) via scikit-learn and gensim
**Consequences**:
- ✅ Complies with enterprise restrictions
- ✅ Faster inference, lower memory
- ✅ Interpretable results
- ❌ Less semantic understanding than transformers (acceptable for audit domain)

### ADR-005: Streaming Pipeline (Not Batch-Load)
**Status**: Accepted
**Context**: Need to process batches efficiently without exhausting memory
**Decision**: Process files one at a time through pipeline, release memory after each
**Consequences**:
- ✅ Constant memory usage (2GB max)
- ✅ Can process arbitrarily large batches
- ✅ Graceful error handling (one file failure doesn't corrupt batch state)
- ❌ Slightly slower than full batch processing (acceptable tradeoff)

### ADR-006: Continue-On-Error Batch Processing
**Status**: Accepted
**Context**: One corrupted file shouldn't block entire audit engagement processing
**Decision**: Catch per-file errors, log, quarantine, continue with remaining files
**Consequences**:
- ✅ Resilient batch processing
- ✅ Detailed error reporting at end
- ✅ User can fix issues and re-run only failed files
- ❌ Requires careful exception design (ProcessingError vs CriticalError)

### ADR-011: Semantic Boundary-Aware Chunking
**Status**: Accepted (Epic 3, Story 3.1) - **Amended 2025-11-13**
**Context**: RAG systems require text chunks that preserve semantic meaning and context. Chunks split mid-sentence or mid-thought reduce LLM comprehension and retrieval accuracy.
**Decision**: Chunking respects sentence boundaries detected by spaCy's sentence segmentation. Chunks never split in the middle of a sentence.
**Implementation**:
- ChunkingEngine uses SentenceSegmenter (Story 2.5.2) for accurate boundary detection
- spaCy `en_core_web_md` model provides production-ready sentence boundary detection
- Chunks respect target size (default 512 tokens) but extend to complete sentences
- Very long sentences (>chunk_size) become single chunks to preserve context
- **Section boundary detection deferred to Story 3.2** (see Amendment below)
**Rationale**:
- Preserves complete thoughts and context within each chunk
- Improves LLM understanding during RAG retrieval
- Maintains grammatical coherence for better embedding quality
- Aligns with document structure (sentences are natural semantic units)
**Trade-offs**:
- ✅ Better semantic coherence and LLM comprehension
- ✅ Deterministic chunking (same input → same chunks)
- ✅ Respects document structure (sentences, paragraphs)
- ❌ Chunks may exceed target size for very long sentences (acceptable - preserves meaning)
- ❌ spaCy adds ~1.8s latency per 10k words (acceptable for batch processing)
**Alternatives Considered**:
- **Character-based splitting** (rejected): Breaks mid-sentence, destroys context
- **Fixed token windows** (rejected): Splits thoughts arbitrarily
- **Paragraph-based chunking** (rejected): Too coarse, paragraphs often exceed limits
**Performance Impact**:
- **Latency:** ~3s for 10k-word document (60% is spaCy segmentation)
- **Memory:** 255 MB peak (51% of 500 MB limit per document)
- **Scaling:** Linear (0.19s per 1,000 words)
- **Acceptable:** Batch processing use case tolerates 3s latency

**Amendment 2025-11-13 (Story 3.1 Code Review):**
- **AC-3.1-2 (Section Boundary Detection) Deferred to Story 3.2**
- **Rationale**: Current document.structure lacks section/heading markers (only contains page_count, word_count, image_count, etc.). Proper implementation requires Epic 2 enhancements to preserve ContentBlock structure (headings, sections) through extraction and normalization stages.
- **Story 3.1 Scope**: Sentence-boundary chunking (AC-3.1-1) is fully implemented and production-ready.
- **Future Work (Story 3.2)**: Section-aware chunking will be addressed alongside entity boundary detection, once Epic 2 provides the necessary structural metadata.

---

_Generated by BMAD Decision Architecture Workflow v1.3.2_
_Date: 2025-11-09_
_For: andrew (Intermediate Skill Level)_
_Project: data-extraction-tool (Knowledge Quality Gateway for Enterprise Gen AI)_
