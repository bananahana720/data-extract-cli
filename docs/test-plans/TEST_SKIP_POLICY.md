# Test Skip Policy
**Project**: data-extractor-tool
**Version**: 1.0
**Last Updated**: 2025-10-30

---

## Purpose

This document defines when and how to skip tests in the data-extractor-tool project. Following these guidelines ensures test skips are well-documented, easily trackable, and reviewed regularly.

---

## When to Skip Tests

### Valid Reasons to Skip

1. **Post-MVP Features**
   - Features explicitly deferred to future sprints
   - Include sprint/issue references when available
   - Example: OCR functionality, advanced chart parsing

2. **Optional Dependencies**
   - Features requiring packages not in core requirements
   - Must check dependency availability programmatically
   - Example: reportlab for PDF generation in tests

3. **Platform-Specific Functionality**
   - Features that only work on specific operating systems
   - Must use proper conditional skip with platform check
   - Example: Unix file permissions tests on Windows

4. **External Service Dependencies**
   - Features requiring external services (databases, APIs)
   - Must document service requirement and setup steps
   - Example: Cloud storage integration tests

5. **Known Limitations**
   - Hardware-specific features (GPU, special sensors)
   - Licensing constraints
   - Performance tests requiring specific environments

### Invalid Reasons to Skip

❌ **DO NOT** skip tests for:
- "Broken" without explanation
- "TODO" without tracking
- "Not implemented" when feature actually exists
- Temporary debugging (use `@pytest.mark.xfail` instead)
- Tests that are "too slow" (use `@pytest.mark.slow` instead)
- Tests that "sometimes fail" (fix the flaky test)

---

## How to Skip Tests

### Method 1: Decorator-Based Skip (PREFERRED)

Use `@pytest.mark.skip` for unconditional skips:

```python
@pytest.mark.skip(reason="OCR functionality deferred to Sprint 5+ (issue #123)")
def test_ocr_extraction():
    """Test OCR text extraction from image-based PDFs."""
    # Test implementation
    pass
```

**Benefits**:
- Easy to discover with `pytest --co`
- Can be filtered with `-k` flag
- Clear in test reports
- Trackable in test analytics

### Method 2: Conditional Skip (For Platform/Dependency)

Use `@pytest.mark.skipif` for conditional skips:

```python
import sys

@pytest.mark.skipif(sys.platform == "win32", reason="Unix-specific file permissions")
def test_file_permissions():
    """Test file permission enforcement."""
    # Test implementation
    pass
```

**For Dependencies**:

```python
import importlib

HAS_OPTIONAL_LIB = importlib.util.find_spec("optional_lib") is not None

@pytest.mark.skipif(not HAS_OPTIONAL_LIB, reason="Requires optional_lib package")
def test_optional_feature():
    """Test feature requiring optional dependency."""
    # Test implementation
    pass
```

### Method 3: Runtime Skip in Fixtures (ACCEPTABLE)

Use `pytest.skip()` inside fixtures when dependency check is complex:

```python
import pytest

@pytest.fixture
def sample_pdf(tmp_path):
    """Create a sample PDF file for testing."""
    try:
        from reportlab.pdfgen import canvas
    except ImportError:
        pytest.skip("reportlab not installed")

    # Create PDF
    pdf_path = tmp_path / "sample.pdf"
    c = canvas.Canvas(str(pdf_path))
    c.drawString(100, 750, "Hello World")
    c.save()

    return pdf_path
```

**Note**: This pattern is acceptable in fixtures because the skip applies to all tests using the fixture.

### Method 4: Runtime Skip in Tests (AVOID)

❌ **AVOID** using `pytest.skip()` directly in test functions:

```python
# BAD: Hard to track, doesn't show in --co
def test_something():
    if not condition:
        pytest.skip("reason")
    # test code
```

✓ **GOOD: Use decorator instead**:

```python
# GOOD: Easy to track, shows in --co
@pytest.mark.skipif(not condition, reason="reason")
def test_something():
    # test code
```

---

## Skip Reason Format

### Required Elements

Every skip reason MUST include:

1. **What**: Brief description of what's being skipped
2. **Why**: Reason for skipping (post-MVP, platform-specific, etc.)
3. **When**: Timeline or condition for un-skipping (optional but recommended)

### Format Template

```
<What> deferred to <Timeline> [(<Issue Reference>)]
```

### Examples

**Good Skip Reasons**:

```python
# Post-MVP with issue tracking
@pytest.mark.skip(reason="OCR functionality deferred to Sprint 5+ (issue #123)")

# Post-MVP without issue (acceptable if no tracking system)
@pytest.mark.skip(reason="Chart detection deferred to post-MVP (no sprint scheduled)")

# Platform-specific
@pytest.mark.skipif(sys.platform == "win32", reason="Unix file permissions not supported on Windows")

# Optional dependency
@pytest.mark.skipif(not HAS_GPU, reason="Requires CUDA-enabled GPU for acceleration tests")

# External service
@pytest.mark.skip(reason="Requires PostgreSQL database (see docs/test-setup.md for configuration)")

# Known limitation
@pytest.mark.skip(reason="Feature requires Python 3.12+ (project targets 3.11)")
```

**Bad Skip Reasons**:

```python
# ❌ Too vague
@pytest.mark.skip(reason="broken")

# ❌ No reason
@pytest.mark.skip

# ❌ Unclear timeline
@pytest.mark.skip(reason="TODO")

# ❌ No explanation
@pytest.mark.skip(reason="skip")

# ❌ Outdated reason
@pytest.mark.skip(reason="Not implemented")  # But feature exists!
```

---

## Custom Markers for Categorization

Use custom pytest markers to categorize skipped tests:

### Registering Markers

In `pytest.ini`:

```ini
[pytest]
markers =
    post_mvp: Features deferred to post-MVP sprints
    slow: Tests that may take more than 1 second
    requires_gpu: Tests requiring GPU hardware
    requires_db: Tests requiring database setup
    platform_specific: Tests that only work on specific platforms
```

### Using Multiple Markers

```python
@pytest.mark.skip(reason="OCR deferred to Sprint 5+")
@pytest.mark.post_mvp
def test_ocr_extraction():
    pass
```

### Filtering by Markers

```bash
# Run only post-MVP tests (even skipped ones show up)
pytest -m post_mvp -v

# Skip post-MVP tests
pytest -m "not post_mvp" -v

# Run slow tests only
pytest -m slow -v

# Skip slow tests
pytest -m "not slow" -v
```

---

## Skip Review Process

### Quarterly Review

Every quarter (or at major milestones):

1. **List all skipped tests**:
   ```bash
   pytest tests/ --co -q | grep -i skip
   ```

2. **Review each skip**:
   - Is the reason still valid?
   - Has the condition changed (e.g., dependency now available)?
   - Should the test be activated?
   - Should the test be deleted (if feature removed)?

3. **Update or remove skips**:
   - Remove skips when conditions change
   - Update reasons if context changes
   - Delete tests if truly obsolete

### Triggers for Ad-Hoc Review

Review skips immediately when:

- **Major feature completion** (e.g., Wave 4 completes infrastructure)
- **Dependency updates** (e.g., new package available)
- **Platform changes** (e.g., dropping Windows support)
- **Sprint planning** (e.g., OCR work scheduled for next sprint)

### Review Checklist

For each skipped test:

- [ ] **Is skip reason clear?** (What, Why, When)
- [ ] **Is skip still valid?** (Condition hasn't changed)
- [ ] **Is there tracking?** (Issue number, sprint reference)
- [ ] **Is marker applied?** (post_mvp, platform_specific, etc.)
- [ ] **Is pattern correct?** (Decorator, not runtime skip)

---

## Common Patterns

### Pattern 1: Post-MVP Feature

```python
@pytest.mark.skip(reason="OCR functionality deferred to Sprint 5+ (no issue tracking yet)")
@pytest.mark.post_mvp
def test_ocr_text_extraction():
    """Test OCR extraction from image-based PDFs."""
    # Test implementation
    pass
```

### Pattern 2: Optional Dependency

```python
import importlib

HAS_REPORTLAB = importlib.util.find_spec("reportlab") is not None

@pytest.mark.skipif(not HAS_REPORTLAB, reason="Requires reportlab for PDF generation in tests")
def test_pdf_generation():
    """Test PDF generation helper for test fixtures."""
    from reportlab.pdfgen import canvas
    # Test implementation
    pass
```

### Pattern 3: Platform-Specific

```python
import sys

@pytest.mark.skipif(
    sys.platform == "win32",
    reason="File permission tests not supported on Windows"
)
@pytest.mark.platform_specific
def test_file_permissions():
    """Test file permission enforcement on Unix systems."""
    # Test implementation
    pass
```

### Pattern 4: External Service

```python
import os

HAS_DB_CONFIG = os.getenv("DATABASE_URL") is not None

@pytest.mark.skipif(
    not HAS_DB_CONFIG,
    reason="Requires PostgreSQL database (set DATABASE_URL env var)"
)
@pytest.mark.requires_db
def test_database_integration():
    """Test database integration."""
    # Test implementation
    pass
```

### Pattern 5: Fixture Dependency

```python
@pytest.fixture
def gpu_context():
    """Provide GPU context for acceleration tests."""
    try:
        import cupy
    except ImportError:
        pytest.skip("Requires cupy for GPU tests")

    context = cupy.cuda.Device(0)
    yield context
    context.synchronize()


def test_gpu_acceleration(gpu_context):
    """Test GPU-accelerated processing."""
    # Test implementation uses gpu_context
    # Automatically skipped if cupy not available
    pass
```

---

## Anti-Patterns to Avoid

### Anti-Pattern 1: Vague Skip Reasons

```python
# ❌ BAD
@pytest.mark.skip(reason="broken")
def test_something():
    pass

# ✓ GOOD
@pytest.mark.skip(reason="Test fails due to bug #456 in dependency v2.3.1, fixed in v2.4.0")
def test_something():
    pass
```

### Anti-Pattern 2: Runtime Skip in Tests

```python
# ❌ BAD
def test_something():
    if not condition:
        pytest.skip("reason")
    # test code

# ✓ GOOD
@pytest.mark.skipif(not condition, reason="reason")
def test_something():
    # test code
```

### Anti-Pattern 3: Skipping Instead of Fixing

```python
# ❌ BAD
@pytest.mark.skip(reason="Test is flaky, sometimes fails")
def test_something():
    pass

# ✓ GOOD: Fix the flaky test or use xfail if truly unpredictable
@pytest.mark.xfail(reason="Known flaky behavior tracked in issue #789")
def test_something():
    pass
```

### Anti-Pattern 4: Outdated Skip Reasons

```python
# ❌ BAD: Feature was implemented in Wave 1
@pytest.mark.skip(reason="DocxExtractor not yet implemented")
def test_docx_extraction():
    pass

# ✓ GOOD: Remove skip, or delete test if redundant with integration tests
def test_docx_extraction():
    from extractors.docx_extractor import DocxExtractor
    # Test implementation
    pass
```

### Anti-Pattern 5: Skip Without Marker

```python
# ❌ BAD: Hard to filter and track
@pytest.mark.skip(reason="OCR deferred to Sprint 5+")
def test_ocr():
    pass

# ✓ GOOD: Use marker for categorization
@pytest.mark.skip(reason="OCR deferred to Sprint 5+")
@pytest.mark.post_mvp
def test_ocr():
    pass
```

---

## Skip vs. XFail

### When to Use Skip

Use `@pytest.mark.skip` when:
- Feature is intentionally not implemented yet
- Test requires unavailable dependency
- Test only works on specific platform
- Test requires external service not in CI

### When to Use XFail

Use `@pytest.mark.xfail` when:
- Test is expected to fail due to known bug
- Test is flaky and unpredictable
- Test documents expected behavior not yet achieved
- Test is for experimental feature

**Example**:

```python
# SKIP: Feature not implemented
@pytest.mark.skip(reason="OCR deferred to Sprint 5+")
def test_ocr():
    pass

# XFAIL: Feature implemented but has known bug
@pytest.mark.xfail(reason="OCR has accuracy issues with rotated text (bug #123)")
def test_ocr_rotated_text():
    # Test implementation - will run but failure is expected
    pass
```

---

## Tools and Commands

### List All Skipped Tests

```bash
# Show skipped tests with reasons
pytest tests/ -v | grep SKIP

# Show skip summary
pytest tests/ -v --tb=no | tail -20

# Collect tests without running (shows skip decorators)
pytest tests/ --co -q
```

### Run Only Skipped Tests

```bash
# Temporarily remove all skips to see what breaks
pytest tests/ --run-skipped

# Note: This requires pytest-skip-markers plugin
pip install pytest-skip-markers
```

### Filter by Skip Reason

```bash
# Skip tests with specific reason pattern
pytest tests/ -k "not ocr"

# Run only OCR tests (even if skipped, they show up)
pytest tests/ -k "ocr"
```

### Generate Skip Report

```bash
# Create skip audit report
pytest tests/ -v --tb=no 2>&1 | grep -A 1 "SKIPPED" > skip_report.txt

# Count skips by reason
pytest tests/ -v --tb=no 2>&1 | grep "SKIPPED" | sort | uniq -c
```

---

## Skip Documentation in Test Docstrings

For skipped tests, include skip rationale in docstring:

```python
@pytest.mark.skip(reason="OCR functionality deferred to Sprint 5+ (issue #123)")
@pytest.mark.post_mvp
def test_ocr_text_extraction():
    """
    Test OCR text extraction from image-based PDFs.

    SKIPPED: OCR functionality deferred to post-MVP Sprint 5+.
    Requires: pdf2image, pytesseract
    Issue: #123
    Estimated Sprint: 5+

    Test Plan:
    1. Create image-based PDF (no native text)
    2. Extract with OCR enabled
    3. Verify extracted text matches image content
    4. Verify confidence scores are set
    """
    # Test implementation
    pass
```

**Benefits**:
- Clear documentation of intent
- Easy to understand when reviewing code
- Requirements clearly stated
- Timeline visible

---

## Reporting Skip Statistics

Include skip statistics in test reports:

```bash
# Generate HTML report with skip details
pytest tests/ --html=report.html --self-contained-html

# Generate JUnit XML for CI
pytest tests/ --junitxml=junit.xml

# Show detailed skip summary
pytest tests/ -v --tb=short -ra
```

---

## Summary

### Key Principles

1. **Skip Intentionally**: Every skip should have a clear, specific reason
2. **Use Decorators**: Prefer `@pytest.mark.skip` over runtime `pytest.skip()`
3. **Categorize**: Use custom markers (post_mvp, etc.) for filtering
4. **Track**: Include issue numbers and timelines in skip reasons
5. **Review**: Audit skips quarterly or at milestones
6. **Document**: Explain skip rationale in test docstrings

### Quick Reference

```python
# Post-MVP feature
@pytest.mark.skip(reason="Feature deferred to Sprint X (issue #Y)")
@pytest.mark.post_mvp
def test_future_feature(): pass

# Platform-specific
@pytest.mark.skipif(sys.platform == "win32", reason="Unix-only")
@pytest.mark.platform_specific
def test_unix_feature(): pass

# Optional dependency
@pytest.mark.skipif(not HAS_LIB, reason="Requires lib package")
def test_optional_feature(): pass

# Fixture skip (acceptable)
@pytest.fixture
def resource():
    try:
        import lib
    except ImportError:
        pytest.skip("lib not installed")
    return lib.Resource()
```

---

**Version History**:
- **v1.0** (2025-10-30): Initial policy created after skip audit
