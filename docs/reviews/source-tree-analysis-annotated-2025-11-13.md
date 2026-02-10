# Source Tree Analysis - Annotated Directory Structure

**Generated**: 2025-11-13
**Project**: Data Extraction Tool (Enterprise Document Processing Pipeline)
**Repository Type**: Monolith with Dual Codebase
**Architecture Pattern**: Modular five-stage pipeline (Extract → Normalize → Chunk → Semantic → Output)

---

## Project Structure Overview

The Data Extraction Tool implements a **dual codebase strategy** during brownfield modernization:

- **GREENFIELD** (`src/data_extract/`): Modern modular architecture following Epic-based development (Python 3.12+, full type safety, pytest)
- **BROWNFIELD** (`src/{cli,core,extractors,...}`): Legacy production code maintained for compatibility during Epic 1-2 migration
- **Both systems coexist** until consolidation is complete (Story 1.4)

---

## Complete Directory Tree with Annotations

```
data-extraction-tool-1/                    # Project root
│
├── src/                                   # Source code (DUAL CODEBASE)
│   │
│   ├── data_extract/                      # ✨ GREENFIELD: New modular pipeline architecture
│   │   │                                  #    Implements 5-stage processing with frozen dataclasses & ABCs
│   │   │
│   │   ├── __init__.py                    # Package initialization
│   │   │
│   │   ├── cli.py                         # → PRIMARY CLI ENTRY POINT (Typer-based)
│   │   │                                  #    data-extract command routes here
│   │   │                                  #    Epic 5 CLI implementation
│   │   │
│   │   ├── chunk/                         # STAGE 3: Semantic-aware chunking
│   │   │   └── __init__.py
│   │   │                                  # Placeholder for spaCy-based sentence boundary detection
│   │   │                                  # To be implemented in Epic 3 (Story 3.1)
│   │   │
│   │   ├── core/                          # Core abstractions & protocols
│   │   │   ├── __init__.py
│   │   │   ├── exceptions.py              # Custom exception hierarchy
│   │   │   ├── models.py                  # Frozen dataclasses:
│   │   │   │                              #   - ExtractionResult (Stage 1 output)
│   │   │   │                              #   - ContentBlock (structural units)
│   │   │   │                              #   - ProcessingResult (Stages 2-4 output)
│   │   │   │                              #   - FormattedOutput (Stage 5 output)
│   │   │   └── pipeline.py                # PipelineStage protocol & orchestration
│   │   │
│   │   ├── config/                        # Configuration management
│   │   │   └── __init__.py                # Config loading & schema validation (Epic 5)
│   │   │
│   │   ├── extract/                       # STAGE 1: Format-specific extraction
│   │   │   ├── __init__.py
│   │   │   ├── adapter.py                 # Unified extractor interface
│   │   │   ├── pdf.py                     # PDF extraction (PyMuPDF + Tesseract fallback)
│   │   │   ├── docx.py                    # DOCX extraction (python-docx)
│   │   │   ├── excel.py                   # XLSX/XLS extraction (openpyxl)
│   │   │   ├── pptx.py                    # PPTX extraction (python-pptx)
│   │   │   ├── csv.py                     # CSV extraction (Python csv module)
│   │   │   └── txt.py                     # TXT extraction (raw text)
│   │   │
│   │   ├── normalize/                     # STAGE 2: Text cleaning & standardization
│   │   │   ├── __init__.py
│   │   │   ├── cleaning.py                # Text normalization (whitespace, encoding)
│   │   │   ├── entities.py                # Named entity standardization
│   │   │   ├── metadata.py                # Content metadata extraction
│   │   │   ├── schema.py                  # Schema validation
│   │   │   ├── validation.py              # Content validation rules
│   │   │   ├── normalizer.py              # Main normalizer orchestrator
│   │   │   └── config.py                  # Normalization configuration
│   │   │
│   │   ├── output/                        # STAGE 5: Multi-format output generation
│   │   │   └── __init__.py                # JSON, TXT, CSV formatters (Epic 3)
│   │   │
│   │   ├── semantic/                      # STAGE 4: Classical NLP analysis
│   │   │   └── __init__.py                # TF-IDF, LSA (scikit-learn)
│   │   │                                  # No transformers per enterprise constraint
│   │   │                                  # To be implemented in Epic 4
│   │   │
│   │   ├── utils/                         # Shared utilities
│   │   │   ├── __init__.py
│   │   │   └── nlp.py                     # spaCy lazy-loader & NLP helpers
│   │   │
│   │   └── __pycache__/                   # Python bytecode cache
│   │
│   ├── cli/                               # 📦 BROWNFIELD: Legacy CLI utilities
│   │   ├── __init__.py
│   │   ├── __main__.py                    # Legacy CLI entry point (deprecated)
│   │   ├── main.py                        # Legacy command dispatcher
│   │   ├── commands.py                    # Legacy command handlers
│   │   └── progress_display.py            # Legacy progress UI (Rich)
│   │
│   ├── core/                              # 📦 BROWNFIELD: Legacy core modules
│   │   ├── __init__.py
│   │   ├── interfaces.py                  # Abstract base classes
│   │   └── models.py                      # Legacy data models
│   │
│   ├── extractors/                        # 📦 BROWNFIELD: Legacy format extractors
│   │   ├── __init__.py
│   │   ├── pdf_extractor.py               # Legacy PDF extraction
│   │   ├── docx_extractor.py              # Legacy DOCX extraction
│   │   ├── excel_extractor.py             # Legacy Excel extraction
│   │   ├── pptx_extractor.py              # Legacy PPTX extraction
│   │   ├── csv_extractor.py               # Legacy CSV extraction
│   │   └── txt_extractor.py               # Legacy text extraction
│   │
│   ├── processors/                        # 📦 BROWNFIELD: Legacy processing modules
│   │   ├── __init__.py
│   │   ├── context_linker.py              # Context preservation
│   │   ├── metadata_aggregator.py         # Metadata collection
│   │   └── quality_validator.py           # Quality assurance
│   │
│   ├── formatters/                        # 📦 BROWNFIELD: Legacy output formatters
│   │   ├── __init__.py
│   │   ├── json_formatter.py              # JSON output
│   │   ├── markdown_formatter.py          # Markdown output
│   │   └── chunked_text_formatter.py      # Chunked text output
│   │
│   ├── infrastructure/                    # 📦 BROWNFIELD: Legacy infrastructure
│   │   ├── __init__.py
│   │   ├── logging_framework.py           # Structured logging (structlog)
│   │   ├── config_manager.py              # Configuration management
│   │   ├── error_handler.py               # Error handling & recovery
│   │   └── progress_tracker.py            # Progress monitoring
│   │
│   ├── pipeline/                          # 📦 BROWNFIELD: Legacy pipeline orchestration
│   │   ├── __init__.py
│   │   ├── extraction_pipeline.py         # Main pipeline workflow
│   │   └── batch_processor.py             # Batch processing engine
│   │
│   └── data_extraction_tool.egg-info/     # Setuptools generated metadata
│
├── tests/                                 # Test suite (pytest with markers)
│   │
│   ├── __pycache__/                       # Python bytecode cache
│   │
│   ├── conftest.py                        # [MISSING - to be created with pytest fixtures]
│   │
│   ├── fixtures/                          # Test data & fixtures (90+ MB)
│   │   ├── README.md                      # Fixture documentation & regeneration scripts
│   │   ├── archer/                        # Real-world sample documents
│   │   ├── docx/                          # DOCX test fixtures
│   │   ├── excel/                         # XLSX test fixtures
│   │   ├── images/                        # Image test fixtures
│   │   ├── pdfs/                          # PDF test fixtures
│   │   │   ├── large/                     # Large PDF samples (100+ MB)
│   │   │   └── scanned/                   # Scanned PDF (OCR test cases)
│   │   ├── edge-cases/                    # Edge case test data
│   │   │   ├── docx/
│   │   │   ├── malformed/                 # Corrupted/invalid files
│   │   │   ├── pdf/
│   │   │   ├── pptx/
│   │   │   ├── txt/
│   │   │   └── xlsx/
│   │   ├── normalization/                 # Text normalization test data
│   │   │   ├── dirty_text_samples/
│   │   │   └── expected_clean_outputs/
│   │   ├── real-world-files/              # Production document samples
│   │   ├── stress_output/                 # Performance test outputs
│   │   └── batch_output_*/                # Batch processing test outputs
│   │
│   ├── unit/                              # Fast unit tests (isolated, <100ms each)
│   │   ├── test_extract/                  # GREENFIELD: Stage 1 extractor tests
│   │   │   ├── test_pdf.py
│   │   │   ├── test_docx.py
│   │   │   ├── test_excel.py
│   │   │   ├── test_pptx.py
│   │   │   ├── test_csv.py
│   │   │   └── test_txt.py
│   │   ├── test_normalize/                # GREENFIELD: Stage 2 normalizer tests
│   │   │   ├── test_cleaning.py
│   │   │   ├── test_entities.py
│   │   │   ├── test_validation.py
│   │   │   └── test_schema.py
│   │   ├── test_utils/                    # GREENFIELD: Utility tests
│   │   │   └── test_nlp.py
│   │   ├── cli/                           # BROWNFIELD: CLI tests
│   │   ├── core/                          # BROWNFIELD: Core module tests
│   │   ├── extractors/                    # BROWNFIELD: Extractor tests
│   │   ├── formatters/                    # BROWNFIELD: Formatter tests
│   │   ├── infrastructure/                # BROWNFIELD: Infrastructure tests
│   │   ├── pipeline/                      # BROWNFIELD: Pipeline tests
│   │   └── processors/                    # BROWNFIELD: Processor tests
│   │
│   ├── integration/                       # Multi-component end-to-end tests
│   │   ├── test_pipeline.py               # Complete 5-stage pipeline tests
│   │   ├── test_extraction_pipeline.py    # Brownfield pipeline integration
│   │   └── [other integration test files]
│   │
│   ├── performance/                       # Performance benchmarks & stress tests
│   │   ├── batch_100_files/               # 100-file batch test data
│   │   │   ├── docx/
│   │   │   ├── mixed/
│   │   │   ├── pdfs/
│   │   │   └── xlsx/
│   │   ├── [performance test files]
│   │   └── [markers: -m "not slow" skips slow tests]
│   │
│   ├── validation/                        # UAT validation tests
│   ├── outputs/                           # Test execution outputs
│   ├── test_cli/                          # [DEPRECATING - move to unit/cli]
│   ├── test_edge_cases/                   # [DEPRECATING - consolidating to fixtures]
│   ├── test_extractors/                   # [CONSOLIDATING to unit/]
│   ├── test_formatters/                   # [CONSOLIDATING to unit/]
│   ├── test_infrastructure/               # [CONSOLIDATING to unit/]
│   ├── test_pipeline/                     # [CONSOLIDATING to unit/]
│   ├── test_processors/                   # [CONSOLIDATING to unit/]
│   └── __pycache__/
│
├── docs/                                  # Comprehensive documentation (90+ files)
│   │                                      #    Organized by epic, story, and domain
│   │
│   ├── README.md                          # Main architecture documentation
│   ├── architecture.md                    # Technical architecture & ADRs
│   ├── epics.md                           # Epic roadmap & breakdown
│   │
│   ├── .archive/                          # ARCHIVED: Pre-BMAD documentation
│   │                                      #    165+ legacy files (2025-11-13 cleanup)
│   │
│   ├── PRD.md                             # Product Requirements Document
│   ├── tech-spec-epic-1.md                # Epic 1 technical specification
│   ├── tech-spec-epic-2.md                # Epic 2 technical specification
│   ├── tech-spec-epic-2.5.md              # Epic 2.5 (Refinement & Quality)
│   │
│   ├── stories/                           # Story-level implementation specs
│   │   ├── 1.1-project-infrastructure.md
│   │   ├── 1.2-brownfield-assessment.md
│   │   ├── 1.3-testing-framework.md
│   │   ├── 1.4-core-pipeline-consolidation.md
│   │   ├── 2.1-pdf-extraction.md
│   │   ├── 2.2-docx-extraction.md
│   │   ├── 2.3-schema-standardization.md
│   │   ├── 2.4-text-cleaning.md
│   │   ├── 2.5-*.md                      # Epic 2.5 quality refinement stories
│   │   └── [other story files]
│   │
│   ├── brownfield-assessment.md           # Complete legacy code analysis
│   ├── ci-cd-pipeline.md                  # CI/CD workflow & configuration
│   ├── ci-cd-infrastructure-analysis.md   # GitHub Actions setup details
│   │
│   ├── uat/                               # User Acceptance Testing framework
│   │   ├── test-cases/                    # Generated UAT test specifications
│   │   ├── test-context/                  # Test infrastructure context (XML)
│   │   ├── test-results/                  # Test execution results
│   │   ├── reviews/                       # QA review & approval reports
│   │   └── tmux-cli-windows-setup.md      # Windows tmux-cli guidance
│   │
│   ├── traceability-*.md                  # Epic-to-implementation traceability
│   ├── performance-baselines-*.md         # NFR baseline measurements
│   ├── TESTING-README.md                  # Test organization & patterns
│   ├── LOGGING_GUIDE.md                   # Logging infrastructure docs
│   ├── ERROR_HANDLING_GUIDE.md            # Error handling patterns
│   ├── troubleshooting-spacy.md           # spaCy setup & troubleshooting
│   ├── tmux-cli-instructions.md           # tmux-cli reference & usage
│   │
│   ├── audit-report-*.md                  # Workflow audit reports (BMAD generated)
│   ├── housekeeping-findings-2025-11-13.md # Documentation cleanup summary
│   └── [40+ other reference docs]
│
├── scripts/                               # Development & utility scripts
│   ├── __pycache__/
│   │
│   ├── profile_pipeline.py                # Performance profiling utility
│   │                                      #   - get_total_memory() for process monitoring
│   │                                      #   - baseline establishment (Story 2.5.1)
│   │
│   ├── run_performance_suite.py           # Batch performance testing
│   ├── run_test_extractions.py            # Extract test runner
│   │
│   ├── generate_large_pdf_fixture.py      # Fixture generation helpers
│   ├── generate_large_excel_fixture.py
│   ├── generate_scanned_pdf_fixture.py
│   ├── create_performance_batch.py
│   │
│   ├── build_package.sh                   # Package build (Linux/macOS)
│   ├── build_package.bat                  # Package build (Windows)
│   ├── verify_package.sh                  # Package verification
│   ├── create_dev_package.sh              # Dev environment setup
│   │
│   ├── test_installation.py               # Installation validation
│   ├── validate_installation.py
│   ├── check_package_contents.py
│   │
│   ├── diagnose_ocr.py                    # OCR diagnostics
│   ├── fix_import_paths.py                # Import path correction
│   ├── regenerate_gold_standard.py        # Test baseline regeneration
│   └── [other utility scripts]
│
├── config/                                # Configuration templates & schemas
│   └── normalize/                         # Normalization config (Story 2.3)
│       └── [YAML/JSON schemas]
│
├── examples/                              # Usage examples & documentation
│   ├── README.md                          # Example guide
│   ├── minimal_extractor.py               # Minimal extractor usage
│   ├── minimal_processor.py               # Minimal processor usage
│   ├── simple_pipeline.py                 # Simple pipeline example
│   ├── pdf_extractor_example.py           # Format-specific examples
│   ├── docx_extractor_example.py
│   ├── excel_extractor_example.py
│   ├── pptx_extractor_example.py
│   ├── docx_with_logging.py               # Logging integration example
│   ├── logging_example.py
│   ├── processor_pipeline_example.py      # Pipeline composition example
│   ├── formatter_examples.py              # Output formatting examples
│   └── sample_input.*                     # Sample input files
│
├── bmad/                                  # BMAD Workflow System (Brownfield Modernization)
│   │                                      #    Epic-based development framework
│   ├── workflows/                         # BMAD workflows (create-story, dev-story, etc.)
│   ├── agents/                            # BMAD agents (dev, qa, pm, architect, etc.)
│   ├── modules/                           # BMAD modules (bmm, cis, etc.)
│   └── [BMAD configuration]
│
├── .github/                               # GitHub configuration
│   └── workflows/                         # CI/CD automation
│       ├── test.yml                       # pytest suite (unit + integration + performance)
│       ├── performance.yml                # Performance regression testing
│       └── performance-regression.yml     # Continuous performance monitoring
│
├── .claude/                               # Claude Code configuration
│   ├── CLAUDE.md                          # Project-specific instructions (THIS FILE)
│   ├── commands/                          # Custom slash commands
│   │   └── bmad/                          # BMAD workflow shortcuts
│   └── hooks/                             # Pre-commit/post-commit hooks
│
├── .mypy_cache/                           # Type checker cache
├── .pytest_cache/                         # pytest cache
├── .ruff_cache/                           # ruff linter cache
│
├── venv/                                  # Python virtual environment (local dev)
│
├── dist/                                  # Built distributions
├── htmlcov/                               # HTML coverage reports
├── logs/                                  # Application logs
├── output/                                # Sample output directory
│
├── .gitignore                             # Git ignore rules
├── .pre-commit-config.yaml                # Pre-commit hooks configuration
│
├── pyproject.toml                         # → PROJECT CONFIGURATION (setuptools)
│                                          #    Entry points, dependencies, tool configs
│
├── setup.py                               # Legacy setup.py (pyproject.toml preferred)
├── MANIFEST.in                            # Package manifest
│
├── pytest.ini                             # pytest configuration & markers
├── README.md                              # Project overview & quickstart
│
├── analyze_profile.py                     # Profile analysis utility
├── create_fixtures.py                     # Fixture creation script
│
├── CLAUDE.md                              # → PROJECT INSTRUCTIONS (for Claude Code)
│                                          #    Architecture, development workflow, commands
│
├── profile.stats                          # Performance profiling data
├── test.log                               # Test execution logs
├── NUL / cli_test_results.txt             # Test output artifacts
├── .coverage.*                            # Coverage reports (by Python process)
│
└── TRASH/                                 # Cleanup staging area
    └── TRASH-FILES.md                     # Archive manifest
```

---

## Critical Folders Explained

### Greenfield Architecture (`src/data_extract/`)

The modern modular five-stage pipeline implementing enterprise-grade document processing:

1. **Extract Stage** (`extract/`) - Format-specific extractors (PDF, DOCX, XLSX, PPTX, CSV, TXT)
   - Unified interface via `adapter.py`
   - PyMuPDF for PDFs + Tesseract fallback for OCR
   - Returns `ExtractionResult` frozen dataclass

2. **Normalize Stage** (`normalize/`) - Text cleaning & standardization
   - Text cleaning (whitespace, encoding normalization)
   - Entity standardization & validation
   - Metadata extraction
   - Returns `ProcessingResult` preserving structure

3. **Chunk Stage** (`chunk/`) - Semantic-aware chunking (Epic 3)
   - spaCy-based sentence boundary detection
   - Placeholder pending implementation

4. **Semantic Stage** (`semantic/`) - Classical NLP analysis (Epic 4)
   - TF-IDF & LSA via scikit-learn
   - No transformer models (enterprise constraint)

5. **Output Stage** (`output/`) - Multi-format generation
   - JSON, TXT, CSV formatters
   - Pending Epic 3 implementation

**Design Patterns**:
- Frozen dataclasses for immutability
- ABC interfaces for extensibility
- Type hints throughout (mypy strict mode)
- Comprehensive test mirrors structure

### Brownfield Legacy (`src/{cli,core,extractors,...}`)

Production code maintained during modernization (Story 1.2 assessment):

- **`cli/`** - Legacy Click-based CLI (pre-Typer)
- **`core/`** - Abstract interfaces & legacy models
- **`extractors/`** - Original format extractors (being modernized)
- **`processors/`** - Content processors (context linker, metadata aggregator, QA)
- **`formatters/`** - Output generators (JSON, Markdown, chunked text)
- **`infrastructure/`** - Logging, config, error handling, progress tracking
- **`pipeline/`** - Batch processor & pipeline orchestration

**Status**: Both systems coexist. Greenfield code supersedes brownfield during Epic consolidation (Story 1.4).

### Test Organization (`tests/`)

**Structure mirrors `src/`**:

- **`unit/`** - Fast isolated tests (markers: unit, extraction, processing, formatting, cli)
  - Test discovery: `test_*.py` files with `test_*()` functions
  - Fixtures in `conftest.py` (shared across tests)

- **`integration/`** - Multi-component workflows
  - End-to-end pipeline validation
  - Markers: integration, pipeline

- **`performance/`** - Benchmarks & stress tests
  - Batch processing (100+ files)
  - NFR validation against baselines
  - Markers: performance, slow

- **`fixtures/`** - Test data (90+ MB)
  - Real-world samples, edge cases, large files
  - Organized by format & test category
  - Regeneration scripts provided

**Coverage Requirements**:
- Epic 1: >60% baseline (enforced in CI)
- Epic 2-4: >80% overall
- Epic 5: >90% critical paths

### Documentation (`docs/`)

**Organized by domain**:

- **Epics & Stories**: `epics.md`, `tech-spec-*.md`, `stories/` directory
- **Architecture**: `architecture.md`, `PRD.md`, ADRs
- **Implementation**: `brownfield-assessment.md`, traceability matrices
- **Operations**: CI/CD docs, testing guides, logging setup, troubleshooting
- **UAT Framework**: `uat/` with test cases, context, results, reviews
- **Archive**: `.archive/` with 165+ pre-BMAD files (legacy documentation)

### Scripts (`scripts/`)

Development utilities for:

- **Performance analysis** (`profile_pipeline.py`, `run_performance_suite.py`)
  - Baselines established in Story 2.5.1
  - Memory monitoring via `get_total_memory()` helper

- **Fixture generation** (`generate_*_fixture.py`)
  - Large PDF/Excel/scanned PDF creation
  - Batch test data generation

- **Installation & validation** (`test_installation.py`, `validate_installation.py`)
  - Package integrity checks

- **Build automation** (`build_package.sh/bat`)
  - Platform-specific build tooling

---

## Entry Points & Key Integration Points

### Primary Entry Points

1. **CLI Entry Point**: `src/data_extract/cli.py` → `data-extract` command
   - Configured in `pyproject.toml` line 90: `data-extract = "data_extract.cli:app"`
   - Typer-based modern CLI
   - Epic 5 implementation

2. **Python Package Entry Point**: `src/data_extract/__init__.py`
   - Public API export for programmatic usage

3. **Brownfield Legacy Entry**: `src/cli/__main__.py` (deprecated)
   - Original Click-based CLI

4. **Testing Entry**: `pytest.ini` configuration
   - Markers: unit, integration, performance, slow, extraction, processing, formatting, pipeline, cli
   - Coverage threshold: 60% (enforced in CI)

### Integration Architecture

**Greenfield ↔ Brownfield Bridge**:

During Epic 1-2 modernization, both systems run in parallel:

```
CLI Invocation
    ↓
src/data_extract/cli.py (Typer)
    ↓
PipelineStage Protocol (ABC)
    ├─ Extract Stage → ExtractionResult
    ├─ Normalize Stage → ProcessingResult
    ├─ Chunk Stage → ProcessingResult
    ├─ Semantic Stage → ProcessingResult
    └─ Output Stage → FormattedOutput

Legacy System (brownfield):
    ↓
src/cli/main.py (Click)
    ↓
extraction_pipeline.py → batch_processor.py
```

**Story 1.4** consolidates both into single modern pipeline.

### Data Flow

```
Input Documents
    ↓
Extract Stage (format-specific)
    ↓ ExtractionResult
Normalize Stage (cleaning & standardization)
    ↓ ProcessingResult
Chunk Stage (semantic boundaries) [Epic 3]
    ↓ ProcessingResult
Semantic Stage (TF-IDF, LSA) [Epic 4]
    ↓ ProcessingResult
Output Stage (JSON/TXT/CSV) [Epic 3]
    ↓ FormattedOutput
```

---

## Dependency & Configuration Cascade

### pyproject.toml (Line 89-90)

```toml
[project.scripts]
data-extract = "data_extract.cli:app"
```

Maps CLI command → entry point module

### Python Version

- **Mandatory**: Python 3.12+ (enterprise requirement per CLAUDE.md)
- Configured in `pyproject.toml` line 10: `requires-python = ">=3.12"`

### Test Configuration (`pytest.ini`)

```ini
testpaths = ["tests"]
addopts = "-v --cov=src --cov-report=term-missing"
markers = [
    performance, slow, unit, integration, extraction,
    processing, formatting, pipeline, cli
]
```

### Pre-commit Hooks (`.pre-commit-config.yaml`)

**Quality gates** (enforced before commit):
1. Black formatting (100 char lines)
2. Ruff linting
3. mypy type checking (strict mode on greenfield only)

Run before push: `pre-commit run --all-files`

---

## Directory Structure Summary Table

| Directory | Purpose | Type | Status |
|-----------|---------|------|--------|
| `src/data_extract/` | Modern modular pipeline | Greenfield | ✅ Active development |
| `src/cli/` | Legacy CLI wrapper | Brownfield | 📦 Maintained, deprecating |
| `src/core/` | Legacy interfaces | Brownfield | 📦 Maintained |
| `src/extractors/` | Legacy extractors | Brownfield | 📦 Being modernized |
| `src/processors/` | Processing modules | Brownfield | 📦 Maintained |
| `src/formatters/` | Output generators | Brownfield | 📦 Being modernized |
| `src/infrastructure/` | Logging, config, errors | Brownfield | 📦 Maintained |
| `src/pipeline/` | Batch orchestration | Brownfield | 📦 Being consolidated |
| `tests/unit/` | Unit tests | Testing | ✅ Active |
| `tests/integration/` | E2E tests | Testing | ✅ Active |
| `tests/performance/` | Benchmarks | Testing | ✅ Active |
| `tests/fixtures/` | Test data | Testing | ✅ 90+ MB data |
| `docs/` | Documentation | Docs | ✅ 90+ files |
| `docs/uat/` | UAT framework | Testing | ✅ Workflows |
| `docs/.archive/` | Legacy docs | Docs | 📦 165+ archived |
| `scripts/` | Dev utilities | DevOps | ✅ Active |
| `.github/workflows/` | CI/CD pipelines | DevOps | ✅ GitHub Actions |
| `config/` | Config templates | Config | ✅ Schemas |
| `examples/` | Usage examples | Docs | ✅ 13 examples |
| `bmad/` | Epic workflows | Automation | ✅ BMAD system |

---

## Key Development Patterns

### Testing Markers

**Run tests selectively**:

```bash
pytest -m unit                    # Fast unit tests only
pytest -m integration            # Integration tests
pytest -m "not slow"             # Skip slow tests
pytest -m "extraction"           # Extraction-specific
```

### Type Checking

```bash
mypy src/data_extract/           # Type check greenfield (strict)
# Brownfield excluded per pyproject.toml
```

### Code Quality

```bash
black src/ tests/                # Format (100 char lines)
ruff check src/ tests/           # Lint
pre-commit run --all-files       # All hooks
```

### Performance Profiling

```bash
python scripts/profile_pipeline.py
python scripts/run_performance_suite.py
```

### Fixture Generation

```bash
python scripts/generate_large_pdf_fixture.py
python scripts/generate_large_excel_fixture.py
python scripts/generate_scanned_pdf_fixture.py
python scripts/create_performance_batch.py
```

---

## Architecture Decision Records (ADRs)

- **ADR-001**: Immutable frozen dataclasses prevent pipeline state corruption
- **ADR-002**: Pluggable extractors via ABC isolate format-specific logic
- **ADR-003**: ContentBlocks preserve document structure over raw text
- **ADR-004**: Classical NLP only (scikit-learn, no transformers - enterprise constraint)
- **ADR-005**: Gradual brownfield modernization without breaking production

See `docs/architecture.md` for full decision rationale.

---

## CI/CD Pipeline Structure

**GitHub Actions Workflows** (`.github/workflows/`):

1. **test.yml** - Main test suite
   - Unit + integration + performance tests
   - Coverage threshold: 60%
   - Runs on push & PR

2. **performance.yml** - Regression testing
   - Compares against baseline (Story 2.5.1)
   - NFR validation (P1: <10 min/100 PDFs, P2: <2GB memory)

3. **performance-regression.yml** - Continuous monitoring
   - Scheduled runs
   - Deviation alerts

---

## Documentation Navigation

**Start Here**:
1. `README.md` - Project overview
2. `CLAUDE.md` - Development guide
3. `docs/PRD/index.md` - Product vision
4. `docs/epics.md` - Implementation roadmap

**Technical Deep Dives**:
- `docs/architecture.md` - System design
- `docs/tech-spec-epic-*.md` - Story-level specs
- `docs/brownfield-assessment.md` - Legacy code analysis

**Operations**:
- `docs/ci-cd-pipeline.md` - CI/CD details
- `docs/TESTING-README.md` - Test patterns
- `docs/troubleshooting-spacy.md` - spaCy setup

**UAT & Quality**:
- `docs/uat/` - Test case generation, execution, review
- `docs/performance-baselines-*.md` - NFR measurements
- `docs/traceability-*.md` - Epic-to-code traceability

---

## Legend

- **✅** - Active/current implementation
- **📦** - Maintenance mode (brownfield)
- **⚠️** - Planned/deprecated
- **→** - Entry point / key file
- **✨** - Greenfield (new modular code)

---

## Summary

The Data Extraction Tool implements a **dual-codebase modernization strategy**:

- **Greenfield** (`src/data_extract/`): Modern 5-stage modular pipeline with frozen dataclasses, ABC protocols, and full type safety
- **Brownfield** (`src/{cli,core,extractors,...}`): Production code maintained for compatibility during migration
- **Both coexist** during Epic 1-2, consolidating in Story 1.4

The architecture prioritizes:
1. **Modularity** - Composable stages with clear interfaces
2. **Type Safety** - Full type hints + mypy strict mode (greenfield only)
3. **Testability** - Comprehensive test suite mirroring src/ structure
4. **Immutability** - Frozen dataclasses prevent state corruption
5. **Enterprise Constraints** - Classical NLP only, no transformers

See `docs/architecture.md` for full technical details.

---

**Document Generated**: 2025-11-13
**BMAD System Integration**: Epic 1-2 brownfield modernization (Story 1.2-1.4)
**Python Version**: 3.12+ (mandatory)
**Quality Gates**: Pre-commit + CI enforcement
