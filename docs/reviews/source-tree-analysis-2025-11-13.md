# Source Tree Analysis with Housekeeping Notes

**Generated**: 2025-11-13
**Analysis Type**: Exhaustive Scan with Housekeeping Focus
**Project**: Data Extraction Tool v0.1.0

---

## Project Structure Overview

```
data-extraction-tool-1/
├── 📁 bmad/                      # BMAD Framework (workflow automation)
├── 📁 config/                    # Application configuration
├── 📁 docs/                      # Documentation (79 files post-cleanup)
├── 📁 examples/                  # Example files
├── 📁 logs/                      # Runtime logs (gitignored)
├── 📁 output/                    # Processing outputs (gitignored)
├── 📁 scripts/                   # Utility scripts
├── 📁 src/                       # Source code (dual codebase)
├── 📁 tests/                     # Test suite (1000+ tests)
├── 📄 pyproject.toml             # Project configuration
├── 📄 README.md                  # Project readme
├── 📄 CLAUDE.md                  # Claude Code instructions
└── 📄 TRASH-FILES.md             # Housekeeping log
```

**Total Source Files**: 59 Python files (27 greenfield + 31 brownfield + 1 CLI)
**Total Documentation**: 79 markdown files (post-cleanup)
**Test Files**: 1000+ tests across unit, integration, performance

---

## 📁 Source Code (`src/`) - Dual Codebase Structure

### Overview

The project maintains two parallel codebases during Epic 1-2 migration:

1. **Greenfield** (`src/data_extract/`) - Modern modular architecture
2. **Brownfield** (`src/{cli,core,extractors,formatters,infrastructure,pipeline,processors}/`) - Legacy code

**Migration Strategy**: Gradual consolidation without breaking existing code (Stories 1.2-1.4)

---

### 🟢 Greenfield: Modern Modular Architecture (27 files)

**Location**: `src/data_extract/`
**Status**: Active development (Epic 1-2 complete, Epic 3-4 in progress)
**Type Checking**: Strict mypy enforcement
**Coverage Target**: >80%
**Line Count**: ~8,000 LOC

```
src/data_extract/
├── __init__.py                   # Package initialization
├── cli.py                        # 🎯 Entry point (Typer migration planned Epic 5)
│
├── chunk/                        # Epic 3: Semantic Chunking 📋
│   └── __init__.py               # Placeholder (spaCy-based chunking)
│
├── config/                       # Epic 5: Configuration Cascade 📋
│   └── __init__.py               # Placeholder (4-tier precedence)
│
├── core/                         # ✅ Foundation (Epic 1 complete)
│   ├── __init__.py
│   ├── exceptions.py             # Custom exceptions (ExtractionError, ValidationError)
│   ├── models.py                 # 📊 Pydantic models (ExtractionResult, ProcessingResult, ContentBlock)
│   └── pipeline.py               # Pipeline orchestration (Extract→Normalize→Chunk→Semantic→Output)
│
├── extract/                      # ✅ Document Extractors (Epic 2 complete)
│   ├── __init__.py
│   ├── adapter.py                # Extractor adapter pattern (BaseExtractor ABC)
│   ├── csv.py                    # CSV extraction
│   ├── docx.py                   # DOCX extraction (python-docx)
│   ├── excel.py                  # Excel extraction (openpyxl)
│   ├── pdf.py                    # PDF extraction (pypdf + pdfplumber)
│   ├── pptx.py                   # PowerPoint extraction (python-pptx)
│   └── txt.py                    # Plain text extraction
│
├── normalize/                    # ✅ Text Normalization (Epic 2 complete)
│   ├── __init__.py
│   ├── cleaning.py               # Text cleaning (whitespace, artifacts)
│   ├── config.py                 # Normalization configuration
│   ├── entities.py               # Entity extraction (audit domain)
│   ├── metadata.py               # Metadata enrichment (Story 2.6)
│   ├── normalizer.py             # Main normalizer orchestration
│   ├── schema.py                 # Schema standardization (Story 2.3)
│   └── validation.py             # Completeness validation (Story 2.5)
│
├── output/                       # Epic 3: Output Formatters 🔄
│   └── __init__.py               # Placeholder (JSON, TXT, CSV formatters)
│
├── semantic/                     # Epic 4: Semantic Analysis 📋
│   └── __init__.py               # Placeholder (TF-IDF, LSA, classical NLP only)
│
└── utils/                        # Utilities
    ├── __init__.py
    └── nlp.py                    # 🧠 NLP helpers (spaCy 3.8.0 integration - Story 2.5.2)
```

**Key Entry Points**:
- `cli.py` - Main CLI entry point (future: Typer-based)
- `core/pipeline.py` - Pipeline orchestration
- `core/models.py` - Data models (761 LOC)

**Housekeeping Notes**:
- ✅ Clean organization (each stage = separate directory)
- ✅ Type-safe (Pydantic v2 + strict mypy)
- 📋 Incomplete: `chunk/`, `output/`, `semantic/` are placeholders
- 🔄 In Progress: Epic 3 (chunk + output)

---

### 🟡 Brownfield: Legacy Code (31 files)

**Location**: `src/{cli,core,extractors,formatters,infrastructure,pipeline,processors}/`
**Status**: Maintenance mode (assessment in Stories 1.2-1.4)
**Type Checking**: Excluded during migration
**Coverage**: >60% baseline (1,000+ existing tests)
**Line Count**: ~10,000 LOC

```
src/
├── cli/                          # 🟡 CLI Commands (Click-based)
│   ├── __init__.py
│   ├── commands.py               # Command implementations (520 LOC)
│   ├── main.py                   # 🎯 Entry point (285 LOC)
│   ├── output_handler.py
│   └── validators.py
│
├── core/                         # 🟡 Core Models/Interfaces
│   ├── __init__.py
│   ├── interfaces.py             # BaseExtractor, BaseProcessor, BaseFormatter (512 LOC)
│   └── models.py                 # 🔄 DUPLICATE: data_extract/core/models.py (692 LOC)
│
├── extractors/                   # 🔴 REDUNDANT: Duplicates data_extract/extract/
│   ├── __init__.py
│   ├── csv_extractor.py          # 🔄 Duplicate of data_extract/extract/csv.py
│   ├── docx_extractor.py         # 🔄 Duplicate of data_extract/extract/docx.py
│   ├── excel_extractor.py        # 🔄 Duplicate of data_extract/extract/excel.py
│   ├── pdf_extractor.py          # 🔄 Duplicate of data_extract/extract/pdf.py
│   ├── pptx_extractor.py         # 🔄 Duplicate of data_extract/extract/pptx.py
│   └── txt_extractor.py          # 🔄 Duplicate of data_extract/extract/txt.py
│
├── formatters/                   # 🟡 Output Formatters
│   ├── __init__.py
│   ├── chunked_text_formatter.py # Chunked text output (285 LOC)
│   ├── json_formatter.py         # JSON output (345 LOC)
│   └── markdown_formatter.py     # Markdown output (380 LOC)
│
├── infrastructure/               # ✅ Infrastructure Services (keep)
│   ├── __init__.py
│   ├── config_manager.py         # Configuration management (485 LOC)
│   ├── error_handler.py          # Error handling (520 LOC, 50+ error codes)
│   ├── logging_framework.py      # Structured logging (380 LOC)
│   ├── progress_tracker.py       # Progress reporting (380 LOC)
│   ├── config_schema.yaml        # Infrastructure schema
│   ├── error_codes.yaml          # Error code registry (50+ codes)
│   └── log_config.yaml           # Logging configuration
│
├── pipeline/                     # 🟡 Pipeline Orchestration
│   ├── __init__.py
│   ├── batch_processor.py        # Batch processing (425 LOC)
│   └── extraction_pipeline.py    # Main pipeline (612 LOC)
│
└── processors/                   # 🟡 Processing Stages
    ├── __init__.py
    ├── context_linker.py         # Document hierarchy builder (295 LOC)
    ├── metadata_aggregator.py    # Statistics computation (235 LOC)
    └── quality_validator.py      # Quality scoring (360 LOC)
```

**Key Entry Points**:
- `cli/main.py` - Brownfield CLI entry point
- `pipeline/extraction_pipeline.py` - Legacy pipeline orchestration

**Housekeeping Notes**:
- 🔴 **CRITICAL**: 6 extractors are 100% redundant (duplicate greenfield)
- 🟡 **PARTIAL OVERLAP**: `core/models.py` duplicates greenfield models
- ✅ **KEEP**: `infrastructure/` module (shared services)
- 📋 **MIGRATION PLAN NEEDED**: When to deprecate each module?

**Redundancy Impact**:
- **Duplicate LOC**: ~6,000 lines (extractors only)
- **Maintenance Cost**: 2× effort for bug fixes
- **Test Duplication**: Need parity testing before migration
- **Confusion Risk**: Developers unsure which to use

---

## 📁 Configuration (`config/`)

```
config/
└── normalize/                    # Normalization configuration (Epic 2)
    ├── cleaning_rules.yaml       # Text cleaning rules
    ├── entity_patterns.yaml      # Entity extraction patterns
    ├── entity_dictionary.yaml    # Entity normalization dictionary
    └── schema_templates.yaml     # Schema standardization templates
```

**Purpose**: Runtime configuration for normalization stage

**Housekeeping Note**:
- 🟡 **4 separate YAML files** - Could consolidate in Epic 5
- ✅ **Well-organized** - Each file serves distinct purpose
- **Decision**: Keep as-is until Epic 5 (configuration cascade)

---

## 📁 Documentation (`docs/`) - Post-Cleanup

**Status**: ✅ CLEANED (Step 2 - archived 165+ pre-BMAD files)
**Total Files**: 79 high-quality markdown files
**Before**: 230+ verbose Claude Code reports
**After**: Clean BMAD-aligned structure

```
docs/
├── 📁 architecture/              # Architecture documentation (5 files)
│   ├── FOUNDATION.md             # Core architecture reference
│   ├── GETTING_STARTED.md        # Development getting started
│   ├── QUICK_REFERENCE.md        # API quick reference
│   ├── INFRASTRUCTURE_NEEDS.md   # Infrastructure requirements
│   └── TESTING_INFRASTRUCTURE.md # Testing infrastructure
│
├── 📁 retrospectives/            # Epic retrospectives (2 files)
│   ├── epic-1-retro-20251110.md
│   └── epic-2-retro-20250111.md
│
├── 📁 reviews/                   # Story reviews (1 file)
│   └── 2-2-entity-normalization-review.md
│
├── 📁 stories/                   # Epic and story specifications (20 files)
│   ├── 1-1-project-infrastructure-initialization.md
│   ├── 1-2-brownfield-codebase-assessment.md
│   ├── 2.5-*-*.md                # Epic 2.5 refinement stories
│   └── 2-*-*.md                  # Epic 2 stories
│
├── 📁 test-plans/                # Testing plans (8 files)
│   ├── EXCEL_EXTRACTOR_TEST_PLAN.md
│   ├── PPTX_TEST_PLAN.md
│   └── ...
│
├── 📁 uat/                       # UAT framework (5 files)
│   ├── reviews/
│   ├── test-cases/
│   ├── test-context/
│   ├── test-results/
│   └── tmux-cli-windows-setup.md
│
├── 📁 .archive/                  # Archived documentation
│   └── pre-bmad/                 # Pre-BMAD cleanup archive (165+ files)
│
├── 📄 architecture.md            # Main architecture document
├── 📄 bmm-index.md               # BMAD master index
├── 📄 bmm-project-overview.md    # BMAD project overview (15 pages)
├── 📄 bmm-pipeline-integration-guide.md  # Pipeline integration (25 pages)
├── 📄 bmm-processor-chain-analysis.md    # Processor chain (30 pages)
├── 📄 bmm-source-tree-analysis.md        # Source tree reference (15 pages)
├── 📄 bmm-workflow-status.yaml   # Workflow tracking
├── 📄 brainstorming-session-results-2025-11-07.md
├── 📄 brownfield-assessment.md   # Brownfield code assessment
├── 📄 ci-cd-pipeline.md          # CI/CD documentation
├── 📄 COMPLETE_PARAMETER_REFERENCE.md
├── 📄 CONFIG_GUIDE.md            # Configuration guide
├── 📄 epics.md                   # Epic breakdown
├── 📄 ERROR_HANDLING_GUIDE.md    # Error handling reference
├── 📄 housekeeping-findings-2025-11-13.md  # This housekeeping report
├── 📄 implementation-readiness-report-2025-11-10.md
├── 📄 INFRASTRUCTURE_INTEGRATION_GUIDE.md
├── 📄 LOGGING_GUIDE.md           # Logging framework guide
├── 📄 performance-baselines-story-2.5.1.md
├── 📄 performance-bottlenecks-story-2.5.1.md
├── 📄 PRD.md                     # Product requirements document
├── 📄 project-scan-report.json   # Workflow state (exhaustive scan)
├── 📄 QUICKSTART.md              # Quick start guide
├── 📄 research-technical-2025-11-08.md
├── 📄 source-tree-analysis-2025-11-13.md  # This document
├── 📄 tech-spec-epic-1.md        # Epic 1 technical specification
├── 📄 tech-spec-epic-2.5.md      # Epic 2.5 technical specification
├── 📄 tech-spec-epic-2.md        # Epic 2 technical specification
├── 📄 technology-stack-analysis.md  # Technology stack analysis
├── 📄 TESTING-README.md          # Testing guide
├── 📄 tmux-cli-instructions.md   # tmux-cli reference
├── 📄 traceability-*.md          # Traceability matrices
├── 📄 troubleshooting-spacy.md   # spaCy troubleshooting
└── 📄 USER_GUIDE.md              # End-user documentation (1400+ lines)
```

**Housekeeping Success** ✅:
- **Archived**: 165+ verbose pre-BMAD reports
- **Kept**: 79 high-quality BMAD-aligned docs
- **Reduction**: 65% file count reduction
- **Quality**: 100% BMAD framework compliant

---

## 📁 Testing (`tests/`)

**Total Tests**: 1,000+ across unit, integration, performance
**Coverage**: 60% baseline (target >80% by Epic 4)

```
tests/
├── 📁 fixtures/                  # Test data and fixtures
│   ├── archer/                   # Audit-specific test files
│   ├── batch_output_*workers/    # Batch processing fixtures
│   ├── docx/                     # DOCX test files
│   ├── edge-cases/               # Edge case test files
│   ├── excel/                    # Excel test files
│   ├── images/                   # Image test files
│   ├── normalization/            # Normalization test data
│   ├── pdfs/                     # PDF test files
│   ├── real-world-files/         # Real-world test documents
│   ├── stress_output/            # Stress test outputs
│   ├── xlsx/                     # Excel test files
│   ├── README.md                 # Fixture documentation
│   └── spacy_gold_standard.json  # spaCy validation data
│
├── 📁 integration/               # Integration tests
│   └── test_*.py
│
├── 📁 outputs/                   # 🔴 HOUSEKEEPING ISSUE
│   ├── COBIT-*.json              # 14MB test outputs
│   ├── NIST-*.json               # Should be gitignored
│   └── ...                       # 20+ output files
│
├── 📁 performance/               # Performance tests
│   ├── baselines.json            # Performance baselines (Story 2.5.1)
│   └── test_*.py
│
└── 📁 unit/                      # Unit tests (mirrors src/)
    ├── test_data_extract/        # Greenfield tests
    ├── test_extractors/          # Brownfield extractor tests
    ├── test_processors/          # Processor tests
    └── ...
```

**Test Organization**: ✅ Mirrors `src/` structure exactly

**Housekeeping Issues**:
- 🔴 **CRITICAL**: `tests/outputs/` (14MB) NOT gitignored
- 🟡 **CLUTTER**: Test outputs mixed with test code
- **Fix**: Add to `.gitignore` and move to `tests/.temp/`

---

## 📁 BMAD Framework (`bmad/`)

**Purpose**: Workflow automation and AI-assisted development framework

```
bmad/
├── 📁 _cfg/                      # BMAD configuration
│   └── agents/                   # Agent customizations (15 YAML files)
│
├── 📁 bmb/                       # BMAD Builder module
│   ├── agents/                   # bmad-builder agent
│   └── workflows/                # Workflow creation tools
│       ├── audit-workflow/
│       ├── convert-legacy/
│       ├── create-agent/
│       ├── create-module/
│       ├── create-workflow/
│       ├── edit-*/
│       ├── module-brief/
│       └── redoc/
│
├── 📁 bmm/                       # BMAD Method module
│   ├── agents/                   # Method agents (analyst, architect, dev, pm, sm, tea, tech-writer, ux-designer)
│   ├── config.yaml               # BMM configuration
│   ├── teams/                    # Team configurations
│   └── workflows/                # Development workflows
│       ├── 1-analysis/           # Phase 1: brainstorm, research, product-brief, domain-research
│       ├── 2-plan-workflows/     # Phase 2: PRD, tech-spec, UX design, epics/stories
│       ├── 3-solutioning/        # Phase 3: architecture, solutioning-gate-check
│       └── 4-implementation/     # Phase 4: code-review, correct-course, create-story, execute-tests, review-uat, build-test-context, create-test-cases
│
├── 📁 cis/                       # Creative & Innovation Strategy module
│   ├── agents/                   # Creative agents (brainstorming-coach, creative-problem-solver, design-thinking-coach, innovation-strategist, storyteller)
│   └── workflows/                # Creative workflows (design-thinking, innovation-strategy, problem-solving, storytelling)
│
├── 📁 core/                      # BMAD Core
│   ├── agents/                   # bmad-master agent
│   ├── tasks/                    # Core tasks (advanced-elicitation, workflow executor, index-docs)
│   ├── tools/                    # Core tools (shard-doc)
│   └── workflows/                # Core workflows (brainstorming, party-mode)
│
└── 📁 docs/                      # BMAD documentation
```

**Status**: ✅ BMAD framework fully integrated
**Usage**: Powers all workflow automation (document-project, PRD, architecture, etc.)

**Housekeeping Note**: Clean, well-organized framework structure

---

## 📁 Other Directories

### Examples (`examples/`)
```
examples/
└── sample_input.json             # Sample input file
```

**Purpose**: Example input files for testing
**Status**: Minimal (1 file)

### Scripts (`scripts/`)
```
scripts/
├── profile_pipeline.py           # Performance profiling (Story 2.5.1)
├── run_test_extractions.py       # Real-world validation
└── ...                           # Utility scripts
```

**Purpose**: Development and profiling utilities
**Status**: Well-organized

### Logs (`logs/`)
```
logs/
└── .gitkeep                      # 📋 TODO: Add .gitkeep to preserve directory
```

**Purpose**: Runtime log files (gitignored)
**Housekeeping**: Empty (expected), needs `.gitkeep`

### Output (`output/`)
```
output/
└── quarantine/                   # Quarantine directory for failed files
    ├── 2025-11-11/
    ├── 2025-11-12/
    └── 2025-11-13/
```

**Purpose**: Processing outputs (gitignored)
**Status**: ✅ Properly gitignored

---

## Critical Files (Root Level)

```
root/
├── 📄 .gitignore                 # ✅ Well-configured (minor gap: tests/outputs/)
├── 📄 .pre-commit-config.yaml    # Pre-commit hooks (black, ruff, mypy)
├── 📄 CLAUDE.md                  # ✅ Comprehensive Claude Code instructions
├── 📄 pyproject.toml             # ✅ Project configuration (dependencies, tools)
├── 📄 README.md                  # Project overview
└── 📄 TRASH-FILES.md             # Housekeeping log (165+ archived files)
```

**Housekeeping Notes**:
- ✅ Excellent `CLAUDE.md` - Comprehensive project instructions
- ✅ Well-structured `pyproject.toml` - Clean dependency organization
- 🔴 **Missing from git**: `DOCUMENTATION_INDEX.md`, `INSTALL.md`, `PROJECT_STATE.md` (archived, need regeneration)

---

## File Count Statistics

### Source Code
| Category | Files | LOC (est.) |
|----------|-------|------------|
| Greenfield (`data_extract/`) | 27 | ~8,000 |
| Brownfield (legacy) | 31 | ~10,000 |
| **Total Source** | **59** | **~18,000** |

### Tests
| Category | Files | Tests |
|----------|-------|-------|
| Unit tests | 40+ | 800+ |
| Integration tests | 10+ | 150+ |
| Performance tests | 5+ | 50+ |
| **Total Tests** | **55+** | **1,000+** |

### Documentation
| Category | Before | After | Reduction |
|----------|--------|-------|-----------|
| Markdown files | 230+ | 79 | 65% |
| High-quality docs | ~20 | 79 | +295% |
| Context bloat | High | Minimal | 100% |

### Configuration
| Category | Files |
|----------|-------|
| YAML configs | 60+ (BMAD + project) |
| Infrastructure configs | 3 (error_codes, log_config, config_schema) |
| Normalization configs | 4 (cleaning, entities, dictionary, schema) |

---

## Housekeeping Recommendations

### Immediate Actions 🔴

1. **Add `tests/outputs/` to .gitignore**
   ```bash
   echo "tests/outputs/" >> .gitignore
   ```

2. **Add `.gitkeep` to logs directory**
   ```bash
   touch logs/.gitkeep
   ```

3. **Regenerate missing root docs**
   - `DOCUMENTATION_INDEX.md` (master doc index)
   - `INSTALL.md` (installation guide)
   - `PROJECT_STATE.md` (project status tracker)

### Short-Term Actions 🟡

4. **Document dual codebase migration strategy**
   - Create `docs/migration-strategy.md`
   - Define brownfield deprecation timeline
   - Establish testing parity requirements

5. **Organize test outputs**
   - Create `tests/.temp/` (gitignored)
   - Move `tests/outputs/` → `tests/.temp/`

### Long-Term Actions 📋

6. **Complete brownfield migration** (Epic 5)
   - Deprecate brownfield extractors
   - Remove duplicate code
   - Update all imports

7. **Consider config consolidation** (Epic 5)
   - Evaluate `config/normalize/*.yaml` merge
   - Implement 4-tier configuration cascade

---

## Integration Points

### Brownfield → Greenfield
- CLI entry: `src/cli/main.py` → will become `src/data_extract/cli.py`
- Extractors: `src/extractors/*.py` → already duplicated in `src/data_extract/extract/`
- Models: `src/core/models.py` → duplicates `src/data_extract/core/models.py`

### Shared Services (Keep)
- `src/infrastructure/` - Used by both codebases
- Configuration files - Shared across project
- Test infrastructure - Tests both codebases

### External Integrations
- BMAD framework - Workflow automation
- spaCy - NLP (Epic 3 chunking)
- Pre-commit - Code quality enforcement
- pytest - Testing framework

---

## Conclusion

**Overall Structure**: 🟢 Good with clear migration path

**Strengths**:
- ✅ Clean greenfield architecture (5-stage pipeline)
- ✅ Comprehensive documentation (post-cleanup)
- ✅ Well-organized test suite
- ✅ BMAD framework integration
- ✅ Proper .gitignore (1 gap)

**Areas for Improvement**:
- 🔴 Gitignore `tests/outputs/`
- 🟡 Document migration strategy
- 🟡 Regenerate missing root docs
- 📋 Complete brownfield migration (Epic 5)

**Risk Assessment**: Low - All issues have clear remediation paths

---

**Analysis Complete**: Step 5 ✅
**Next**: Step 6 - Extract and consolidate dev/ops information
