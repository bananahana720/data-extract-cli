# CI/CD Pipeline

## GitHub Actions Workflows

### 1. Test & Quality Checks (`.github/workflows/test.yml`)

**Triggers:** Every push, pull request

**Jobs:**
- **test**: Runs pytest with coverage (Python 3.12, 3.13)
  - Unit tests first (fail-fast)
  - Integration tests
  - Remaining tests
  - Coverage threshold: ≥60%

- **lint**: Ruff linting checks
- **type-check**: Mypy type checking (greenfield code only)
- **format-check**: Black formatting validation
- **pre-commit**: All pre-commit hooks validation
- **status-check**: Aggregates all job results

**Caching:**
- Pip dependencies: keyed on `pyproject.toml`
- spaCy models: keyed on spaCy version + model version

**Duration:** ~8-12 minutes (jobs run in parallel)

**Branch Protection Rules (Main):**
- ✅ All tests passed (3.12)
- ✅ Linting passed (Ruff)
- ✅ Type checking passed (Mypy)
- ✅ Format checking passed (Black)
- ✅ Pre-commit hooks passed
- ✅ Status check passed (all jobs)

### 2. Performance Regression (`.github/workflows/performance-regression.yml`)

**Triggers:** Push to main, weekly (Monday 2:00 AM UTC), manual dispatch

**Purpose:** Detect performance regressions before deployment

**Baseline** (from Story 2.5.2):
- Throughput: 14.57 files/min (100 PDFs in 6.86 min)
- Memory: 4.15 GB peak (batch processing)

**Thresholds** (10% regression tolerance):
- Min throughput: 13.1 files/min
- Max memory: 4.56 GB

**Duration:** ~30-45 minutes

### 3. Performance Baseline (`.github/workflows/performance.yml`)

**Triggers:** Weekly, manual dispatch

**Purpose:** Track performance metrics over time

**Duration:** Variable based on workload

## Local Development CI Checks

**Before every push, run locally:**

```bash
# Quick check (2 minutes)
pre-commit run --all-files

# Full CI mirror (5 minutes)
pytest tests/ -v --cov=src
ruff check src/ tests/
mypy src/data_extract/
black --check src/ tests/
```

## Coverage Reporting

- **Local:** HTML report at `htmlcov/index.html`
- **CI:** Uploaded to Codecov
- **Threshold:** ≥60% enforced by CI

**Coverage by Module Target:**
```
src/data_extract/core/       - 100%
src/data_extract/extract/    - 85%+
src/data_extract/normalize/  - 80%+
src/data_extract/chunk/      - 80%+
src/data_extract/output/     - 80%+
src/data_extract/semantic/   - 75%+
```

## Troubleshooting CI Failures

### Tests pass locally but fail in CI

1. Check Python version: CI uses 3.12 and 3.13
2. Run tests with markers: `pytest -m unit` then `pytest -m integration`
3. Check for test isolation: `pytest -n auto` (parallel execution)
4. Ensure spaCy model is installed: `python -m spacy validate`

### Coverage below threshold

1. Run coverage locally: `coverage report --show-missing`
2. Focus on greenfield code: `src/data_extract/`
3. Add missing tests before pushing

### Pre-commit hook failures

1. Run locally: `pre-commit run --all-files`
2. Auto-fix issues:
   ```bash
   black src/ tests/
   ruff check src/ tests/ --fix
   ```
3. Fix type errors manually: `mypy src/data_extract/`

### Performance regression detected

1. Review results in Actions artifacts
2. Compare against baselines: `docs/performance-baselines-story-2.5.1.md`
3. Profile changes: `python scripts/profile_pipeline.py`
4. Update baselines if regression is intentional (with justification)

---
