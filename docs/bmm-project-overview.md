# Project Overview - Data Extraction Tool

**Generated**: 2025-11-30
**Project Type**: CLI Tool / Data Processing Pipeline
**Status**: V1.0 RELEASED (All 5 Epics COMPLETE)
**Primary Language**: Python 3.11+ (minimum), 3.12+ recommended

---

## Executive Summary

This project is an **enterprise-grade document extraction and processing pipeline** designed for RAG (Retrieval-Augmented Generation) optimization and AI-ready knowledge curation. The tool extracts structured content from enterprise documents (DOCX, PDF, PPTX, XLSX, CSV, TXT) through a composable five-stage pipeline.

**Current Capabilities**:
- **5-Stage Pipeline**: Extract → Normalize → Chunk → Semantic → Output
- **Multi-format extraction**: 6 format extractors (PDF, DOCX, XLSX, PPTX, CSV, TXT)
- **Semantic analysis**: TF-IDF vectorization, LSA topic extraction, similarity analysis (Epic 4)
- **Quality metrics**: Readability scoring (Flesch, SMOG), coherence analysis
- **Multiple outputs**: JSON, CSV, TXT formats with schema validation
- **CLI**: Typer-based CLI with Rich console UI (Epic 5 enhancement)

**Completed Enhancements**:
- **Epic 4**: Classical NLP knowledge curation (TF-IDF, LSA, similarity, deduplication)
- **Intelligent caching**: 10x speedup on cache hit for TF-IDF vectorization
- **Quality integration**: 0.12ms per chunk quality scoring

---

## Project Classification

### Repository Structure
- **Type**: Monolith (single cohesive codebase)
- **Architecture Pattern**: 5-Stage Modular Pipeline
- **Dual Codebase**: Greenfield (`src/data_extract/`) + Brownfield (legacy)

### Technology Stack

| Category | Technologies | Purpose |
|----------|-------------|---------|
| **Runtime** | Python 3.11/3.12/3.13 | Core execution |
| **CLI** | Typer 0.9+, Rich 13.0+ | Type-safe CLI and terminal UI |
| **Data Models** | Pydantic v2 | Runtime validation |
| **Document Processing** | python-docx, pdfplumber, python-pptx, openpyxl | Format extraction |
| **Chunking** | spaCy 3.7.2+ | Sentence boundary detection |
| **Semantic Analysis** | scikit-learn 1.3+, joblib | TF-IDF, LSA, similarity |
| **Quality Metrics** | textstat 0.7.3+ | Readability scoring |
| **Testing** | pytest 8.0+ | Test framework |
| **Quality** | black, ruff, mypy | Code quality |

### Project Metrics

| Metric | Value | Status |
|--------|-------|--------|
| **Epic Status** | Epic 4 Complete, Epic 5 In Progress | ✅ On Track |
| **Source Files** | 107 Python files | - |
| **Lines of Code** | 33,707 | - |
| **Data Models** | 22 classes | ✅ Documented |
| **Test Files** | 229 | - |
| **Test Fixtures** | 112 | - |
| **CI/CD Workflows** | 4 | - |
| **Documentation** | 200+ files | ✅ Comprehensive |

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    CLI Layer (Typer + Rich)                 │
│  Commands: extract, analyze, deduplicate, cluster, cache    │
│  Epic 5: Enhanced UX, presets, batch processing             │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│              Stage 1: EXTRACT (src/data_extract/extract/)   │
│  Format-specific document ingestion:                        │
│  - PDFExtractor (with OCR fallback)                         │
│  - DocxExtractor (Word documents)                           │
│  - ExcelExtractor (multi-sheet workbooks)                   │
│  - PptxExtractor (PowerPoint)                               │
│  - CsvExtractor (CSV/TSV)                                   │
│  - TxtExtractor (plain text)                                │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│              Stage 2: NORMALIZE (src/data_extract/normalize/)│
│  Text cleaning & standardization:                           │
│  - Entity standardization & canonicalization                │
│  - Schema-driven validation                                 │
│  - Metadata extraction & enrichment                         │
│  - Quality metrics computation                              │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│              Stage 3: CHUNK (src/data_extract/chunk/)       │
│  Semantic-aware chunking:                                   │
│  - Sentence boundary detection (spaCy)                      │
│  - Entity boundary preservation                             │
│  - Metadata enrichment per chunk                            │
│  - Quality scoring                                          │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│              Stage 4: SEMANTIC (src/data_extract/semantic/) │
│  Classical NLP analysis (Epic 4):                           │
│  - TF-IDF vectorization with intelligent caching            │
│  - LSA topic extraction                                     │
│  - Cosine similarity & deduplication                        │
│  - Readability metrics (Flesch, SMOG, ARI)                  │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│              Stage 5: OUTPUT (src/data_extract/output/)     │
│  Format-specific output generation:                         │
│  - JSON with schema validation                              │
│  - CSV tabular output                                       │
│  - Plain text for LLM upload                                │
│  - Organization strategies (BY_DOCUMENT, BY_ENTITY, FLAT)   │
└─────────────────────────────────────────────────────────────┘

         ═════════════════════════════════════════════
              Cross-Cutting Infrastructure
         ═════════════════════════════════════════════
         - ConfigManager: YAML/ENV config with precedence
         - LoggingFramework: Structured JSON logging
         - ErrorHandler: Error codes with recovery
         - CacheManager: Intelligent result caching
```

---

## Key Design Patterns

### 1. **Immutability Pattern** (ADR-001)
- Frozen Pydantic v2 models (`model_config = ConfigDict(frozen=True)`)
- Frozen dataclasses for chunk metadata
- Prevents pipeline state corruption

### 2. **Interface-Based Design** (ADR-002)
- `BaseExtractor` ABC for all format extractors
- `BaseFormatter` ABC for all output formatters
- Pluggable components without modifying core pipeline

### 3. **Classical NLP Only** (ADR-004)
- Enterprise constraint: No transformer models
- Uses scikit-learn for TF-IDF, LSA, cosine similarity
- spaCy for sentence boundary detection only

### 4. **Gradual Brownfield Migration** (ADR-005)
- Both codebases coexist during migration
- Greenfield (`src/data_extract/`) for new features
- Brownfield for legacy compatibility

---

## Epic Status

### Completed Epics

| Epic | Description | Stories | Status |
|------|-------------|---------|--------|
| **Epic 1** | Foundation | 4 | ✅ Complete |
| **Epic 2** | Extract & Normalize | 6 | ✅ Complete |
| **Epic 2.5** | Infrastructure | 6 | ✅ Complete |
| **Epic 3** | Chunk & Output | 7 | ✅ Complete |
| **Epic 3.5** | Tooling & Automation | 11 | ✅ Complete |
| **Epic 4** | Knowledge Curation via Classical NLP | 6 | ✅ Complete |

### Current Epic

**Epic 5: Enhanced CLI UX & Batch Processing**
- Story 5-0: UAT Testing Framework (tmux-cli) - Foundation
- Stories 5-1 through 5-7: CLI enhancements
- Status: IN PROGRESS

### Epic 4 Achievements (2025-11-25)

- TF-IDF vectorization with intelligent caching (10x speedup on cache hit)
- Similarity analysis with 100% precision (47x faster than requirements)
- LSA topic extraction and document clustering
- Quality metrics integration (0.12ms per chunk, 88% under requirement)
- Full CLI integration: `semantic analyze`, `deduplicate`, `cluster`, `cache`
- Multi-agent orchestration validated (9 agents caught issues in Story 4-1)

---

## Entry Points

### Primary CLI
```bash
data-extract                    # Main CLI (Typer)
data-extract --help
data-extract version

# Semantic Analysis Commands (Epic 4)
data-extract analyze            # TF-IDF analysis
data-extract deduplicate        # Find duplicates
data-extract cluster            # Document clustering
data-extract cache              # Cache management
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

# Automation Scripts
python scripts/run_quality_gates.py     # P0: Quality gates
python scripts/init_claude_session.py   # P0: Session init
python scripts/smoke_test_semantic.py   # P1: Semantic validation
```

---

## Quality Gates

**Pre-commit workflow (0 violations required)**:
1. `black src/ tests/` → Format code
2. `ruff check src/ tests/` → Lint code
3. `mypy src/data_extract/` → Type check (strict mode)
4. `pytest` → Run tests

**CI/CD Enforcement**:
- 4 GitHub workflows (test, security, performance, UAT)
- Coverage threshold: 60% overall, 80% greenfield
- Pre-commit hooks enforced on all commits

---

## Documentation Map

### Core Documentation
- [bmm-index.md](./bmm-index.md) - Master navigation
- [bmm-source-tree-analysis.md](./bmm-source-tree-analysis.md) - Source code organization
- [bmm-data-models.md](./bmm-data-models.md) - All 22 data models
- [TESTING-README.md](./TESTING-README.md) - Test infrastructure and execution

### Architecture
- [architecture/](./architecture/) - Technical architecture (19 files)
- [PRD/](./PRD/) - Product requirements (12 sections)

### Guides
- [QUICKSTART.md](./QUICKSTART.md) - Five-minute setup
- [CONFIG_GUIDE.md](./CONFIG_GUIDE.md) - Configuration
- [TESTING-README.md](./TESTING-README.md) - Test execution
- [automation-guide.md](./automation-guide.md) - P0 scripts

### Epic Documentation
- [tech-spec-epic-4.md](./tech-spec-epic-4.md) - Classical NLP (COMPLETE)
- [tech-spec-epic-5.md](./tech-spec-epic-5.md) - Enhanced CLI (COMPLETE)
- [USER_GUIDE.md](./USER_GUIDE.md) - CLI workflows and usage

### Playbooks
- [playbooks/semantic-analysis-intro.ipynb](./playbooks/semantic-analysis-intro.ipynb) - TF-IDF/LSA tutorial
- [playbooks/semantic-analysis-reference.md](./playbooks/semantic-analysis-reference.md) - API reference

---

## Next Steps

### Immediate (Epic 5 Implementation)
1. Complete UAT Testing Framework (Story 5-0)
2. Refactored command structure (Story 5-1)
3. Configuration management with presets (Story 5-2)
4. Real-time progress indicators (Story 5-3)
5. Error recovery with session resume (Story 5-6)
6. Incremental batch processing (Story 5-7)

### Strategic Planning
- See [sprint-status.yaml](./sprint-status.yaml) for authoritative status
- See [USER_GUIDE.md](./USER_GUIDE.md) for user workflows

---

**Document Status**: ✅ Complete | **Generated**: 2025-11-30 | **Workflow**: document-project v1.2.0
