# 5. Dependency Analysis

## 5.1 Current Dependencies (Brownfield)

**From imports and story context:**

| Package | Version | Status | Usage | Epic 1 Compatible? | Notes |
|---------|---------|--------|-------|-------------------|-------|
| **Extraction** |
| `pypdf` | >=3.0.0 | ✅ Compatible | PDF native text | ✅ YES | Modern pypdf (was PyPDF2) |
| `python-docx` | >=0.8.11 | ✅ Compatible | DOCX extraction | ✅ YES | |
| `python-pptx` | >=0.6.21 | ✅ Compatible | PPTX extraction | ✅ YES | |
| `openpyxl` | >=3.0.10 | ✅ Compatible | XLSX extraction | ✅ YES | |
| `pdfplumber` | >=0.10.0 | ✅ Compatible | PDF table extraction | ✅ YES | |
| `Pillow` | >=10.0.0 | ✅ Compatible | Image processing | ✅ YES | PIL fork |
| `pytesseract` | >=0.3.10 | ⚠️ Optional | OCR capability | ✅ YES | Requires tesseract binary |
| `pdf2image` | >=1.16.0 | ⚠️ Optional | PDF → Image for OCR | ✅ YES | Requires poppler binary |
| `chardet` | >=5.0.0 | ⚠️ Optional | CSV encoding detection | ✅ YES | Optional enhancement |
| **CLI** |
| `click` | >=8.1.0 | ⚠️ Replace | Brownfield CLI | ❌ **REPLACE with Typer** | Epic 5 migration |
| `rich` | >=13.0.0 | ✅ Compatible | Progress display | ✅ YES | Keep for Epic 5 CLI |
| **Epic 1 New Dependencies** |
| `pydantic` | >=2.0.0,<3.0 | ✅ New | Data models | ✅ YES | Required (ADR-002) |
| `PyYAML` | >=6.0.0,<7.0 | ✅ New | Config loading | ✅ YES | |
| `structlog` | >=24.0.0,<25.0 | ✅ New | Structured logging | ✅ YES | Required (ADR) |
| `typer` | >=0.12.0,<0.13 | ✅ New | CLI framework | ✅ YES | Epic 5 (replaces Click) |
| **Testing** |
| `pytest` | >=8.0.0,<9.0 | ✅ Compatible | Test framework | ✅ YES | |
| `pytest-cov` | >=4.0.0,<5.0 | ✅ Compatible | Coverage reporting | ✅ YES | |
| `black` | >=24.0.0,<25.0 | ✅ Compatible | Code formatting | ✅ YES | |
| `mypy` | >=1.11.0,<2.0 | ✅ Compatible | Type checking | ✅ YES | |
| `ruff` | >=0.6.0,<0.7 | ✅ Compatible | Linting | ✅ YES | |
| **Future Dependencies (Epic 2-4)** |
| `spacy` | >=3.7.0,<4.0 | 🔮 Planned | Entity extraction | Epic 2 | Large models |
| `nltk` | >=3.8.0,<4.0 | 🔮 Planned | Sentence tokenization | Epic 3 | Alternative to spaCy |
| `scikit-learn` | >=1.3.0,<2.0 | 🔮 Planned | TF-IDF, LSA | Epic 4 | Classical NLP |
| `textstat` | >=0.7.0,<0.8 | 🔮 Planned | Readability metrics | Epic 4 | Quality assessment |

## 5.2 Dependency Upgrade Plan

**No upgrades required for Epic 1:**
- All brownfield dependencies are compatible with Epic 1 tech spec
- Version ranges are appropriate (loose enough for flexibility, tight enough for stability)
- `python-docx`, `pypdf`, `openpyxl`, `python-pptx`, `pdfplumber` all up-to-date

**Migration required:**
- **Click → Typer** (Epic 5, Story 5.1)
  - Breaking change: Complete CLI rewrite
  - Timeline: Epic 5
  - Impact: High (entire CLI module)
  - Mitigation: Typer is Click-compatible in design, similar API

## 5.3 Dependency Conflicts & Resolutions

**No conflicts detected:**
- All dependencies are compatible with Python 3.12+ (ADR-004 requirement)
- No version conflicts between brownfield and Epic 1 dependencies
- All packages have active maintenance

**Optional dependencies:**
- `pytesseract`, `pdf2image`: OCR capability (optional feature)
- `chardet`: CSV encoding detection enhancement (graceful fallback)
- Recommendation: Document as optional in pyproject.toml extras

## 5.4 pyproject.toml Updates

**Current state (from Story 1.1):**
- Epic 1 dependencies already added
- Version ranges properly pinned
- All brownfield dependencies preserved

**Required updates:**
- ❌ None for Epic 1
- ⚠️ Epic 2: Add spaCy/nltk when implementing entity extraction
- ⚠️ Epic 4: Add scikit-learn, textstat for semantic analysis

## 5.5 External Binary Dependencies

**Required binaries (not Python packages):**
1. **Tesseract OCR** (for pytesseract)
   - Required for: FR-E2 (OCR for Scanned Documents)
   - Installation: `brew install tesseract` (macOS), `apt-get install tesseract-ocr` (Ubuntu)
   - Configuration: `tesseract_cmd` in config or env var

2. **Poppler** (for pdf2image)
   - Required for: PDF → Image conversion for OCR
   - Installation: `brew install poppler` (macOS), `apt-get install poppler-utils` (Ubuntu)
   - Configuration: `poppler_path` in config or env var

**Documentation needed:**
- **Story 1.3:** Update README.md with binary dependency instructions
- **Story 1.3:** Add troubleshooting guide for OCR setup

---
