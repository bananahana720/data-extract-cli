# CI/CD Pipeline Documentation

## Overview

The data-extraction-tool uses GitHub Actions for continuous integration with multiple quality gates and performance monitoring.

## Workflows

### 1. Test & Quality Checks (`.github/workflows/test.yml`)

Runs on every push and pull request.

**Jobs**:
- **test**: Runs pytest with coverage across Python 3.12 and 3.13
  - Unit tests (fast feedback)
  - Integration tests (after unit passes)
  - Remaining tests (unmarked)
  - Coverage threshold: ≥60%

- **lint**: Ruff linting
- **type-check**: Mypy type checking (greenfield code only)
- **format-check**: Black formatting validation
- **pre-commit**: Pre-commit hooks validation
- **status-check**: Aggregates all job results

**Caching**:
- Pip dependencies: `~/.cache/pip` (keyed on `pyproject.toml`)
- spaCy models: `~/.cache/spacy` (keyed on spaCy version + model)

**Duration**: ~8-12 minutes total (jobs run in parallel)

### 2. Performance Regression (`.github/workflows/performance-regression.yml`)

Runs on push to main, weekly schedule (Monday 2:00 AM UTC), and manual dispatch (workflow_dispatch).

**Purpose**: Detect performance regressions before they impact users.

**Baseline** (from Story 2.5.2.1):
- Throughput: 14.57 files/min (100 PDFs in 6.86 min)
- Memory: 4.15 GB peak (batch processing)

**Thresholds** (10% regression tolerance):
- Min throughput: 13.1 files/min
- Max memory: 4.56 GB

**Runs**: `tests/performance/test_cli_benchmarks.py`

**Duration**: ~30-45 minutes (processes 100 files)

### 3. Performance Baseline (`.github/workflows/performance.yml`)

Existing performance tracking workflow (lightweight). Runs on weekly schedule and supports manual dispatch (workflow_dispatch).

## Branch Protection Rules

Main branch requires:
- ✅ Tests & Coverage (3.12)
- ✅ Linting (Ruff)
- ✅ Type Checking (Mypy)
- ✅ Format Checking (Black)
- ✅ Pre-commit Hooks
- ✅ Status Check (all jobs passed)

## Local Development

**Before pushing**, run quality checks locally:

```bash
# Quick check (recommended before every push)
pre-commit run --all-files

# Full CI mirror (before major changes)
pytest tests/ -v --cov=src
ruff check src/ tests/
mypy src/data_extract/
black --check src/ tests/
```

**Coverage threshold**: Your changes must maintain ≥60% coverage.

## Coverage Reporting

Coverage is tracked in CI and uploaded to Codecov:
- **HTML report**: Download from GitHub Actions artifacts
- **Codecov dashboard**: View trends and coverage maps

**Current coverage**: Check badge in README.md

## Performance Monitoring

Performance baselines are documented in `docs/performance-baselines-story-2.5.1.md`.

**Key metrics tracked**:
- Throughput (files/min)
- Memory usage (GB peak)
- Processing time per file type

**Regression detection**: Automated in performance-regression.yml workflow.

## Troubleshooting

### "Tests pass locally but fail in CI"

1. Check Python version: CI uses 3.12 and 3.13
2. Run tests with same markers: `pytest -m unit` then `pytest -m integration`
3. Check for test isolation issues (use `pytest -n auto` to detect)

### "Coverage below threshold"

1. Check which modules lack coverage: `coverage report --show-missing`
2. Focus on greenfield code (`src/data_extract/`) - brownfield is excluded from mypy
3. Add tests before pushing

### "Pre-commit hook failures in CI"

1. Run locally: `pre-commit run --all-files`
2. Install hooks if not present: `pre-commit install`
3. Auto-fix issues: `black src/ tests/` and `ruff check --fix src/ tests/`

### "Performance regression detected"

1. Review performance test results in Actions artifacts
2. Compare against baselines in `docs/performance-baselines-story-2.5.1.md`
3. Profile code changes: Use `scripts/profile_pipeline.py`
4. If regression is intentional (new features), update baselines with justification

## CI/CD Maturity: 80/100

**Strengths**:
- Multi-stage quality gates
- Performance regression detection
- Efficient caching (pip + spaCy)
- Fail-fast testing (unit → integration)
- Pre-commit validation

**Future enhancements** (Epic 4-5):
- Parallel test execution (pytest-xdist)
- Burn-in loop for flaky test detection
- Nightly full regression suite
- Release automation
- Artifact retention optimization

---

**Last Updated**: Story 2.5-4 (Epic 3 Readiness)
