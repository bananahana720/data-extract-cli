# Development & Operations Guide

**Generated**: 2025-11-13
**Project**: Data Extraction Tool v0.1.0
**Audience**: Developers, Contributors, DevOps

---

## Quick Start

```bash
# 1. Clone and setup
git clone [repository-url]
cd data-extraction-tool-1
python -m venv venv
venv\Scripts\activate  # Windows
pip install -e ".[dev]"

# 2. Install pre-commit hooks
pre-commit install

# 3. Install spaCy model
python -m spacy download en_core_web_md

# 4. Run tests
pytest

# You're ready to develop!
```

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Development Workflow](#development-workflow)
4. [Testing Strategy](#testing-strategy)
5. [Code Quality](#code-quality)
6. [CI/CD Pipeline](#cicd-pipeline)
7. [Contribution Guidelines](#contribution-guidelines)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required

| Component | Minimum | Recommended | Purpose |
|-----------|---------|-------------|---------|
| **Python** | 3.12.0 | 3.13.x | Primary language (mandatory enterprise requirement) |
| **Git** | 2.0+ | Latest | Version control |
| **pip** | Latest | Latest | Package management |

### Optional

| Component | Purpose | Installation |
|-----------|---------|--------------|
| **Tesseract** | OCR support | [tesseract-ocr.github.io](https://tesseract-ocr.github.io/) |
| **Poppler** | PDF → Image conversion | [poppler.freedesktop.org](https://poppler.freedesktop.org/) |
| **tmux** | UAT workflow testing | `sudo apt install tmux` (Linux/WSL) |

### Verify Prerequisites

```bash
# Check Python version (must be 3.12+)
python --version
# Output: Python 3.12.x or 3.13.x

# Check Git
git --version

# Check pip
pip --version
```

**Enterprise Constraint**: Python 3.12+ is **mandatory**. Do not downgrade.

---

## Installation

### 1. Clone Repository

```bash
git clone [repository-url]
cd data-extraction-tool-1
```

### 2. Create Virtual Environment

**Windows**:
```bash
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux**:
```bash
python -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

**Core + Development Tools**:
```bash
pip install -e ".[dev]"
```

This installs:
- Core dependencies (Pydantic, PyYAML, python-docx, pypdf, etc.)
- Testing tools (pytest, pytest-cov, pytest-xdist, pytest-mock)
- Code quality tools (black, ruff, mypy, pre-commit)
- Development utilities (psutil, memory-profiler, reportlab)

**With OCR Support** (optional):
```bash
pip install -e ".[ocr]"
```

Requires system dependencies:
- Tesseract OCR binary
- Poppler (for pdf2image)

**All Dependencies**:
```bash
pip install -e ".[all]"  # Core + dev + OCR
```

### 4. Install Pre-commit Hooks

**Critical**: This enforces code quality before every commit.

```bash
pre-commit install
```

Pre-commit will now automatically run on `git commit`:
- Black (code formatting)
- Ruff (linting)
- Mypy (type checking on greenfield code)
- YAML syntax validation
- Trailing whitespace removal
- Debug statement detection

### 5. Install spaCy Language Model

**Required for Epic 3** (chunking with sentence boundary detection):

```bash
# Download model (43MB, one-time)
python -m spacy download en_core_web_md

# Verify installation
python -m spacy validate

# Test in Python
python -c "import spacy; nlp = spacy.load('en_core_web_md'); print(f'Model: {nlp.meta[\"version\"]}')"
```

**Performance**: Model loads in ~1.2s, processes 4000+ words/sec.

**Troubleshooting**: See `docs/troubleshooting-spacy.md`

---

## Development Workflow

### Project Structure

```
src/
├── data_extract/          # Greenfield (modern architecture)
│   ├── extract/           # Document extractors
│   ├── normalize/         # Text normalization
│   ├── chunk/             # Semantic chunking
│   ├── semantic/          # Classical NLP
│   └── output/            # Output formatters
│
└── {cli,core,extractors,processors,formatters,infrastructure,pipeline}/
                          # Brownfield (legacy, maintenance mode)
```

### Branch Strategy

**Main Branches**:
- `main` - Production-ready code (protected)
- `develop` - Integration branch (optional)

**Feature Branches**:
```bash
git checkout -b feature/your-feature-name
```

**Branch Naming**:
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation updates
- `refactor/` - Code refactoring
- `test/` - Test improvements

### Development Cycle

```bash
# 1. Create feature branch
git checkout -b feature/my-feature

# 2. Make changes
# ... edit code ...

# 3. Run pre-commit checks manually (optional, runs on commit)
pre-commit run --all-files

# 4. Run tests
pytest

# 5. Commit (pre-commit hooks run automatically)
git add .
git commit -m "feat: add my feature"

# 6. Push
git push origin feature/my-feature

# 7. Create pull request on GitHub
```

### Code Organization

**Greenfield (New Code)**: `src/data_extract/`
- ✅ Strict mypy type checking
- ✅ >80% coverage target
- ✅ Epic-based development (1→2→3→4→5)

**Brownfield (Legacy)**: `src/{cli,extractors,processors,formatters,core,pipeline,infrastructure}/`
- ⚠️ Maintenance mode (Stories 1.2-1.4)
- ⚠️ Type checking excluded during migration
- ⚠️ >60% coverage baseline

**When to use which**:
- **New features**: Always use greenfield (`src/data_extract/`)
- **Bug fixes**: Fix in brownfield if that's where the bug is
- **Infrastructure**: Use `src/infrastructure/` (shared by both)

---

## Testing Strategy

### Test Organization

Tests mirror `src/` structure exactly:

```
tests/
├── unit/                  # Fast, isolated tests
│   ├── test_data_extract/ # Greenfield tests
│   └── test_extractors/   # Brownfield tests
├── integration/           # Multi-component tests
├── performance/           # Benchmarks
└── fixtures/              # Test data
```

### Running Tests

**All Tests**:
```bash
pytest
```

**By Category** (using markers):
```bash
pytest -m unit              # Fast unit tests only
pytest -m integration       # Integration tests
pytest -m performance       # Performance benchmarks
pytest -m "not slow"        # Skip slow tests
```

**Specific Test File**:
```bash
pytest tests/unit/test_extract/test_pdf.py
```

**Specific Test Function**:
```bash
pytest tests/unit/test_extract/test_pdf.py::test_basic_extraction
```

**With Coverage**:
```bash
pytest --cov=src --cov-report=html
# View: open htmlcov/index.html
```

**Parallel Execution**:
```bash
pytest -n auto  # Auto-detect CPU cores
pytest -n 4     # Use 4 workers
```

**Debug Mode**:
```bash
pytest --pdb tests/unit/test_name.py        # Drop to debugger on failure
pytest -vv --showlocals tests/unit/test.py  # Verbose with variables
pytest -s tests/unit/test.py                 # Show print statements
```

### Test Markers

| Marker | Purpose | Example |
|--------|---------|---------|
| `unit` | Fast, isolated tests | `@pytest.mark.unit` |
| `integration` | Multi-component tests | `@pytest.mark.integration` |
| `performance` | Benchmarks | `@pytest.mark.performance` |
| `slow` | Long-running tests | `@pytest.mark.slow` |

**Usage in Code**:
```python
import pytest

@pytest.mark.unit
def test_fast_unit():
    assert 1 + 1 == 2

@pytest.mark.integration
@pytest.mark.slow
def test_full_pipeline():
    # ... complex integration test ...
    pass
```

### Coverage Requirements

| Epic | Threshold | Status |
|------|-----------|--------|
| Epic 1 | >60% | ✅ Enforced in CI |
| Epic 2-4 | >80% | 🎯 Target |
| Epic 5 | >90% (critical paths) | 📋 Planned |

**Check Coverage**:
```bash
pytest --cov=src --cov-report=term-missing
# Shows which lines are not covered
```

---

## Code Quality

### Automated Quality Checks

Quality is enforced at three levels:
1. **Local**: Pre-commit hooks (on every commit)
2. **CI**: GitHub Actions (on every push/PR)
3. **Manual**: Developer-initiated checks

### Pre-commit Hooks

Automatically run on `git commit`:

| Hook | Purpose | Fix |
|------|---------|-----|
| **black** | Code formatting (100 char lines) | Auto-fix |
| **ruff** | Linting (replaces flake8 + isort) | Auto-fix |
| **mypy** | Static type checking (greenfield only) | Manual fix |
| **trailing-whitespace** | Remove trailing spaces | Auto-fix |
| **end-of-file-fixer** | Ensure files end with newline | Auto-fix |
| **check-yaml** | YAML syntax validation | Manual fix |
| **check-large-files** | Block files >1MB | Manual fix |
| **debug-statements** | Detect `import pdb`, `breakpoint()` | Manual fix |

**Manual Pre-commit Run**:
```bash
# Run all hooks on all files
pre-commit run --all-files

# Run specific hook
pre-commit run black --all-files
pre-commit run mypy --all-files
```

### Black (Code Formatting)

**Configuration**: `pyproject.toml`
```toml
[tool.black]
line-length = 100
target-version = ['py312']
```

**Manual Run**:
```bash
# Format all code
black src/ tests/

# Check without modifying
black --check src/ tests/
```

**Pre-commit**: ✅ Runs automatically on commit

### Ruff (Linting)

**Configuration**: `pyproject.toml`
```toml
[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W"]
ignore = ["E501"]  # Line too long (handled by black)
```

**Manual Run**:
```bash
# Lint with auto-fix
ruff check --fix src/ tests/

# Check without modifying
ruff check src/ tests/
```

**Pre-commit**: ✅ Runs automatically with `--fix`

### Mypy (Type Checking)

**Configuration**: `pyproject.toml`
```toml
[tool.mypy]
python_version = "3.12"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
exclude = [
    "src/(cli|extractors|processors|formatters|core|pipeline|infrastructure)/",
]
```

**Scope**:
- ✅ **Strict** on greenfield (`src/data_extract/`)
- ⚠️ **Excluded** on brownfield (during migration)

**Manual Run**:
```bash
# Type check greenfield code (must run from project root)
mypy src/data_extract/
```

**Common Fixes**:
```python
# Add type hints
def process_file(path: str) -> ProcessingResult:
    ...

# Import types
from typing import List, Dict, Optional

# Use Pydantic for validation
from pydantic import BaseModel

class Config(BaseModel):
    name: str
    value: int
```

**Pre-commit**: ✅ Runs automatically (greenfield only)

### Quality Checklist (Before PR)

```bash
# 1. Format code
black src/ tests/

# 2. Lint code
ruff check --fix src/ tests/

# 3. Type check (from project root)
mypy src/data_extract/

# 4. Run tests
pytest

# 5. Check coverage
pytest --cov=src --cov-report=term-missing

# 6. Run all pre-commit hooks
pre-commit run --all-files

# If all pass, you're ready to commit!
```

---

## CI/CD Pipeline

### GitHub Actions Workflows

**Location**: `.github/workflows/`

#### 1. Test & Quality Checks (`test.yml`)

**Triggers**:
- Every push to `main`, `develop`, `feature/**`
- Every pull request to `main`, `develop`

**Matrix**: Python 3.12, 3.13

**Steps**:
1. Checkout code
2. Set up Python (3.12 or 3.13)
3. Cache pip dependencies
4. Cache spaCy models (transparent caching)
5. Install dependencies (`pip install -e ".[dev]"`)
6. Download spaCy model (`en_core_web_md`)
7. Run unit tests with coverage
8. Run integration tests (append coverage)
9. Check coverage threshold (>60%)
10. Upload coverage to Codecov (if configured)

**Coverage Enforcement**: Fails if coverage < 60%

#### 2. Performance Regression (`performance-regression.yml`)

**Triggers**:
- Push to `main`
- Weekly schedule (Monday 2am UTC)
- Manual trigger (`workflow_dispatch`)

**Timeout**: 60 minutes

**Steps**:
1. Checkout code
2. Set up Python 3.12
3. Cache dependencies + spaCy models
4. Install dependencies
5. Download spaCy model
6. Run performance tests
7. Load performance baselines (`tests/performance/baselines.json`)
8. Compare current vs. baseline
9. Fail if regression detected (>10% slower)
10. Generate performance report

**Baselines**: Established in Story 2.5.1

#### 3. Performance Benchmarks (`performance.yml`)

**Purpose**: Update performance baselines
**Trigger**: Manual only
**Scope**: Full benchmark suite

### CI/CD Best Practices

**spaCy Model Caching**:
```yaml
- name: Cache spaCy models
  uses: actions/cache@v4
  with:
    path: ~/.cache/spacy
    key: ${{ runner.os }}-spacy-3.7.2-en_core_web_md
```
✅ **Transparent**: Developers don't need to manage caching

**Pip Dependency Caching**:
```yaml
- name: Cache dependencies
  uses: actions/cache@v4
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('pyproject.toml') }}
```
✅ **Fast CI**: Avoids re-downloading dependencies every run

**Pre-commit in CI**:
- ✅ Same hooks run locally and in CI
- ✅ Ensures consistency
- ✅ Catches issues before merge

### Deployment

**Status**: No automated deployment (CLI tool)
**Distribution**: Manual installation via `pip install -e .`
**Future** (Epic 5):
- PyPI package publication
- Automated releases
- Version tagging

---

## Contribution Guidelines

### Code Style

1. **Follow PEP 8** (enforced by Black + Ruff)
2. **100-character line length** (not 79)
3. **Type hints required** on all public functions (greenfield)
4. **Docstrings required** on public APIs (Google style)

**Example**:
```python
def extract_pdf(file_path: str, options: ExtractionOptions) -> ExtractionResult:
    """Extract text and tables from a PDF file.

    Args:
        file_path: Path to PDF file
        options: Extraction configuration options

    Returns:
        ExtractionResult with extracted content blocks

    Raises:
        FileNotFoundError: If PDF file doesn't exist
        ExtractionError: If extraction fails
    """
    ...
```

### Commit Messages

**Format**: `<type>: <description>`

**Types**:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation
- `style:` - Formatting (no code change)
- `refactor:` - Code restructuring
- `test:` - Adding tests
- `chore:` - Build/tooling changes

**Examples**:
```
feat: add spaCy integration for sentence boundary detection
fix: resolve PDF table extraction edge case
docs: update installation guide with Python 3.13 support
test: add integration test for batch processing
chore: update black to 24.10.0
```

### Pull Request Process

1. **Create feature branch** from `main`
2. **Implement changes** with tests
3. **Run quality checks** locally (`pre-commit run --all-files`)
4. **Ensure tests pass** (`pytest`)
5. **Check coverage** (`pytest --cov=src`)
6. **Push branch** and **create PR**
7. **Wait for CI** (all checks must pass)
8. **Code review** (if team workflow)
9. **Merge** when approved and green

### Testing Requirements

**All PRs must include**:
- ✅ Unit tests for new code
- ✅ Integration tests for new features
- ✅ Coverage maintained or improved
- ✅ All existing tests pass

**Test Quality**:
- Use descriptive test names (`test_pdf_extractor_handles_scanned_pdfs`)
- One assertion focus per test
- Use fixtures for common test data
- Mock external dependencies

### Documentation Requirements

**Update documentation when**:
- Adding new features
- Changing APIs
- Modifying configuration
- Updating dependencies

**Files to update**:
- `README.md` - For user-facing changes
- `CLAUDE.md` - For development guidance
- `docs/` - For detailed documentation
- Docstrings - For code documentation

---

## Troubleshooting

### Common Issues

#### spaCy Model Not Found

**Error**: `OSError: [E050] Can't find model 'en_core_web_md'`

**Solution**:
```bash
python -m spacy download en_core_web_md
python -m spacy validate
```

**Details**: See `docs/troubleshooting-spacy.md`

#### Pre-commit Hook Failures

**Error**: `black failed`, `ruff failed`, `mypy failed`

**Solution**:
```bash
# Let pre-commit auto-fix what it can
git add .
git commit  # Hooks will auto-fix and abort

# Review auto-fixes
git diff

# Re-commit
git add .
git commit
```

For mypy failures, manually fix type issues.

#### Test Failures

**Check**:
1. Did you install dev dependencies? (`pip install -e ".[dev]"`)
2. Did you download spaCy model?
3. Is your Python version 3.12+?

**Debug**:
```bash
pytest -vv --showlocals --pdb tests/path/to/failing_test.py
```

#### Coverage Below Threshold

**Error**: `coverage: total of 58% is less than fail-under=60%`

**Solution**: Add tests to increase coverage
```bash
# See uncovered lines
pytest --cov=src --cov-report=term-missing

# Focus on uncovered files/lines
```

---

## Performance Profiling

### Memory Profiling

**Story 2.5.1** established performance baselines.

**Profile Pipeline**:
```bash
python scripts/profile_pipeline.py
```

**Line-by-line Memory**:
```bash
# Requires memory-profiler
python -m memory_profiler scripts/your_script.py
```

### Benchmark Tests

**Run Benchmarks**:
```bash
pytest tests/performance/ -v
```

**Baselines**: `tests/performance/baselines.json`

---

## Environment Variables

**Supported**:
- `DATA_EXTRACT_*` prefix (Epic 5 configuration cascade)

**Example** (`.env` file):
```bash
DATA_EXTRACT_LOG_LEVEL=DEBUG
DATA_EXTRACT_OUTPUT_DIR=./output
```

**Loading** (Epic 5):
```bash
pip install python-dotenv
```

---

## Additional Resources

### Documentation
- **User Guide**: `docs/USER_GUIDE.md`
- **Architecture**: `docs/architecture.md`
- **API Reference**: `docs/architecture/QUICK_REFERENCE.md`
- **Error Handling**: `docs/ERROR_HANDLING_GUIDE.md`
- **Logging**: `docs/LOGGING_GUIDE.md`
- **Configuration**: `docs/CONFIG_GUIDE.md`
- **Infrastructure**: `docs/INFRASTRUCTURE_INTEGRATION_GUIDE.md`

### BMAD Workflows
- **Story Creation**: `/bmad:bmm:workflows:create-story`
- **Code Review**: `/bmad:bmm:workflows:code-review`
- **UAT Testing**: `/bmad:bmm:workflows:execute-tests`

### Community
- **Issues**: [GitHub Issues](repository-url/issues)
- **Discussions**: [GitHub Discussions](repository-url/discussions) (if enabled)

---

## Quick Reference

### Essential Commands

```bash
# Setup
pip install -e ".[dev]"
pre-commit install
python -m spacy download en_core_web_md

# Development
pytest                          # Run all tests
pytest -m unit                  # Unit tests only
pre-commit run --all-files      # Quality checks
black src/ tests/               # Format code
ruff check --fix src/           # Lint code
mypy src/data_extract/          # Type check

# Debugging
pytest --pdb                    # Debug on failure
pytest -vv --showlocals         # Verbose output
pytest --cov=src --cov-report=html  # Coverage report
```

### File Locations

| Purpose | Location |
|---------|----------|
| Source code (greenfield) | `src/data_extract/` |
| Source code (brownfield) | `src/{cli,extractors,processors,...}` |
| Tests | `tests/` |
| Documentation | `docs/` |
| Configuration | `pyproject.toml`, `config/` |
| CI/CD | `.github/workflows/` |
| Pre-commit | `.pre-commit-config.yaml` |
| BMAD workflows | `bmad/bmm/workflows/` |

---

**Guide Status**: ✅ Complete
**Last Updated**: 2025-11-13
**Next Review**: Epic 5 (configuration cascade, deployment)
