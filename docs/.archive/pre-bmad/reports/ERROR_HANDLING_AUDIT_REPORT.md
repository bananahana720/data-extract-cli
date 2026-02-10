# Error Handling Standardization - Audit Report

**Mission**: P2-T4 - Standardize Error Handling Across Modules
**Agent**: npl-integrator
**Date**: 2025-10-30
**Status**: Audit Complete - Ready for Implementation

---

## Executive Summary

### Current State
The data-extractor-tool has **robust error handling infrastructure** (`src/infrastructure/error_handler.py`) with:
- Standardized error codes (E001-E999)
- Category-based exceptions (ValidationError, ExtractionError, etc.)
- Recovery patterns (retry, skip, abort)
- User-friendly message templates
- Context propagation and logging integration

However, **not all modules use it consistently**:
- Some modules use raw exceptions (`ValueError`, `RuntimeError`)
- Error context quality varies across modules
- Bare `except:` blocks without proper handling
- Inconsistent error message formatting

### Impact
- **Severity**: LOW (system functional, but error messages inconsistent)
- **Priority**: HIGH (Sprint 1, Week 1-2, foundational quality improvement)
- **User Experience**: Inconsistent error messages confuse non-technical users
- **Troubleshooting**: Missing context makes debugging harder

### Assessment Findings
From ADR assessment gap analysis:
- **Gap**: Inconsistent error handling patterns
- **Locations**: Extractors, processors, CLI commands
- **Estimated Effort**: 2-4 hours
- **Prerequisites**: None (infrastructure already exists)

---

## Infrastructure Analysis

### Error Handler Capabilities

**File**: `src/infrastructure/error_handler.py` (496 lines)

**Key Features**:
1. **Error Code System**
   - E001-E099: Validation errors
   - E100-E199: Extraction errors
   - E200-E299: Processing errors
   - E300-E399: Formatting errors
   - E400-E499: Configuration errors
   - E500-E599: Resource errors
   - E600-E699: External service errors
   - E700-E799: Pipeline errors
   - E900-E999: Unknown errors

2. **Exception Hierarchy**
   ```python
   DataExtractionError (base)
   ├── ValidationError (E0xx)
   ├── ExtractionError (E1xx)
   ├── ProcessingError (E2xx)
   ├── FormattingError (E3xx)
   ├── ConfigError (E4xx)
   ├── ResourceError (E5xx)
   ├── ExternalServiceError (E6xx)
   ├── PipelineError (E7xx)
   └── UnknownError (E9xx)
   ```

3. **Key Methods**
   - `create_error(error_code, context)` - Create typed exception
   - `get_recovery_action(error_code)` - Get recovery strategy
   - `retry_with_backoff(operation)` - Automatic retry logic
   - `format_for_user(error)` - User-friendly messages
   - `format_for_developer(error)` - Debug information
   - `log_error(error)` - Structured logging

4. **Error Context Attributes**
   ```python
   DataExtractionError(
       error_code="E001",
       message="User-friendly message",
       technical_message="Technical details",
       category="ValidationError",
       recoverable=True/False,
       suggested_action="What to do",
       context={"key": "value"},  # Rich context
       original_exception=e
   )
   ```

---

## Module-by-Module Audit

### Category 1: COMPLIANT (Using Error Infrastructure)

#### ✅ DocxExtractor (`src/extractors/docx_extractor.py`)
**Status**: Fully compliant
**Error Handling**: Lines 321-350
```python
# GOOD: Uses error handler correctly
except InvalidXmlError as e:
    if self.error_handler:
        error = self.error_handler.create_error(
            "E110",
            file_path=str(file_path),
            original_exception=e
        )
        self.error_handler.log_error(error)
        return ExtractionResult(
            success=False,
            errors=(error.message,),
            # ... proper result structure
        )
```

**Strengths**:
- Uses `error_handler.create_error()` with proper error codes
- Captures original exceptions
- Provides rich context (file_path)
- Returns structured ExtractionResult
- Logs errors appropriately

**Areas for Enhancement**: None critical

---

#### ✅ ExcelExtractor (`src/extractors/excel_extractor.py`)
**Status**: Mostly compliant
**Error Handling**: Lines 217-320

**Strengths**:
- Uses error handler for main error paths
- Proper error codes (E500 for permissions, E100 for general)
- Context includes file_path and error details

**Issues Found**:
1. **Bare except blocks** (Lines 215, 392)
   ```python
   # BAD: Bare except without context
   except:
       pass  # If we can't load values, use formulas only
   ```

   **Impact**: Silent failures, no logging
   **Fix**: Use specific exception types, log warnings
   ```python
   # GOOD: Specific exception with logging
   except Exception as e:
       self.logger.warning(
           f"Could not load cell values: {e}",
           extra={"sheet": sheet.title, "cell": cell.coordinate}
       )
   ```

2. **Generic Exception catch** (Line 236)
   ```python
   # MEDIOCRE: Too broad, but has fallback
   except Exception as e:
       return ExtractionResult(
           success=False,
           errors=(f"Excel extraction failed: {str(e)}",),
           # Missing error handler usage
       )
   ```

   **Fix**: Use error handler for consistency
   ```python
   # GOOD: Use error handler infrastructure
   except Exception as e:
       error = self.error_handler.create_error(
           "E100",
           file_path=str(file_path),
           original_exception=e,
           context={"operation": "excel_extraction"}
       )
       self.error_handler.log_error(error)
       return ExtractionResult(
           success=False,
           errors=(error.message,),
           document_metadata=metadata
       )
   ```

**Priority**: MEDIUM (2 bare excepts, 1 missing error handler usage)

---

#### ⚠️ PdfExtractor (`src/extractors/pdf_extractor.py`)
**Status**: Partially compliant
**Note**: File truncated in grep output, need full analysis

**Known Issues**:
- ImportError handling for optional dependencies (lines 32, 42)
- Need to verify error handling in main extraction logic

**Action**: Full file review required

---

### Category 2: NON-COMPLIANT (Raw Exceptions)

#### ❌ BatchProcessor (`src/pipeline/batch_processor.py`)
**Status**: Partially compliant, has raw exceptions

**Issues Found**:
1. **Raw ValueError** (Lines 97, 101)
   ```python
   # BAD: Raw exception
   if max_workers <= 0:
       raise ValueError("max_workers must be > 0")
   ```

   **Impact**: Inconsistent error format, no error code
   **Fix**: Use ConfigError with proper error code
   ```python
   # GOOD: Use error infrastructure
   if max_workers <= 0:
       error = self.error_handler.create_error(
           "E400",  # Config error
           parameter="max_workers",
           value=max_workers,
           message="Worker count must be positive",
           suggested_action="Specify a positive integer for max_workers"
       )
       raise error
   ```

2. **Generic Exception logging** (Lines 184, 255)
   ```python
   # MEDIOCRE: Logs exception but doesn't use error handler
   except Exception as e:
       self.logger.exception(f"Unexpected error processing {file_path}: {e}")

       # Creates result directly instead of using error handler
       results_map[file_path] = PipelineResult(...)
   ```

   **Fix**: Use error handler for consistency
   ```python
   # GOOD: Use error handler
   except Exception as e:
       error = self.error_handler.create_error(
           "E700",  # Pipeline error
           file_path=str(file_path),
           original_exception=e,
           operation="batch_processing"
       )
       self.error_handler.log_error(error)

       results_map[file_path] = PipelineResult(
           source_file=file_path,
           success=False,
           failed_stage=ProcessingStage.VALIDATION,
           all_errors=(error.message,),  # User-friendly message
           # ...
       )
   ```

**Priority**: HIGH (user-facing errors, validation logic)

---

#### ❌ ExtractionPipeline (`src/pipeline/extraction_pipeline.py`)
**Status**: Partially compliant, has raw exception

**Issues Found**:
1. **Raw ValueError** (Line 258)
   ```python
   # BAD: Raw exception in dependency ordering
   raise ValueError(
       "Circular dependency detected in processor chain. "
       f"Processors: {list(graph.keys())}"
   )
   ```

   **Impact**: Technical error message, no error code
   **Fix**: Use PipelineError with proper context
   ```python
   # GOOD: Use error infrastructure
   error = self.error_handler.create_error(
       "E700",
       message="Cannot arrange processors due to circular dependencies",
       technical_message=f"Circular dependency detected: {list(graph.keys())}",
       processors=list(graph.keys()),
       suggested_action="Review processor dependencies and remove circular references"
   )
   self.error_handler.log_error(error)
   raise error
   ```

2. **Generic Exception handling** (Multiple locations: 381, 419, 502, 529, 578)
   ```python
   # MEDIOCRE: Catches and logs but inconsistent error messages
   except Exception as e:
       error_msg = f"Validation failed: {e}"
       all_errors.append(error_msg)
       self.logger.exception(error_msg)

       return PipelineResult(...)  # Direct string error
   ```

   **Fix**: Use error handler for structured errors
   ```python
   # GOOD: Use error handler
   except Exception as e:
       error = self.error_handler.create_error(
           "E001",  # Validation error
           file_path=str(file_path),
           original_exception=e,
           stage="validation"
       )
       self.error_handler.log_error(error)
       all_errors.append(error.message)  # User-friendly

       return PipelineResult(
           source_file=file_path,
           success=False,
           failed_stage=ProcessingStage.VALIDATION,
           all_errors=tuple(all_errors),
           # ...
       )
   ```

**Priority**: HIGH (core orchestration logic, affects all processing)

---

#### ⚠️ CLI Commands (`src/cli/commands.py`)
**Status**: Non-compliant, no error handler usage

**Issues Found**:
1. **Generic Exception catch** (Lines 60, 303, 452, 546)
   ```python
   # BAD: Generic catch without error handler
   except Exception as e:
       console.print(f"[red]Error: {e}[/red]")
       if verbose:
           import traceback
           console.print(traceback.format_exc())
   ```

   **Impact**: No error codes, raw technical messages shown to users
   **Fix**: Use error handler + user-friendly formatting
   ```python
   # GOOD: Use error handler with rich formatting
   except Exception as e:
       error = error_handler.create_error(
           "E900",  # Unknown error for unexpected issues
           original_exception=e,
           operation="file_extraction",
           file_path=str(file_path)
       )
       error_handler.log_error(error)

       # Show user-friendly message
       console.print(f"[red]✗ {error.message}[/red]")
       console.print(f"\n{error.suggested_action}")

       if verbose:
           # Show technical details only in verbose mode
           console.print(f"\n[dim]{error_handler.format_for_developer(error)}[/dim]")
   ```

2. **Bare except blocks** (Lines 491, 497)
   ```python
   # BAD: Bare except silences errors
   except:
       pass
   ```

   **Impact**: Silent failures, impossible to debug
   **Fix**: At minimum log the exception
   ```python
   # GOOD: Log even if continuing
   except Exception as e:
       logger.warning(f"Could not format output summary: {e}")
       # Continue with other operations
   ```

3. **Custom error formatting** (Lines 163-188)
   ```python
   def format_user_error(error_msg: str, suggestion: Optional[str] = None):
       # Custom logic duplicates error handler functionality
       if 'not found' in error_msg.lower():
           user_msg = "The file you specified could not be found..."
       # ...
   ```

   **Issue**: Duplicates error handler's message templates
   **Fix**: Use error handler's `format_for_user()` method
   ```python
   # GOOD: Use existing infrastructure
   def format_user_error(error: DataExtractionError) -> str:
       """Format error using error handler infrastructure."""
       return error_handler.format_for_user(error)
   ```

**Priority**: CRITICAL (user-facing, inconsistent error experience)

---

### Category 3: INFRASTRUCTURE & CORE (No Changes Needed)

#### ✅ ErrorHandler (`src/infrastructure/error_handler.py`)
**Status**: Infrastructure itself
**Note**: One `RuntimeError` at line 385 is acceptable (internal logic error)

#### ✅ Core Models (`src/core/models.py`)
**Status**: Data structures only, no error handling needed

#### ✅ Core Interfaces (`src/core/interfaces.py`)
**Status**: Abstract base classes, error handling in implementations

#### ✅ Processors
**Status**: Need verification, likely compliant based on architecture

#### ✅ Formatters
**Status**: Need verification, likely compliant based on architecture

---

## Error Handling Patterns - Compliance Matrix

| Module | Raw Exceptions | Bare Except | Error Handler Usage | Context Quality | Priority |
|--------|---------------|-------------|---------------------|----------------|----------|
| **DocxExtractor** | ✅ None | ✅ None | ✅ Full | ✅ Excellent | N/A |
| **ExcelExtractor** | ✅ None | ❌ 2 found | ⚠️ Partial | ⚠️ Good | MEDIUM |
| **PdfExtractor** | ⚠️ TBD | ⚠️ TBD | ⚠️ TBD | ⚠️ TBD | TBD |
| **PptxExtractor** | ⚠️ TBD | ⚠️ TBD | ⚠️ TBD | ⚠️ TBD | TBD |
| **BatchProcessor** | ❌ 2 ValueErrors | ✅ None | ⚠️ Partial | ⚠️ Good | HIGH |
| **ExtractionPipeline** | ❌ 1 ValueError | ✅ None | ⚠️ Partial | ⚠️ Good | HIGH |
| **CLI Commands** | ✅ None | ❌ 2 bare | ❌ None | ❌ Poor | CRITICAL |
| **Processors** | ⚠️ TBD | ⚠️ TBD | ⚠️ TBD | ⚠️ TBD | TBD |
| **Formatters** | ⚠️ TBD | ⚠️ TBD | ⚠️ TBD | ⚠️ TBD | TBD |

**Legend**:
- ✅ Compliant
- ⚠️ Needs review or partial compliance
- ❌ Non-compliant
- TBD: To be determined (needs full file review)

---

## Discovered Issues Summary

### Critical Issues (Block User Experience)
1. **CLI Commands** - No error handler usage, raw exceptions shown to users
2. **CLI Commands** - Bare except blocks silence errors

### High Priority (Core System Components)
3. **BatchProcessor** - Raw ValueError in validation
4. **ExtractionPipeline** - Raw ValueError for circular dependencies
5. **BatchProcessor** - Generic exception handling without error codes

### Medium Priority (Format-Specific)
6. **ExcelExtractor** - 2 bare except blocks
7. **ExcelExtractor** - Generic exception without error handler

### Low Priority (Review Needed)
8. **PdfExtractor** - Full review needed (file truncated in audit)
9. **PptxExtractor** - Full review needed
10. **Processors** (3 modules) - Verify compliance
11. **Formatters** (3 modules) - Verify compliance

---

## Implementation Plan

### Phase 1: Critical User-Facing Issues (1-1.5 hours)
**Target**: CLI Commands
**Goal**: Consistent error experience for end users

**Tasks**:
1. Import ErrorHandler in CLI commands module
2. Replace generic exception catches with error handler usage
3. Remove bare except blocks or add logging
4. Use `format_for_user()` for display
5. Test CLI error scenarios (file not found, invalid format, etc.)

**Files**:
- `src/cli/commands.py` (lines 60, 303, 452, 491, 497, 546)

**Testing**:
- Test file not found error
- Test unsupported format error
- Test permission denied error
- Test verbose error output
- Test batch processing errors

---

### Phase 2: Core Pipeline Components (1 hour)
**Target**: BatchProcessor, ExtractionPipeline
**Goal**: Consistent error handling in orchestration layer

**Tasks**:
1. Replace raw ValueErrors with ConfigError/PipelineError
2. Standardize exception handling in try/catch blocks
3. Use error handler for all error creation
4. Ensure proper error context propagation
5. Test pipeline error scenarios

**Files**:
- `src/pipeline/batch_processor.py` (lines 97, 101, 184, 255)
- `src/pipeline/extraction_pipeline.py` (line 258, exception handlers)

**Testing**:
- Test invalid configuration errors
- Test circular dependency detection
- Test batch processing failures
- Test pipeline stage failures

---

### Phase 3: Extractor Refinements (0.5-1 hour)
**Target**: ExcelExtractor, PdfExtractor (if needed)
**Goal**: Remove bare except blocks, improve error context

**Tasks**:
1. Replace bare except blocks with specific exceptions
2. Add warning logging for non-critical failures
3. Verify PdfExtractor compliance
4. Test error scenarios for each extractor

**Files**:
- `src/extractors/excel_extractor.py` (lines 215, 236, 392)
- `src/extractors/pdf_extractor.py` (full review)

**Testing**:
- Test corrupted Excel files
- Test formula extraction errors
- Test PDF extraction failures (if changes needed)

---

### Phase 4: Verification & Testing (0.5-1 hour)
**Target**: Full system validation
**Goal**: Ensure no regressions, consistent error behavior

**Tasks**:
1. Review remaining extractors (PptxExtractor, etc.)
2. Verify processors use error infrastructure
3. Verify formatters use error infrastructure
4. Run full test suite
5. Test error scenarios end-to-end
6. Update documentation

**Files**:
- All remaining src modules
- Integration tests
- Documentation updates

**Testing**:
- Run full pytest suite
- Test real-world error scenarios
- Verify error messages are user-friendly
- Verify error logging is consistent
- Check error context is captured

---

## Testing Strategy

### Unit Tests
For each modified module, add/verify error handling tests:

```python
def test_error_uses_error_handler():
    """Verify errors use error handler infrastructure."""
    handler = ErrorHandler()

    # Trigger error condition
    with pytest.raises(DataExtractionError) as exc_info:
        # ... test code ...

    error = exc_info.value
    assert error.error_code.startswith("E")
    assert error.message != ""
    assert error.context is not None
```

### Integration Tests
Test error flows through complete pipeline:

```python
def test_pipeline_error_propagation():
    """Verify errors propagate correctly through pipeline."""
    pipeline = ExtractionPipeline()

    # Test file not found
    result = pipeline.process_file(Path("nonexistent.docx"))
    assert not result.success
    assert result.failed_stage == ProcessingStage.VALIDATION
    assert len(result.all_errors) > 0
    assert "not found" in result.all_errors[0].lower()
```

### CLI Error Tests
Test user-facing error messages:

```python
def test_cli_error_messages_user_friendly():
    """Verify CLI shows user-friendly error messages."""
    runner = CliRunner()

    result = runner.invoke(extract_command, ["nonexistent.docx"])

    assert result.exit_code != 0
    assert "could not be found" in result.output.lower()
    assert "check the file path" in result.output.lower()
    # Should NOT show stack traces without --verbose
    assert "Traceback" not in result.output
```

---

## Quality Standards

Each error handling instance must meet these criteria:

### ✅ Completeness
- Uses error handler infrastructure
- Provides error code from registry
- Includes original exception if wrapping
- Returns structured result (not raises, for expected errors)

### ✅ Context Richness
- File path (if applicable)
- Operation being performed
- Relevant parameters/settings
- Stage in pipeline (if applicable)

### ✅ User Experience
- User-friendly message (no jargon)
- Actionable suggested action
- Technical details in verbose mode only
- Consistent formatting across CLI

### ✅ Developer Experience
- Structured logging
- Stack trace preservation
- Error code for documentation lookup
- Context for debugging

### ✅ Testability
- Unit tests for error conditions
- Integration tests for error flows
- CLI tests for error display
- Error recovery tests where applicable

---

## Success Criteria

### Completion Checklist
- [ ] All raw exceptions replaced with error handler usage
- [ ] All bare except blocks removed or logged
- [ ] All modules use consistent error patterns
- [ ] Error messages user-friendly across system
- [ ] Error context captured comprehensively
- [ ] Integration tests verify error flows
- [ ] No regressions in existing tests (400+ tests passing)
- [ ] CLI error display consistent and helpful
- [ ] Documentation updated with error handling patterns

### Quality Metrics
- **Error Code Coverage**: 100% of user-facing errors have error codes
- **Context Capture**: 100% of errors include operation context
- **User-Friendly Messages**: 100% of CLI errors use format_for_user()
- **Logging Integration**: 100% of errors logged via error_handler
- **Test Coverage**: Maintain >85% coverage after changes

---

## Risk Assessment

### Low Risk Changes
- ExcelExtractor bare except blocks (local, well-tested)
- DocxExtractor (already compliant, no changes)

### Medium Risk Changes
- BatchProcessor validation (input validation, clear failure modes)
- ExtractionPipeline dependency ordering (rare edge case)

### High Risk Changes
- CLI commands (user-facing, high visibility)
- Pipeline exception handling (affects all file processing)

### Mitigation Strategies
1. **Incremental changes**: One module at a time
2. **Test after each change**: Run full suite
3. **Preserve behavior**: Only change error format, not logic
4. **Monitor carefully**: CLI changes need thorough testing

---

## Next Steps

1. **Immediate**: Complete audit of remaining modules (Phase 4 prep)
   - PdfExtractor full review
   - PptxExtractor review
   - Processors review (3 modules)
   - Formatters review (3 modules)

2. **Implementation**: Follow 4-phase plan (2-4 hours total)
   - Phase 1: CLI Commands (critical)
   - Phase 2: Pipeline components (high priority)
   - Phase 3: Extractors (medium priority)
   - Phase 4: Verification (all modules)

3. **Validation**: Comprehensive testing
   - Unit tests for error conditions
   - Integration tests for error flows
   - CLI tests for user experience
   - Real-world file testing

4. **Documentation**: Update architecture docs
   - Error handling patterns documented
   - Best practices guide
   - Examples of proper usage

---

## Recommendations

### For Immediate Action
1. **Prioritize CLI** - Most visible to users, highest UX impact
2. **Use TDD approach** - Write error tests first, then fix
3. **Test with real files** - Verify user-friendly messages work

### For Long-Term
1. **Linting rule**: Detect bare except blocks in CI
2. **Error code registry**: Expand error_codes.yaml as needed
3. **Error analytics**: Track error frequency in production
4. **User feedback**: Collect feedback on error message clarity

### For Team
1. **Code review focus**: Check error handling in all PRs
2. **Testing emphasis**: Require error scenario tests
3. **Documentation**: Keep error handling patterns updated

---

## Appendix: Error Handler Quick Reference

### Creating Errors
```python
# Import
from src.infrastructure import ErrorHandler

# Initialize
error_handler = ErrorHandler()

# Create error
error = error_handler.create_error(
    "E001",  # Error code from registry
    file_path=str(file_path),  # Context
    operation="validation",
    original_exception=e  # If wrapping
)

# Log error
error_handler.log_error(error)

# Format for user
user_message = error_handler.format_for_user(error)

# Format for developer
debug_info = error_handler.format_for_developer(error)
```

### Error Codes by Category
- **E001-E099**: Validation (file not found, invalid format, etc.)
- **E100-E199**: Extraction (parsing errors, corrupted files)
- **E200-E299**: Processing (context linking, metadata, quality)
- **E300-E399**: Formatting (output generation errors)
- **E400-E499**: Configuration (invalid settings, missing config)
- **E500-E599**: Resources (memory, disk, timeouts)
- **E600-E699**: External services (OCR, APIs)
- **E700-E799**: Pipeline (orchestration, dependencies)
- **E900-E999**: Unknown (unexpected errors)

### Common Patterns

**File Access Error**:
```python
error = error_handler.create_error(
    "E001",
    file_path=str(file_path),
    original_exception=e
)
```

**Extraction Error**:
```python
error = error_handler.create_error(
    "E100",
    file_path=str(file_path),
    file_format="pdf",
    original_exception=e
)
```

**Configuration Error**:
```python
error = error_handler.create_error(
    "E400",
    parameter="max_workers",
    value=max_workers,
    message="Worker count must be positive"
)
```

---

**End of Audit Report**
