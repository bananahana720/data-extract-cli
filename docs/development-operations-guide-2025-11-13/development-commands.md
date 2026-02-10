# Development Commands

## Code Quality Gates (Required before every commit)

Run this checklist **before committing code**:

```bash
# 1. Format code (fixes issues automatically)
black src/ tests/

# 2. Lint code (fixes many issues, shows others)
ruff check src/ tests/ --fix

# 3. Type check (must fix manually)
mypy src/data_extract/

# 4. Run tests
pytest -m "not performance" --timeout=30

# OR run all pre-commit hooks at once
pre-commit run --all-files
```

**Quality Bar:** All checks must pass (0 violations required).

## Testing

### Run All Tests

```bash
# Run complete test suite (excludes slow performance tests)
pytest -m "not performance" --timeout=30

# With HTML coverage report
pytest -m "not performance" --timeout=30 --cov=src --cov-report=html
# Open htmlcov/index.html to view detailed coverage

# Parallel execution (faster, requires pytest-xdist)
pytest -m "not performance" -n auto --timeout=30
```

### Run Tests by Category

```bash
# Unit tests only (fast, ~0.3 seconds)
pytest -m unit

# Integration tests (slower, ~10 seconds)
pytest -m integration --timeout=30

# Extraction tests
pytest -m extraction

# Processing tests
pytest -m processing

# Formatting tests
pytest -m formatting

# Pipeline tests
pytest -m pipeline

# CLI tests
pytest -m cli

# Skip slow tests
pytest -m "not slow" --timeout=30

# Skip performance tests (they may hang)
pytest -m "not performance" --timeout=30
```

### Run Specific Tests

```bash
# Run specific test file
pytest tests/unit/test_extract/test_pdf.py -v

# Run specific test function
pytest tests/unit/test_extract/test_pdf.py::test_basic_extraction -v

# Run specific test class
pytest tests/unit/test_extract/test_pdf.py::TestPDFExtraction -v

# Run with verbose output
pytest tests/ -vv

# Run with local variables on failure
pytest tests/ --showlocals

# Run with detailed traceback
pytest tests/ --tb=long

# Drop to debugger on failure
pytest tests/ --pdb

# Show print statements
pytest tests/ -s
```

### Coverage Analysis

```bash
# Generate coverage report
pytest --cov=src --cov-report=html --cov-report=term-missing -m "not performance"

# View HTML report
# Windows: start htmlcov/index.html
# macOS: open htmlcov/index.html
# Linux: xdg-open htmlcov/index.html

# Check coverage of specific module
pytest --cov=src/data_extract/extract --cov-report=term-missing
```

**Coverage Requirements:**
- **Epic 1:** >60% baseline (achieved: 88%)
- **Epic 2-4:** >80% overall
- **Epic 5:** >90% critical paths

## Code Quality

### Black (Code Formatting)

```bash
# Format code in-place (100 char line length)
black src/ tests/

# Check formatting without changes
black --check src/ tests/

# Format specific file
black src/data_extract/core.py
```

### Ruff (Linting)

```bash
# Check for linting issues
ruff check src/ tests/

# Auto-fix fixable issues
ruff check src/ tests/ --fix

# Check specific file
ruff check src/data_extract/core.py

# Show detailed error info
ruff check src/ --output-format=verbose
```

### Mypy (Type Checking)

```bash
# Type check greenfield code (strict mode)
mypy src/data_extract/

# Type check with detailed output
mypy src/data_extract/ --show-error-codes --show-error-context

# Type check specific file
mypy src/data_extract/core.py

# Note: Mypy excludes brownfield packages during migration
# See pyproject.toml [tool.mypy] section for exclusions
```

## Pre-commit Hooks

```bash
# Install hooks (one-time)
pre-commit install

# Run all hooks on all files (recommended before pushing)
pre-commit run --all-files

# Run specific hook
pre-commit run black --all-files
pre-commit run ruff --all-files
pre-commit run mypy --all-files

# Update hook versions
pre-commit autoupdate

# Uninstall hooks
pre-commit uninstall
```

## Manual Quality Check (Complete Workflow)

```bash
# This is the complete sequence to verify code before committing:

# 1. Format code
black src/ tests/

# 2. Auto-fix linting issues
ruff check src/ tests/ --fix

# 3. Check type safety
mypy src/data_extract/
# If failures, fix them manually and re-run

# 4. Run tests with coverage
pytest -m "not performance" --timeout=30 --cov=src --cov-report=term-missing

# 5. Run all pre-commit hooks
pre-commit run --all-files

# 6. Commit (hooks will run again automatically)
git add .
git commit -m "Your message"
```

## Performance Testing

```bash
# Run performance benchmarks (long-running)
pytest tests/performance/ -v

# Run specific performance test
pytest tests/performance/test_cli_benchmarks.py -v

# Run with timeout
pytest tests/performance/ --timeout=300

# Profile pipeline for bottlenecks
python scripts/profile_pipeline.py

# View performance baselines
cat docs/performance-baselines-story-2.5.1.md
```

**Note:** Performance tests may hang due to PDF processing complexity. See Troubleshooting section.

---
