# Data Extraction Tool - Test Infrastructure Reference

**Generated**: 2025-11-30
**Scan Level**: Exhaustive
**Total Test Files**: 229
**Total Fixtures**: 112

---

## Overview

This document catalogs the comprehensive test infrastructure for the Data Extraction Tool, including test organization, fixtures, markers, and CI/CD workflows.

---

## Test Directory Structure

```
tests/
├── conftest.py                     [15 core fixtures]
│
├── fixtures/                       [Comprehensive test data]
│   ├── docx/                       [DOCX sample files]
│   ├── pdfs/                       [PDF fixtures]
│   │   ├── large/
│   │   └── scanned/
│   ├── excel/                      [XLSX fixtures]
│   ├── images/                     [Image test files]
│   ├── semantic/                   [Epic 4 test data]
│   │   ├── corpus/                 [55 real documents]
│   │   │   ├── audit-reports/      [20 documents]
│   │   │   ├── compliance-docs/    [17 documents]
│   │   │   └── risk-matrices/      [18 documents]
│   │   └── gold-standard/          [Pre-computed models]
│   ├── generated/edge_cases/       [9 edge case files]
│   ├── normalization/              [Text cleaning test data]
│   └── real_world_files/           [5 enterprise documents]
│
├── unit/                           [116 test files]
│   ├── cli/                        [CLI unit tests]
│   ├── data_extract/               [Greenfield tests]
│   │   ├── extract/
│   │   ├── normalize/
│   │   ├── chunk/
│   │   ├── semantic/
│   │   ├── output/
│   │   ├── core/
│   │   └── cli/
│   └── test_cli/                   [Story-specific tests]
│       ├── test_story_5_1/
│       ├── test_story_5_2/
│       ├── test_story_5_3/
│       ├── test_story_5_5/
│       ├── test_story_5_6/
│       └── test_story_5_7/
│
├── integration/                    [52 test files]
│   ├── conftest.py                 [23 fixtures]
│   ├── test_semantic/              [Semantic integration]
│   └── test_fixtures/              [Fixture validation]
│
├── behavioral/                     [11 BDD-style tests]
│   ├── epic_4/
│   └── epic_5/
│
├── uat/                            [8 UAT tests]
│   ├── conftest.py                 [12 fixtures]
│   ├── framework/                  [tmux-cli framework]
│   └── journeys/                   [User journey tests]
│
├── performance/                    [14 performance tests]
│   ├── conftest.py                 [8 fixtures]
│   ├── batch_100_files/            [100-file batch]
│   └── baselines.json              [Performance baselines]
│
└── validation/                     [1 test file]
```

---

## Test File Statistics

| Category | Files | Purpose |
|----------|-------|---------|
| **Unit Tests** | 116 | Isolated component testing |
| **Integration Tests** | 52 | Multi-component testing |
| **Behavioral Tests** | 11 | BDD-style GIVEN-WHEN-THEN |
| **UAT Tests** | 8 | User acceptance (tmux-cli) |
| **Performance Tests** | 14 | Benchmarking & regression |
| **Validation Tests** | 1 | Bug fix validation |
| **Legacy Tests** | 24 | Being migrated |
| **Total** | 229 | |

---

## Pytest Markers

### Priority Markers (CI/CD Gate Control)

| Marker | Purpose | When to Run |
|--------|---------|-------------|
| `P0` | Critical path tests | Every PR, must pass |
| `P1` | Core functionality | PR gate |
| `P2` | Extended coverage | Nightly |

### Category Markers

| Marker | Purpose |
|--------|---------|
| `unit` | Fast, isolated component tests |
| `integration` | Multi-component tests |
| `performance` | Benchmarking tests |
| `slow` | Tests exceeding 1 second |
| `behavioral` | BDD-style tests |
| `uat` | User acceptance tests |
| `journey` | User journey tests |
| `e2e` | End-to-end scenario tests |

### Module Markers

| Marker | Purpose |
|--------|---------|
| `extraction` | Extractor module tests |
| `processing` | Processor module tests |
| `formatting` | Formatter module tests |
| `pipeline` | Pipeline orchestration tests |
| `cli` | CLI command tests |
| `chunking` | Chunking module tests |
| `semantic` | Semantic analysis tests |
| `infrastructure` | Config, logging, error handling |

### Story-Specific Markers

| Marker | Purpose |
|--------|---------|
| `epic4` | Epic 4 tests (semantic analysis) |
| `epic5` | Epic 5 tests (enhanced CLI) |
| `tfidf` | TF-IDF vectorization (Story 4-1) |
| `similarity` | Similarity analysis (Story 4-2) |
| `lsa` | Latent Semantic Analysis (Story 4-3) |
| `quality_metrics` | Text quality scoring (Story 4-4) |
| `story_5_1` | Command structure |
| `story_5_2` | Configuration management |
| `story_5_5` | Preset configurations |

### Special Markers

| Marker | Purpose |
|--------|---------|
| `subprocess` | CLI via subprocess |
| `edge_case` | Boundary conditions |
| `stress` | Resource-intensive tests |
| `cross_format` | Multi-format validation |
| `entity_aware` | Entity-aware chunking |
| `quality` | Quality scoring tests |
| `schema` | JSON schema validation |
| `test_id(id)` | Unique test identifier |

---

## Fixture Architecture

### Root Conftest (`tests/conftest.py`)

**15 Core Fixtures:**

| Fixture | Scope | Purpose |
|---------|-------|---------|
| `sample_content_block` | function | PARAGRAPH type block |
| `sample_heading_block` | function | HEADING type block |
| `sample_table_block` | function | TABLE with metadata |
| `sample_image_block` | function | IMAGE type block |
| `sample_content_blocks` | function | Mixed content list |
| `sample_document_metadata` | function | Document metadata |
| `sample_extraction_result` | function | Successful extraction |
| `failed_extraction_result` | function | Error scenario |
| `sample_processing_result` | function | Post-processing output |
| `temp_test_file` | function | Generator for temp TXT |
| `empty_test_file` | function | Edge case: empty file |
| `large_test_file` | function | Performance: 1MB file |
| `fixture_dir` | function | Path to tests/fixtures/ |
| `validate_extraction_result` | function | Callable validator |
| `validate_processing_result` | function | Callable validator |

### Integration Conftest (`tests/integration/conftest.py`)

**23 Fixtures:**

| Fixture | Scope | Purpose |
|---------|-------|---------|
| `sample_docx_file` | function | Valid DOCX with content |
| `sample_pdf_file` | function | Valid PDF with text |
| `sample_text_file` | function | Plain text |
| `large_docx_file` | function | 100+ paragraphs (~1MB) |
| `corrupted_docx_file` | function | Invalid DOCX |
| `corrupted_pdf_file` | function | Truncated PDF |
| `empty_docx_file` | function | Empty document |
| `multiple_test_files` | function | 5-file batch (mixed) |
| `batch_test_directory` | function | Batch directory |
| `configured_pipeline` | function | Fully wired pipeline |
| `batch_processor` | function | 2-worker processor |
| `cli_runner` | function | Click CliRunner |
| `config_file` | function | Valid YAML config |
| `invalid_config_file` | function | Invalid config |
| `output_directory` | function | Temporary output |
| `performance_timer` | function | Timer with elapsed |
| `progress_tracker` | function | Progress collector |
| `cleanup_temp_files` | function | Auto-cleanup (autouse) |

### Semantic Unit Conftest (`tests/unit/data_extract/semantic/conftest.py`)

**15 Fixtures:**

| Fixture | Scope | Purpose |
|---------|-------|---------|
| `simple_documents` | function | 5 simple test docs |
| `single_document` | function | Single doc isolation |
| `empty_document` | function | Edge case |
| `special_char_document` | function | Normalization testing |
| `mock_tfidf_vectors` | function | 5×10 numpy arrays |
| `mock_vocabulary` | function | 10-term vocabulary |
| `mock_idf_weights` | function | IDF weight values |
| `tfidf_config` | function | TF-IDF params |
| `lsa_config` | function | LSA params |
| `similarity_config` | function | Cosine similarity config |
| `quality_config` | function | Quality metrics config |
| `expected_similarity_matrix` | function | 5×5 symmetric matrix |
| `expected_quality_scores` | function | Readability scores |
| `tokenizer` | function | Whitespace tokenizer |
| `vector_comparator` | function | np.allclose wrapper |

### UAT Conftest (`tests/uat/conftest.py`)

**12 Fixtures:**

| Fixture | Scope | Purpose |
|---------|-------|---------|
| `tmux_available` | session | tmux check |
| `tmux_cli_available` | session | tmux-cli check |
| `tmux_session` | function | TmuxSession generator |
| `sample_corpus_dir` | function | Sample documents path |
| `expected_outputs_dir` | function | Expected results path |
| `temp_output_dir` | function | Temporary output |
| `sample_pdf_files` | function | PDFs in corpus |
| `sample_docx_files` | function | DOCXs in corpus |
| `sample_xlsx_files` | function | XLSXs in corpus |
| `cli_command` | function | "data-extract" string |
| `activate_venv_command` | function | Venv activation |
| `journey_state` | function | Multi-step test state |

### Performance Conftest (`tests/performance/conftest.py`)

**8 Fixtures:**

| Fixture | Scope | Purpose |
|---------|-------|---------|
| `performance_timer` | function | Execution timer |
| `memory_profiler` | function | Memory tracking |
| `baseline_metrics` | function | Performance baselines |
| `resource_monitor` | function | Resource tracking |
| `batch_100_files` | session | 100-file test batch |
| `throughput_calculator` | function | Files/minute calc |
| `baseline_comparator` | function | Regression detection |
| `performance_reporter` | function | Report generation |

---

## CI/CD Workflows

### Workflow 1: `test.yml` - Main Test & Quality Pipeline

**Triggers**: Push to main/develop/feature/**, PR to main/develop

**Jobs**:

| Job | Purpose | Python |
|-----|---------|--------|
| `burn-in` | Smoke tests, 10× changed test iterations | 3.12 |
| `test` | Full test suite with coverage | 3.12, 3.13 |
| `lint` | Ruff linting | 3.12 |
| `type-check` | Mypy strict on greenfield | 3.12 |
| `format-check` | Black formatting | 3.12 |
| `pre-commit` | All pre-commit hooks | 3.12 |
| `status-check` | Aggregate gate | - |

**Coverage Threshold**: 60% (fail_under=60)

### Workflow 2: `security.yml` - Security Scanning

**Triggers**: Push main/develop, PR main, Daily 2 AM UTC, Manual

**Scans**:
- GitLeaks (secrets detection)
- pip-audit (dependency vulnerabilities)
- Safety (known CVEs)
- Git history scanning

### Workflow 3: `performance.yml` - Performance Regression

**Triggers**: Push main, Weekly Monday 2 AM UTC, Manual

**Thresholds**:
- **Minimum throughput**: 13.1 files/min
- **Maximum memory**: 4.56 GB
- **Baseline throughput**: 14.57 files/min
- **Baseline memory**: 4.15 GB

### Workflow 4: `uat.yaml` - User Acceptance Testing

**Purpose**: Validate CLI user journeys (Story 5-0)

**Framework**: tmux-cli based testing

---

## Test Fixtures Data

### Semantic Corpus

| Category | Documents | Purpose |
|----------|-----------|---------|
| **audit-reports/** | 20 | Audit document analysis |
| **compliance-docs/** | 17 | Compliance processing |
| **risk-matrices/** | 18 | Risk assessment matrices |
| **Total** | 55 | Enterprise document corpus |

### Gold Standard Models

| File | Purpose |
|------|---------|
| `tfidf_vectorizer.joblib` | Pre-trained TF-IDF model |
| `lsa_model.joblib` | Pre-trained LSA model |
| `gold_standard_annotations.json` | Reference annotations |
| `tfidf_annotations.json` | TF-IDF reference data |
| `lsa_annotations.json` | LSA reference data |
| `readability_annotations.json` | Readability metrics |
| `entity_annotations.json` | Entity extraction reference |

### Edge Case Fixtures

| File | Size | Purpose |
|------|------|---------|
| `empty.txt` | 0 bytes | Empty file handling |
| `single_char.txt` | 1 char | Minimal input |
| `whitespace_only.txt` | - | Whitespace handling |
| `null_bytes.txt` | - | Binary null handling |
| `mixed_encoding.txt` | - | UTF-8 + Latin-1 |
| `long_line.txt` | - | Very long line |
| `many_lines.txt` | 100k+ | High line count |
| `unicode.txt` | - | Emoji, non-Latin |
| `large_1mb.txt` | 1 MB | Large file handling |

### Real-World Enterprise Documents

| File | Domain |
|------|--------|
| `NIST_SP-800-53_rev5-derived-OSCAL.xlsx` | Security controls |
| `NIST.SP.800-37r2.pdf` | RMF guidance |
| `COBIT-2019-Framework-*.pdf` | Governance framework |
| `OWASP-LLM_GenAI-Security-*.pdf` | AI security |
| `Compliance-Risk-Management-*.pdf` | Risk framework |

---

## Test Execution Patterns

### Fast Development (Local)
```bash
pytest -m unit                      # Unit tests only
pytest -m "not slow"                # Skip slow tests
pytest -m P0                        # Critical path only
pytest tests/unit/data_extract/     # Greenfield only
```

### Full Suite (CI/CD)
```bash
pytest --cov=src --cov-report=term --cov-report=xml -v
```

### Selective Testing
```bash
pytest -m semantic                  # Epic 4 only
pytest -m epic5                     # Epic 5 only
pytest -m story_5_1                 # Specific story
pytest -k "test_tfidf"              # Pattern match
```

### Performance Testing
```bash
pytest -m performance tests/performance/test_throughput.py
```

### Coverage Analysis
```bash
pytest --cov=src --cov-report=html
open htmlcov/index.html
```

---

## Performance Baselines

**Source**: `tests/performance/baselines.json`

| Metric | Baseline | Threshold | Tolerance |
|--------|----------|-----------|-----------|
| **Throughput** | 14.57 files/min | 13.1 files/min | -10.1% |
| **Memory** | 4.15 GB | 4.56 GB | +9.9% |
| **Batch Size** | 100 files | - | Mixed formats |

---

## Fixture Summary by Conftest

| Conftest Location | Fixtures | Scope |
|-------------------|----------|-------|
| `tests/conftest.py` | 15 | function |
| `tests/integration/conftest.py` | 23 | function |
| `tests/unit/data_extract/semantic/conftest.py` | 15 | function |
| `tests/integration/test_semantic/conftest.py` | 16 | function |
| `tests/uat/conftest.py` | 12 | session/function |
| `tests/performance/conftest.py` | 8 | function/session |
| Story-specific conftest files | Varies | function |
| **Total** | **112** | - |

---

## Test Organization Best Practices

1. **Mirror `src/` structure**: Tests at `tests/unit/` mirror `src/` exactly
2. **Use markers**: Tag tests with appropriate markers for selective execution
3. **Story-specific tests**: Place in `tests/unit/test_cli/test_story_X_Y/`
4. **Fixtures**: Define in nearest `conftest.py` for appropriate scope
5. **Test IDs**: Use `@pytest.mark.test_id` for traceability

---

**Last Updated**: 2025-11-30 | **Workflow**: document-project v1.2.0
