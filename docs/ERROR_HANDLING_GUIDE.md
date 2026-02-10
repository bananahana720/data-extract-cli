# Error Handling Guide

**Version**: 1.0.0
**Last Updated**: 2025-10-29 (Wave 2 - Agent 3)
**Status**: Production Ready

This guide provides comprehensive documentation for the error handling infrastructure in the data extraction system.

---

## Table of Contents

1. [Overview](#overview)
2. [Error Code System](#error-code-system)
3. [Exception Classes](#exception-classes)
4. [ErrorHandler Usage](#errorhandler-usage)
5. [Recovery Patterns](#recovery-patterns)
6. [User-Friendly Messages](#user-friendly-messages)
7. [Integration Examples](#integration-examples)
8. [Error Code Reference](#error-code-reference)

---

## Overview

The error handling infrastructure provides:

- **Standardized error codes** (E001-E999) for documentation and troubleshooting
- **Category-based exceptions** for type-safe error handling
- **Recovery patterns** (retry, skip, abort) for automated error recovery
- **User-friendly messages** for non-technical auditors
- **Developer debug information** with context and stack traces
- **Logging integration** for monitoring and debugging

### Design Principles

1. **User-Centric**: Non-technical users get clear, actionable messages
2. **Developer-Friendly**: Technical details available for debugging
3. **Systematic**: Errors categorized and coded for easy reference
4. **Recoverable**: Built-in retry logic with exponential backoff
5. **Observable**: Comprehensive logging at appropriate levels

---

## Error Code System

Error codes follow the pattern `EXXX` where X is a digit (E001-E999).

### Error Code Categories

| Range | Category | Description |
|-------|----------|-------------|
| E001-E099 | ValidationError | Input validation failures |
| E100-E199 | ExtractionError | Content extraction failures |
| E200-E299 | ProcessingError | Content processing failures |
| E300-E399 | FormattingError | Output formatting failures |
| E400-E499 | ConfigError | Configuration issues |
| E500-E599 | ResourceError | Resource constraints (memory, disk, time) |
| E600-E699 | ExternalServiceError | External service failures (OCR, etc.) |
| E700-E799 | PipelineError | Pipeline orchestration failures |
| E900-E999 | UnknownError | Unexpected/unhandled errors |

### Error Code Structure

Each error code includes:

```yaml
E001:
  category: ValidationError
  message: "User-friendly message for non-technical users"
  technical_message: "Technical message with {placeholders} for developers"
  recoverable: false  # Whether error can be recovered from
  suggested_action: "What user should do to resolve the issue"
```

---

## Exception Classes

### Base Exception: DataExtractionError

All exceptions inherit from `DataExtractionError`:

```python
from src.infrastructure import DataExtractionError

error = DataExtractionError(
    error_code="E001",
    message="User-friendly message",
    technical_message="Technical details for developers",
    category="ValidationError",
    recoverable=False,
    suggested_action="Check file path and try again",
    context={"file_path": "/docs/report.docx"},
    original_exception=FileNotFoundError("No such file")
)
```

### Category-Specific Exceptions

```python
from src.infrastructure import (
    ValidationError,      # Input validation (E001-E099)
    ExtractionError,      # Content extraction (E100-E199)
    ProcessingError,      # Content processing (E200-E299)
    FormattingError,      # Output formatting (E300-E399)
    ConfigError,          # Configuration (E400-E499)
    ResourceError,        # Resources (E500-E599)
    ExternalServiceError, # External services (E600-E699)
    PipelineError,        # Pipeline (E700-E799)
    UnknownError,         # Unknown/unexpected (E900-E999)
)
```

Each category exception automatically sets its `category` attribute:

```python
error = ValidationError(
    error_code="E001",
    message="File not found"
)
assert error.category == "ValidationError"
```

---

## ErrorHandler Usage

### Basic Usage

```python
from src.infrastructure import ErrorHandler

# Initialize handler (loads error codes from YAML)
handler = ErrorHandler()

# Create error from code
error = handler.create_error(
    error_code="E001",
    file_path="/docs/report.docx"
)

# Format for user
print(handler.format_for_user(error))
# Output: "The file you specified could not be found. Please check
#          the file path and try again."

# Format for developer
print(handler.format_for_developer(error))
# Output: "[E001] File not found: /docs/report.docx
#          Context: file_path=/docs/report.docx"
```

### Creating Errors with Context

```python
# Context variables are substituted into technical_message
error = handler.create_error(
    "E100",
    file_path="/docs/report.docx",
    file_size="5.2MB",
    error_details="Invalid XML structure"
)

# Technical message will have placeholders filled:
# "Failed to open document: /docs/report.docx"
```

### Wrapping Exceptions

```python
try:
    doc = Document(file_path)
except FileNotFoundError as e:
    error = handler.create_error(
        "E001",
        file_path=str(file_path),
        original_exception=e
    )
    raise error
```

### Unknown Error Codes

If an error code is not in the registry, ErrorHandler handles it gracefully:

```python
error = handler.create_error(
    "E999",
    custom_message="Something unexpected happened"
)
# Returns UnknownError with generic message
```

---

## Recovery Patterns

The ErrorHandler supports three recovery patterns:

### 1. RETRY - Transient Errors

For errors that may succeed if retried (network issues, temporary locks):

```python
from src.infrastructure import ErrorHandler, RecoveryAction

handler = ErrorHandler()

# Check if error is retryable
action = handler.get_recovery_action("E104")  # Partial extraction failure
if action == RecoveryAction.RETRY:
    result = handler.retry_with_backoff(
        operation=lambda: extract_file(path),
        max_retries=3,
        initial_delay=1.0,
        backoff_factor=2.0
    )
```

**Retry Logic**:
- First retry: 1.0s delay
- Second retry: 2.0s delay
- Third retry: 4.0s delay
- After 3 failures, raises last exception

**Retryable Errors**:
- E104: Partial extraction failure
- E600: OCR service unavailable
- E601: OCR service error

### 2. SKIP - Recoverable but Non-Critical

For errors where processing can continue without the failed item:

```python
action = handler.get_recovery_action("E105")  # Unsupported feature
if action == RecoveryAction.SKIP:
    # Log warning and continue
    handler.log_error(error, level=logging.WARNING)
    continue  # Process next item
```

**Skippable Errors**:
- E105: Unsupported feature encountered
- E203: Image analysis failed (non-blocking)

### 3. ABORT - Fatal Errors

For errors that cannot be recovered:

```python
action = handler.get_recovery_action("E001")  # File not found
if action == RecoveryAction.ABORT:
    # Cannot continue, return failure
    return ExtractionResult(
        success=False,
        errors=(str(error),)
    )
```

**Non-Recoverable Errors**:
- All validation errors (E001-E099)
- Fatal extraction errors (E100, E101, E102)
- Configuration errors (E400-E499)

---

## User-Friendly Messages

### Design Philosophy

Messages for non-technical users (auditors) must be:

1. **Clear**: Avoid technical jargon
2. **Actionable**: Tell user what to do
3. **Non-Alarming**: Professional but not scary
4. **Specific**: Explain what went wrong

### Good vs. Bad Messages

**Bad** (Technical Jargon):
```
FileNotFoundError: [Errno 2] No such file or directory: '/docs/report.docx'
```

**Good** (User-Friendly):
```
The file you specified could not be found. Please check the file path and try again.

What to do: Verify the file path is correct and the file exists.
```

### Message Structure

User-friendly messages follow this pattern:

```
[What happened]  <-- Clear description of the problem

What to do: [Suggested action]  <-- Concrete next step
```

### Examples

```python
handler = ErrorHandler()

# File not found
error = handler.create_error("E001", file_path="/docs/report.docx")
print(handler.format_for_user(error))
# "The file you specified could not be found. Please check the
#  file path and try again."

# Permission denied
error = handler.create_error("E002", file_path="/protected/file.docx")
print(handler.format_for_user(error))
# "You don't have permission to access this file. Please check
#  file permissions."

# Corrupted file
error = handler.create_error("E101", file_path="/docs/broken.docx")
print(handler.format_for_user(error))
# "The document structure is invalid. The file may be corrupted."
```

---

## Integration Examples

### In Extractors

```python
from pathlib import Path
from src.core import BaseExtractor, ExtractionResult
from src.infrastructure import ErrorHandler

class DocxExtractor(BaseExtractor):
    def __init__(self, config=None):
        super().__init__(config)
        self.error_handler = ErrorHandler()

    def extract(self, file_path: Path) -> ExtractionResult:
        # Validate file
        is_valid, errors = self.validate_file(file_path)
        if not is_valid:
            error = self.error_handler.create_error(
                "E001" if "not found" in errors[0] else "E004",
                file_path=str(file_path)
            )
            self.error_handler.log_error(error)

            return ExtractionResult(
                success=False,
                errors=(self.error_handler.format_for_user(error),)
            )

        # Try extraction with retry
        try:
            action = self.error_handler.get_recovery_action("E104")
            if action == RecoveryAction.RETRY:
                doc = self.error_handler.retry_with_backoff(
                    lambda: Document(file_path),
                    max_retries=3
                )
            else:
                doc = Document(file_path)

        except Exception as e:
            error = self.error_handler.create_error(
                "E100",
                file_path=str(file_path),
                original_exception=e
            )
            self.error_handler.log_error(error)

            return ExtractionResult(
                success=False,
                errors=(self.error_handler.format_for_user(error),),
                warnings=(self.error_handler.format_for_developer(error),)
            )

        # ... extraction logic ...
```

### In Pipeline

```python
from src.infrastructure import ErrorHandler, RecoveryAction

class ExtractionPipeline:
    def __init__(self):
        self.error_handler = ErrorHandler()

    def process_file(self, file_path: Path) -> PipelineResult:
        try:
            # Extract
            result = self.extractor.extract(file_path)

            if not result.success:
                # Check recovery action
                action = self.error_handler.get_recovery_action("E100")
                if action == RecoveryAction.ABORT:
                    return PipelineResult(
                        success=False,
                        failed_stage=ProcessingStage.EXTRACTION,
                        all_errors=result.errors
                    )

            # ... continue pipeline ...

        except Exception as e:
            error = self.error_handler.create_error(
                "E900",
                file_path=str(file_path),
                original_exception=e
            )
            self.error_handler.log_error(error, level=logging.ERROR)

            return PipelineResult(
                success=False,
                failed_stage=ProcessingStage.VALIDATION,
                all_errors=(self.error_handler.format_for_user(error),)
            )
```

### In CLI

```python
from src.infrastructure import ErrorHandler

def main():
    handler = ErrorHandler()

    try:
        result = pipeline.process_file(file_path)

        if not result.success:
            for error_msg in result.all_errors:
                print(f"Error: {error_msg}", file=sys.stderr)
            sys.exit(1)

    except Exception as e:
        error = handler.create_error(
            "E900",
            original_exception=e
        )
        print(handler.format_for_user(error), file=sys.stderr)

        if verbose:
            print("\nDebug information:", file=sys.stderr)
            print(handler.format_for_developer(error), file=sys.stderr)

        sys.exit(1)
```

---

## Error Code Reference

### Validation Errors (E001-E099)

| Code | Message | Recoverable | Action |
|------|---------|-------------|--------|
| E001 | File not found | No | Verify file path |
| E002 | Permission denied | No | Check file permissions |
| E003 | File is empty | No | Provide file with content |
| E004 | Path is a directory | No | Specify a file, not directory |
| E005 | Unsupported file type | No | Convert to supported format |
| E006 | File too large | No | Split file or increase limit |

### Extraction Errors (E100-E199)

| Code | Message | Recoverable | Action |
|------|---------|-------------|--------|
| E100 | Failed to open document | No | Check if file is corrupted |
| E101 | Invalid document structure | No | Verify file integrity |
| E102 | Document is password-protected | No | Remove password protection |
| E103 | No extractable content | No | Verify document has text |
| E104 | Partial extraction failure | Yes (Retry) | Review extracted content |
| E105 | Unsupported feature | Yes (Skip) | Manual review may be needed |

#### DOCX-Specific (E110-E129)

| Code | Message | Recoverable | Action |
|------|---------|-------------|--------|
| E110 | Invalid DOCX XML structure | No | Re-save in Microsoft Word |
| E111 | Embedded object extraction failed | Yes (Skip) | Some content may be missing |

#### PDF-Specific (E130-E149)

| Code | Message | Recoverable | Action |
|------|---------|-------------|--------|
| E130 | Unsupported PDF encryption | No | Remove encryption |
| E131 | PDF requires OCR | Yes (Retry) | OCR processing will be attempted |

### Processing Errors (E200-E299)

| Code | Message | Recoverable | Action |
|------|---------|-------------|--------|
| E200 | Context linking failed | Yes (Skip) | Content extracted but unstructured |
| E201 | Metadata aggregation failed | Yes (Skip) | Some statistics missing |
| E202 | Quality validation failed | Yes (Skip) | Review output carefully |
| E203 | Image analysis failed | Yes (Skip) | Image metadata incomplete |

### Formatting Errors (E300-E399)

| Code | Message | Recoverable | Action |
|------|---------|-------------|--------|
| E300 | Formatting failed | No | Try different output format |
| E301 | Failed to write output | No | Check permissions and disk space |
| E302 | JSON serialization error | No | Contact support |

### Configuration Errors (E400-E499)

| Code | Message | Recoverable | Action |
|------|---------|-------------|--------|
| E400 | Config file not found | No | Verify config file exists |
| E401 | Invalid config value | No | Check config syntax |
| E402 | Missing required config | No | Add required setting |
| E403 | Config value out of range | No | Adjust value to valid range |

### Resource Errors (E500-E599)

| Code | Message | Recoverable | Action |
|------|---------|-------------|--------|
| E500 | Out of memory | No | Process smaller file |
| E501 | Insufficient disk space | No | Free up disk space |
| E502 | Operation timeout | No | Increase timeout or process smaller file |
| E503 | Cannot create temp file | No | Check temp directory permissions |

### External Service Errors (E600-E699)

| Code | Message | Recoverable | Action |
|------|---------|-------------|--------|
| E600 | OCR service unavailable | Yes (Retry) | Verify OCR service is running |
| E601 | OCR service error | Yes (Retry) | Retry operation |

### Pipeline Errors (E700-E799)

| Code | Message | Recoverable | Action |
|------|---------|-------------|--------|
| E700 | Pipeline initialization failed | No | Check system configuration |
| E701 | Missing pipeline component | No | Verify all components installed |
| E702 | No suitable extractor | No | Verify file format is supported |

### Unknown Errors (E900-E999)

| Code | Message | Recoverable | Action |
|------|---------|-------------|--------|
| E900 | Unexpected error | No | Contact support |
| E901 | Programming error (assertion) | No | Report bug to development team |

---

## Best Practices

### 1. Always Use Error Codes

```python
# Good
error = handler.create_error("E001", file_path=path)

# Bad - loses error code context
raise Exception("File not found")
```

### 2. Provide Context

```python
# Good - rich context for debugging
error = handler.create_error(
    "E100",
    file_path=path,
    file_size=path.stat().st_size,
    user=current_user
)

# Bad - minimal context
error = handler.create_error("E100")
```

### 3. Use Recovery Actions

```python
# Good - respects recovery pattern
action = handler.get_recovery_action(error.error_code)
if action == RecoveryAction.RETRY:
    handler.retry_with_backoff(operation)
elif action == RecoveryAction.SKIP:
    continue
else:  # ABORT
    return failure_result

# Bad - always retries or never retries
for _ in range(3):
    try:
        operation()
    except:
        continue
```

### 4. Log Errors Appropriately

```python
# Good - logs with appropriate level
if error.recoverable:
    handler.log_error(error, level=logging.WARNING)
else:
    handler.log_error(error, level=logging.ERROR)

# Bad - always logs as ERROR
logging.error(str(error))
```

### 5. Format for Audience

```python
# For CLI output (users)
print(handler.format_for_user(error))

# For logs (developers)
logger.error(handler.format_for_developer(error))

# For API responses (both)
return {
    "error": handler.format_for_user(error),
    "debug": handler.format_for_developer(error) if debug_mode else None
}
```

---

## Testing Error Handling

### Unit Tests

```python
def test_error_creation():
    handler = ErrorHandler()
    error = handler.create_error("E001", file_path="/test.docx")

    assert error.error_code == "E001"
    assert isinstance(error, ValidationError)
    assert "/test.docx" in error.technical_message
    assert not error.recoverable

def test_retry_pattern():
    handler = ErrorHandler()
    attempts = []

    def failing_op():
        attempts.append(1)
        if len(attempts) < 3:
            raise Exception("Fail")
        return "success"

    result = handler.retry_with_backoff(failing_op, max_retries=3)
    assert result == "success"
    assert len(attempts) == 3
```

### Integration Tests

```python
def test_extractor_error_handling(tmp_path):
    handler = ErrorHandler()
    extractor = DocxExtractor()

    # Non-existent file
    result = extractor.extract(tmp_path / "missing.docx")
    assert not result.success
    assert "E001" in result.errors[0] or "not found" in result.errors[0].lower()

    # Empty file
    empty_file = tmp_path / "empty.docx"
    empty_file.touch()
    result = extractor.extract(empty_file)
    assert not result.success
```

---

## FAQ

**Q: When should I create a new error code?**
A: Create a new error code when you encounter a distinct error scenario that users or developers need to troubleshoot separately.

**Q: How do I add a new error code?**
A: Add it to `src/infrastructure/error_codes.yaml` following the existing pattern. Ensure it's in the correct category range.

**Q: Should I use ErrorHandler or raise exceptions directly?**
A: Use ErrorHandler for operational errors (file not found, etc.). Raise exceptions directly for programming errors (bugs).

**Q: How do I test error messages with non-technical users?**
A: Show them the `format_for_user()` output and ask: "What would you do if you saw this message?" Iterate based on feedback.

**Q: Can I override error messages?**
A: Yes, use the `custom_message` parameter: `handler.create_error("E001", custom_message="Custom text")`

**Q: How do I add logging to error handling?**
A: ErrorHandler integrates with Python's logging module. Use `handler.log_error(error)` which logs with appropriate levels.

---

## Next Steps

1. **For Developers**: Review the [Integration Examples](#integration-examples) section
2. **For Users**: See [User-Friendly Messages](#user-friendly-messages) for what to expect
3. **For Testing**: Check [Testing Error Handling](#testing-error-handling) patterns

---

**End of Error Handling Guide**
