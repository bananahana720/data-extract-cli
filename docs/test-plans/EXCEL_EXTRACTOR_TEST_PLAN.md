# Excel Extractor Test Plan - TDD Implementation

**Status**: Planning Complete - Ready for Red-Green-Refactor
**Agent**: Wave 3 Agent 5
**Date**: 2025-10-29
**Coverage Target**: >85%

---

## Overview

This test plan defines the complete TDD strategy for implementing ExcelExtractor following strict Red-Green-Refactor methodology. All tests will be written BEFORE implementation code.

---

## Requirements Coverage

### R1: Multi-Sheet Extraction
**Requirement**: Extract all sheets with names
**Test Cases**:
1. `test_single_sheet_workbook` - Workbook with one sheet
2. `test_multi_sheet_workbook` - Workbook with multiple sheets
3. `test_sheet_names_preserved` - Sheet names correctly captured
4. `test_empty_sheets_handled` - Empty sheets don't cause failures

**Expected Behavior**:
- Each sheet represented as separate ContentBlock with `sheet` position
- Sheet names stored in `Position.sheet` field
- Empty sheets produce blocks with empty content
- Sheet order preserved

**Integration Points**:
- `Position` model with `sheet` field
- `ContentBlock` with `ContentType.TABLE`

---

### R2: Table/Cell Content Extraction
**Requirement**: Extract values and formulas
**Test Cases**:
1. `test_cell_values_extracted` - Basic cell text/numbers
2. `test_formula_extraction` - Formulas preserved in metadata
3. `test_merged_cells_handled` - Merged cells don't duplicate
4. `test_empty_cells_handled` - Empty cells represented correctly
5. `test_data_types_preserved` - Numbers, dates, strings differentiated

**Expected Behavior**:
- Cell values extracted as primary content
- Formulas stored in `metadata['formula']` if present
- Merged cells use top-left value only
- Data types indicated in `metadata['cell_type']`

**Integration Points**:
- `ContentBlock.content` for cell values
- `ContentBlock.metadata` for formulas and types
- `TableMetadata` for table structure

---

### R3: Chart/Pivot Metadata Extraction
**Requirement**: Extract visual element metadata
**Test Cases**:
1. `test_chart_detection` - Charts identified
2. `test_chart_metadata` - Chart type, title, data range captured
3. `test_pivot_table_detection` - Pivot tables identified
4. `test_pivot_metadata` - Source range captured

**Expected Behavior**:
- Charts produce `ContentType.CHART` blocks
- Chart metadata includes type, title, data_range
- Pivot tables produce metadata blocks
- Visual elements linked to source sheets

**Integration Points**:
- `ContentType.CHART`
- `ContentBlock.metadata` for chart details
- `related_ids` for linking to data

---

### R4: Sheet Structure Preservation
**Requirement**: Preserve relationships between sheets
**Test Cases**:
1. `test_cross_sheet_references` - References to other sheets tracked
2. `test_sheet_order_preserved` - Sheet sequence maintained
3. `test_workbook_structure` - Overall workbook organization captured

**Expected Behavior**:
- Cross-sheet formulas indicate dependencies
- Sheet extraction order matches workbook order
- Workbook-level metadata includes sheet count/names

**Integration Points**:
- `DocumentMetadata` for workbook info
- `ContentBlock.metadata` for cross-references

---

### R5: Infrastructure Integration
**Requirement**: Use all infrastructure modules
**Test Cases**:
1. `test_config_manager_integration` - Accepts ConfigManager
2. `test_config_values_respected` - Uses config settings
3. `test_backward_compatible_dict_config` - Still accepts dict
4. `test_logging_operations` - Logs extraction events
5. `test_error_codes_used` - Uses ErrorHandler for errors
6. `test_structured_logging` - Uses `extra` for log fields

**Expected Behavior**:
- Constructor accepts ConfigManager or dict
- Config values loaded from `extractors.excel` section
- Logging at start/end of extraction
- Error codes E170-E189 for Excel errors
- All infrastructure optional (graceful fallback)

**Integration Points**:
- `ConfigManager` for configuration
- `get_logger()` for structured logging
- `ErrorHandler` for error codes

---

## Test Strategy Framework

### Test Organization

```
tests/test_extractors/test_excel_extractor.py
├── Validation Tests (E001, E002)
├── Basic Extraction Tests
│   ├── Single sheet
│   ├── Multi-sheet
│   └── Empty workbook
├── Content Extraction Tests
│   ├── Cell values
│   ├── Formulas
│   ├── Data types
│   └── Merged cells
├── Advanced Features Tests
│   ├── Charts
│   ├── Pivot tables
│   └── Cross-sheet references
├── Infrastructure Tests
│   ├── Config integration
│   ├── Logging
│   └── Error handling
└── Edge Cases Tests
    ├── Large workbooks
    ├── Protected sheets
    └── Corrupted files
```

### Test Types

**Unit Tests** (70% of coverage):
- Individual method testing
- Format validation
- Content type detection
- Data extraction logic

**Integration Tests** (25% of coverage):
- Infrastructure component usage
- Config loading
- Logging integration
- Error code usage

**Edge Case Tests** (5% of coverage):
- File not found
- Permission errors
- Corrupted Excel files
- Very large workbooks

---

## TDD Cycle Plan

### Cycle 1: File Validation (RED phase)
**Goal**: Validate Excel files correctly

**Tests to Write**:
```python
def test_supports_xlsx_format(excel_extractor):
    """Test .xlsx format is supported."""
    assert excel_extractor.supports_format(Path("test.xlsx"))

def test_supports_xls_format(excel_extractor):
    """Test .xls format is supported."""
    assert excel_extractor.supports_format(Path("test.xls"))

def test_rejects_non_excel_format(excel_extractor):
    """Test non-Excel files rejected."""
    assert not excel_extractor.supports_format(Path("test.docx"))

def test_file_not_found_error(excel_extractor):
    """Test missing file returns error."""
    result = excel_extractor.extract(Path("nonexistent.xlsx"))
    assert not result.success
    assert "E001" in result.errors[0]  # File not found
```

**Implementation**:
- Minimal `ExcelExtractor` class
- `supports_format()` checks extensions
- `extract()` validates file exists
- Uses `ErrorHandler` for E001

---

### Cycle 2: Single Sheet Extraction (GREEN phase)
**Goal**: Extract content from single-sheet workbook

**Tests to Write**:
```python
def test_extract_single_sheet(excel_extractor, single_sheet_xlsx):
    """Test extracting single sheet workbook."""
    result = excel_extractor.extract(single_sheet_xlsx)

    assert result.success
    assert len(result.content_blocks) > 0
    assert result.content_blocks[0].position.sheet == "Sheet1"

def test_sheet_content_extracted(excel_extractor, single_sheet_xlsx):
    """Test cell values extracted."""
    result = excel_extractor.extract(single_sheet_xlsx)

    # Find block with actual content
    content_blocks = [b for b in result.content_blocks if b.content]
    assert len(content_blocks) > 0
```

**Implementation**:
- Add openpyxl dependency
- Open workbook
- Extract first sheet
- Create ContentBlock per sheet
- Set Position with sheet name

---

### Cycle 3: Multi-Sheet Extraction (GREEN phase)
**Goal**: Extract all sheets from workbook

**Tests to Write**:
```python
def test_multi_sheet_workbook(excel_extractor, multi_sheet_xlsx):
    """Test extracting workbook with multiple sheets."""
    result = excel_extractor.extract(multi_sheet_xlsx)

    assert result.success
    # Get unique sheet names
    sheets = {b.position.sheet for b in result.content_blocks if b.position}
    assert len(sheets) == 3  # Expecting 3 sheets
    assert "Sheet1" in sheets
    assert "Sheet2" in sheets
    assert "Sheet3" in sheets

def test_sheet_order_preserved(excel_extractor, multi_sheet_xlsx):
    """Test sheets extracted in correct order."""
    result = excel_extractor.extract(multi_sheet_xlsx)

    # Extract sheet names in order
    sheet_names = []
    for block in result.content_blocks:
        if block.position and block.position.sheet:
            if block.position.sheet not in sheet_names:
                sheet_names.append(block.position.sheet)

    assert sheet_names == ["Sheet1", "Sheet2", "Sheet3"]
```

**Implementation**:
- Loop through all sheets in workbook
- Create blocks for each sheet
- Preserve sheet order
- Track sheet names

---

### Cycle 4: Cell Content Extraction (GREEN phase)
**Goal**: Extract cell values and structure

**Tests to Write**:
```python
def test_cell_values_in_table_metadata(excel_extractor, data_xlsx):
    """Test cell values extracted into TableMetadata."""
    result = excel_extractor.extract(data_xlsx)

    # Find table blocks
    tables = [b for b in result.content_blocks if b.block_type == ContentType.TABLE]
    assert len(tables) > 0

    # Check table has cells
    table = tables[0]
    assert "table_id" in table.metadata
    # Find corresponding TableMetadata in result.tables

def test_data_types_preserved(excel_extractor, data_xlsx):
    """Test different data types handled correctly."""
    result = excel_extractor.extract(data_xlsx)

    # Verify numbers, strings, dates differentiated
    # Check metadata['cell_type'] field
```

**Implementation**:
- Read cell values from sheet
- Store in TableMetadata structure
- Create `ContentType.TABLE` blocks
- Add to `result.tables`
- Set cell_type in metadata

---

### Cycle 5: Formula Extraction (GREEN phase)
**Goal**: Preserve formulas in metadata

**Tests to Write**:
```python
def test_formulas_in_metadata(excel_extractor, formula_xlsx):
    """Test formulas stored in metadata."""
    result = excel_extractor.extract(formula_xlsx)

    # Find blocks with formulas
    blocks_with_formulas = [
        b for b in result.content_blocks
        if b.metadata.get("has_formulas")
    ]
    assert len(blocks_with_formulas) > 0

def test_formula_value_and_result(excel_extractor, formula_xlsx):
    """Test both formula and calculated value captured."""
    result = excel_extractor.extract(formula_xlsx)

    # Check that cells with formulas have both value and formula
    # metadata['formulas'] = {cell_ref: formula_string}
```

**Implementation**:
- Check if cell has formula
- Store formula string in metadata
- Store calculated value as content
- Add `has_formulas` flag

---

### Cycle 6: Infrastructure Integration (REFACTOR phase)
**Goal**: Integrate ConfigManager, logging, error handling

**Tests to Write**:
```python
def test_accepts_config_manager(test_config_file):
    """Test ExcelExtractor accepts ConfigManager."""
    config = ConfigManager(test_config_file)
    extractor = ExcelExtractor(config)
    assert extractor is not None

def test_uses_config_values(test_config_file):
    """Test config values applied."""
    config = ConfigManager(test_config_file)
    config.config_data["extractors"] = {
        "excel": {
            "max_rows": 1000,
            "include_formulas": True
        }
    }
    extractor = ExcelExtractor(config)
    assert extractor.max_rows == 1000
    assert extractor.include_formulas == True

def test_logging_integration(excel_extractor, single_sheet_xlsx, caplog):
    """Test extraction events logged."""
    import logging
    caplog.set_level(logging.INFO)

    result = excel_extractor.extract(single_sheet_xlsx)

    # Check for start/end log messages
    assert any("Starting Excel extraction" in rec.message for rec in caplog.records)
    assert any("Excel extraction complete" in rec.message for rec in caplog.records)

def test_error_codes_for_invalid_file(excel_extractor):
    """Test ErrorHandler used for errors."""
    result = excel_extractor.extract(Path("nonexistent.xlsx"))

    assert not result.success
    # Should use error code E001 or E170-E189
    assert any(code in result.errors[0] for code in ["E001", "E170"])
```

**Implementation**:
- Follow `INFRASTRUCTURE_INTEGRATION_GUIDE.md`
- Accept ConfigManager in __init__
- Initialize logger and error handler
- Add logging to extract() method
- Use error codes for failures
- Handle boolean False correctly

---

### Cycle 7: Advanced Features (GREEN phase)
**Goal**: Charts and pivot tables

**Tests to Write**:
```python
def test_chart_detection(excel_extractor, chart_xlsx):
    """Test charts detected and extracted."""
    result = excel_extractor.extract(chart_xlsx)

    charts = [b for b in result.content_blocks if b.block_type == ContentType.CHART]
    assert len(charts) > 0

def test_chart_metadata(excel_extractor, chart_xlsx):
    """Test chart metadata captured."""
    result = excel_extractor.extract(chart_xlsx)

    charts = [b for b in result.content_blocks if b.block_type == ContentType.CHART]
    chart = charts[0]

    assert "chart_type" in chart.metadata
    assert "title" in chart.metadata
    assert "data_range" in chart.metadata
```

**Implementation**:
- Iterate through sheet._charts
- Create CHART ContentBlocks
- Extract chart type, title, data range
- Link to source sheet

---

## Test Fixtures Required

### Fixture Files (tests/fixtures/excel/)

1. **simple_single_sheet.xlsx** - Basic single sheet
   - 3x3 grid of text/numbers
   - No formatting

2. **multi_sheet.xlsx** - Three sheets
   - Sheet1: Data table
   - Sheet2: More data
   - Sheet3: Empty

3. **with_formulas.xlsx** - Contains formulas
   - Simple arithmetic: =A1+B1
   - Cross-cell references: =SUM(A1:A10)

4. **with_charts.xlsx** - Contains chart
   - Bar chart from data range
   - Chart title and labels

5. **large_workbook.xlsx** - Performance test
   - 10 sheets
   - 1000 rows each

6. **corrupted.xlsx** - Invalid file
   - For error handling tests

### Pytest Fixtures

```python
@pytest.fixture
def excel_extractor():
    """Create ExcelExtractor instance."""
    return ExcelExtractor()

@pytest.fixture
def single_sheet_xlsx():
    """Path to single sheet test file."""
    return Path(__file__).parent.parent / "fixtures" / "excel" / "simple_single_sheet.xlsx"

@pytest.fixture
def multi_sheet_xlsx():
    """Path to multi-sheet test file."""
    return Path(__file__).parent.parent / "fixtures" / "excel" / "multi_sheet.xlsx"

# ... more fixtures
```

---

## Error Code Mapping

Excel-specific errors use E170-E189 range:

| Code | Category | Description |
|------|----------|-------------|
| E001 | Validation | File not found (shared) |
| E002 | Validation | File not readable (shared) |
| E170 | Extraction | General Excel error |
| E171 | Extraction | Invalid Excel format |
| E172 | Extraction | Sheet not found |
| E173 | Extraction | Formula evaluation error |
| E174 | Extraction | Chart extraction error |
| E500 | Resource | Permission denied (shared) |

---

## Configuration Schema

Add to `config_schema.yaml`:

```yaml
extractors:
  excel:
    # Sheet selection
    sheet_names: null  # null = all sheets, or list of names

    # Content extraction
    include_formulas: true
    include_charts: true
    include_pivot_tables: false  # Phase 2

    # Performance limits
    max_rows: null  # null = unlimited
    max_columns: null  # null = unlimited

    # Cell handling
    skip_empty_cells: false
    preserve_formatting: false  # Phase 2
```

---

## Performance Targets

| Metric | Target | Test |
|--------|--------|------|
| Small file (10 rows) | <0.5s | `test_small_file_performance` |
| Medium file (100 rows) | <2s | `test_medium_file_performance` |
| Large file (1000 rows) | <10s | `test_large_file_performance` |
| Memory (100 rows) | <50MB | `test_memory_usage` |

---

## Implementation Dependencies

### Required Libraries

```toml
[project.dependencies]
openpyxl = "^3.1.0"  # Excel file reading
```

### Import Structure

```python
from pathlib import Path
from typing import Optional, Union
import logging
import time

try:
    from openpyxl import load_workbook
    from openpyxl.utils.exceptions import InvalidFileException
except ImportError:
    raise ImportError("openpyxl required. Install: pip install openpyxl")

from core import BaseExtractor, ExtractionResult, ContentBlock, ContentType, Position
from core import DocumentMetadata, TableMetadata

try:
    from infrastructure import (
        ConfigManager,
        get_logger,
        ErrorHandler,
        ProgressTracker,
    )
    INFRASTRUCTURE_AVAILABLE = True
except ImportError:
    INFRASTRUCTURE_AVAILABLE = False
```

---

## Coverage Targets

### Minimum Coverage: 85%

**Critical Paths** (must be 100%):
- File validation
- Sheet extraction
- Error handling
- Infrastructure integration

**Secondary Paths** (>80%):
- Formula extraction
- Chart detection
- Edge cases

**Optional Paths** (>60%):
- Performance optimizations
- Advanced formatting

---

## Success Criteria Checklist

- [ ] All tests written before implementation code
- [ ] Red-Green-Refactor cycles followed strictly
- [ ] Test coverage >85%
- [ ] All tests passing
- [ ] Infrastructure integrated correctly
- [ ] Error codes E170-E189 defined and used
- [ ] Configuration schema updated
- [ ] Example usage created
- [ ] Handoff document written
- [ ] No regressions in existing tests

---

## Next Actions

1. Create test file structure
2. Write fixtures (Excel files)
3. Start Cycle 1 (RED): Write validation tests
4. Implement minimal code (GREEN)
5. Refactor for quality (REFACTOR)
6. Repeat for each cycle

---

**Implementation Start**: After test plan approval
**Estimated Duration**: 4-6 hours (strict TDD)
**Risk Level**: Low (following proven DocxExtractor pattern)
