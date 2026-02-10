# Configuration System Fix Report

**Date**: 2025-10-30
**Issue**: Configuration system not working from wheel installation
**Status**: IDENTIFIED - FIX IN PROGRESS

---

## Root Cause Analysis

### Issue #1: Config Not Passed to Components ✅ FIXED

**Problem**: In `src/cli/commands.py`, all extractors, processors, and formatters were instantiated WITHOUT the config parameter.

**Code Before**:
```python
pipeline.register_extractor("docx", DocxExtractor())  # ← NO CONFIG!
pipeline.add_processor(ContextLinker())              # ← NO CONFIG!
pipeline.add_formatter(JsonFormatter())              # ← NO CONFIG!
```

**Impact**: All components used hardcoded defaults - no configuration could be customized.

**Fix Applied** (lines 71-84, 99-105):
```python
pipeline.register_extractor("docx", DocxExtractor(config=config))
pipeline.add_processor(ContextLinker(config=config))
pipeline.add_formatter(JsonFormatter(config=config))
```

---

### Issue #2: Missing Config Sections Cause Errors ⚠️ NOT FIXED

**Problem**: Extractors call `get_section("extractors.docx")` without default parameter.

**Location**: All extractors
- `src/extractors/docx_extractor.py:121`
- `src/extractors/pdf_extractor.py:134-140`
- `src/extractors/pptx_extractor.py:102-111`
- `src/extractors/excel_extractor.py:111-125`

**Error**:
```
ConfigurationError: Configuration key not found: extractors.docx
```

**Why This Happens**:
1. User creates config file with only PDF settings
2. DOCX extractor tries to load `extractors.docx` section
3. Section doesn't exist
4. `ConfigManager.get_section()` has no default
5. Raises ConfigurationError

**Example User Config** (causes error):
```yaml
extractors:
  pdf:
    use_ocr: false
# Missing: extractors.docx section
```

**Fix Needed**:
```python
# BEFORE (in docx_extractor.py:121)
extractor_config = self._config_manager.get_section("extractors.docx")

# AFTER
extractor_config = self._config_manager.get_section("extractors.docx", default={})
```

This needs to be applied to ALL extractors, processors, and formatters.

---

## Files That Need Fixing

### Extractors (5 files)

1. **src/extractors/docx_extractor.py:121**
   ```python
   extractor_config = self._config_manager.get_section("extractors.docx", default={})
   ```

2. **src/extractors/pdf_extractor.py** (doesn't use get_section, uses direct access - OK)

3. **src/extractors/pptx_extractor.py:100-111**
   ```python
   extractor_config = self._config_manager.get_section("extractors.pptx", default={})
   ```

4. **src/extractors/excel_extractor.py:109-125**
   ```python
   extractor_config = self._config_manager.get_section("extractors.excel", default={})
   ```

5. **src/extractors/txt_extractor.py** (check if uses config)

### Processors (3 files)

1. **src/processors/context_linker.py** (check usage)

2. **src/processors/metadata_aggregator.py** (check usage)

3. **src/processors/quality_validator.py** (check usage)

### Formatters (3 files)

1. **src/formatters/json_formatter.py** (check usage)

2. **src/formatters/markdown_formatter.py** (check usage)

3. **src/formatters/chunked_text_formatter.py** (check usage)

---

## Testing Plan

### Test 1: Minimal Config
```yaml
# Only configure one extractor
extractors:
  pdf:
    use_ocr: false
```

**Expected**: Should work for all file types, using defaults for unconfigured extractors

### Test 2: Partial Config
```yaml
extractors:
  docx:
    skip_empty: false
processors:
  quality_validator:
    needs_review_threshold: 80.0
# Missing: formatters section
```

**Expected**: Should work, using defaults for unconfigured sections

### Test 3: Empty Config
```yaml
# Empty file
```

**Expected**: Should work, using all defaults

### Test 4: Full Config
```yaml
# All sections configured
extractors:
  docx: {...}
  pdf: {...}
  pptx: {...}
  excel: {...}
processors:
  context_linker: {...}
  metadata_aggregator: {...}
  quality_validator: {...}
formatters:
  json: {...}
  markdown: {...}
  chunked_text: {...}
```

**Expected**: Should use all custom values

---

## Fix Implementation Steps

1. ✅ Fixed config passing in CLI (commands.py)
2. ⚠️ Need to add `default={}` to all `get_section()` calls
3. ⚠️ Rebuild wheel
4. ⚠️ Test with all 4 test scenarios

---

## Status

**Issue #1**: ✅ FIXED - Config now passed to components
**Issue #2**: ⚠️ IN PROGRESS - Need to add defaults to get_section calls
**Wheel**: ⚠️ Rebuilt but not yet tested with partial configs
**Testing**: ⚠️ Pending

---

## Next Actions

1. Add `default={}` to all `get_section()` calls in extractors/processors/formatters
2. Rebuild wheel
3. Test with minimal config file
4. Verify all components use config correctly
5. Update documentation with config examples
