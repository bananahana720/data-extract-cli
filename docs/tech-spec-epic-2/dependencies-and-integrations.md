# Dependencies and Integrations

## Python Dependencies

**New Dependencies for Epic 2** (add to `pyproject.toml`):

```toml
[project.dependencies]
# Existing from Epic 1
pydantic = ">=2.0.0,<3.0"
pyyaml = ">=6.0.0,<7.0"
structlog = ">=24.0.0,<25.0"

# New for Epic 2
spacy = ">=3.7.0,<3.8"           # NLP: sentence boundaries, entity recognition (Story 2.2)
textstat = ">=0.7.0,<0.8"        # Readability metrics (Story 2.6)
pillow = ">=10.0.0,<11.0"        # Image preprocessing for OCR (Story 2.4)
pytesseract = ">=0.3.0,<0.4"     # OCR confidence scoring (Story 2.4)
beautifulsoup4 = ">=4.12.0,<5.0" # Archer HTML/XML parsing (Story 2.3)
lxml = ">=5.0.0,<6.0"            # XML parser for BeautifulSoup (Story 2.3)
```

**spaCy Language Model** (system-level dependency):
```bash
# Install after pip install
python -m spacy download en_core_web_md
```

**Tesseract OCR Engine** (system-level dependency):
- **Linux**: `sudo apt-get install tesseract-ocr`
- **macOS**: `brew install tesseract`
- **Windows**: Download installer from https://github.com/UB-Mannheim/tesseract/wiki

## Dependency Details by Story

| Dependency | Version | Story | Purpose | License |
|------------|---------|-------|---------|---------|
| **spacy** | 3.7.x | 2.2 | Sentence tokenization, NER patterns, entity recognition | MIT |
| **en_core_web_md** | 3.7.x | 2.2 | spaCy language model (50MB, includes word vectors) | MIT |
| **textstat** | 0.7.x | 2.6 | Readability metrics (Flesch-Kincaid, Gunning Fog, SMOG) | MIT |
| **pytesseract** | 0.3.x | 2.4 | Tesseract OCR wrapper, confidence scoring | Apache 2.0 |
| **Pillow** | 10.x | 2.4 | Image preprocessing (deskew, denoise, contrast enhancement) | PIL License |
| **beautifulsoup4** | 4.12.x | 2.3 | HTML/XML parsing for Archer exports | MIT |
| **lxml** | 5.x | 2.3 | Fast XML parser backend for BeautifulSoup | BSD |
| **pydantic** | 2.x | All | Data validation, configuration management (already in Epic 1) | MIT |
| **pyyaml** | 6.x | 2.1 | Configuration file parsing (already in Epic 1) | MIT |
| **structlog** | 24.x | All | Structured logging for audit trail (already in Epic 1) | MIT/Apache 2.0 |

## Integration Points

**Epic 1 → Epic 2 Integration**:
- **Input**: `ExtractionResult` from `src/data_extract/extract/` stage
  - Contains `List[ContentBlock]` with raw extracted text
  - Metadata includes source file, extraction confidence, document structure
- **Output**: `ProcessingResult` to `src/data_extract/chunk/` stage (Epic 3)
  - Contains normalized `List[ContentBlock]` with cleaned text
  - Enriched metadata with quality scores, entity tags, validation reports
- **Shared**: Pipeline protocols from `src/data_extract/core/pipeline.py`
- **Shared**: Data models from `src/data_extract/core/models.py`

**Configuration Integration**:
- **Input**: Configuration cascade (CLI flags > env vars > YAML > defaults)
  - `NormalizationConfig` loaded by `src/data_extract/normalize/config.py`
  - User-editable YAML files in `config/normalize/` directory
- **Configuration Files**:
  - `config/normalize/cleaning_rules.yaml` - OCR artifact patterns, thresholds
  - `config/normalize/entity_patterns.yaml` - 6 entity type regex patterns
  - `config/normalize/entity_dictionary.yaml` - Abbreviation expansions
  - `config/normalize/schema_templates.yaml` - Document type schemas

**Brownfield Integration** (from Story 1.2 Assessment):
- **Existing Extractors**: `src/extractors/` (PDF, DOCX, XLSX, PPTX, CSV)
  - Epic 2 normalizers work with outputs from existing extractors
  - No refactoring of extractors required (maintain "ADAPT AND EXTEND" strategy)
- **Existing Data Models**: Some models may need extension for Epic 2
  - Add `EntityType`, `DocumentType`, `QualityFlag` enums
  - Extend `Metadata` with quality scores and entity tags
  - Add `CleaningResult`, `ValidationReport` models

**External System Integration**:
- **None**: Epic 2 operates on extracted content only (no external APIs)
- **File System Only**: Read input documents, write quarantine files
- **No Database**: All state in-memory per document (streaming architecture)

## Dependency Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| **spaCy model download** (en_core_web_md, 50MB) | HIGH - Required for Story 2.2 | Document in setup instructions, include in CI/CD pipeline |
| **Tesseract not installed** | HIGH - Blocks Story 2.4 OCR validation | Check for Tesseract in setup script, provide clear install instructions |
| **Version conflicts** (spaCy requires specific Python/numpy versions) | MEDIUM - May conflict with other deps | Pin compatible versions in pyproject.toml, test in CI |
| **Performance overhead** (spaCy model loading ~2 seconds) | LOW - One-time cost per batch | Lazy load model, cache in ProcessingContext |
| **Windows path issues** (Tesseract executable path) | LOW - Windows-specific | Detect Tesseract path automatically, allow override in config |

## Installation Verification

After Epic 2 dependencies installed, verify:
```bash
# Verify Python packages
pip list | grep -E "(spacy|textstat|pytesseract|pillow|beautifulsoup4|lxml)"

# Verify spaCy model
python -m spacy validate

# Verify Tesseract
tesseract --version

# Run verification script
python scripts/verify_epic2_deps.py
```
