# Development & Operations Guide

**Version:** 2.0
**Date:** 2025-11-13
**Project:** Data Extraction Tool
**Status:** Epic 1 Complete - Foundation Established

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Development Commands](#development-commands)
4. [Testing Strategy](#testing-strategy)
5. [CI/CD Pipeline](#cicd-pipeline)
6. [Build & Deployment](#build--deployment)
7. [Troubleshooting](#troubleshooting)
8. [Additional Resources](#additional-resources)

---

## Prerequisites

### Python Version

**Mandatory Requirement:** Python 3.12 or higher

```bash
# Verify your Python version
python --version
# Expected output: Python 3.12.x or 3.13.x
```

**Downloads:**
- **Windows**: https://www.python.org/downloads/
- **macOS**: `brew install python@3.12` or https://www.python.org/downloads/
- **Linux**: `sudo apt install python3.12` (Ubuntu/Debian) or equivalent for your distribution

### System Dependencies

#### Optional: OCR Support (pytesseract)

For processing scanned PDFs without native text, install Tesseract:

**Windows:**
1. Download installer: https://github.com/UB-Mannheim/tesseract/wiki
2. Install to default location: `C:\Program Files\Tesseract-OCR`
3. Set environment variable (optional if installed to default):
   ```bash
   set TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
   ```

**macOS:**
```bash
brew install tesseract
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt install tesseract-ocr
```

**Linux (Fedora/RHEL):**
```bash
sudo dnf install tesseract
```

#### Git

Required for version control:

**Windows/macOS:** Download from https://git-scm.com/
**Linux:** `sudo apt install git` (Ubuntu/Debian) or equivalent

### Platform Notes

- **Windows**: Primary target platform - all features tested on Windows 11
- **macOS**: Fully supported - minor differences in path handling
- **Linux**: Fully supported - tested on Ubuntu 22.04+

---

## Installation

### 1. Clone the Repository

```bash
# Clone the repository
git clone [repository-url]
cd data-extraction-tool
```

### 2. Create Virtual Environment

#### Windows

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate

# Verify activation (prompt should show "venv")
```

#### macOS/Linux

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate

# Verify activation (prompt should show "venv")
```

### 3. Install Development Dependencies

```bash
# Install in editable mode with development dependencies
pip install -e ".[dev]"

# This installs:
# - Core dependencies (pydantic, PyYAML, structlog, spacy)
# - Development tools (pytest, black, mypy, ruff, pre-commit)
# - Type stubs (types-PyYAML)
# - Performance monitoring (psutil, memory-profiler)
# - Test utilities (pytest-cov, pytest-xdist, pytest-mock)
```

### 4. Download spaCy Language Model

**Required for all chunking operations** (Epic 3+)

```bash
# Download English language model (~33-43 MB)
python -m spacy download en_core_web_md

# Verify installation
python -m spacy validate
# Expected: "✔ Loaded compatibility table"

# Test model loading
python -c "import spacy; nlp = spacy.load('en_core_web_md'); print(f'Model loaded: {nlp.meta[\"version\"]}')"
```

**Troubleshooting spaCy:**
- Model doesn't load? See `docs/troubleshooting-spacy.md`
- Behind corporate proxy? See Proxy Configuration section below
- Manual download option available in troubleshooting guide

### 5. Install Pre-commit Hooks

```bash
# Install git hooks for automatic code quality checks
pre-commit install

# Verify installation
git hooks list
# Expected: shows pre-commit hook installed
```

Pre-commit hooks enforce:
- Black formatting (100 char lines)
- Ruff linting
- Mypy type checking
- YAML syntax validation
- Large file detection

### 6. Verify Installation

```bash
# Check spaCy model
python -m spacy validate
# Expected output: "✔ Loaded compatibility table"

# Run test suite (excluding slow performance tests)
pytest -m "not performance" --timeout=30
# Expected: 900+ tests passing, coverage > 60%

# Check code formatting
black --check src/
# Expected: "All done! ✨ 🍰 ✨" or formatting issues listed

# Run linter
ruff check src/ tests/
# Expected: No output if clean, or issues listed

# Run type checker
mypy src/data_extract/
# Expected: "Success: no issues found in X source files"

# Verify CLI entry point
data-extract
# Expected: Help message or placeholder confirmation
```

### Optional: OCR Support

```bash
# Install OCR dependencies (requires Tesseract system package)
pip install -e ".[ocr]"

# Verify OCR installation
python -c "import pytesseract; print('OCR support available')"
```

### Optional: All Dependencies

```bash
# Install everything (dev + OCR)
pip install -e ".[all]"
```

---

## Development Commands

### Code Quality Gates (Required before every commit)

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

### Testing

#### Run All Tests

```bash
# Run complete test suite (excludes slow performance tests)
pytest -m "not performance" --timeout=30

# With HTML coverage report
pytest -m "not performance" --timeout=30 --cov=src --cov-report=html
# Open htmlcov/index.html to view detailed coverage

# Parallel execution (faster, requires pytest-xdist)
pytest -m "not performance" -n auto --timeout=30
```

#### Run Tests by Category

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

#### Run Specific Tests

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

#### Coverage Analysis

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

### Code Quality

#### Black (Code Formatting)

```bash
# Format code in-place (100 char line length)
black src/ tests/

# Check formatting without changes
black --check src/ tests/

# Format specific file
black src/data_extract/core.py
```

#### Ruff (Linting)

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

#### Mypy (Type Checking)

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

### Pre-commit Hooks

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

### Manual Quality Check (Complete Workflow)

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

### Performance Testing

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

## Testing Strategy

### Test Organization

Tests mirror source structure exactly:

```
tests/
├── unit/                 # Fast, isolated tests
│   ├── test_extract/
│   ├── test_normalize/
│   ├── test_chunk/
│   ├── test_semantic/
│   └── test_output/
├── integration/          # Multi-component tests
│   ├── test_pipeline_orchestration.py
│   └── test_end_to_end.py
├── performance/          # Benchmarks and stress tests
└── fixtures/             # Shared test data
```

### Test Markers

Available markers (defined in `pytest.ini`):

- `unit` - Fast unit tests (< 1s each)
- `integration` - Integration tests (< 10s each)
- `slow` - Slow running tests (> 5s)
- `performance` - Performance benchmarks (skip in CI)
- `extraction` - Extraction stage tests
- `processing` - Processing stage tests
- `formatting` - Formatting stage tests
- `pipeline` - Pipeline orchestration tests
- `cli` - Command-line interface tests
- `edge_case` - Edge cases and boundary conditions
- `stress` - Resource-intensive tests
- `infrastructure` - Infrastructure component tests
- `cross_format` - Cross-format validation

### Test Execution Strategy

**Recommended approach:**
1. Run unit tests first (fail-fast, instant feedback)
2. Run integration tests
3. Run specific test category if debugging

```bash
# Fail-fast approach (stop on first failure)
pytest -x -m "not performance" --timeout=30

# Run slow tests with longer timeout
pytest -m slow --timeout=120

# Run tests in parallel (faster)
pytest -n auto -m "not performance" --timeout=30
```

### Coverage Requirements

**Current Status (Epic 1):**
- Overall: 88% (923/1047 tests)
- Unit tests: 100% passing
- Integration tests: 71% passing
- CLI tests: 82% passing
- Extractor tests: 98% passing
- Performance tests: Disabled (PDF processing issue)

**Targets by Epic:**
- Epic 1: >60% (achieved: 88%)
- Epic 2: >80%
- Epic 3: >85%
- Epic 4: >85%
- Epic 5: >90% critical paths

### Known Test Issues

See `docs/TESTING-README.md` for complete test status and known issues.

**Quick Wins (2 hours for +2% coverage):**
- PDF path handling (15 tests)
- Tuple vs. object returns (9 tests)
- Import path correction (3 tests)

---

## CI/CD Pipeline

### GitHub Actions Workflows

#### 1. Test & Quality Checks (`.github/workflows/test.yml`)

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

#### 2. Performance Regression (`.github/workflows/performance-regression.yml`)

**Triggers:** Push to main, weekly (Monday 2:00 AM UTC), manual dispatch

**Purpose:** Detect performance regressions before deployment

**Baseline** (from Story 2.5.2):
- Throughput: 14.57 files/min (100 PDFs in 6.86 min)
- Memory: 4.15 GB peak (batch processing)

**Thresholds** (10% regression tolerance):
- Min throughput: 13.1 files/min
- Max memory: 4.56 GB

**Duration:** ~30-45 minutes

#### 3. Performance Baseline (`.github/workflows/performance.yml`)

**Triggers:** Weekly, manual dispatch

**Purpose:** Track performance metrics over time

**Duration:** Variable based on workload

### Local Development CI Checks

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

### Coverage Reporting

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

### Troubleshooting CI Failures

#### Tests pass locally but fail in CI

1. Check Python version: CI uses 3.12 and 3.13
2. Run tests with markers: `pytest -m unit` then `pytest -m integration`
3. Check for test isolation: `pytest -n auto` (parallel execution)
4. Ensure spaCy model is installed: `python -m spacy validate`

#### Coverage below threshold

1. Run coverage locally: `coverage report --show-missing`
2. Focus on greenfield code: `src/data_extract/`
3. Add missing tests before pushing

#### Pre-commit hook failures

1. Run locally: `pre-commit run --all-files`
2. Auto-fix issues:
   ```bash
   black src/ tests/
   ruff check src/ tests/ --fix
   ```
3. Fix type errors manually: `mypy src/data_extract/`

#### Performance regression detected

1. Review results in Actions artifacts
2. Compare against baselines: `docs/performance-baselines-story-2.5.1.md`
3. Profile changes: `python scripts/profile_pipeline.py`
4. Update baselines if regression is intentional (with justification)

---

## Build & Deployment

### Package Distribution

**Current Status:** Development-only (Epic 5 implements full distribution)

### Build Process

```bash
# Install build dependencies
pip install build twine

# Build distribution
python -m build

# This creates:
# - dist/data-extraction-tool-0.1.0.tar.gz (source)
# - dist/data_extraction_tool-0.1.0-py3-none-any.whl (wheel)

# Verify build
twine check dist/*
```

### CLI Entry Point

```bash
# Verify CLI is installed
which data-extract  # macOS/Linux
where data-extract  # Windows

# Test CLI
data-extract --help
data-extract --version

# The CLI loads from: src/data_extract/cli.py
# Entry point defined in: pyproject.toml [project.scripts]
```

### Local Installation for Testing

```bash
# Install package in development mode (already done with -e)
pip install -e .

# Reinstall if modified
pip install -e . --force-reinstall

# Uninstall
pip uninstall data-extraction-tool
```

### Virtual Environment Management

#### Create backup of current environment

```bash
# Generate requirements file
pip freeze > requirements.txt

# Later: recreate from requirements
pip install -r requirements.txt
```

#### Reset virtual environment

```bash
# Remove venv
rm -rf venv  # macOS/Linux
rmdir /s venv  # Windows

# Recreate and reinstall
python -m venv venv
venv\Scripts\activate  # or source venv/bin/activate
pip install -e ".[dev]"
python -m spacy download en_core_web_md
pre-commit install
```

---

## Troubleshooting

### Common Setup Issues

#### "python not found" or "python --version shows 2.x"

```bash
# Check if Python 3.12+ is installed
python3 --version
python3.12 --version

# If 3.12+ found, use explicitly
python3.12 -m venv venv
python3.12 -m pip install -e ".[dev]"
```

#### "venv not found" after activation

```bash
# Windows: venv not created
python -m venv venv

# macOS/Linux: venv not created
python3 -m venv venv

# Make sure you're in project root
cd data-extraction-tool
```

#### "pip: command not found"

```bash
# Upgrade pip
python -m pip install --upgrade pip

# Or use python -m pip instead of pip
python -m pip install -e ".[dev]"
```

#### "ImportError: No module named spacy"

```bash
# Install spaCy with specific version
pip install "spacy>=3.7.2,<4.0"

# Download model
python -m spacy download en_core_web_md

# Verify
python -c "import spacy; print(spacy.__version__)"
```

### spaCy Model Issues

See `docs/troubleshooting-spacy.md` for comprehensive spaCy troubleshooting.

**Quick fixes:**

```bash
# Model not found
python -m spacy download en_core_web_md

# Version mismatch
pip install --upgrade "spacy>=3.7.2,<4.0"
python -m spacy download en_core_web_md

# Validation
python -m spacy validate

# Manual installation if download fails
# Download from: https://github.com/explosion/spacy-models/releases
# Then: pip install path/to/en_core_web_md-3.8.0-py3-none-any.whl
```

### Code Quality Issues

#### "ruff check" reports errors

```bash
# Auto-fix most issues
ruff check src/ tests/ --fix

# Manually fix remaining issues
# See ruff output for line numbers and descriptions
```

#### "mypy" reports type errors

```bash
# Type errors must be fixed manually
mypy src/data_extract/
# See output, then fix type hints in code

# Ignore specific errors (not recommended)
# Add '# type: ignore' on problematic lines
```

#### "black" reports formatting issues

```bash
# Auto-fix formatting
black src/ tests/

# Check without fixing
black --check src/ tests/
```

### Test Issues

#### "pytest: command not found"

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Or run as module
python -m pytest
```

#### "Tests hang or timeout"

```bash
# Run with timeout
pytest --timeout=30

# Run specific test
pytest tests/unit/ -v

# Skip performance tests (they may hang)
pytest -m "not performance"

# See tests/performance/README.md for known issues
```

#### "ImportError: cannot import from src"

```bash
# Make sure you're in project root
cd data-extraction-tool

# Verify package is installed
pip install -e .

# Check Python path
python -c "import sys; print(sys.path)"
```

#### "Coverage below threshold"

```bash
# Generate detailed coverage report
pytest --cov=src --cov-report=term-missing

# Identify which modules need coverage
coverage report | grep -v "100%"

# Add missing tests
# Tests should mirror src/ structure in tests/
```

### Pre-commit Hook Issues

#### "Pre-commit hook failed"

```bash
# Check which hook failed
pre-commit run --all-files -v

# Fix the issue (usually code formatting)
black src/ tests/

# Run hooks again
pre-commit run --all-files

# Retry commit
git add .
git commit -m "message"
```

#### "Hook timeout or hangs"

```bash
# Increase timeout in .pre-commit-config.yaml if needed
# Or skip hooks temporarily (not recommended)
git commit --no-verify
```

### Platform-Specific Issues

#### Windows Path Issues

```bash
# Use forward slashes in Python code
Path("src/data_extract/core.py")  # OK
Path("src\data_extract\core.py")  # Avoid in code

# On command line, backslashes are fine
cd src\data_extract
```

#### macOS/Linux Permission Denied

```bash
# Use user-level installation
pip install --user -e ".[dev]"

# Or use sudo (not recommended)
sudo pip install -e ".[dev]"
```

#### Network/Proxy Issues (spaCy Download)

```bash
# Set proxy environment variables
export HTTP_PROXY=http://proxy.company.com:8080
export HTTPS_PROXY=http://proxy.company.com:8080

# Then download model
python -m spacy download en_core_web_md

# Alternative: manual download
# See docs/troubleshooting-spacy.md for links
```

---

## Additional Resources

### Documentation

- **Architecture**: `docs/architecture.md` - System design and ADRs
- **PRD**: `docs/PRD/index.md` - Product requirements
- **Tech Spec**: `docs/tech-spec-epic-1.md` - Epic 1 technical specification
- **Epics & Stories**: `docs/epics.md`, `docs/stories/` - Implementation roadmap
- **CI/CD**: `docs/ci-cd-pipeline.md` - Detailed CI/CD documentation
- **Testing**: `docs/TESTING-README.md` - Comprehensive test guide
- **spaCy**: `docs/troubleshooting-spacy.md` - spaCy troubleshooting
- **Performance**: `docs/performance-baselines-story-2.5.1.md` - Performance metrics

### Quick Reference

#### Common Commands Cheat Sheet

```bash
# Setup
python -m venv venv
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows
pip install -e ".[dev]"
python -m spacy download en_core_web_md
pre-commit install

# Development
black src/ tests/
ruff check src/ tests/ --fix
mypy src/data_extract/
pytest -m "not performance"
pre-commit run --all-files

# Testing
pytest                              # All tests
pytest -m unit                      # Unit only
pytest -m integration               # Integration only
pytest --cov=src --cov-report=html  # With coverage
pytest -x                           # Stop on first failure
pytest -n auto                      # Parallel
pytest tests/unit/test_extract/test_pdf.py::test_name  # Specific test

# Debugging
pytest --pdb tests/                 # Drop to debugger
pytest -vv --showlocals tests/      # Verbose with locals
pytest -s tests/                    # Show print statements
pytest --tb=long tests/             # Full tracebacks

# CI/CD Local
pre-commit run --all-files
pytest --cov=src -m "not performance"

# Cleanup
rm -rf venv __pycache__ .pytest_cache htmlcov *.egg-info
```

#### File Locations

- **Main Code**: `src/data_extract/`
- **Legacy Code**: `src/{cli,core,extractors,processors,formatters,infrastructure,pipeline}/`
- **Tests**: `tests/`
- **Configuration**: `pyproject.toml`, `pytest.ini`, `.pre-commit-config.yaml`
- **CI/CD**: `.github/workflows/`
- **Documentation**: `docs/`
- **Fixtures**: `tests/fixtures/`
- **Scripts**: `scripts/`

### External Resources

- [Python 3.12 Docs](https://docs.python.org/3.12/)
- [pytest Documentation](https://docs.pytest.org/)
- [Black Code Formatter](https://black.readthedocs.io/)
- [Ruff Linter](https://docs.astral.sh/ruff/)
- [mypy Type Checker](https://mypy.readthedocs.io/)
- [Pre-commit Framework](https://pre-commit.com/)
- [spaCy Documentation](https://spacy.io/)
- [GitHub Actions](https://docs.github.com/en/actions)
- [Pydantic v2 Docs](https://docs.pydantic.dev/latest/)

### Getting Help

1. **Setup Issues**: Review prerequisites and installation steps above
2. **Test Failures**: Check `docs/TESTING-README.md` and `docs/test-quick-wins.md`
3. **spaCy Problems**: See `docs/troubleshooting-spacy.md`
4. **Architecture Questions**: Review `docs/architecture.md` and CLAUDE.md
5. **Story Context**: Check `docs/stories/` for implementation details
6. **Performance**: See `docs/performance-baselines-story-2.5.1.md`

---

## Development Workflow Summary

### Daily Development Cycle

```bash
# 1. Start work (one-time setup)
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -e ".[dev]"

# 2. Before each coding session
source venv/bin/activate
git pull origin main

# 3. Create feature branch
git checkout -b story/X-Y-name

# 4. Develop and test (repeat)
# ... write code ...
black src/ tests/
ruff check src/ tests/ --fix
mypy src/data_extract/
pytest -m "not performance"

# 5. Before committing
pre-commit run --all-files

# 6. Commit changes
git add .
git commit -m "Descriptive message"

# 7. Push to remote
git push origin story/X-Y-name

# 8. Create pull request on GitHub
# ... tests run automatically ...
```

### Quality Gates Checklist

Before committing, verify:

- [ ] Code formatted: `black src/ tests/` ✓
- [ ] Linting passes: `ruff check src/ tests/` ✓
- [ ] Types checked: `mypy src/data_extract/` ✓
- [ ] Tests pass: `pytest -m "not performance"` ✓
- [ ] Pre-commit hooks pass: `pre-commit run --all-files` ✓
- [ ] Coverage maintained: `pytest --cov=src` > 60% ✓

**Zero violations required. No exceptions.**

---

## Version Information

**Current Versions** (as of 2025-11-13):

- Python: 3.12+ (mandatory)
- spaCy: 3.7.2+
- Pydantic: 2.x
- pytest: 8.x
- Black: 24.x
- Ruff: 0.6.x
- mypy: 1.11.x
- Pre-commit: 3.x

See `pyproject.toml` for exact pinned versions.

---

**Last Updated:** 2025-11-13
**Maintained By:** Development Team
**Epic Status:** 1 - Foundation Complete (88% test coverage achieved)
