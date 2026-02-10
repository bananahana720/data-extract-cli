# BMad Method Documentation Index

**Generated**: 2025-12-01
**Project**: Data Extraction Tool - Enterprise Document Processing Pipeline
**Status**: V1.0 RELEASED (All 5 Epics COMPLETE)
**Scan Level**: Exhaustive (full source reading)

---

## Quick Navigation

**New to This Project?** Start here:
1. [Project Overview](./bmm-project-overview.md) - What this project does
2. [Architecture](./architecture/) - Technical architecture (sharded, 19 files)
3. [Source Tree Analysis](./bmm-source-tree-analysis.md) - Codebase structure reference

**Ready to Develop?**
4. [QUICKSTART.md](./QUICKSTART.md) - Five-minute setup
5. [Development Guide](./development-operations-guide.md) - Dev/ops setup
6. [Testing Guide](./TESTING-README.md) - Test execution

**For AI-Assisted Development:**
7. [Data Models Reference](./bmm-data-models.md) - All 22 data models
8. [Test Infrastructure](./bmm-test-infrastructure.md) - 229 test files documented

---

## Project Summary

**Data Extraction Tool** transforms messy corporate audit documents into AI-optimized outputs using a five-stage modular pipeline:

```
Extract → Normalize → Chunk → Semantic → Output
```

### Current Status

| Metric | Value |
|--------|-------|
| **Version** | V1.0 RELEASED (2025-12-01) |
| **Python** | 3.11+ (minimum), 3.12+ recommended |
| **Source Files** | 107 Python files |
| **Lines of Code** | 33,707 |
| **Data Models** | 22 classes |
| **Test Files** | 229 |
| **Test Fixtures** | 112 |
| **CI/CD Workflows** | 4 |
| **Total Tests** | 3,575 tests passing |

### Architecture

**Dual Codebase Structure:**
- **Greenfield** (`src/data_extract/`) - Modern 5-stage pipeline (60 files, ~18,000 LOC)
- **Brownfield** (`src/cli/, extractors/, etc.`) - Legacy code (47 files, ~15,000 LOC)

**Key Patterns:**
- Immutability (ADR-001): Frozen Pydantic v2 models
- Interface-Based Design (ADR-002): BaseExtractor, BaseFormatter ABCs
- Classical NLP Only (ADR-004): No transformers (enterprise constraint)
- Gradual Migration (ADR-005): Both codebases coexist

---

## BMM-Generated Documentation

### Core Analysis Documents

| Document | Purpose | Lines |
|----------|---------|-------|
| [bmm-project-overview.md](./bmm-project-overview.md) | Project summary with strategic context | ~300 |
| [bmm-source-tree-analysis.md](./bmm-source-tree-analysis.md) | Complete source code organization | ~500 |
| [bmm-data-models.md](./bmm-data-models.md) | All 22 data models documented | ~400 |
| [bmm-test-infrastructure.md](./bmm-test-infrastructure.md) | 229 test files, CI/CD workflows | ~500 |
| [bmm-index.md](./bmm-index.md) | This navigation index | ~250 |

### Legacy BMM Documents (Historical Reference)

| Document | Status | Notes |
|----------|--------|-------|
| [bmm-pipeline-integration-guide](./bmm-pipeline-integration-guide/) | Sharded | Pre-Epic 4 pipeline analysis |
| [bmm-processor-chain-analysis](./bmm-processor-chain-analysis/) | Sharded | Brownfield processor patterns |

---

## Technology Stack

### Core Dependencies

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **CLI** | Typer | >=0.9.0 | Type-safe CLI framework |
| **Data Models** | Pydantic v2 | >=2.0.0 | Runtime validation |
| **PDF** | pdfplumber, PyMuPDF | Latest | PDF extraction |
| **Office** | python-docx, openpyxl | Latest | Office document handling |
| **Chunking** | spaCy | >=3.7.2 | Sentence boundary detection |
| **Semantic** | scikit-learn | >=1.3.0 | TF-IDF, LSA, similarity |
| **Quality** | textstat | >=0.7.3 | Readability metrics |
| **Output** | Rich | >=13.0.0 | Rich console UI |

### Development Tools

| Tool | Purpose |
|------|---------|
| **black** | Code formatting (100 char lines) |
| **ruff** | Linting (replaces flake8 + isort) |
| **mypy** | Type checking (strict on greenfield) |
| **pytest** | Testing framework |
| **pre-commit** | Git hooks enforcement |
| **uv** | Fast package manager |

---

## Pipeline Stages

### Stage 1: Extract (`src/data_extract/extract/`)
- Format-specific document ingestion
- Supports: PDF, DOCX, XLSX, PPTX, CSV, TXT
- Interface: `BaseExtractor` ABC

### Stage 2: Normalize (`src/data_extract/normalize/`)
- Text cleaning and entity standardization
- Schema-driven validation
- Quality metrics computation

### Stage 3: Chunk (`src/data_extract/chunk/`)
- Semantic-aware chunking via spaCy
- Entity boundary preservation
- Metadata enrichment

### Stage 4: Semantic (`src/data_extract/semantic/`)
- TF-IDF vectorization with caching
- LSA topic extraction
- Similarity analysis and deduplication
- Readability metrics (Flesch, SMOG, etc.)

### Stage 5: Output (`src/data_extract/output/`)
- Multiple formats: JSON, CSV, TXT
- Schema validation
- Organization strategies

---

## Entry Points

### Primary CLI
```bash
data-extract                    # Main CLI (Typer)
data-extract --help
data-extract version
data-extract analyze            # Semantic analysis
data-extract deduplicate        # Deduplication
data-extract cluster            # Document clustering
```

### Development Commands
```bash
# Setup
uv venv && uv pip install -e ".[dev]"
python -m spacy download en_core_web_md

# Quality Gates
black src/ tests/
ruff check src/ tests/ --fix
mypy src/data_extract/
pytest

# Automation
python scripts/run_quality_gates.py
python scripts/init_claude_session.py
```

---

## Existing Documentation

### Core Docs (docs/)
- **[index.md](./index.md)** - Master documentation index (350 lines, updated today)
- **[architecture/](./architecture/)** - Technical architecture (19 files)
- **[PRD/](./PRD/)** - Product requirements (12 sections)
- **[sprint-status.yaml](./sprint-status.yaml)** - Authoritative status tracking

### Guides
- **[QUICKSTART.md](./QUICKSTART.md)** - Five-minute setup
- **[CONFIG_GUIDE.md](./CONFIG_GUIDE.md)** - Configuration management
- **[TESTING-README.md](./TESTING-README.md)** - Test execution guide
- **[automation-guide.md](./automation-guide.md)** - P0 scripts

### Epic Documentation
- **[tech-spec-epic-4.md](./tech-spec-epic-4.md)** - Classical NLP (COMPLETE)
- **[tech-spec-epic-5.md](./tech-spec-epic-5.md)** - Enhanced CLI (IN PROGRESS)
- **[ux-design-specification.md](./ux-design-specification.md)** - 7 user journeys

### Playbooks
- **[playbooks/semantic-analysis-intro.ipynb](./playbooks/semantic-analysis-intro.ipynb)** - TF-IDF/LSA tutorial
- **[playbooks/semantic-analysis-reference.md](./playbooks/semantic-analysis-reference.md)** - API reference

---

## Quick Reference by Task

| I want to... | Start here |
|--------------|------------|
| **Set up the project** | [QUICKSTART.md](./QUICKSTART.md) |
| **Understand the architecture** | [architecture/](./architecture/) |
| **Run tests** | [TESTING-README.md](./TESTING-README.md) |
| **Configure the tool** | [CONFIG_GUIDE.md](./CONFIG_GUIDE.md) |
| **Use automation scripts** | [automation-guide.md](./automation-guide.md) |
| **Learn TF-IDF/LSA** | [playbooks/semantic-analysis-intro.ipynb](./playbooks/semantic-analysis-intro.ipynb) |
| **Check project status** | [sprint-status.yaml](./sprint-status.yaml) |
| **Understand data models** | [bmm-data-models.md](./bmm-data-models.md) |
| **Navigate source code** | [bmm-source-tree-analysis.md](./bmm-source-tree-analysis.md) |
| **Understand test setup** | [bmm-test-infrastructure.md](./bmm-test-infrastructure.md) |

---

## BMad Workflow Commands

```bash
# Check status
/bmad:bmm:workflows:workflow-status

# Development workflows
/bmad:bmm:workflows:dev-story         # Execute a story
/bmad:bmm:workflows:code-review       # Code review with AC validation

# Planning workflows
/bmad:bmm:workflows:prd               # Product requirements
/bmad:bmm:workflows:architecture      # Architecture design
/bmad:bmm:workflows:sprint-planning   # Sprint tracking
```

---

## Document Metadata

| Attribute | Value |
|-----------|-------|
| **Generated** | 2025-12-01 |
| **Workflow** | document-project (full_rescan) |
| **Scan Level** | Exhaustive |
| **Project Type** | Data Pipeline CLI Tool |
| **Status** | V1.0 RELEASED (All 5 Epics Complete) |
| **Python Files** | 107 |
| **Test Files** | 229 |
| **Data Models** | 22 |
| **Total Tests** | 3,575 passing |

---

**Last Updated**: 2025-12-01 | **Workflow**: document-project v1.2.0
