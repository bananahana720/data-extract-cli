# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

<!-- MODULE: CORE-OVERVIEW -->
## Project Overview

**Data Extraction Tool** - Enterprise document processing pipeline for RAG workflows. Transforms messy corporate audit documents into AI-optimized outputs using a five-stage modular pipeline architecture.

**Status**: V1.0 RELEASE - Enhanced CLI UX & Batch Processing (COMPLETE - all 5 epics done)
**Python**: 3.11+ (minimum version requirement)
**Architecture**: `Extract → Normalize → Chunk → Semantic → Output`
<!-- END MODULE: CORE-OVERVIEW -->

<!-- MODULE: CRITICAL-RULES -->
## Critical Rules

**[CRITICAL]** Fill AC evidence table BEFORE marking review status - prevents review cycles
**[CRITICAL]** Run Black → Ruff → Mypy → Tests BEFORE marking task complete - quality gate enforcement
**[CRITICAL]** Fix violations immediately when discovered - don't accumulate tech debt
**[CRITICAL]** Mirror test structure to src/ exactly - prevents test organization issues
**[CRITICAL]** Never break brownfield code during greenfield migration - both systems must coexist

For complete lessons learned, see `docs/retrospective-lessons.md`.
<!-- END MODULE: CRITICAL-RULES -->

<!-- MODULE: ARCHITECTURE -->
## Core Architecture

### Five-Stage Pipeline Pattern

Each stage is a composable, testable component using frozen dataclasses and ABC interfaces:

1. **Extract** (`src/data_extract/extract/`) - Document format-specific extraction (PDF, DOCX, XLSX, PPTX, CSV, images+OCR)
2. **Normalize** (`src/data_extract/normalize/`) - Text cleaning, entity standardization
3. **Chunk** (`src/data_extract/chunk/`) - Semantic-aware chunking (spaCy-based)
4. **Semantic** (`src/data_extract/semantic/`) - Classical NLP analysis (TF-IDF, LSA - no transformers per enterprise constraints)
5. **Output** (`src/data_extract/output/`) - Multiple formats (JSON, TXT, CSV)

### Design Principles

**[REQUIRED]** Modularity - Each stage independent, testable, replaceable
**[REQUIRED]** Immutability - Frozen dataclasses prevent pipeline state mutations
**[REQUIRED]** Type Safety - Full type hints + Pydantic v2 validation enforced by mypy
**[REQUIRED]** Interface-Based - All modules implement ABCs (BaseExtractor, BaseProcessor, BaseFormatter)
**[REQUIRED]** Determinism - Same input always produces same output

### Greenfield-Only Structure (V1.0)

**Greenfield** (`src/data_extract/`) - Primary codebase (74 Python files, ~19,700 LOC)
**Brownfield** (`src/{cli,core,extractors,processors,formatters,infrastructure,pipeline}/`) - Archived in TRASH (legacy code, no longer active)

**[MIGRATION COMPLETE]** Brownfield code moved to TRASH-FILES.md. All new development uses greenfield exclusively.
<!-- END MODULE: ARCHITECTURE -->

<!-- MODULE: COMMANDS -->
## Development Commands

### Setup
```bash
# Install uv package manager (if not already installed)
# macOS/Linux:
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows:
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or via pip:
pip install uv

# Setup project with uv (all platforms)
uv venv                    # Create virtual environment
uv pip install -e ".[dev]" # Install dependencies
pre-commit install         # Setup pre-commit hooks
```

### spaCy Model Setup (Required for Epic 3)
```bash
python -m spacy download en_core_web_md
python -m spacy validate
```

### Semantic Dependencies Setup (Required for Epic 4)
```bash
# Dependencies are installed via uv pip install -e ".[dev]"
# Verify installation with smoke test:
python scripts/smoke_test_semantic.py
```

**Semantic Stack:**
- **scikit-learn** (≥1.3.0) - TF-IDF vectorization, LSA, cosine similarity
- **joblib** (≥1.3.0) - Model serialization and caching
- **textstat** (≥0.7.3) - Readability metrics (Flesch, SMOG, etc.)

**Performance Baselines:**
- TF-IDF fit/transform: <100ms for 1k-word document
- Full pipeline: <500ms for 10 documents
- CI validation: Smoke test runs automatically after dependency installation

**Learning Resources:**
- **TF-IDF/LSA Playbook**: `docs/playbooks/semantic-analysis-intro.ipynb` - Interactive Jupyter notebook for junior developers
- **Quick Reference**: `docs/playbooks/semantic-analysis-reference.md` - API reference and troubleshooting guide
- **Test Corpus**: `tests/fixtures/semantic_corpus.py` - Pre-built corpus for examples

### Testing
```bash
pytest                      # Run all tests
pytest --cov=src           # With coverage
pytest -m unit             # Fast unit tests only
pytest -m integration      # Integration tests
pytest -n auto             # Parallel execution
```

**[REQUIRED]** Test Markers: `unit`, `integration`, `extraction`, `processing`, `formatting`, `chunking`, `pipeline`, `cli`, `slow`, `performance`

### Code Quality (Enforced by Pre-commit)
```bash
black src/ tests/          # Format code (100 char line length)
ruff check src/ tests/     # Lint code
mypy src/data_extract/     # Type check (strict mode, excludes brownfield)
pre-commit run --all-files # Run all pre-commit hooks
```

**[CRITICAL]** Pre-commit hooks run on `git commit` AND are validated in CI. Always run `pre-commit run --all-files` before pushing.

### CLI Entry Point
```bash
data-extract    # Typer-based CLI (full implementation in Epic 5)
```
<!-- END MODULE: COMMANDS -->

<!-- MODULE: AUTOMATION -->
## Development Automation (Epic 3.5)

**P0 Scripts** (60% token reduction, 75% faster development):
- `scripts/generate_story_template.py` - Story template generator
- `scripts/run_quality_gates.py` - Quality gate runner (Black/Ruff/Mypy/coverage)
- `scripts/init_claude_session.py` - Session initializer (git sync, deps, spaCy)

**P1 Scripts** (Dependency & Test Infrastructure):
- `scripts/audit_dependencies.py` - Dependency auditing with AST parsing and caching
- `scripts/generate_tests.py` - Story-driven test generation with fixture creation

**P1 Scripts** (Environment & Performance):
- `scripts/setup_environment.py` - Cross-platform environment setup (uv, deps, spaCy, hooks)
- `scripts/validate_performance.py` - Performance baseline validation and regression detection

**P2 Scripts** (Documentation & Fixtures):
- `scripts/generate_docs.py` - API documentation, coverage reports, architecture diagrams
- `scripts/generate_fixtures.py` - Test fixture generation (PDF/DOCX/XLSX, semantic corpus)

**Sprint & Security Tools**:
- `scripts/manage_sprint_status.py` - Sprint status tracking, velocity calculation, Slack/Teams notifications
- `scripts/scan_security.py` - Security scanning (secrets, vulnerabilities, SAST, GitLeaks)

**Usage:** See `docs/automation-guide.md` for complete documentation and examples.
<!-- END MODULE: AUTOMATION -->

<!-- MODULE: CONVENTIONS -->
## Code Conventions

### Style (Enforced by Tools)
**[REQUIRED]** Formatting - Black (100 char lines, target Python 3.11+)
**[REQUIRED]** Linting - Ruff (replaces flake8 + isort)
**[REQUIRED]** Type Checking - Mypy strict mode (excludes brownfield during migration)

### Naming
**[REQUIRED]** Classes: `PascalCase` (e.g., `DocxExtractor`)
**[REQUIRED]** Functions/methods: `snake_case` (e.g., `extract_content`)
**[REQUIRED]** Constants: `UPPER_SNAKE_CASE` (e.g., `MAX_CHUNK_SIZE`)
**[REQUIRED]** Modules: `snake_case` (e.g., `context_linker.py`)

### Required Standards
**[REQUIRED]** Type hints on all public functions
**[REQUIRED]** Google-style docstrings for public APIs
**[REQUIRED]** Tests for all new functionality
**[CRITICAL]** Pre-commit compliance (black, ruff, mypy must pass)
<!-- END MODULE: CONVENTIONS -->

<!-- MODULE: TESTING -->
## Testing Strategy

### Organization
**[CRITICAL]** Tests mirror `src/` structure exactly
**[REQUIRED]** Use pytest fixtures for test data
**[REQUIRED]** Use markers for selective execution
**[RECOMMENDED]** Include integration and performance tests

### Coverage Requirements
**[REQUIRED]** Baseline: >60% overall (includes brownfield)
**[REQUIRED]** Greenfield (`src/data_extract/`): >80% coverage
**[RECOMMENDED]** Epic 5 critical paths: >90% coverage
<!-- END MODULE: TESTING -->

<!-- MODULE: CURRENT-STATE -->
## Epic Status

### V1.0 Release (2025-12-01)

**All Epics Complete:**
- **Epic 1**: Foundation (4 stories - COMPLETE)
- **Epic 2**: Extract & Normalize (6 stories - COMPLETE)
- **Epic 2.5**: Infrastructure (6 stories - COMPLETE)
- **Epic 3**: Chunk & Output (7 stories - COMPLETE)
- **Epic 3.5**: Tooling & Automation (11 stories - COMPLETE 2025-11-18)
- **Epic 4**: Knowledge Curation via Classical NLP (6 stories - COMPLETE 2025-11-25)
- **Epic 5**: Enhanced CLI UX & Batch Processing (8 stories - COMPLETE 2025-11-29)

**V1.0 Release Metrics (2025-11-30 Assessment):**
- PRD Completion: 100% (FR-1 through FR-8 all implemented)
- Greenfield Codebase: 74 Python files, ~19,700 LOC (primary & active)
- Test Coverage: 3,575 tests (Core: 971 pass, CLI: 674 pass, UAT: 66 pass, Scripts: 170 pass)
- UAT Validation: 66 tests across 7 user journeys (100% pass rate)
- Quality Gates: All passing (Black/Ruff clean, Mypy 0 violations on greenfield)
- Performance: All NFRs met or exceeded (TF-IDF 10ms vs 100ms, Similarity 4.8ms vs 200ms, Quality metrics 0.12ms vs 10ms)
- CLI Commands: 9 operational (process, extract, retry, validate, status, semantic, cache, config, session)
- Deployment Readiness: 8/10 (READY with minor optional fixes)

**Epic 5 Achievements (2025-11-25 to 2025-11-29):**
- UAT Testing Framework (Story 5-0) - 46 UAT tasks defined
- Refactored Command Structure (Story 5-1) - 9 commands with Rich UI
- Configuration Management (Story 5-2) - 6-layer cascade system
- Real-Time Progress Indicators (Story 5-3) - Rich terminal components
- Summary Statistics (Story 5-4) - Comprehensive reporting
- Preset Configurations (Story 5-5) - Common workflow shortcuts
- Graceful Error Handling (Story 5-6) - Session recovery
- Batch Processing Optimization (Story 5-7) - Incremental updates

**Key Learnings from Full Project:**
- UAT-first foundation prevents UX drift
- Multi-agent orchestration catches architectural issues early
- Verification loop discipline essential for quality
- Performance excellence achieved (10-80x faster than requirements)
- Incremental delivery enables rapid iteration

### Documentation
- **PRD Status**: COMPLETE (all functional requirements implemented)
- **Architecture**: 5-stage pipeline fully operational (Extract → Normalize → Chunk → Semantic → Output)
- **Brownfield Migration**: COMPLETE (legacy code archived, greenfield is primary)
- **CLI Entry Point**: `data-extract` with 9 commands operational

See `docs/sprint-status.yaml` and `docs/retrospectives/epic-5-retro-2025-11-30.md` for complete details.
<!-- END MODULE: CURRENT-STATE -->

<!-- MODULE: QUALITY-GATES -->
## Quality Gates

**[CRITICAL]** Pre-commit workflow (0 violations required):
1. `black src/ tests/` → Fix formatting
2. `ruff check src/ tests/` → Fix linting
3. `mypy src/data_extract/` → Fix type violations (run from project root)
4. Run tests → Fix failures
5. Commit clean code

**[REQUIRED]** Fix validation issues immediately (don't defer tech debt)
**[REQUIRED]** Always include integration tests (catch memory/NFR issues)
**[RECOMMENDED]** Profile before optimizing (establish baselines first)
<!-- END MODULE: QUALITY-GATES -->

<!-- MODULE: TECHNOLOGY -->
## Technology Stack

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| CLI | Typer | Type-safe, modern |
| Data Models | Pydantic v2 | Runtime validation |
| PDF | PyMuPDF | Fast, OCR fallback |
| Office | python-docx, openpyxl | Standard libraries |
| Chunking | spaCy | Sentence boundaries |
| Semantic | scikit-learn | TF-IDF, LSA |
| Testing | pytest | Industry standard |
| Quality | black, ruff, mypy | Modern toolchain |

**[CRITICAL]** Enterprise Constraint: Classical NLP only - no transformer models allowed.
<!-- END MODULE: TECHNOLOGY -->

<!-- MODULE: KEY-DECISIONS -->
## Key Architecture Decisions

**[REQUIRED]** ADR-001: Immutable models prevent pipeline state corruption
**[REQUIRED]** ADR-002: Pluggable extractors isolate format-specific logic
**[REQUIRED]** ADR-003: ContentBlocks preserve document structure
**[CRITICAL]** ADR-004: Classical NLP only (enterprise constraint)
**[CRITICAL]** ADR-005: Gradual brownfield modernization

See `docs/architecture.md` for full details.
<!-- END MODULE: KEY-DECISIONS -->

<!-- MODULE: REFERENCES -->
## Documentation References

### Core Documentation
- `docs/epic-3-reference.md` - Complete Epic 3 implementation guide
- `docs/automation-guide.md` - P0 scripts and automation tools
- `docs/retrospective-lessons.md` - Comprehensive lessons from Epics 1-4
- `docs/architecture.md` - Technical architecture and ADRs
- `docs/sprint-status.yaml` - Current development status (authoritative)
- `docs/ux-design-specification.md` - CLI UX design with 7 user journeys

### Epic Documentation
- `docs/tech-spec-epic-*.md` - Epic technical specifications
- `docs/stories/` - Story-level implementation specs
- `docs/performance-baselines-epic-*.md` - Performance benchmarks

### Playbooks and Guides
- `docs/playbooks/semantic-analysis-intro.ipynb` - TF-IDF/LSA interactive tutorial (Epic 4 prep)
- `docs/playbooks/semantic-analysis-reference.md` - Quick API reference for semantic analysis

### Configuration
- `pyproject.toml` - Project configuration and dependencies
- `.pre-commit-config.yaml` - Code quality hooks
<!-- END MODULE: REFERENCES -->

<!-- MODULE: IMPORTANT-NOTES -->
## Important Notes

### BMAD Workflow Integration
**[AVAILABLE]** This project uses BMAD (Better Method for AI-Assisted Development) custom slash commands:
- `/bmad:bmm:workflows:code-review` - Senior Developer code review with AC validation
- `/bmad:bmm:workflows:dev-story` - Story implementation workflow
- `/bmad:core:agents:bmad-master` - Master orchestration agent for multi-agent taskforce coordination
- See `.claude/commands/` for all available BMAD workflows
- For AI agent orchestration, use the bmad-master agent with model=opus and ultrathink protocols

### Search Tools
**[CRITICAL]** Always use ripgrep (rg), never grep. The tool is configured to use rg for performance.

### Type Checking
**[REQUIRED]** Mypy excludes brownfield packages during migration. New code in `src/data_extract/` must pass strict type checking.

### Error Handling
**[RECOMMENDED]** Pipeline uses "continue-on-error" pattern - graceful degradation per file. Don't fail entire batch on single document error.

### Documentation
**[REQUIRED]** README files only when explicitly requested - don't create documentation proactively.

### UAT Testing (Epic 5)
**[AVAILABLE]** tmux-cli based automated UAT testing for CLI validation
- Instructions: `docs/tmux-cli-instructions.md`
- Framework: `tests/uat/` (to be created in Story 5-0)
- Runs on every PR to validate user journeys
<!-- END MODULE: IMPORTANT-NOTES -->
