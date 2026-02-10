# AI Data Extractor v1.0.6 Implementation Summary

**Version**: 1.0.5 → 1.0.6
**Features**: DOCX Image Extraction + CSV File Support
**Date**: 2025-11-06
**Estimated Effort**: ~5.5 hours (parallelized)
**Risk Level**: LOW

---

## 1. Executive Overview

### What We're Building

Two new extraction capabilities:

1. **DOCX Image Extraction**: Extract embedded images from Word documents with metadata (format, dimensions, alt text)
2. **CSV Extractor**: Full support for CSV/TSV files with auto-detection of delimiters, encodings, and headers

### Why This Matters

- **Format Coverage**: Completes common office format support (CSV is ubiquitous in data workflows)
- **Feature Parity**: DOCX extractor already handles text and tables; images are the missing piece
- **User Demand**: CSVs are frequently requested, DOCX images marked TODO since v1.0.0

### Technical Approach

Multi-agent orchestration with parallel development streams:

- Leverage proven patterns from v1.0.4 (PPTX images) and v1.0.5
- Both features implement existing BaseExtractor interface
- No breaking changes to 778 existing tests
- Infrastructure (tables, images, pipeline) already exists
- TDD approach with ≥85% coverage target

### Timeline

**Total**: ~5.5 hours with parallelization (6.5 hours sequential)

- Phase 1: Discovery & Design (50 min)
- Phase 2: Interface Protocol (15 min)
- Phase 3: Implementation (2 hours, parallel)
- Phase 4: Integration (1 hour)
- Phase 5: Validation & Packaging (1 hour)

### Risk Assessment

**LOW RISK** because:
- Following established patterns (v1.0.4 PPTX images, v1.0.5 conventions)
- No core refactoring required
- Independent features (no cross-dependencies)
- Comprehensive validation at 4 checkpoints
- Regression prevention via existing test suite

---

## 2. Feature Specifications

### 2.1 DOCX Image Extraction

#### Current State
- DocxExtractor exists in `src/extractors/docx_extractor.py`
- Text extraction: ✅ Working
- Table extraction: ✅ Working (v1.0.5)
- Image extraction: ❌ Marked TODO

#### Target State
Extract embedded images from DOCX files with complete metadata.

#### Technical Details

**Implementation**:
```python
# New method in DocxExtractor
def _extract_image_metadata(self) -> tuple[ImageMetadata, ...]:
    """Extract embedded images using python-docx API."""
    images = []

    # Iterate through inline shapes (embedded images)
    for shape in self.document.inline_shapes:
        if shape.type == WD_INLINE_SHAPE.PICTURE:
            image_data = shape._inline.graphic.graphicData.pic.blipFill.blip.embed
            image_part = self.document.part.related_parts[image_data]

            images.append(ImageMetadata(
                image_id=len(images),
                content_type=image_part.content_type,  # e.g., "image/png"
                width=shape.width,
                height=shape.height,
                data=base64.b64encode(image_part.blob).decode('utf-8'),
                alt_text=shape._inline.docPr.name or "",
                slide_number=None,  # Not applicable for DOCX
                position_x=None,    # Inline with text flow
                position_y=None
            ))

    return tuple(images)
```

**API Used**: `python-docx` library (already installed)
- Access via `Document.inline_shapes`
- Image data in `shape._inline.graphic.graphicData.pic.blipFill.blip`
- Binary data from `image_part.blob`

**Data Flow**:
```
DOCX file → python-docx parser → inline_shapes
  → ImageMetadata(base64 encoded)
  → ExtractionResult.images
  → Pipeline processors
  → JSON/HTML formatters (image data preserved)
```

**Configuration**:
```yaml
extractors:
  docx:
    extract_images: true          # Enable/disable (default: true)
    max_paragraph_length: null    # Existing option
```

**Error Handling**:
- Missing image data: Log warning, skip image, continue extraction
- Corrupted image: Log error, populate partial metadata
- Unknown format: Log warning, extract as binary blob
- Empty document: Return empty tuple, no errors

**Pattern Source**: PPTX image extraction (v1.0.4) - proven to work with 100% success rate

#### Integration Points

**No Changes Required**:
- `ImageMetadata` dataclass: Already exists
- Pipeline processors: Already handle images
- JSON formatter: Already serializes images
- HTML formatter: Already renders images

**Changes Required**:
- DocxExtractor: Add `_extract_image_metadata()` method
- DocxExtractor: Call method in `extract()` and populate result
- Tests: Add image extraction test cases

---

### 2.2 CSV Extractor

#### Current State
- No CSV support
- Users must convert CSV → XLSX to process

#### Target State
Native CSV/TSV file support with intelligent parsing.

#### Technical Details

**Implementation**:
```python
class CSVExtractor(BaseExtractor):
    """Extract structured data from CSV/TSV files."""

    def __init__(self, config: dict):
        super().__init__(config)
        self.max_rows = config.get('max_rows')
        self.delimiter = config.get('delimiter')  # None = auto-detect
        self.encoding = config.get('encoding')    # None = auto-detect
        self.has_header = config.get('has_header', True)

    def extract(self, file_path: Path) -> ExtractionResult:
        """Extract CSV as TableMetadata."""
        # 1. Detect encoding (UTF-8 → Latin-1 → fallback)
        encoding = self._detect_encoding(file_path)

        # 2. Detect delimiter (comma, tab, semicolon)
        delimiter = self._detect_delimiter(file_path, encoding)

        # 3. Parse CSV using stdlib csv.reader
        rows = self._parse_csv(file_path, encoding, delimiter)

        # 4. Extract headers (first row or generate)
        headers = self._extract_headers(rows)

        # 5. Build TableMetadata
        table = TableMetadata(
            table_id=0,
            headers=headers,
            rows=tuple(rows[1:] if self.has_header else rows),
            caption=file_path.stem,
            page_number=None  # Not applicable
        )

        return ExtractionResult(
            content_blocks=tuple(),  # CSV is pure tabular data
            images=tuple(),
            tables=(table,),
            metadata={"encoding": encoding, "delimiter": delimiter},
            success=True,
            errors=tuple()
        )

    def supports_format(self, file_path: Path) -> bool:
        return file_path.suffix.lower() in ['.csv', '.tsv']

    def get_supported_extensions(self) -> list[str]:
        return ['.csv', '.tsv']
```

**Auto-Detection Strategy**:

1. **Encoding Detection**:
   ```python
   def _detect_encoding(self, file_path: Path) -> str:
       # Try UTF-8 first (most common)
       try:
           file_path.read_text(encoding='utf-8')
           return 'utf-8'
       except UnicodeDecodeError:
           pass

       # Fallback to Latin-1 (never fails)
       return 'latin-1'
   ```

2. **Delimiter Detection**:
   ```python
   def _detect_delimiter(self, file_path: Path, encoding: str) -> str:
       # Use csv.Sniffer on first 1KB
       sample = file_path.read_text(encoding=encoding, errors='ignore')[:1024]
       sniffer = csv.Sniffer()
       return sniffer.sniff(sample).delimiter
   ```

3. **Header Detection**:
   - If `has_header=True`: Use first row as column names
   - If `has_header=False`: Generate names (Column_1, Column_2, ...)
   - Heuristic: First row has different data type distribution than others

**Configuration**:
```yaml
extractors:
  csv:
    max_rows: null                 # Limit rows (null = unlimited)
    delimiter: null                # Force delimiter (null = auto)
    encoding: null                 # Force encoding (null = auto)
    has_header: true               # First row is header
    skip_empty_rows: true          # Ignore blank rows
```

**Error Handling**:
- Encoding errors: Try fallback chain, use `errors='replace'` if all fail
- Malformed rows: Log warning, pad with empty strings or truncate
- Empty file: Return empty TableMetadata with warning
- Inconsistent columns: Use max column count, pad short rows

**Data Model Decision** (to be finalized in Phase 1):

**Option A** (Recommended): CSV → Single TABLE ContentBlock
```python
tables=(TableMetadata(...),)
content_blocks=tuple()  # Empty - CSV is pure tabular
```

**Option B**: CSV → Multiple TEXT ContentBlocks (one per row)
```python
content_blocks=(
    ContentBlock(content="Row 1 data", ...),
    ContentBlock(content="Row 2 data", ...),
)
```

**Phase 1 will evaluate and document rationale.**

#### Integration Points

**No Changes Required**:
- `TableMetadata` dataclass: Already exists
- Pipeline processors: Already handle tables
- Formatters: Already serialize tables

**Changes Required**:
- New file: `src/extractors/csv_extractor.py`
- Pipeline: Register CSV extractor in factory
- Config: Add CSV section to default config
- Tests: Comprehensive CSV test suite

---

## 3. Architectural Approach

### Design Principles

Both features strictly follow established patterns:

**SOLID Compliance**:
- **Single Responsibility**: CSVExtractor only parses CSV, DocxExtractor only handles DOCX
- **Open/Closed**: Extend via BaseExtractor, no modifications to core pipeline
- **Liskov Substitution**: Both extractors fully implement BaseExtractor interface
- **Interface Segregation**: Use only required methods from dependencies
- **Dependency Inversion**: Depend on abstractions (BaseExtractor) not concrete classes

**Immutability**:
- All dataclasses frozen (`@dataclass(frozen=True)`)
- Return tuples, not lists
- No mutations of ExtractionResult after creation

**Modularity**:
- Features are independent (separate files, no shared state)
- Can be developed in parallel
- Can be tested in isolation
- Can be enabled/disabled via config

**Extensibility**:
- Follow BaseExtractor contract exactly
- Use existing dataclasses (ImageMetadata, TableMetadata)
- Integrate via pipeline factory registration

### Common Interface Protocol

Both features implement the same contract:

```python
from abc import ABC, abstractmethod
from pathlib import Path
from dataclasses import dataclass

class BaseExtractor(ABC):
    """Abstract base for all extractors."""

    def __init__(self, config: dict):
        """Initialize with configuration dict."""
        self.config = config

    @abstractmethod
    def extract(self, file_path: Path) -> ExtractionResult:
        """
        Extract data from file.

        Returns:
            ExtractionResult with content_blocks, images, tables, metadata
        """
        pass

    @abstractmethod
    def supports_format(self, file_path: Path) -> bool:
        """Check if extractor can handle this file."""
        pass

    @abstractmethod
    def get_supported_extensions(self) -> list[str]:
        """Return list of supported file extensions."""
        pass

# Example implementation
class CSVExtractor(BaseExtractor):
    def extract(self, file_path: Path) -> ExtractionResult:
        # Parse CSV, build TableMetadata, return result
        pass

    def supports_format(self, file_path: Path) -> bool:
        return file_path.suffix.lower() in ['.csv', '.tsv']

    def get_supported_extensions(self) -> list[str]:
        return ['.csv', '.tsv']
```

### Data Flow Architecture

```
┌─────────────┐
│  Input File │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────┐
│ ExtractionPipeline          │
│  - validate_file()          │
│  - select_extractor()       │  ← Factory pattern
└──────┬──────────────────────┘
       │
       ▼
┌─────────────────────────────┐
│ Specific Extractor          │
│  - DocxExtractor (images)   │
│  - CSVExtractor (new)       │
└──────┬──────────────────────┘
       │
       ▼
┌─────────────────────────────┐
│ ExtractionResult            │
│  content_blocks: tuple      │
│  images: tuple              │  ← DOCX images here
│  tables: tuple              │  ← CSV tables here
│  metadata: dict             │
│  success: bool              │
│  errors: tuple              │
└──────┬──────────────────────┘
       │
       ▼
┌─────────────────────────────┐
│ Processors (optional)       │
│  - TextProcessor            │
│  - ImageProcessor           │
│  - TableProcessor           │
└──────┬──────────────────────┘
       │
       ▼
┌─────────────────────────────┐
│ Formatters                  │
│  - JSONFormatter            │
│  - HTMLFormatter            │
│  - MarkdownFormatter        │
└──────┬──────────────────────┘
       │
       ▼
┌─────────────┐
│ Output File │
└─────────────┘
```

### Infrastructure Integration

Both features use existing infrastructure:

**ConfigManager**:
```python
# Load extractor config with fallback defaults
csv_config = config_manager.get('extractors.csv', {
    'max_rows': None,
    'delimiter': None,
    'encoding': None,
    'has_header': True
})

extractor = CSVExtractor(csv_config)
```

**LoggingFramework**:
```python
# Structured logging with context
logger.info("Extracting images from DOCX", extra={
    "file_path": str(file_path),
    "image_count": len(images)
})

logger.warning("Failed to decode image", extra={
    "image_id": image_id,
    "error": str(error)
})
```

**ErrorHandler**:
```python
# Graceful degradation
try:
    images = self._extract_image_metadata()
except Exception as e:
    logger.error(f"Image extraction failed: {e}")
    images = tuple()  # Continue with empty images
    errors.append(f"Image extraction error: {e}")

return ExtractionResult(
    content_blocks=blocks,
    images=images,
    tables=tables,
    success=len(errors) == 0,
    errors=tuple(errors)
)
```

**ProgressTracker** (CLI):
```python
# Progress updates for batch processing
with ProgressTracker(total=len(files)) as tracker:
    for file in files:
        result = pipeline.extract(file)
        tracker.update(1, file_name=file.name)
```

### Why This Approach Works

**1. Proven Patterns**

DOCX image extraction directly follows PPTX pattern from v1.0.4:
- Same `ImageMetadata` structure
- Same base64 encoding approach
- Same error handling strategy
- 100% success rate in v1.0.4 smoke tests

**2. No Breaking Changes**

- BaseExtractor interface unchanged
- ExtractionResult structure unchanged
- All 778 existing tests remain valid
- Pipeline automatically handles new extractors

**3. Independent Features**

```
Modified Files by Feature:

DOCX Images:
  - src/extractors/docx_extractor.py
  - tests/test_extractors/test_docx_extractor.py

CSV Extractor:
  - src/extractors/csv_extractor.py (new)
  - tests/test_extractors/test_csv_extractor.py (new)
  - src/pipeline/extraction_pipeline.py (register)

Shared:
  - config.yaml.example (add sections)
  - docs/* (documentation updates)
```

No file conflicts → safe parallel development

**4. Infrastructure Already Exists**

Tables and images have been supported since v1.0.0:
- `TableMetadata` dataclass: Mature
- `ImageMetadata` dataclass: Proven
- JSON formatter: Handles both
- HTML formatter: Renders both
- Pipeline processors: Process both

We're adding sources, not capabilities.

---

## 4. Implementation Workflow

### Phase 1: Discovery & Design (50 minutes)

**Goal**: Understand existing patterns and design both features before writing code.

#### Stream 1: DOCX Image Analysis (25 min)
**Agent**: Explorer (pattern analysis specialist)

**Tasks**:
1. Analyze `python-docx` API documentation for image access
2. Review PPTX image extraction implementation (`src/extractors/pptx_extractor.py`)
3. Examine `ImageMetadata` dataclass structure
4. Document image extraction approach

**Output**: Technical specification for DOCX image extraction

#### Stream 2: CSV Data Model Design (25 min)
**Agent**: Explorer (data modeling specialist)

**Tasks**:
1. Analyze CSV → ContentBlock mapping options
2. Review existing `TableMetadata` usage in XLSX extractor
3. Evaluate: CSV as single table vs. CSV as multiple blocks
4. Document recommendation with rationale

**Output**: Technical specification for CSV extractor

#### Synthesis (10 min)
**Agent**: npl-technical-writer

**Task**: Combine both specs into unified design document

**Output**:
- `docs/planning/PRD_DOCX_IMAGE_EXTRACTION.md`
- `docs/planning/PRD_CSV_EXTRACTOR.md`

#### 🚦 Checkpoint 1: Specification Review
**User reviews both specs and approves approach before implementation begins.**

---

### Phase 2: Interface Protocol (15 minutes)

**Goal**: Extract and document common patterns from existing extractors for consistency.

**Agent**: Explorer + npl-technical-writer

**Tasks**:
1. Analyze 5 existing extractors (DocxExtractor, PdfExtractor, PptxExtractor, XlsxExtractor, TxtExtractor)
2. Document common patterns:
   - Config loading approach
   - Error handling style
   - Logging conventions
   - Data structure usage
   - Test patterns
3. Create reference guide for implementers

**Output**: `docs/planning/PRD_INTEGRATION_DEPLOYMENT.md` (includes interface protocol section)

**Why**: Ensures both features follow identical conventions

---

### Phase 3: Implementation (2 hours - PARALLEL)

**Goal**: Build both features using Test-Driven Development (TDD).

#### Stream A: DOCX Image Implementation (1 hour)

**Task 3A-1: Write Tests (RED state)** (20 min)
**Agent**: npl-tdd-builder

```python
# tests/test_extractors/test_docx_extractor.py

def test_extract_images_from_docx():
    """Test image extraction returns ImageMetadata."""
    extractor = DocxExtractor({})
    result = extractor.extract(Path("test_files/document_with_images.docx"))

    assert result.success
    assert len(result.images) == 2
    assert result.images[0].content_type == "image/png"
    assert result.images[0].width > 0
    assert len(result.images[0].data) > 0  # Base64 encoded

def test_extract_images_disabled_via_config():
    """Test images skipped when config disables."""
    extractor = DocxExtractor({'extract_images': False})
    result = extractor.extract(Path("test_files/document_with_images.docx"))

    assert result.success
    assert len(result.images) == 0

def test_extract_handles_corrupted_images():
    """Test graceful degradation for corrupted images."""
    extractor = DocxExtractor({})
    result = extractor.extract(Path("test_files/document_corrupted_image.docx"))

    assert result.success  # Continues despite error
    assert len(result.errors) > 0  # Logs error
```

**Task 3A-2: Implement Feature (GREEN state)** (30 min)
**Agent**: general-purpose (code implementation)

Add `_extract_image_metadata()` method to DocxExtractor, integrate with `extract()` method.

**Task 3A-3: Code Review** (10 min)
**Agent**: npl-code-reviewer

Verify:
- ✅ Follows PPTX pattern
- ✅ Error handling present
- ✅ Config respected
- ✅ Tests pass
- ✅ Logging added

#### Stream B: CSV Extractor Implementation (1.5 hours)

**Task 3B-1: Write Tests (RED state)** (30 min)
**Agent**: npl-tdd-builder

```python
# tests/test_extractors/test_csv_extractor.py

def test_extract_basic_csv():
    """Test basic CSV extraction."""
    extractor = CSVExtractor({})
    result = extractor.extract(Path("test_files/simple.csv"))

    assert result.success
    assert len(result.tables) == 1
    assert result.tables[0].headers == ("Name", "Age", "City")
    assert len(result.tables[0].rows) == 3

def test_auto_detect_delimiter():
    """Test automatic delimiter detection."""
    extractor = CSVExtractor({})

    # Comma-separated
    result_csv = extractor.extract(Path("test_files/comma.csv"))
    assert result_csv.success

    # Tab-separated
    result_tsv = extractor.extract(Path("test_files/tab.tsv"))
    assert result_tsv.success

def test_auto_detect_encoding():
    """Test encoding auto-detection."""
    extractor = CSVExtractor({})

    # UTF-8 with BOM
    result_utf8 = extractor.extract(Path("test_files/utf8_bom.csv"))
    assert result_utf8.success

    # Latin-1
    result_latin = extractor.extract(Path("test_files/latin1.csv"))
    assert result_latin.success

def test_max_rows_limit():
    """Test row limit configuration."""
    extractor = CSVExtractor({'max_rows': 10})
    result = extractor.extract(Path("test_files/large.csv"))

    assert result.success
    assert len(result.tables[0].rows) == 10

def test_malformed_csv_handling():
    """Test graceful handling of malformed rows."""
    extractor = CSVExtractor({})
    result = extractor.extract(Path("test_files/malformed.csv"))

    assert result.success  # Continues despite errors
    assert len(result.errors) > 0  # Logs warnings
```

**Task 3B-2: Implement Feature (GREEN state)** (45 min)
**Agent**: general-purpose (code implementation)

Create `CSVExtractor` class in new file, implement all methods.

**Task 3B-3: Code Review** (15 min)
**Agent**: npl-code-reviewer

Verify:
- ✅ BaseExtractor interface complete
- ✅ Auto-detection working
- ✅ Error handling robust
- ✅ Config options functional
- ✅ Tests pass

#### Why Parallel Works

Features are completely independent:
- Different source files
- Different test files
- No shared data structures modified
- Both use existing infrastructure

Agents can work simultaneously without conflicts.

#### 🚦 Checkpoint 2: Implementation Validation
**Orchestrator verifies:**
- All unit tests pass (DOCX images + CSV extractor)
- Code reviews approve both implementations
- Coverage ≥85% for new code

---

### Phase 4: Integration (1 hour)

**Goal**: Connect features to pipeline and validate end-to-end functionality.

#### Task 4A: Pipeline Registration (15 min)
**Agent**: general-purpose

Register CSVExtractor in pipeline factory:

```python
# src/pipeline/extraction_pipeline.py

class ExtractionPipeline:
    def __init__(self, config: ConfigManager):
        self.extractors = {
            '.pdf': PdfExtractor(config.get('extractors.pdf', {})),
            '.docx': DocxExtractor(config.get('extractors.docx', {})),
            '.pptx': PptxExtractor(config.get('extractors.pptx', {})),
            '.xlsx': XlsxExtractor(config.get('extractors.xlsx', {})),
            '.txt': TxtExtractor(config.get('extractors.txt', {})),
            '.csv': CSVExtractor(config.get('extractors.csv', {})),  # NEW
            '.tsv': CSVExtractor(config.get('extractors.csv', {})),  # NEW
        }
```

#### Task 4B: End-to-End Tests (30 min)
**Agent**: npl-tdd-builder

Create integration tests:

```python
# tests/integration/test_new_features_integration.py

def test_docx_images_through_pipeline():
    """Test DOCX images flow through full pipeline."""
    pipeline = ExtractionPipeline(config)
    result = pipeline.extract(Path("test_files/document_with_images.docx"))

    # Verify extraction
    assert result.success
    assert len(result.images) > 0

    # Verify formatting
    json_output = JSONFormatter().format(result)
    assert "images" in json_output
    assert json_output["images"][0]["content_type"]

def test_csv_through_pipeline():
    """Test CSV extraction through full pipeline."""
    pipeline = ExtractionPipeline(config)
    result = pipeline.extract(Path("test_files/data.csv"))

    # Verify extraction
    assert result.success
    assert len(result.tables) == 1

    # Verify formatting
    json_output = JSONFormatter().format(result)
    assert "tables" in json_output
    assert len(json_output["tables"][0]["rows"]) > 0

def test_mixed_format_batch():
    """Test batch processing with DOCX, CSV, PDF together."""
    pipeline = ExtractionPipeline(config)

    files = [
        Path("test_files/document.docx"),
        Path("test_files/data.csv"),
        Path("test_files/report.pdf"),
    ]

    for file in files:
        result = pipeline.extract(file)
        assert result.success
```

#### Task 4C: CLI Manual Testing (15 min)
**Agent**: general-purpose

Test actual CLI commands:

```bash
# DOCX with images
python -m cli extract test_files/document_with_images.docx --format json --output output.json

# CSV file
python -m cli extract test_files/data.csv --format json --output data.json

# Batch mixed formats
python -m cli batch test_files/ output/ --format html

# Configuration override
python -m cli extract large.csv --config custom_config.yaml --format markdown
```

#### 🚦 Checkpoint 3: Integration Validation
**User tests CLI commands and verifies outputs are correct.**

---

### Phase 5: Validation & Packaging (1 hour)

**Goal**: Ensure production-ready quality and create deployable package.

#### Task 5A: Smoke Tests (20 min)
**Agent**: general-purpose

Run smoke test suite with real-world files:

```bash
# Smoke test configuration
smoke_test_files = [
    "corporate_report.docx",      # DOCX with embedded images
    "sales_data.csv",             # Comma-separated CSV
    "export.tsv",                 # Tab-separated values
    "international.csv",          # UTF-8 with special chars
    "legacy_export.csv",          # Latin-1 encoding
    "large_dataset.csv",          # 5000+ rows
    "mixed_presentation.pptx",    # Existing functionality
    "financial_report.pdf",       # Existing functionality
]

# Success criteria: 100% pass rate
pytest tests/smoke/ -v --smoke-test-files=smoke_test_files.txt
```

**Expected Results**:
- ✅ All 8 files extract successfully
- ✅ DOCX images present in output
- ✅ CSV data correctly parsed
- ✅ No regressions in existing formats
- ✅ Error logs only for expected issues (warnings, not failures)

#### Task 5B: Documentation Updates (20 min)
**Agent**: npl-technical-writer

Update documentation files:

1. **PROJECT_STATE.md**:
   - Version: 1.0.5 → 1.0.6
   - Status: Add DOCX images ✅, CSV support ✅
   - Test count: 778 → 828+

2. **CLAUDE.md**:
   - Module inventory: Add `csv_extractor.py`
   - Recent changes: Document v1.0.6 features

3. **USER_GUIDE.md**:
   - Add CSV extraction examples
   - Add DOCX image extraction examples
   - Update configuration reference

4. **config.yaml.example**:
   ```yaml
   extractors:
     docx:
       extract_images: true  # NEW
     csv:                    # NEW SECTION
       max_rows: null
       delimiter: null
       encoding: null
       has_header: true
   ```

#### Task 5C: Build Package (10 min)
**Agent**: general-purpose

```bash
# Update version
echo "1.0.6" > VERSION

# Build wheel
python -m build

# Verify package
ls -lh dist/ai_data_extractor-1.0.6-py3-none-any.whl
```

#### Task 5D: Clean Environment Test (10 min)
**Agent**: general-purpose

Validate package in fresh environment:

```bash
# Create clean virtual environment
python -m venv test_env
source test_env/bin/activate

# Install package
pip install dist/ai_data_extractor-1.0.6-py3-none-any.whl

# Test CLI
python -m cli --version
# Expected: 1.0.6

python -m cli extract test.csv --format json
# Expected: Successful extraction

deactivate
```

#### 🚦 Checkpoint 4: Production Readiness
**Orchestrator validates:**
- ✅ 100% smoke test pass rate
- ✅ All 828+ tests passing
- ✅ Documentation complete
- ✅ Package builds successfully
- ✅ Clean environment test passes
- ✅ Coverage >92% overall

**User gives final approval to deploy.**

---

## 5. Quality Assurance

### Testing Strategy

#### Test-Driven Development (TDD)

Both features follow Red-Green-Refactor cycle:

1. **RED**: Write tests first (they fail)
2. **GREEN**: Implement minimum code to pass tests
3. **REFACTOR**: Clean up code while keeping tests green

**Example Flow**:
```
Write test: test_extract_basic_csv() [RED - test fails]
  ↓
Implement: CSVExtractor.extract() [GREEN - test passes]
  ↓
Add test: test_auto_detect_delimiter() [RED - new test fails]
  ↓
Implement: _detect_delimiter() [GREEN - all tests pass]
  ↓
Refactor: Extract helper methods [GREEN - tests still pass]
```

#### Coverage Targets

**New Code**: ≥85% coverage
- DOCX image extraction: Target 90% (simpler, fewer edge cases)
- CSV extractor: Target 85% (complex, many edge cases)

**Overall Project**: Maintain >92% coverage
- Starting: 92.3% (778 tests)
- Target: >92% (828+ tests)

**How We Measure**:
```bash
pytest --cov=src --cov-report=term --cov-report=html
```

#### Test Categories

**Unit Tests** (Phase 3):
```python
# test_csv_extractor.py
test_extract_basic_csv()              # Happy path
test_auto_detect_delimiter()          # Comma, tab, semicolon
test_auto_detect_encoding()           # UTF-8, Latin-1, fallbacks
test_max_rows_limit()                 # Configuration
test_malformed_csv_handling()         # Error cases
test_empty_file()                     # Edge case
test_single_column()                  # Edge case
test_no_header_mode()                 # Configuration variant
```

**Integration Tests** (Phase 4):
```python
# test_new_features_integration.py
test_docx_images_through_pipeline()   # End-to-end DOCX
test_csv_through_pipeline()           # End-to-end CSV
test_mixed_format_batch()             # Multi-format batch
test_cli_docx_images()                # CLI integration
test_cli_csv_extraction()             # CLI integration
```

**Smoke Tests** (Phase 5):
```python
# Real-world files
corporate_report.docx      # Business document with images
sales_data.csv            # Typical CSV export
international.csv         # UTF-8 special characters
legacy_export.csv         # Latin-1 encoding
large_dataset.csv         # Performance test (5000+ rows)
```

#### Regression Prevention

**Requirement**: All 778 existing tests must pass throughout development.

**Strategy**:
1. Run full test suite after each feature implementation
2. No modifications to existing test files (only additions)
3. No changes to existing extractor interfaces
4. Checkpoint 2 validates zero regressions before proceeding

**Command**:
```bash
# Run all tests
pytest tests/ -v

# Check for regressions
pytest tests/test_extractors/ -k "not csv" -v  # Existing extractors only
```

### Validation Checkpoints

Four mandatory validation gates before proceeding:

#### Checkpoint 1: Specifications Approved
**After**: Phase 1 (Discovery & Design)
**Validates**:
- ✅ Technical approach sound
- ✅ Design decisions documented
- ✅ Data models defined
- ✅ User approves specifications

**Blocker If**: Design flaws identified, unclear requirements

#### Checkpoint 2: Implementations Pass Tests
**After**: Phase 3 (Implementation)
**Validates**:
- ✅ All unit tests pass (DOCX + CSV)
- ✅ Code reviews approve both features
- ✅ Coverage ≥85% for new code
- ✅ Zero regressions (778 existing tests pass)

**Blocker If**: Tests fail, coverage low, regressions detected

#### Checkpoint 3: Integration Working
**After**: Phase 4 (Integration)
**Validates**:
- ✅ Features work in pipeline
- ✅ Integration tests pass
- ✅ CLI commands functional
- ✅ User validates outputs correct

**Blocker If**: Pipeline errors, CLI broken, output incorrect

#### Checkpoint 4: Ready for Deployment
**After**: Phase 5 (Validation & Packaging)
**Validates**:
- ✅ 100% smoke test pass rate
- ✅ All 828+ tests passing
- ✅ Documentation updated
- ✅ Package builds successfully
- ✅ Clean environment test passes

**Blocker If**: Smoke tests fail, package broken, docs incomplete

### Success Criteria

#### Feature-Level Success

**DOCX Image Extraction**:
```
✅ Images extracted from DOCX files
✅ ImageMetadata populated (format, dimensions, data)
✅ Base64 encoding working
✅ Configuration option functional (extract_images: true/false)
✅ Error handling graceful (corrupted images don't break extraction)
✅ Flows through pipeline to JSON/HTML formatters
✅ Unit tests pass (15+ test cases)
```

**CSV Extractor**:
```
✅ CSV files supported (.csv, .tsv)
✅ Auto-detection works (delimiter, encoding, headers)
✅ Configuration options functional (max_rows, delimiter, encoding)
✅ Malformed data handled gracefully
✅ Data mapped to TableMetadata correctly
✅ Registered in pipeline factory
✅ Unit tests pass (20+ test cases)
✅ Integration tests pass (5+ scenarios)
```

#### System-Level Success

**Testing**:
```
✅ 778 existing tests pass (zero regressions)
✅ 50+ new tests pass
✅ Integration tests pass (both features + pipeline)
✅ Smoke tests 100% pass rate (8 real-world files)
✅ Coverage maintained >92% overall
```

**Integration**:
```
✅ CLI commands work for new features
✅ Batch processing handles mixed formats
✅ Configuration loading correct
✅ Error messages informative
✅ Logging structured and useful
```

**Deployment**:
```
✅ Package builds successfully (v1.0.6 wheel)
✅ Clean environment installation works
✅ Version number updated everywhere
✅ Documentation complete and accurate
```

**Validation Commands**:
```bash
# Feature validation
python -m cli extract document_with_images.docx --format json
python -m cli extract data.csv --format json

# System validation
pytest tests/ -q                     # All tests pass
pytest --cov=src --cov-report=term   # Coverage >92%
python -m cli --version              # Shows 1.0.6

# Package validation
pip install dist/ai_data_extractor-1.0.6-py3-none-any.whl
python -m cli extract test.csv --format json  # Works in clean env
```

---

## 6. Risk Management

### Identified Risks & Mitigations

#### HIGH → MEDIUM: CSV Encoding Issues

**Risk Description**:
CSV files come in many encodings (UTF-8, UTF-8-BOM, Latin-1, CP1252, etc.). Wrong detection causes:
- Garbled text (special characters)
- Parsing failures
- Silent data corruption

**Impact**: Users can't extract international CSVs or legacy exports.

**Mitigation**:
1. **Auto-Detection Chain**:
   ```python
   encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
   for encoding in encodings:
       try:
           text = file.read_text(encoding=encoding)
           return encoding, text
       except UnicodeDecodeError:
           continue
   # Fallback: latin-1 (never fails, may have wrong chars)
   ```

2. **Configuration Override**:
   ```yaml
   extractors:
     csv:
       encoding: 'cp1252'  # User specifies if auto-detect fails
   ```

3. **Comprehensive Tests**:
   - UTF-8 with BOM
   - UTF-8 without BOM
   - Latin-1
   - CP1252 (Windows default)
   - Mixed encodings in batch

**Contingency**: If auto-detection fails, user can specify encoding in config. Error message provides guidance:
```
ERROR: Unable to decode CSV file
TRY: Set 'extractors.csv.encoding' in config to one of: utf-8, latin-1, cp1252
```

**Residual Risk**: LOW (fallback always succeeds, may have wrong characters)

---

#### MEDIUM: CSV Data Model Choice

**Risk Description**:
Unclear whether CSV should map to:
- **Option A**: Single TABLE ContentBlock (CSV is tabular data)
- **Option B**: Multiple TEXT ContentBlocks (one per row)

Wrong choice may require refactoring after implementation.

**Impact**: If Option B chosen but Option A better, need to rewrite CSV extractor.

**Mitigation**:
1. **Phase 1 Evaluation**: Dedicated task to analyze both options
2. **Document Rationale**: Write design decision record with pros/cons
3. **Early Validation**: Review with user before implementation begins

**Evaluation Criteria**:
```
Option A (Single TABLE):
  ✅ Preserves CSV structure naturally
  ✅ Leverages existing TableMetadata
  ✅ Formatters already handle tables
  ❌ CSV with no header is awkward

Option B (Multiple TEXT blocks):
  ✅ Flexible for non-tabular CSVs
  ❌ Loses column structure
  ❌ Formatters don't expect rows as blocks
  ❌ More complex implementation
```

**Contingency**: If wrong choice, refactor in Phase 3 before integration. Cost: ~30 minutes.

**Residual Risk**: LOW (Phase 1 decision reduces uncertainty)

---

#### MEDIUM → LOW: Image Format Edge Cases

**Risk Description**:
DOCX files may contain:
- Unknown image formats (not PNG/JPEG/GIF)
- Vector graphics (SVG, WMF, EMF)
- Corrupted image data
- Images without dimensions

**Impact**: Extraction fails or returns incomplete metadata.

**Mitigation**:
1. **Follow PPTX Pattern**: Proven approach from v1.0.4 handles most formats
2. **Graceful Degradation**:
   ```python
   try:
       format = image_part.content_type
       data = base64.b64encode(image_part.blob)
   except Exception as e:
       logger.warning(f"Image {image_id} extraction failed: {e}")
       continue  # Skip this image, continue with others
   ```

3. **Partial Metadata**: Populate what's available, leave rest as None:
   ```python
   ImageMetadata(
       image_id=0,
       content_type=image_part.content_type if available else "unknown",
       width=shape.width if available else None,
       height=shape.height if available else None,
       data=base64_data if available else "",
       alt_text=shape.name if available else ""
   )
   ```

4. **Comprehensive Tests**:
   - PNG, JPEG, GIF images
   - Unknown formats
   - Corrupted data
   - Missing dimensions

**Contingency**: Log warning, include partial metadata, continue extraction. User sees warning in logs but extraction succeeds.

**Residual Risk**: LOW (graceful degradation prevents failures)

---

#### MEDIUM: Performance (Large CSVs)

**Risk Description**:
Large CSV files (10,000+ rows, 50+ columns) may:
- Consume excessive memory (all rows loaded at once)
- Slow down extraction (seconds → minutes)
- Overwhelm formatters (huge JSON output)

**Impact**: Users can't process large datasets efficiently.

**Mitigation**:
1. **Configuration Option**:
   ```yaml
   extractors:
     csv:
       max_rows: 1000  # Limit rows processed
   ```

2. **Lazy Loading** (future enhancement):
   ```python
   # Phase 3 implementation loads all rows
   rows = list(csv.reader(file))

   # Future: Stream rows, limit in parser
   rows = itertools.islice(csv.reader(file), max_rows)
   ```

3. **Performance Tests**:
   - Small CSV (10 rows): <0.1s
   - Medium CSV (1000 rows): <1s
   - Large CSV (10,000 rows): <5s
   - Huge CSV (100,000 rows): Use max_rows

4. **Documentation**:
   ```markdown
   ## Performance Considerations

   For large CSV files (>10,000 rows), use `max_rows` to limit:

   ```yaml
   extractors:
     csv:
       max_rows: 5000  # Process first 5000 rows only
   ```
   ```

**Contingency**: If performance unacceptable, add streaming in v1.0.7. For v1.0.6, document limits and provide max_rows config.

**Residual Risk**: MEDIUM (acceptable for v1.0.6, future enhancement needed)

---

#### LOW: Pipeline Integration

**Risk Description**:
New features may break existing pipeline:
- Factory registration wrong
- Formatter doesn't handle new data
- Processor crashes on new structures

**Impact**: Pipeline fails to extract files or produce output.

**Mitigation**:
1. **Checkpoint 2 Isolation**: Test features independently before integration
2. **Integration Tests**: Comprehensive tests in Phase 4 validate end-to-end
3. **Existing Infrastructure**: Tables and images already supported, no formatter changes needed
4. **Code Review**: Verify registration logic correct

**Contingency**: Integration tests catch issues before user testing. Fix in Phase 4 before Checkpoint 3.

**Residual Risk**: LOW (infrastructure already supports data types)

---

### Risk Summary

| Risk | Initial | Mitigated | Contingency |
|------|---------|-----------|-------------|
| CSV Encoding | HIGH | MEDIUM | User-specified encoding |
| CSV Data Model | MEDIUM | LOW | Phase 1 decision + early validation |
| Image Formats | MEDIUM | LOW | Graceful degradation |
| Performance | MEDIUM | MEDIUM | max_rows config, future streaming |
| Pipeline Integration | LOW | LOW | Comprehensive testing |

**Overall Risk**: LOW - No high-risk items after mitigation

---

## 7. Technical Details

### File Modifications Expected

#### New Files (5)

```
src/extractors/csv_extractor.py
  - CSVExtractor class (250-300 lines)
  - Methods: extract(), _detect_encoding(), _detect_delimiter()
  - Config handling, error handling, logging

tests/test_extractors/test_csv_extractor.py
  - 20+ test cases (400-500 lines)
  - Happy path, edge cases, error handling
  - Configuration tests, encoding tests

tests/integration/test_new_features_integration.py
  - 5+ integration tests (150-200 lines)
  - Pipeline integration for DOCX images
  - Pipeline integration for CSV
  - CLI integration tests

docs/planning/PRD_DOCX_IMAGE_EXTRACTION.md
  - Technical specification (1500-2000 words)
  - Design decisions, API analysis, implementation plan

docs/planning/PRD_CSV_EXTRACTOR.md
  - Technical specification (2000-2500 words)
  - Data model design, auto-detection strategy, test plan
```

#### Modified Files (8)

```
src/extractors/docx_extractor.py
  - Add _extract_image_metadata() method (~50 lines)
  - Update extract() to call image method and populate result
  - Add error handling for image extraction
  - Add config check for extract_images option

src/pipeline/extraction_pipeline.py
  - Register CSV extractor in factory (~2 lines)
  - Add .csv and .tsv to supported formats list

tests/test_extractors/test_docx_extractor.py
  - Add 10+ image extraction test cases (~200 lines)
  - Test: basic extraction, config disabled, error handling

docs/PROJECT_STATE.md
  - Version: 1.0.5 → 1.0.6
  - Status: Add completed features
  - Test count: 778 → 828+
  - Coverage: Update metrics

docs/CLAUDE.md
  - Module inventory: Add csv_extractor.py
  - Recent changes: Document v1.0.6 features
  - Architecture: Note CSV integration

docs/USER_GUIDE.md
  - Add CSV extraction examples (~200 lines)
  - Add DOCX image extraction examples (~100 lines)
  - Update configuration reference
  - Add troubleshooting section for CSV encoding

config.yaml.example
  - Add extract_images option to docx section
  - Add csv section with all options
  - Add comments explaining each option

README.md
  - Update supported formats list (add CSV)
  - Update feature list (add DOCX images)
  - Update version number
```

### Dependencies

**Required**: None (all dependencies already installed)

**Used**:
```python
# DOCX image extraction
from docx import Document  # Already installed (python-docx)
import base64              # stdlib

# CSV extraction
import csv                 # stdlib
from pathlib import Path   # stdlib

# Infrastructure (already in use)
from src.config import ConfigManager
from src.logging import get_logger
from src.models import ExtractionResult, ImageMetadata, TableMetadata
```

**No `requirements.txt` changes needed.**

### Configuration Schema

```yaml
# config.yaml.example

extractors:
  docx:
    # Existing options
    max_paragraph_length: null       # No limit
    preserve_formatting: false

    # NEW: Image extraction
    extract_images: true             # Enable/disable image extraction
                                     # Default: true
                                     # Set false to skip images (faster)

  # NEW SECTION: CSV/TSV extractor
  csv:
    # Row limit for large files
    max_rows: null                   # Process all rows (null = unlimited)
                                     # Example: 5000 (limits to first 5000 rows)

    # Delimiter detection
    delimiter: null                  # Auto-detect (null = auto)
                                     # Options: ',', '\t', ';', '|'
                                     # Only set if auto-detection fails

    # Encoding detection
    encoding: null                   # Auto-detect (null = auto)
                                     # Options: 'utf-8', 'latin-1', 'cp1252'
                                     # Only set if auto-detection fails

    # Header row handling
    has_header: true                 # First row is column names
                                     # If false, generates Column_1, Column_2, ...

    # Empty row handling
    skip_empty_rows: true            # Ignore blank rows
                                     # If false, includes empty rows in output
```

**Configuration Examples**:

```yaml
# Example 1: Process large CSV (limit rows)
extractors:
  csv:
    max_rows: 1000

# Example 2: Force encoding (auto-detect failed)
extractors:
  csv:
    encoding: 'cp1252'

# Example 3: CSV without header row
extractors:
  csv:
    has_header: false

# Example 4: Disable DOCX images (faster extraction)
extractors:
  docx:
    extract_images: false
```

### Data Structures

**ImageMetadata** (existing, no changes):
```python
@dataclass(frozen=True)
class ImageMetadata:
    image_id: int
    content_type: str          # "image/png", "image/jpeg", etc.
    width: Optional[int]       # Pixels
    height: Optional[int]      # Pixels
    data: str                  # Base64-encoded image data
    alt_text: str              # Alt text or filename
    slide_number: Optional[int]  # None for DOCX
    position_x: Optional[float]  # None for DOCX (inline)
    position_y: Optional[float]  # None for DOCX (inline)
```

**TableMetadata** (existing, used by CSV):
```python
@dataclass(frozen=True)
class TableMetadata:
    table_id: int
    headers: tuple[str, ...]        # Column names
    rows: tuple[tuple[str, ...], ...]  # Data rows
    caption: Optional[str]          # Table caption or filename
    page_number: Optional[int]      # None for CSV
```

**ExtractionResult** (existing, no changes):
```python
@dataclass(frozen=True)
class ExtractionResult:
    content_blocks: tuple[ContentBlock, ...]  # Text content
    images: tuple[ImageMetadata, ...]         # DOCX images here
    tables: tuple[TableMetadata, ...]         # CSV tables here
    metadata: dict                            # Extractor-specific metadata
    success: bool                             # Overall success flag
    errors: tuple[str, ...]                   # Error messages
```

---

## 8. Timeline & Effort

### Total Estimated Time

**~5.5 hours** (with parallelization)
**~6.5 hours** (if sequential)

**Parallelization Benefit**: Saves ~1 hour by running independent streams simultaneously

### Phase Breakdown

#### Phase 1: Discovery & Design (50 minutes)

```
├─ Stream 1: DOCX Image Analysis (25 min)
│  ├─ Analyze python-docx API (10 min)
│  ├─ Review PPTX pattern (10 min)
│  └─ Document approach (5 min)
│
├─ Stream 2: CSV Data Model Design (25 min)
│  ├─ Evaluate data model options (10 min)
│  ├─ Review TableMetadata usage (10 min)
│  └─ Document recommendation (5 min)
│
└─ Synthesis: Unified design document (10 min)
   └─ 🚦 Checkpoint 1: User reviews specs
```

**Deliverables**:
- PRD_DOCX_IMAGE_EXTRACTION.md
- PRD_CSV_EXTRACTOR.md
- Design decision rationale

---

#### Phase 2: Interface Protocol (15 minutes)

```
└─ Extract common patterns from 5 extractors (15 min)
   ├─ Analyze existing code (10 min)
   └─ Document conventions (5 min)

**Deliverables**:
- Interface protocol reference
- Implementation guidelines
```

---

#### Phase 3: Implementation (2 hours - PARALLEL)

```
├─ Stream A: DOCX Images (1 hour)
│  ├─ Write tests (RED state) (20 min)
│  ├─ Implement feature (GREEN state) (30 min)
│  └─ Code review (10 min)
│
└─ Stream B: CSV Extractor (1.5 hours)
   ├─ Write tests (RED state) (30 min)
   ├─ Implement feature (GREEN state) (45 min)
   └─ Code review (15 min)

   └─ 🚦 Checkpoint 2: Implementations validated
```

**Deliverables**:
- src/extractors/docx_extractor.py (modified)
- src/extractors/csv_extractor.py (new)
- tests/test_extractors/test_docx_extractor.py (modified)
- tests/test_extractors/test_csv_extractor.py (new)
- All unit tests passing

---

#### Phase 4: Integration (1 hour)

```
└─ Sequential integration tasks (1 hour)
   ├─ Register CSV in pipeline (15 min)
   ├─ Write integration tests (30 min)
   ├─ Manual CLI testing (15 min)
   └─ 🚦 Checkpoint 3: User validates CLI
```

**Deliverables**:
- Pipeline registration complete
- Integration tests passing
- CLI commands functional

---

#### Phase 5: Validation & Packaging (1 hour)

```
└─ Sequential validation tasks (1 hour)
   ├─ Smoke tests (20 min)
   ├─ Documentation updates (20 min)
   ├─ Build package (10 min)
   ├─ Clean environment test (10 min)
   └─ 🚦 Checkpoint 4: Final approval
```

**Deliverables**:
- 100% smoke test pass rate
- Updated documentation
- v1.0.6 wheel package
- Production-ready release

---

### Checkpoint & Review Time (~30 minutes total)

```
Checkpoint 1: Spec review (5 min)
Checkpoint 2: Implementation validation (10 min)
Checkpoint 3: CLI testing (10 min)
Checkpoint 4: Final approval (5 min)
```

### Agent Task Assignments (17 tasks)

**Agent Types**:
- **Explorer**: Pattern analysis (2 tasks)
- **npl-technical-writer**: Documentation (3 tasks)
- **npl-tdd-builder**: Test creation (2 tasks)
- **general-purpose**: Implementation (7 tasks)
- **npl-code-reviewer**: Quality gates (2 tasks)
- **Orchestrator**: Checkpoints (4 tasks)

### Critical Path

```
Phase 1 (parallel streams) → Checkpoint 1 → Phase 2 (sequential)
  → Phase 3 (parallel streams) → Checkpoint 2
  → Phase 4 (sequential) → Checkpoint 3
  → Phase 5 (sequential) → Checkpoint 4
```

**Longest path**: Stream B (CSV) → Integration → Validation = ~4.5 hours
**Parallelization saves**: ~1 hour compared to sequential execution

---

## 9. Success Metrics

### Functional Validation

#### DOCX Image Extraction

```bash
# Test basic extraction
python -m cli extract test_files/document_with_images.docx --format json --output output.json

# Expected output.json:
{
  "images": [
    {
      "image_id": 0,
      "content_type": "image/png",
      "width": 800,
      "height": 600,
      "data": "iVBORw0KGgoAAAANSUhEUgAA...",  // Base64 encoded
      "alt_text": "Company Logo"
    },
    {
      "image_id": 1,
      "content_type": "image/jpeg",
      "width": 1024,
      "height": 768,
      "data": "/9j/4AAQSkZJRgABAQEAYABgAAD...",
      "alt_text": "Product Screenshot"
    }
  ],
  "content_blocks": [...],  // Text still extracted
  "tables": [...]           // Tables still extracted
}

# Test HTML output (images rendered)
python -m cli extract test_files/document_with_images.docx --format html --output output.html

# Expected: HTML with <img src="data:image/png;base64,..."> tags

# Test config disabled
python -m cli extract test_files/document_with_images.docx --format json --config no_images.yaml

# Expected: No images in output (empty images array)
```

✅ **Success**: Images extracted with metadata, base64 data present, formatters render correctly

---

#### CSV Extraction

```bash
# Test basic CSV
python -m cli extract test_files/sales_data.csv --format json --output sales.json

# Expected sales.json:
{
  "tables": [
    {
      "table_id": 0,
      "headers": ["Product", "Quantity", "Price"],
      "rows": [
        ["Widget A", "100", "$25.00"],
        ["Widget B", "50", "$35.00"],
        ["Widget C", "75", "$20.00"]
      ],
      "caption": "sales_data"
    }
  ]
}

# Test TSV (tab-separated)
python -m cli extract test_files/export.tsv --format json --output export.json

# Expected: Same structure, auto-detected tab delimiter

# Test encoding detection
python -m cli extract test_files/international.csv --format json --output international.json

# Expected: Special characters correctly decoded (UTF-8 detected)

# Test row limit
python -m cli extract test_files/large.csv --format json --config limit_rows.yaml

# Expected: Only first N rows in output (per config max_rows)
```

✅ **Success**: CSV parsed correctly, delimiters/encodings detected, data mapped to tables

---

#### Batch Processing

```bash
# Test mixed format batch
python -m cli batch test_files/ output/ --format html

# test_files/ contains:
#   - report.docx (with images)
#   - data.csv
#   - presentation.pptx
#   - spreadsheet.xlsx
#   - document.pdf

# Expected: 5 HTML files in output/, all formats extracted correctly

# Test progress tracking
python -m cli batch large_dataset/ output/ --format json

# Expected: Progress bar shows, all files processed, no crashes
```

✅ **Success**: All formats handled in one batch, mixed extraction works seamlessly

---

### Quality Validation

#### Test Suite

```bash
# Run all tests
pytest tests/ -v

# Expected output:
======================== test session starts =========================
collected 828 items

tests/test_extractors/test_docx_extractor.py ............... [778]
tests/test_extractors/test_csv_extractor.py ................. [798]
tests/integration/test_new_features_integration.py ....... [805]
[... more tests ...]

======================== 828 passed in 45.2s =========================

# No failures, no regressions
```

✅ **Success**: 778 original + 50 new = 828 tests passing

---

#### Coverage

```bash
# Check coverage
pytest --cov=src --cov-report=term

# Expected output:
Name                                  Stmts   Miss  Cover
---------------------------------------------------------
src/extractors/docx_extractor.py        250     15    94%
src/extractors/csv_extractor.py         180     20    89%
src/extractors/pdf_extractor.py         220     10    95%
[... other modules ...]
---------------------------------------------------------
TOTAL                                  5500    250    95%

# Overall: >92% (target maintained)
# New code: DOCX 94%, CSV 89% (both above 85% target)
```

✅ **Success**: Coverage targets met, >92% overall maintained

---

#### Smoke Tests

```bash
# Run smoke test suite
pytest tests/smoke/ -v --real-world-files

# Expected output:
tests/smoke/test_real_world_files.py::test_corporate_report_docx PASSED
tests/smoke/test_real_world_files.py::test_sales_data_csv PASSED
tests/smoke/test_real_world_files.py::test_export_tsv PASSED
tests/smoke/test_real_world_files.py::test_international_csv PASSED
tests/smoke/test_real_world_files.py::test_legacy_export_csv PASSED
tests/smoke/test_real_world_files.py::test_large_dataset_csv PASSED
tests/smoke/test_real_world_files.py::test_mixed_presentation_pptx PASSED
tests/smoke/test_real_world_files.py::test_financial_report_pdf PASSED

======================== 8 passed in 12.3s =========================

# 100% pass rate
```

✅ **Success**: All real-world files extract successfully, no failures

---

### Production Readiness

#### Package Build

```bash
# Build package
python -m build

# Expected output:
Successfully built ai_data_extractor-1.0.6.tar.gz and ai_data_extractor-1.0.6-py3-none-any.whl

# Verify files
ls -lh dist/
# Expected:
-rw-r--r-- 1 user group 125K Nov  6 10:00 ai_data_extractor-1.0.6-py3-none-any.whl
-rw-r--r-- 1 user group 110K Nov  6 10:00 ai_data_extractor-1.0.6.tar.gz
```

✅ **Success**: Package builds without errors

---

#### Clean Environment Test

```bash
# Create clean environment
python -m venv test_env
source test_env/bin/activate  # Windows: test_env\Scripts\activate

# Install package
pip install dist/ai_data_extractor-1.0.6-py3-none-any.whl

# Expected:
Successfully installed ai-data-extractor-1.0.6

# Test CLI
python -m cli --version

# Expected:
1.0.6

# Test extraction
python -m cli extract test.csv --format json

# Expected: JSON output with table data

# Cleanup
deactivate
```

✅ **Success**: Package installs cleanly, CLI works in fresh environment

---

### Summary Dashboard

```
Feature Validation:
  ✅ DOCX images extracted with metadata
  ✅ CSV files supported (.csv, .tsv)
  ✅ Auto-detection working (delimiter, encoding)
  ✅ Configuration options functional
  ✅ Error handling graceful
  ✅ Pipeline integration seamless

System Validation:
  ✅ 828 tests passing (778 original + 50 new)
  ✅ Coverage >92% (95% actual)
  ✅ Integration tests pass
  ✅ CLI commands functional
  ✅ Smoke tests 100% pass rate

Deployment Validation:
  ✅ Package builds successfully
  ✅ Clean environment installation works
  ✅ Version updated to 1.0.6
  ✅ Documentation complete

OVERALL STATUS: READY FOR PRODUCTION ✅
```

---

## 10. What Happens Next

### Upon Your Approval

**Step 1: Orchestrator Initialization**
- Reviews full orchestration plan
- Assigns agents to initial tasks
- Sets up tracking for 17 tasks across 5 phases

**Step 2: Phase 1 Begins (Discovery)**
- Two parallel agents start pattern analysis:
  - **Agent 1**: Examines python-docx API and PPTX pattern for image extraction
  - **Agent 2**: Evaluates CSV data model options and designs approach
- Both agents produce technical specifications independently
- Technical writer synthesizes specs into unified design documents

**Step 3: Checkpoint 1 (Your Review)**
- You receive two PRD documents:
  - PRD_DOCX_IMAGE_EXTRACTION.md
  - PRD_CSV_EXTRACTOR.md
- Review technical approaches, data model decisions, implementation plans
- Provide feedback or approve to proceed

**Step 4: Phases 2-5 Execute**
- Interface protocol extracted from existing code
- Parallel implementation streams (DOCX images + CSV extractor)
- Integration and testing
- Documentation and packaging
- Checkpoints occur at end of each phase

**Step 5: Validation Checkpoints**
- **Checkpoint 2** (after implementation): Verify tests pass, no regressions
- **Checkpoint 3** (after integration): You test CLI commands, validate outputs
- **Checkpoint 4** (after validation): Final approval before deployment

**Step 6: Deployment**
- v1.0.6 wheel package built and validated
- Documentation updated
- PROJECT_STATE.md reflects new version
- Ready for production use

---

### Your Involvement

You'll be involved at key decision points:

**Required Reviews**:

1. **After Phase 1** (Specifications):
   - Review technical approach for both features
   - Approve data model decision (CSV → tables vs blocks)
   - Validate design before implementation starts
   - **Time needed**: ~15 minutes to read specs

2. **After Phase 3** (Implementation):
   - Review implementation summary (tests passed, coverage met)
   - No code review needed (agents handle that)
   - **Time needed**: ~5 minutes to verify metrics

3. **After Phase 4** (Integration):
   - Test CLI commands manually:
     ```bash
     python -m cli extract document_with_images.docx --format json
     python -m cli extract data.csv --format json
     ```
   - Verify outputs look correct
   - **Time needed**: ~10 minutes for manual testing

4. **After Phase 5** (Validation):
   - Final approval to deploy v1.0.6
   - Review smoke test results (should be 100% pass rate)
   - **Time needed**: ~5 minutes to review summary

**Optional Reviews**:
- You can request to see intermediate outputs at any checkpoint
- You can pause execution to ask questions or provide feedback
- Orchestrator will notify you of progress and blockers

---

### Estimated Calendar Time

**If Run Continuously** (no pauses):
- Total execution: ~5.5 hours
- All phases run back-to-back
- Checkpoints are brief validations
- **Best for**: Quick deployment, unblocked schedule

**With Review Pauses** (realistic):
- Day 1: Phase 1 + your spec review (~1 hour + review time)
- Day 2: Phases 2-3 + your validation (~3 hours + review time)
- Day 3: Phases 4-5 + your final approval (~2.5 hours + review time)
- **Calendar time**: 1-2 days with normal review pauses
- **Best for**: Thoughtful review, allows time for questions

**Accelerated**:
- Morning: Phases 1-2 + spec review
- Afternoon: Phases 3-4 + CLI testing
- Next morning: Phase 5 + final approval
- **Calendar time**: 1.5 days
- **Best for**: Moderate urgency, some review time

---

### Orchestration Mechanics

**How Multi-Agent Orchestration Works**:

1. **Task Queue**: Orchestrator maintains queue of 17 tasks
2. **Parallel Execution**: Independent tasks run simultaneously (Phase 1, Phase 3)
3. **Sequential Gates**: Checkpoints block progress until validated
4. **Agent Specialization**: Tasks assigned to specialized agents (explorer, TDD builder, code reviewer)
5. **Progress Tracking**: You can see status of all tasks at any time

**Example Progress View**:
```
Phase 1: Discovery & Design [ACTIVE]
  ├─ Task 1A: Analyze DOCX image API [COMPLETE] ✅
  ├─ Task 1B: Design CSV data model [IN PROGRESS] 🔄
  └─ Task 1C: Synthesize specs [PENDING] ⏳

Phase 2: Interface Protocol [PENDING]
Phase 3: Implementation [PENDING]
Phase 4: Integration [PENDING]
Phase 5: Validation [PENDING]
```

**Checkpoint Behavior**:
- Orchestrator pauses execution
- Presents summary of completed work
- Waits for your approval
- If approved: Continues to next phase
- If blocked: Addresses issues, re-runs tasks if needed

---

### Communication During Execution

**You'll Receive**:

1. **Phase Start Notifications**:
   ```
   Phase 1 (Discovery & Design) started
   - Stream 1: Analyzing DOCX image API
   - Stream 2: Designing CSV data model
   Estimated completion: 50 minutes
   ```

2. **Checkpoint Summaries**:
   ```
   Checkpoint 1: Specifications Ready for Review

   Completed:
   - DOCX image extraction spec (PRD_DOCX_IMAGE_EXTRACTION.md)
   - CSV extractor spec (PRD_CSV_EXTRACTOR.md)

   Decision Needed:
   - Approve CSV data model choice (single TABLE ContentBlock)

   Action: Please review specs and approve to proceed
   ```

3. **Progress Updates**:
   ```
   Phase 3 (Implementation) progress:
   - Stream A (DOCX images): Tests written ✅, Implementation 60% 🔄
   - Stream B (CSV extractor): Tests written ✅, Implementation 40% 🔄
   ```

4. **Issue Alerts**:
   ```
   ⚠️  Issue Detected: Test failure in CSV delimiter detection
   Impact: Blocks Checkpoint 2
   Action: Investigating and fixing
   ```

**You Can**:
- Ask questions at any time
- Request to see specific files or outputs
- Pause execution to provide feedback
- Override orchestrator decisions if needed

---

### Success Scenario

**Happy Path** (no blockers):

```
Day 1 Morning:
  10:00 - Orchestration begins, Phase 1 starts
  10:50 - Phase 1 complete, specs ready
  11:00 - You review specs (15 min)
  11:15 - Approve specs, Phase 2 starts
  11:30 - Phase 2 complete, Phase 3 starts

Day 1 Afternoon:
  13:30 - Phase 3 complete, Checkpoint 2 passed
  13:45 - Phase 4 starts (integration)
  14:45 - Phase 4 complete, you test CLI (10 min)
  15:00 - Approve integration, Phase 5 starts

Day 2 Morning:
  09:00 - Phase 5 complete, smoke tests 100% pass
  09:15 - You review final summary (5 min)
  09:20 - Final approval, v1.0.6 deployed ✅

Total Calendar Time: ~1.5 days
Total Your Time: ~35 minutes (reviews + testing)
```

---

### What You Get at the End

**Deliverables**:

1. **Working Features**:
   - DOCX image extraction functional
   - CSV/TSV file support functional
   - Both integrated with pipeline

2. **Comprehensive Tests**:
   - 828+ tests passing (zero regressions)
   - >92% coverage maintained
   - 100% smoke test pass rate

3. **Complete Documentation**:
   - Updated USER_GUIDE.md with examples
   - Updated PROJECT_STATE.md (v1.0.6)
   - Updated configuration reference
   - Technical specs (PRDs) for both features

4. **Deployable Package**:
   - ai_data_extractor-1.0.6-py3-none-any.whl
   - Validated in clean environment
   - Ready for distribution

5. **Implementation Record**:
   - Design decision documents
   - Test results and coverage reports
   - Smoke test results
   - Validation checkpoints passed

**Ready to Use**:
```bash
pip install dist/ai_data_extractor-1.0.6-py3-none-any.whl
python -m cli extract any_file.csv --format json
python -m cli extract document_with_images.docx --format html
```

---

## Ready to Begin?

This implementation plan provides:

✅ **Clear Scope**: Two well-defined features with proven patterns
✅ **Low Risk**: Leveraging v1.0.4/v1.0.5 patterns, comprehensive validation
✅ **Quality Assurance**: TDD approach, 85%+ coverage, 4 validation checkpoints
✅ **Parallel Efficiency**: ~5.5 hours with multi-agent orchestration
✅ **User Control**: Reviews at critical decision points
✅ **Production Ready**: Comprehensive testing, documentation, packaging

When you're ready to proceed, approve this plan and orchestration will begin with Phase 1 (Discovery & Design).

**Questions before we start?**
