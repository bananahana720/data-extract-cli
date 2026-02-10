# Project Initialization

This is a **brownfield project** with existing extraction capabilities. The architecture builds on this foundation:

## Existing Foundation (Assessed)
- Document extraction infrastructure (PyMuPDF, python-docx, pytesseract)
- Basic text processing and structure preservation
- Initial output generation

## New Architecture Integration
Rather than a fresh starter template, we'll refactor existing code into the new modular pipeline architecture defined below. Story 1.2 (Brownfield Assessment) will map existing code to new structure.

## Development Setup
```bash
# Python 3.12 virtual environment
python3.12 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install with pinned dependencies
pip install -e ".[dev]"

# Pre-commit hooks for code quality
pre-commit install
```
