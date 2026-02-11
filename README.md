# Data Extraction Tool

**Version**: 1.0.0
**Status**: Production Ready
**Python**: 3.11+ (Required)

Enterprise document processing pipeline optimized for RAG workflows. Transforms messy corporate audit documents into AI-ready outputs using a five-stage modular architecture.

## What Makes This Special

**RAG-Optimized Output**: Purpose-built chunking strategies preserve semantic boundaries and context for LLM consumption.

**Enterprise Accuracy**: 66 UAT tests across 7 user journeys validate real-world document processing workflows.

**Classical NLP Power**: TF-IDF, LSA, and semantic similarity without transformer models - 10-80x faster than requirements.

**Flexible Configuration**: 6-layer config cascade from CLI flags to YAML presets enables both quick workflows and complex batch processing.

## Quick Start

### Install with uv (Recommended)

```bash
# Install uv package manager
curl -LsSf https://astral.sh/uv/install.sh | sh  # macOS/Linux
# OR: powershell -c "irm https://astral.sh/uv/install.ps1 | iex"  # Windows

# Setup project
git clone [repository-url]
cd data-extraction-tool
uv venv
uv pip install -e ".[dev]"
pre-commit install

# Download spaCy model (required for chunking)
python -m spacy download en_core_web_md
```

### First Commands

```bash
# Process a single document
data-extract process input.pdf

# Process with deterministic idempotency key
data-extract process input.pdf --idempotency-key daily-audit-run

# Process directory with semantic analysis
data-extract process docs/ --semantic --semantic-report --semantic-export-graph --format json

# Batch processing with preset configuration
data-extract process inputs/ --preset quality

# Check processing status
data-extract status
```

## Architecture

Five-stage modular pipeline with frozen dataclasses and ABC interfaces:

```
Extract → Normalize → Chunk → Semantic → Output
```

**Extract** - Format-specific extraction (PDF, DOCX, XLSX, PPTX, CSV, images+OCR)
**Normalize** - Text cleaning, entity standardization
**Chunk** - Semantic-aware chunking with spaCy sentence boundaries
**Semantic** - Classical NLP analysis (TF-IDF, LSA, similarity scoring)
**Output** - Multiple formats (JSON, TXT, CSV with full metadata)

## Key Features

### 9 CLI Commands

- `process` - Core document processing with progress indicators
- `extract` - Extraction-only mode for raw content
- `retry` - Reprocess failed documents from session
- `validate` - Dry-run validation before processing
- `status` - Real-time session statistics and tracking
- `semantic` - Standalone semantic analysis on existing extractions
- `cache` - Cache management (clear, stats)
- `config` - Config inspection and preset management
- `session` - Session recovery and cleanup

### Output Formats

**JSON** - Full metadata with chunk boundaries, entities, quality scores
**TXT** - Plain text optimized for LLM context windows
**CSV** - Tabular format for analysis and tracking

### Configuration Management

6-layer cascade system:

1. CLI flags (highest precedence)
2. Environment variables (DATA_EXTRACT_*)
3. Project config file (`.data-extract.yaml`)
4. User config file (`~/.data-extract/config.yaml`)
5. Preset config (`~/.data-extract/presets/*.yaml` and built-ins)
6. System defaults (lowest precedence)

**Built-in Presets**: `quality`, `speed`, `balanced`

## Documentation

- **Quick Start**: This README
- **User Guide**: `docs/user-guide.md` - Complete CLI reference with examples
- **Architecture**: `docs/architecture.md` - Technical design and ADRs
- **Development**: `docs/development-operations-guide-*.md` - Contributing guide
- **Automation**: `docs/automation-guide.md` - P0-P2 automation scripts
- **UX Design**: `docs/ux-design-specification.md` - 7 user journeys with UAT tests

## Development

### Testing

```bash
# Run all tests (3,575 total)
pytest

# With coverage
pytest --cov=src --cov-report=html

# Specific categories
pytest -m unit          # Fast unit tests only
pytest -m integration   # Integration tests
pytest -n auto          # Parallel execution

# UAT validation
pytest tests/uat/       # 66 UAT tests across 7 user journeys
```

### Code Quality

```bash
# Format code
black src/ tests/

# Lint code
ruff check src/ tests/

# Type check (strict mode on greenfield)
mypy src/data_extract/

# Run all quality gates
scripts/run_quality_gates.py

# Run scoped refactor milestone gates (4 required checks)
scripts/run_refactor_gates.py
```

### Pre-commit Hooks

Automatically enforced on every commit:

- **black** - Code formatting (100 char lines)
- **ruff** - Linting and import sorting
- **mypy** - Type checking (strict mode)

**CRITICAL**: Never bypass hooks with `--no-verify`

### Coverage Requirements

- **Baseline**: >60% overall (includes archived brownfield)
- **Greenfield** (`src/data_extract/`): >80% coverage
- **Critical Paths**: >90% coverage (CLI, pipeline orchestration)

## Technology Stack

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| CLI | Typer + Rich | Type-safe, modern terminal UX |
| Data Models | Pydantic v2 | Runtime validation |
| PDF | PyMuPDF | Fast extraction, OCR fallback |
| Office Docs | python-docx, openpyxl, python-pptx | Standard libraries |
| Chunking | spaCy (en_core_web_md) | Sentence boundaries |
| Semantic | scikit-learn | TF-IDF, LSA, cosine similarity |
| Readability | textstat | Flesch, SMOG metrics |
| Testing | pytest | Industry standard |
| Quality | black, ruff, mypy | Modern toolchain |
| Package Manager | uv | Fast dependency resolution |

**Enterprise Constraint**: Classical NLP only - no transformer models

## Project Status

### V1.0 Release Metrics (2025-12-01)

**Completion**: 100% (All 5 epics delivered)

**Codebase**:
- Greenfield: 74 Python files, ~19,700 LOC (primary & active)
- Brownfield: Archived in TRASH-FILES.md (migration complete)

**Testing**:
- Total Tests: 3,575 (Core: 971, CLI: 674, UAT: 66, Scripts: 170)
- UAT Validation: 66 tests across 7 user journeys (100% pass rate)
- Coverage: >60% overall, >80% greenfield

**Quality**:
- Black/Ruff: Clean (0 violations)
- Mypy: 0 violations on greenfield (strict mode)
- Pre-commit: All hooks passing

**Performance** (vs Requirements):
- TF-IDF fit/transform: 10ms (10x faster than 100ms requirement)
- Semantic similarity: 4.8ms (42x faster than 200ms requirement)
- Quality metrics: 0.12ms (83x faster than 10ms requirement)

**CLI Commands**: 9 operational with Rich terminal UI

**Deployment Readiness**: 8/10 (Production ready with minor optional fixes)

### Epic Breakdown

**Epic 1**: Foundation (4 stories) - Infrastructure, testing framework, pipeline architecture
**Epic 2**: Extract & Normalize (6 stories) - Multi-format extraction, text cleaning
**Epic 2.5**: Infrastructure (6 stories) - Performance optimization, CI/CD
**Epic 3**: Chunk & Output (7 stories) - Semantic chunking, multi-format output
**Epic 3.5**: Tooling & Automation (11 stories) - P0-P2 automation scripts
**Epic 4**: Knowledge Curation (6 stories) - Classical NLP semantic analysis
**Epic 5**: Enhanced CLI UX (8 stories) - Rich UI, batch processing, config management

See `docs/sprint-status.yaml` for detailed tracking.

## Contributing

Internal enterprise F100 cybersecurity tool. Development follows BMad Method with story-based implementation.

### Code Standards

**[REQUIRED]** Type hints on all public functions
**[REQUIRED]** Google-style docstrings for public APIs
**[REQUIRED]** Tests for all new functionality
**[REQUIRED]** Black formatting (100 char lines)
**[REQUIRED]** Ruff linting compliance
**[REQUIRED]** Mypy strict mode compliance
**[CRITICAL]** Pre-commit hooks must pass (never use `--no-verify`)

### Naming Conventions

- Classes: `PascalCase`
- Functions/methods: `snake_case`
- Constants: `UPPER_SNAKE_CASE`
- Modules: `snake_case`

### Branch Strategy

- `main` - Production-ready code
- `story/X-Y-name` - Story implementation branches
- Epic-level integration on completion

## License

Proprietary - Internal enterprise use only

## Support

For questions or issues:

1. Check documentation in `docs/`
2. Review user guide: `docs/user-guide.md`
3. Consult architecture: `docs/architecture.md`
4. Review retrospectives: `docs/retrospectives/`

---

**Production Release**: All functional requirements implemented, UAT validated, deployment ready.
