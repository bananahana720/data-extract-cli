# Installation

## 1. Clone the Repository

```bash
# Clone the repository
git clone [repository-url]
cd data-extraction-tool
```

## 2. Create Virtual Environment

### Windows

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate

# Verify activation (prompt should show "venv")
```

### macOS/Linux

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate

# Verify activation (prompt should show "venv")
```

## 3. Install Development Dependencies

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

## 4. Download spaCy Language Model

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

## 5. Install Pre-commit Hooks

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

## 6. Verify Installation

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

## Optional: OCR Support

```bash
# Install OCR dependencies (requires Tesseract system package)
pip install -e ".[ocr]"

# Verify OCR installation
python -c "import pytesseract; print('OCR support available')"
```

## Optional: All Dependencies

```bash
# Install everything (dev + OCR)
pip install -e ".[all]"
```

---
