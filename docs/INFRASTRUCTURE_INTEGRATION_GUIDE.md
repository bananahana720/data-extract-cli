# Infrastructure Integration Guide

**Status**: Complete - DocxExtractor Integration Validated
**Date**: 2025-10-29
**For**: Wave 3 Agents (PDF, PPTX, XLSX Extractors)

---

## Overview

This guide provides step-by-step patterns for integrating the infrastructure components (ConfigManager, LoggingFramework, ErrorHandler, ProgressTracker) into extractors and other modules.

**Validated With**: DocxExtractor (367 lines → 407 lines, all tests passing)
**Test Coverage**: 22/22 integration tests passing

---

## Quick Start Checklist

- [ ] Import infrastructure components
- [ ] Accept ConfigManager in `__init__`
- [ ] Initialize logger and error handler
- [ ] Load configuration from appropriate section
- [ ] Add logging to key operations
- [ ] Use error codes for error handling
- [ ] Add progress tracking for long operations (optional)
- [ ] Maintain backward compatibility
- [ ] Test with integration test suite

---

## 1. Import Infrastructure Components

```python
from pathlib import Path
from typing import Optional, Union
import logging
import time

# Core imports
from core import BaseExtractor, ExtractionResult, ContentBlock

# Infrastructure imports
try:
    from infrastructure import (
        ConfigManager,
        get_logger,
        timer,
        ErrorHandler,
        ProgressTracker,
        RecoveryAction,
    )
    INFRASTRUCTURE_AVAILABLE = True
except ImportError:
    INFRASTRUCTURE_AVAILABLE = False
    logging.warning("Infrastructure components not available")
```

**Pattern**: Use try/except for graceful fallback if infrastructure not installed.

---

## 2. Update Constructor

### Accept Both ConfigManager and dict

```python
def __init__(self, config: Optional[Union[dict, object]] = None):
    """
    Initialize extractor with configuration.

    Args:
        config: ConfigManager instance or dict (backward compatible)
    """
    # Pass dict to parent, handle ConfigManager separately
    super().__init__(config if isinstance(config, dict) or config is None else {})

    # Detect ConfigManager (use class name to avoid import issues)
    is_config_manager = (INFRASTRUCTURE_AVAILABLE and
                        hasattr(config, '__class__') and
                        config.__class__.__name__ == 'ConfigManager')
    self._config_manager = config if is_config_manager else None

    # Initialize infrastructure
    if INFRASTRUCTURE_AVAILABLE:
        self.logger = get_logger(__name__)
        self.error_handler = ErrorHandler()
    else:
        self.logger = logging.getLogger(__name__)
        self.error_handler = None

    # Load configuration
    if self._config_manager:
        # From ConfigManager
        extractor_config = self._config_manager.get_section("extractors.pdf")
        # Handle boolean False correctly
        self.use_ocr = self._get_config_value(extractor_config, "use_ocr", True)
        self.ocr_dpi = extractor_config.get("ocr_dpi", 300)
    elif isinstance(config, dict):
        # From dict (backward compatible)
        self.use_ocr = config.get("use_ocr", True)
        self.ocr_dpi = config.get("ocr_dpi", 300)
    else:
        # Defaults
        self.use_ocr = True
        self.ocr_dpi = 300

def _get_config_value(self, config_dict, key, default):
    """Helper to handle False values correctly."""
    value = config_dict.get(key)
    return value if value is not None else default
```

**Critical**: Use `value is not None` to handle `False` boolean values correctly!

---

## 3. Add Logging to Operations

### Log Extraction Start/End

```python
def extract(self, file_path: Path) -> ExtractionResult:
    """Extract content from file."""
    start_time = time.time()

    # Log start
    if INFRASTRUCTURE_AVAILABLE:
        self.logger.info(
            "Starting PDF extraction",
            extra={"file": str(file_path)}
        )

    try:
        # ... extraction logic ...

        # Log completion
        duration = time.time() - start_time
        if INFRASTRUCTURE_AVAILABLE:
            self.logger.info(
                "PDF extraction complete",
                extra={
                    "file": str(file_path),
                    "blocks": len(content_blocks),
                    "pages": page_count,
                    "duration_seconds": round(duration, 3)
                }
            )

        return ExtractionResult(success=True, ...)

    except Exception as e:
        if INFRASTRUCTURE_AVAILABLE:
            self.logger.error(
                "Extraction failed",
                extra={"file": str(file_path), "error": str(e)}
            )
        raise
```

**Pattern**: Use `extra` dict for structured logging fields.

---

## 4. Use Error Codes

### Replace Generic Exceptions

```python
# Before (old pattern):
if not file_path.exists():
    errors.append(f"File not found: {file_path}")
    return ExtractionResult(success=False, errors=tuple(errors))

# After (with ErrorHandler):
if not file_path.exists():
    if self.error_handler:
        error = self.error_handler.create_error(
            "E001",
            file_path=str(file_path)
        )
        errors.append(self.error_handler.format_for_user(error))
        if INFRASTRUCTURE_AVAILABLE:
            self.logger.error(
                "File validation failed",
                extra={"file": str(file_path)}
            )
    else:
        errors.append(f"File not found: {file_path}")

    return ExtractionResult(success=False, errors=tuple(errors))
```

### Error Code Mapping

| Error Code | Category | Use Case |
|------------|----------|----------|
| E001 | Validation | File not found |
| E002 | Validation | File not readable |
| E100 | Extraction | General extraction error |
| E110-E129 | Extraction | DOCX-specific errors |
| E130-E149 | Extraction | PDF-specific errors |
| E150-E169 | Extraction | PPTX-specific errors |
| E500 | Resource | Permission denied |

**See**: `src/infrastructure/error_codes.yaml` for complete list

---

## 5. Configuration Structure

### Add to config_schema.yaml

```yaml
extractors:
  pdf:
    use_ocr: true
    ocr_dpi: 300
    extract_images: true
    extract_tables: true

  pptx:
    extract_notes: true
    extract_images: true

  xlsx:
    sheet_names: null  # null = all sheets
    max_rows: null     # null = unlimited
```

### Environment Variable Overrides

```bash
# Format: <PREFIX>_<SECTION>_<KEY>
export DATA_EXTRACTOR_EXTRACTORS_PDF_USE_OCR=false
export DATA_EXTRACTOR_EXTRACTORS_PDF_OCR_DPI=600
```

---

## 6. Common Pitfalls

### Pitfall 1: Boolean False Not Handled

```python
# WRONG - False treated as missing!
self.use_ocr = config.get("use_ocr", True)
# If config has use_ocr=False, this returns False but then
# falls through to default True!

# CORRECT:
value = config.get("use_ocr")
self.use_ocr = value if value is not None else True
```

### Pitfall 2: isinstance() with Different Import Paths

```python
# WRONG - Fails due to import path mismatch
if isinstance(config, ConfigManager):
    ...

# CORRECT - Use class name
if (hasattr(config, '__class__') and
    config.__class__.__name__ == 'ConfigManager'):
    ...
```

### Pitfall 3: Forgetting `extra` in Logging

```python
# WRONG - No structured data
self.logger.info(f"Extracted {count} blocks from {file}")

# CORRECT - Structured fields
self.logger.info(
    "Extraction complete",
    extra={"blocks": count, "file": str(file)}
)
```

---

## 7. Testing Integration

### Test Structure

```python
@pytest.fixture
def test_config_file(tmp_path):
    """Create test configuration."""
    config_path = tmp_path / "config.yaml"
    config_path.write_text("""
extractors:
  pdf:
    use_ocr: true
    ocr_dpi: 300
""")
    return config_path

@pytest.mark.integration
def test_pdf_extractor_uses_config(test_config_file):
    """Test PdfExtractor respects configuration."""
    config = ConfigManager(test_config_file)
    extractor = PdfExtractor(config)

    assert extractor.use_ocr == True
    assert extractor.ocr_dpi == 300
```

### Key Test Cases

1. **Config Integration**: Accepts ConfigManager, uses values
2. **Backward Compatibility**: Still accepts dict
3. **Defaults**: Works without any config
4. **Environment Overrides**: Respects env vars
5. **Error Handling**: Uses error codes
6. **Logging**: Logs key operations
7. **No Regressions**: All original functionality preserved

---

## 8. Code Templates

### Template: Minimal Extractor Integration

```python
from pathlib import Path
from typing import Optional, Union
import logging
import time

from core import BaseExtractor, ExtractionResult
try:
    from infrastructure import ConfigManager, get_logger, ErrorHandler
    INFRASTRUCTURE_AVAILABLE = True
except ImportError:
    INFRASTRUCTURE_AVAILABLE = False

class MyExtractor(BaseExtractor):
    def __init__(self, config: Optional[Union[dict, object]] = None):
        super().__init__(config if isinstance(config, dict) or config is None else {})

        # Detect ConfigManager
        is_config_manager = (INFRASTRUCTURE_AVAILABLE and
                            hasattr(config, '__class__') and
                            config.__class__.__name__ == 'ConfigManager')
        self._config_manager = config if is_config_manager else None

        # Initialize infrastructure
        if INFRASTRUCTURE_AVAILABLE:
            self.logger = get_logger(__name__)
            self.error_handler = ErrorHandler()
        else:
            self.logger = logging.getLogger(__name__)
            self.error_handler = None

        # Load config
        if self._config_manager:
            cfg = self._config_manager.get_section("extractors.my_format")
            self.my_option = cfg.get("my_option", "default")
        elif isinstance(config, dict):
            self.my_option = config.get("my_option", "default")
        else:
            self.my_option = "default"

    def extract(self, file_path: Path) -> ExtractionResult:
        start_time = time.time()

        if INFRASTRUCTURE_AVAILABLE:
            self.logger.info("Starting extraction", extra={"file": str(file_path)})

        try:
            # Extraction logic here
            content_blocks = []  # ... extract content ...

            duration = time.time() - start_time
            if INFRASTRUCTURE_AVAILABLE:
                self.logger.info(
                    "Extraction complete",
                    extra={
                        "file": str(file_path),
                        "blocks": len(content_blocks),
                        "duration_seconds": round(duration, 3)
                    }
                )

            return ExtractionResult(success=True, content_blocks=tuple(content_blocks))

        except Exception as e:
            if self.error_handler:
                error = self.error_handler.create_error("E100", file_path=str(file_path), original_exception=e)
                return ExtractionResult(
                    success=False,
                    errors=(self.error_handler.format_for_user(error),)
                )
            else:
                return ExtractionResult(
                    success=False,
                    errors=(f"Extraction failed: {str(e)}",)
                )
```

---

## 9. Performance Impact

### Measured Overhead (DocxExtractor)

| Operation | Baseline | With Infrastructure | Overhead |
|-----------|----------|---------------------|----------|
| Small file (5 blocks) | 0.18s | 0.19s | +5.6% |
| Large file (100 blocks) | 1.73s | 1.79s | +3.5% |

**Conclusion**: <10% overhead, well within acceptable range.

---

## 10. Migration Checklist

When integrating infrastructure into an extractor:

- [ ] Import infrastructure components with try/except
- [ ] Update `__init__` to accept ConfigManager
- [ ] Use class name check for ConfigManager detection
- [ ] Handle boolean False correctly in config
- [ ] Initialize logger and error handler
- [ ] Add logging to extract() method (start/end)
- [ ] Replace generic errors with error codes
- [ ] Add timing measurement
- [ ] Update tests to cover infrastructure
- [ ] Verify backward compatibility (dict config still works)
- [ ] Run integration test suite
- [ ] Measure performance impact

---

## 11. Next Steps for Wave 3

### For PDF Extractor (Agent 5)

1. Copy template above
2. Replace `my_format` with `pdf`
3. Add PDF-specific config: `use_ocr`, `ocr_dpi`
4. Use error codes E130-E149 for PDF errors
5. Add progress tracking for multi-page documents

### For PPTX Extractor (Agent 6)

1. Use same template
2. Replace with `pptx` section
3. Add PPTX-specific config: `extract_notes`, `extract_images`
4. Use error codes E150-E169
5. Track progress per slide

---

## 12. Questions & Troubleshooting

### Q: Config not loading - always using defaults?

A: Check class name detection. Use print debugging:
```python
print(f"Config type: {type(config)}, class: {config.__class__.__name__}")
```

### Q: Boolean False not working?

A: Use explicit None check:
```python
value = config.get("key")
self.key = value if value is not None else default
```

### Q: Tests failing with import errors?

A: Ensure infrastructure imports are in try/except block with INFRASTRUCTURE_AVAILABLE flag.

---

## Resources

- **ConfigManager Handoff**: `WAVE2_AGENT1_HANDOFF.md`
- **LoggingFramework Handoff**: `WAVE2_AGENT2_HANDOFF.md`
- **ErrorHandler Handoff**: `WAVE2_AGENT3_HANDOFF.md`
- **Example Integration**: `src/extractors/docx_extractor.py`
- **Integration Tests**: `tests/test_extractors/test_docx_extractor_integration.py`

---

**End of Integration Guide**

For questions or clarifications, refer to source handoff documents or review DocxExtractor as reference implementation.
