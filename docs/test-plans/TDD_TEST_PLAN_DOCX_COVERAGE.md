# TDD Test Plan: DOCX Extractor Coverage Increase (70% → 85%)

**Mission**: P2-T1 - Increase DOCX extractor test coverage from 70% to 85%
**Date**: 2025-10-30
**Approach**: Strict Red-Green-Refactor TDD methodology
**Target**: 85% line coverage (from current 70%)

---

## Current State Analysis

**Baseline Metrics** (2025-10-30):
- **Coverage**: 70% (151 statements, 45 missing)
- **Tests Passing**: 22/22 integration tests
- **Missing Lines**: 45 (see detailed analysis below)

**Coverage Report**:
```
Name                               Stmts   Miss  Cover   Missing
----------------------------------------------------------------
src\extractors\docx_extractor.py     151     45    70%   31-32, 61-67, 115-116, 149, 153, 157, 203, 236, 240-244, 275, 321-352, 375, 385, 389, 393, 432
```

---

## Gap Analysis

### Priority 1: HIGH - Error Handling (15 lines)
**Lines 321-352**: Exception handling blocks not exercised

**Missing Coverage**:
- Line 321-329: `InvalidXmlError` handler
- Line 331-339: `PermissionError` handler
- Line 341-349: Generic `Exception` handler
- Line 351-352: Return failed result

**Impact**: Error paths completely untested - critical for production robustness

**Test Cases Needed**:
1. Corrupted DOCX file (invalid XML structure)
2. Permission denied scenario (locked/read-protected file)
3. Unexpected exceptions during extraction
4. Verify error messages are user-friendly
5. Verify partial results returned appropriately

---

### Priority 2: HIGH - Content Type Detection (4 lines)
**Lines 375, 385, 389, 393**: Content type classification branches

**Missing Coverage**:
- Line 375: No style → PARAGRAPH
- Line 385: "list" in style → LIST_ITEM
- Line 389: "quote"/"block" in style → QUOTE
- Line 393: "code"/"source" in style → CODE

**Impact**: Feature not validated - content classification untested

**Test Cases Needed**:
1. Paragraph with no style (None style)
2. Paragraph with list style (e.g., "List Bullet")
3. Paragraph with quote style (e.g., "Quote", "Block Text")
4. Paragraph with code style (e.g., "Code", "Source Code")
5. Mixed document with all content types

---

### Priority 3: MEDIUM - Feature Behaviors (7 lines)
**Lines 203, 236, 240-244, 275**: Configuration-driven behaviors

**Missing Coverage**:
- Line 203: Error fallback without ErrorHandler
- Line 236: Empty paragraph skip logic
- Lines 240-244: Paragraph truncation with warning
- Line 275: Warning for empty document

**Impact**: Configuration options not validated, edge cases untested

**Test Cases Needed**:
1. Empty document (no paragraphs) → warning
2. Document with empty paragraphs + skip_empty=True
3. Long paragraph exceeding max_paragraph_length
4. Extractor without ErrorHandler (fallback mode)

---

### Priority 4: MEDIUM - Configuration Handling (3 lines)
**Lines 115-116**: ConfigManager attribute check

**Missing Coverage**:
- Lines 115-116: ConfigManager without `get_section` method

**Impact**: Low - defensive coding path, unlikely scenario

**Test Case Needed**:
1. Mock ConfigManager without expected methods

---

### Priority 5: LOW - Interface Methods (3 lines)
**Lines 149, 153, 157**: Simple return statements

**Missing Coverage**:
- Line 149: `supports_format` return False path
- Line 153: `get_supported_extensions` return
- Line 157: `get_format_name` return

**Impact**: Very low - simple getters, likely test harness issue

**Test Cases Needed**:
1. Test `supports_format` with non-DOCX file
2. Test `get_supported_extensions` directly
3. Test `get_format_name` directly

---

### Priority 6: LOW - Metadata Parsing (1 line)
**Line 432**: Keyword parsing from comma-separated string

**Missing Coverage**:
- Line 432: Comma-split logic for keywords

**Impact**: Low - minor metadata feature

**Test Case Needed**:
1. Document with comma-separated keywords in metadata

---

### Priority 7: LOWEST - Infrastructure Fallbacks (9 lines)
**Lines 31-32, 61-67**: Import and decorator fallbacks

**Missing Coverage**:
- Lines 31-32: ImportError for docx library
- Lines 61-67: Fallback decorator when infrastructure unavailable

**Impact**: Very low - defensive code for missing dependencies

**Test Cases**: Skip - difficult to mock import failures, low value

---

## Test Implementation Plan

### Phase 1: Error Handling Tests (Target: +10% coverage)
**Estimated Effort**: 2 hours

#### Test 1.1: Corrupted DOCX File (RED)
```python
def test_docx_extractor_corrupt_file_invalid_xml():
    """Test extraction of DOCX with invalid XML structure."""
    # Create corrupted file (ZIP with invalid XML)
    # Expected: success=False, error contains "DOCX structure error" or E110
```

#### Test 1.2: Permission Denied (RED)
```python
def test_docx_extractor_permission_denied():
    """Test extraction when file is read-protected."""
    # Create file and set permissions to deny read
    # Expected: success=False, error contains "Permission denied" or E500
```

#### Test 1.3: Unexpected Exception (RED)
```python
def test_docx_extractor_unexpected_exception():
    """Test extraction with unexpected failure."""
    # Mock Document() to raise RuntimeError
    # Expected: success=False, error contains "Unexpected error" or E100
```

#### Test 1.4: Error Without ErrorHandler (RED)
```python
def test_docx_extractor_error_without_handler():
    """Test error handling when ErrorHandler unavailable."""
    # Mock INFRASTRUCTURE_AVAILABLE = False
    # Trigger validation error
    # Expected: Plain string errors, not structured error codes
```

---

### Phase 2: Content Type Detection Tests (Target: +3% coverage)
**Estimated Effort**: 1 hour

#### Test 2.1: Paragraph Without Style (RED)
```python
def test_docx_extractor_paragraph_no_style():
    """Test content type detection for paragraphs without style."""
    # Create DOCX with paragraph where style=None
    # Expected: ContentType.PARAGRAPH
```

#### Test 2.2: List Style Detection (RED)
```python
def test_docx_extractor_list_style():
    """Test detection of LIST_ITEM content type."""
    # Create DOCX with "List Bullet" or "List Number" style
    # Expected: ContentType.LIST_ITEM
```

#### Test 2.3: Quote Style Detection (RED)
```python
def test_docx_extractor_quote_style():
    """Test detection of QUOTE content type."""
    # Create DOCX with "Quote" or "Block Text" style
    # Expected: ContentType.QUOTE
```

#### Test 2.4: Code Style Detection (RED)
```python
def test_docx_extractor_code_style():
    """Test detection of CODE content type."""
    # Create DOCX with "Code" or "Source Code" style
    # Expected: ContentType.CODE
```

---

### Phase 3: Feature Behavior Tests (Target: +3% coverage)
**Estimated Effort**: 1.5 hours

#### Test 3.1: Empty Document Warning (RED)
```python
def test_docx_extractor_empty_document_warning():
    """Test extraction of completely empty document."""
    # Create DOCX with no paragraphs
    # Expected: success=True, warnings contains "No content extracted"
```

#### Test 3.2: Skip Empty Paragraphs (RED)
```python
def test_docx_extractor_skip_empty_config():
    """Test skip_empty configuration."""
    # Create DOCX with mix of empty and non-empty paragraphs
    # Config: skip_empty=True
    # Expected: Only non-empty paragraphs extracted
```

#### Test 3.3: Paragraph Truncation (RED)
```python
def test_docx_extractor_paragraph_truncation():
    """Test max_paragraph_length with truncation."""
    # Create DOCX with paragraph > max_paragraph_length
    # Config: max_paragraph_length=100
    # Expected: Paragraph truncated, warning generated
```

---

### Phase 4: Configuration Tests (Target: +2% coverage)
**Estimated Effort**: 30 minutes

#### Test 4.1: ConfigManager Edge Case (RED)
```python
def test_docx_extractor_config_manager_missing_method():
    """Test handling of malformed ConfigManager."""
    # Create mock object with __class__.__name__ = 'ConfigManager' but no get_section
    # Expected: Falls back to defaults gracefully
```

---

### Phase 5: Interface Method Tests (Target: +2% coverage)
**Estimated Effort**: 30 minutes

#### Test 5.1: Supports Format Edge Cases (RED)
```python
def test_docx_extractor_supports_format_negative():
    """Test supports_format returns False for non-DOCX."""
    extractor = DocxExtractor()
    assert extractor.supports_format(Path("test.pdf")) is False
    assert extractor.supports_format(Path("test.txt")) is False
    assert extractor.supports_format(Path("test.DOCX")) is True  # case-insensitive
```

#### Test 5.2: Interface Methods (RED)
```python
def test_docx_extractor_interface_methods():
    """Test interface contract methods."""
    extractor = DocxExtractor()
    assert extractor.get_supported_extensions() == [".docx"]
    assert extractor.get_format_name() == "Microsoft Word"
```

---

### Phase 6: Metadata Tests (Target: +1% coverage)
**Estimated Effort**: 30 minutes

#### Test 6.1: Comma-Separated Keywords (RED)
```python
def test_docx_extractor_keywords_parsing():
    """Test parsing of comma-separated keywords in metadata."""
    # Create DOCX with core_properties.keywords = "test, extraction, docx"
    # Expected: keywords tuple = ("test", "extraction", "docx")
```

---

## Test Implementation Guidelines

### TDD Cycle for Each Test

**RED Phase**:
1. Write test that calls DocxExtractor with specific input
2. Assert expected behavior
3. Run test → FAILS (red)
4. Verify failure is due to uncovered line, not code bug

**GREEN Phase**:
1. If code exists and should work, investigate test harness
2. If code missing, report gap (out of scope - no production changes)
3. Verify test exercises target lines

**REFACTOR Phase**:
1. Improve test clarity and documentation
2. Extract fixtures for reusability
3. Ensure test is independent and repeatable

### Test Quality Checklist

Each test must:
- [ ] Follow AAA pattern (Arrange, Act, Assert)
- [ ] Have clear, descriptive name (test_docx_extractor_BEHAVIOR)
- [ ] Include comprehensive docstring
- [ ] Test ONE specific behavior
- [ ] Be independent (no shared state)
- [ ] Execute quickly (<1 second)
- [ ] Use fixtures appropriately
- [ ] Assert all expected behaviors

---

## Success Criteria

**Coverage Target**: ≥85% (from 70%)
- **Gap to Close**: 15 percentage points
- **Lines to Cover**: ~23 of 45 missing lines

**Quality Metrics**:
- All new tests passing ✅
- Existing 22 tests still passing (no regressions) ✅
- Test execution time <10 seconds total ✅
- Each test documents specific coverage goal ✅

**Deliverables**:
1. ✅ Updated test file with new tests
2. ✅ Coverage report showing ≥85%
3. ✅ Test execution evidence (pytest output)
4. ✅ Summary report with metrics

---

## Implementation Notes

**File Location**: `tests/test_extractors/test_docx_extractor_integration.py` (add to existing)

**Fixtures to Create**:
- `corrupted_docx_file`: ZIP with invalid XML
- `read_protected_docx_file`: File with denied permissions
- `styled_docx_file`: Document with list/quote/code styles
- `long_paragraph_docx_file`: Paragraph exceeding length limit
- `keywords_docx_file`: Document with comma-separated keywords

**Mocking Strategy**:
- Use `pytest.MonkeyPatch` for infrastructure availability
- Use `unittest.mock.patch` for Document() constructor
- Use `os.chmod` for permission scenarios (Windows: `icacls`)

**Windows-Specific Considerations**:
- Permission tests may need `icacls` on Windows (not `chmod`)
- File locks behave differently on Windows
- May need `@pytest.mark.skipif(sys.platform == "win32")` for permission tests

---

## Risk Assessment

**Low Risk**:
- Interface method tests (simple getters)
- Metadata parsing tests (straightforward)

**Medium Risk**:
- Content type detection (requires DOCX style manipulation)
- Configuration tests (mocking complexity)

**High Risk**:
- Error handling tests (difficult to trigger some scenarios)
- Permission tests (platform-dependent, may not work on Windows)

**Mitigation**:
- For high-risk tests, document expected behavior clearly
- Use `@pytest.mark.skip` with justification if test is infeasible
- Provide alternative validation evidence (manual testing, code review)

---

## Timeline Estimate

**Phase 1 (Error Handling)**: 2 hours → +10% coverage
**Phase 2 (Content Types)**: 1 hour → +3% coverage
**Phase 3 (Features)**: 1.5 hours → +3% coverage
**Phase 4 (Configuration)**: 0.5 hours → +2% coverage
**Phase 5 (Interface)**: 0.5 hours → +2% coverage
**Phase 6 (Metadata)**: 0.5 hours → +1% coverage

**Total Estimated Effort**: 6 hours → +21% coverage (target: +15%)
**Buffer**: 1 hour for refactoring, documentation, validation

**Total**: 7 hours to achieve 85% coverage

---

## Next Steps

1. ✅ Baseline established (70% coverage, 45 missing lines)
2. ⏳ Begin Phase 1: Error handling tests (HIGH PRIORITY)
3. ⏳ Verify coverage increase after each phase
4. ⏳ Generate final report when 85% achieved

**Start**: Phase 1, Test 1.1 (Corrupted DOCX)

---

**Plan Version**: 1.0
**Author**: TDD Builder Agent
**Status**: READY FOR IMPLEMENTATION
