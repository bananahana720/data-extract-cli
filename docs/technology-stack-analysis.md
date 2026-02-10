# Technology Stack Analysis

**Generated**: 2025-11-13
**Project**: Data Extraction Tool
**Version**: 0.1.0 (Epic 1 - Foundation)
**Analysis Type**: Exhaustive Scan with Housekeeping Focus

---

## Executive Summary

**Language**: Python 3.12+ (Current: 3.13.9)
**Architecture**: Modular five-stage pipeline (`Extract → Normalize → Chunk → Semantic → Output`)
**Development Status**: Brownfield modernization (dual codebase: greenfield + legacy)
**Primary Target**: Windows (cross-platform support)

---

## Core Technology Stack

### Language & Runtime

| Component | Version | Purpose | Status |
|-----------|---------|---------|--------|
| Python | 3.12+ (3.13.9 installed) | Primary language | ✅ Exceeds minimum |
| pip | Latest | Package management | ✅ Active |
| venv | Built-in | Virtual environment | ✅ Active |

**Enterprise Constraint**: Python 3.12+ mandatory (no downgrade allowed)

### Build & Packaging

| Component | Version | Purpose | Configuration |
|-----------|---------|---------|---------------|
| setuptools | >=61.0 | Build backend | `pyproject.toml` |
| wheel | Latest | Binary distribution | `pyproject.toml` |
| Package name | `data-extraction-tool` | PyPI package | `pyproject.toml` |
| Entry point | `data-extract` | CLI command | `data_extract.cli:app` |

### Data Models & Validation

| Component | Version | Purpose | Usage |
|-----------|---------|---------|-------|
| Pydantic | >=2.0.0,<3.0 | Runtime validation + schema generation | Core models (ExtractionResult, ProcessingResult, FormattedOutput) |
| Type hints | Native Python 3.12+ | Static type safety | All public APIs |
| mypy | >=1.11.0,<2.0 | Static type checking | Strict mode on greenfield code |

**Design Principle**: Immutable frozen dataclasses prevent pipeline state mutations

### CLI & UI

| Component | Version | Purpose | Usage |
|-----------|---------|---------|-------|
| Click | >=8.1.0 | CLI framework | Command routing, argument parsing |
| Rich | >=13.0.0 | Terminal UI | Progress bars, tables, syntax highlighting |
| Typer | Future (Epic 5) | Type-safe CLI | Planned replacement for Click |

### Document Processing

#### Core Extractors

| Format | Library | Version | Capabilities |
|--------|---------|---------|--------------|
| PDF | pypdf | >=3.0.0 | Native text extraction |
| PDF | pdfplumber | >=0.10.0 | Table extraction, layout analysis |
| DOCX | python-docx | >=0.8.11 | Text, tables, images, styles |
| XLSX | openpyxl | >=3.0.10 | Multi-sheet, formulas, charts |
| PPTX | python-pptx | >=0.6.21 | Slides, images, speaker notes |
| CSV | Native Python | Built-in | Basic CSV parsing |
| TXT | Native Python | Built-in | Plain text |

#### OCR (Optional)

| Component | Version | Purpose | System Dependencies |
|-----------|---------|---------|---------------------|
| pytesseract | >=0.3.10 | OCR wrapper | Requires Tesseract binary |
| pdf2image | >=1.16.0 | PDF → Image conversion | Requires poppler |
| Pillow | >=10.0.0 | Image processing | Core dependency |
| deskew | >=1.5.0 | Image deskewing | Enhances OCR accuracy |
| scikit-image | >=0.22.0 | Image preprocessing | Advanced OCR workflows |

**Enterprise Note**: OCR optional due to system dependency requirements

### NLP & Text Processing

#### Story 2.5.2 Integration (Completed)

| Component | Version | Purpose | Usage |
|-----------|---------|---------|-------|
| spaCy | >=3.7.2,<4.0 | Sentence boundary detection | Epic 3 chunking (semantic-aware splits) |
| en_core_web_md | 3.8.0 | English language model | 43MB, loads in ~1.2s, 4000+ words/sec |
| beautifulsoup4 | >=4.12.0,<5.0 | HTML/XML parsing | Text extraction, cleaning |
| lxml | >=5.0.0,<6.0 | XML parser | Fast BS4 backend |

**Enterprise Constraint**: Classical NLP only - **NO transformer-based LLMs allowed**

**Performance**: spaCy model cached in CI, transparent to developers

### Infrastructure

#### Configuration Management

| Component | Version | Purpose | Configuration Files |
|-----------|---------|---------|---------------------|
| PyYAML | >=6.0.0,<7.0 | YAML parsing | `config/*.yaml`, `src/infrastructure/*.yaml` |
| python-dotenv | >=1.0.0,<2.0 | Environment variables | `.env` support |
| Pydantic | >=2.0.0,<3.0 | Config validation | Runtime schema enforcement |

**Config Files**:
- `pyproject.toml` - Project configuration
- `src/infrastructure/config_schema.yaml` - Infrastructure schema
- `src/infrastructure/error_codes.yaml` - Error code registry
- `src/infrastructure/log_config.yaml` - Logging configuration
- `config/normalize/*.yaml` - Normalization rules (4 files)
- `bmad/bmm/config.yaml` - BMAD framework config
- `docs/bmm-workflow-status.yaml` - Workflow tracking

#### Logging & Monitoring

| Component | Version | Purpose | Usage |
|-----------|---------|---------|-------|
| structlog | >=24.0.0,<25.0 | Structured logging | JSON logs, correlation IDs, audit trails |
| psutil | >=5.9.0,<6.0 | System monitoring | Performance profiling (Story 2.5.1) |
| memory-profiler | >=0.61.0,<1.0 | Memory profiling | Line-by-line analysis (optional, dev only) |

**Audit Requirement**: Structured JSON logs for enterprise compliance

### Testing Infrastructure

#### Core Testing

| Component | Version | Purpose | Usage |
|-----------|---------|---------|-------|
| pytest | >=8.0.0,<9.0 | Test framework | 1000+ tests (brownfield + greenfield) |
| pytest-cov | >=5.0.0,<6.0 | Coverage reporting | HTML reports, 60% minimum threshold |
| pytest-xdist | >=3.6.0,<4.0 | Parallel execution | `pytest -n auto` |
| pytest-mock | >=3.11.0 | Mocking utilities | Test isolation |

**Test Markers**:
- `unit` - Fast unit tests
- `integration` - Multi-component tests
- `extraction` - Extractor-specific
- `performance` - Benchmarks
- `slow` - Long-running tests

#### Coverage Requirements

| Epic | Threshold | Status |
|------|-----------|--------|
| Epic 1 | >60% | ✅ Enforced in CI |
| Epic 2-4 | >80% | 🎯 Target |
| Epic 5 | >90% (critical paths) | 📋 Planned |

#### Test Fixtures & Utilities

| Component | Version | Purpose | Usage |
|-----------|---------|---------|-------|
| reportlab | >=3.5.0,<5.0 | PDF fixture generation | Creates test PDFs programmatically |
| fixtures | Custom | Test data | `tests/fixtures/` directory |

**Test Organization**: Mirrors `src/` structure exactly

### Code Quality & Linting

#### Enforced via Pre-commit

| Tool | Version | Purpose | Configuration |
|------|---------|---------|---------------|
| black | >=24.0.0,<25.0 | Code formatting | 100 char lines, Python 3.12 target |
| ruff | >=0.6.0,<0.7 | Fast linting | Replaces flake8 + isort |
| mypy | >=1.11.0,<2.0 | Static type checking | Strict mode (excludes brownfield) |
| pre-commit | >=3.0.0,<4.0 | Git hooks | Runs on commit + in CI |

**Pre-commit Enforcement**: Runs locally AND in CI for consistency

**Type Checking Exclusions** (during brownfield migration):
```python
exclude = [
    "src/(cli|extractors|processors|formatters|core|pipeline|infrastructure)/",
]
```

### Type Stubs

| Package | Version | Purpose |
|---------|---------|---------|
| types-PyYAML | >=6.0.0 | YAML type hints for mypy |

---

## Configuration Architecture

### Four-Tier Cascade (Epic 5)

1. **CLI flags** (highest precedence)
2. **Environment variables** (`DATA_EXTRACT_*` prefix)
3. **YAML config file** (`~/.data-extract/config.yaml` or project-local)
4. **Hardcoded defaults** (lowest precedence)

**Epic 1 Status**: Infrastructure set up, full cascade in Epic 5

### Configuration Files by Purpose

| File | Purpose | Epic | Status |
|------|---------|------|--------|
| `pyproject.toml` | Build, deps, tools | Epic 1 | ✅ Complete |
| `src/infrastructure/config_schema.yaml` | Infrastructure schema | Epic 1 | ✅ Complete |
| `src/infrastructure/error_codes.yaml` | Error registry (50+ codes) | Epic 1 | ✅ Complete |
| `src/infrastructure/log_config.yaml` | Logging framework | Epic 1 | ✅ Complete |
| `config/normalize/cleaning_rules.yaml` | Text cleaning | Epic 2 | ✅ Complete |
| `config/normalize/entity_patterns.yaml` | Entity extraction | Epic 2 | ✅ Complete |
| `config/normalize/entity_dictionary.yaml` | Entity normalization | Epic 2 | ✅ Complete |
| `config/normalize/schema_templates.yaml` | Schema standardization | Epic 2 | ✅ Complete |

---

## Dual Codebase Structure

### Greenfield (Modern)

**Location**: `src/data_extract/`
**Status**: Active development (Epic-based)
**Coverage**: >80% target
**Type Checking**: Strict mypy enforcement

**Modules**:
- `extract/` - Document extractors (PDF, DOCX, XLSX, PPTX, CSV, TXT)
- `normalize/` - Text cleaning, entity standardization
- `chunk/` - Semantic chunking (spaCy-based)
- `semantic/` - Classical NLP (TF-IDF, LSA)
- `output/` - Multiple formatters (JSON, TXT, CSV)

### Brownfield (Legacy)

**Location**: `src/{cli,core,extractors,processors,formatters,pipeline,infrastructure}/`
**Status**: Being assessed (Story 1.2-1.4)
**Coverage**: >60% baseline (1000+ tests)
**Type Checking**: Excluded during migration

**Assessment**: Gradual consolidation, no breaking changes during migration

---

## Development Workflow

### Local Development Commands

```bash
# Setup
python -m venv venv
venv\Scripts\activate  # Windows
pip install -e ".[dev]"
pre-commit install

# spaCy model (one-time)
python -m spacy download en_core_web_md

# Testing
pytest                          # All tests
pytest -m unit                  # Unit tests only
pytest --cov=src --cov-report=html  # With coverage

# Code quality (runs automatically on commit)
black src/ tests/
ruff check src/ tests/
mypy src/data_extract/

# Manual pre-commit validation
pre-commit run --all-files
```

### CI/CD Pipeline

**Location**: `.github/workflows/`

**Stages**:
1. **Pre-commit checks** (black, ruff, mypy)
2. **Test execution** (pytest with coverage)
3. **Coverage enforcement** (60% minimum)
4. **Performance regression tests** (baselines from Story 2.5.1)

**spaCy Caching**: Models automatically cached in CI (no manual action)

---

## Dependency Management

### Core Dependencies (18)

Required for all environments:
- pydantic, PyYAML, python-dotenv, structlog (infrastructure)
- beautifulsoup4, lxml, spacy (text processing)
- python-docx, pypdf, python-pptx, openpyxl, click, rich, pdfplumber, Pillow (document processing)

### Optional Dependencies

#### OCR (5 packages)

```bash
pip install -e ".[ocr]"
```

Includes: pytesseract, pdf2image, deskew, scikit-image

**System Requirements**: Tesseract binary, poppler

#### Development (10+ packages)

```bash
pip install -e ".[dev]"
```

Includes: pytest ecosystem, black, ruff, mypy, pre-commit, psutil, memory-profiler, reportlab, type stubs

#### All Dependencies

```bash
pip install -e ".[all]"  # ocr + dev
```

---

## Housekeeping Observations

### ✅ Strengths

1. **Well-structured `pyproject.toml`** - Clear dependency organization
2. **Proper optional dependencies** - OCR separated from core
3. **Modern tooling** - Black, Ruff, mypy, pre-commit
4. **Configuration separation** - Infrastructure vs. normalization vs. BMAD
5. **Epic-based development** - Clear progression path
6. **Type safety focus** - Strict mypy on greenfield code

### ⚠️ Housekeeping Opportunities

1. **Configuration consolidation**:
   - 4 separate normalization YAML files in `config/normalize/`
   - Could be consolidated into single config with sections
   - Consider: `config/normalization.yaml` with subsections

2. **Dependency version pinning**:
   - Most deps use range constraints (`>=X,<Y`)
   - Good for flexibility, but consider exact pins in production

3. **Type stubs coverage**:
   - Only `types-PyYAML` included
   - Missing: `types-python-docx`, `types-openpyxl`, etc.
   - Not critical (libraries have inline types) but improves mypy accuracy

4. **Test organization**:
   - `tests/outputs/` contains actual test output files
   - Should be in `.gitignore` or `tests/temp/`
   - Cleanup opportunity

5. **Virtual environment**:
   - `venv/` directory present in repo
   - Should verify `.gitignore` excludes it

### 📋 Recommendations

1. **Immediate**:
   - Add `tests/outputs/` to `.gitignore`
   - Verify `venv/` is gitignored
   - Document spaCy model setup prominently (already in CLAUDE.md ✅)

2. **Future (Epic 5)**:
   - Consolidate `config/normalize/*.yaml` into single file
   - Consider `pyproject.toml` migration for runtime config (PEP 517/518)
   - Add optional type stubs for better IDE experience

3. **Documentation**:
   - Create architecture decision record (ADR) for Python 3.12+ requirement
   - Document why no transformer models (enterprise constraint)

---

## Technology Decisions (ADRs)

### ADR-001: Python 3.12+ Mandatory

**Decision**: Require Python 3.12 or higher
**Rationale**: Enterprise requirement, modern features, better performance
**Status**: ✅ Enforced in `pyproject.toml`

### ADR-002: Classical NLP Only

**Decision**: No transformer-based LLMs (BERT, GPT, etc.)
**Rationale**: Enterprise security restrictions
**Technologies**: spaCy, scikit-learn, gensim
**Status**: ✅ Enforced by architecture review

### ADR-003: Immutable Data Models

**Decision**: Use frozen dataclasses + Pydantic v2
**Rationale**: Prevent pipeline state corruption
**Status**: ✅ Core architecture principle

### ADR-004: Dual Codebase During Migration

**Decision**: Maintain greenfield and brownfield simultaneously
**Rationale**: Gradual modernization without breaking production
**Status**: 🔄 In progress (Epic 1-2)

### ADR-005: Pre-commit Enforcement in CI

**Decision**: Run pre-commit hooks both locally and in CI
**Rationale**: Ensure consistency between environments
**Status**: ✅ Implemented in `.github/workflows/`

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-11-13 | Initial comprehensive technology stack analysis |
|  |  | Exhaustive scan with housekeeping focus |
|  |  | Documented all dependencies, configs, and architecture |

---

**Analysis Status**: ✅ Complete
**Next Step**: Exhaustive file-by-file scan (Step 4)
