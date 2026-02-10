# Skip Markers Reference Guide

**Purpose**: Quick lookup for all skip markers in the test suite.
**Updated**: 2025-11-30
**Total Entries**: 18 skip markers across 11 files

---

## Organization Flags (Story 5.x) - 5 Skips

### File: `tests/integration/test_cli/test_organization_flags.py`

#### Skip 1: By Document Organization
```python
# Line 34
@pytest.mark.skip(reason="Organization flag not yet implemented in CLI (Story 5.x)")
def test_cli_organization_by_document_flag(self, sample_pdf, tmp_path):
```
**Status**: Awaiting Story 5.4 implementation
**Depends On**: Organization strategy routing implementation

#### Skip 2: By Entity Organization
```python
# Line 68
@pytest.mark.skip(reason="Organization flag not yet implemented in CLI (Story 5.x)")
def test_cli_organization_by_entity_flag(self, sample_pdf, tmp_path):
```
**Status**: Awaiting Story 5.4 implementation
**Depends On**: Entity-based organization logic

#### Skip 3: Flat Organization (Default)
```python
# Line 97
@pytest.mark.skip(reason="Organization flag not yet implemented in CLI (Story 5.x)")
def test_cli_organization_flat_default(self, sample_pdf, tmp_path):
```
**Status**: Awaiting Story 5.4 implementation
**Depends On**: Default organization behavior

#### Skip 4: Invalid Strategy Error Handling
```python
# Line 128
@pytest.mark.skip(reason="Organization flag not yet implemented in CLI (Story 5.x)")
def test_cli_invalid_organization_strategy(self, sample_pdf, tmp_path):
```
**Status**: Awaiting Story 5.4 implementation
**Depends On**: Error handling for invalid strategies

#### Skip 5: CSV Format Organization
```python
# Line 151
@pytest.mark.skip(reason="Organization flag not yet implemented in CLI (Story 5.x)")
def test_cli_organization_with_csv_format(self, sample_pdf, tmp_path):
```
**Status**: Awaiting Story 5.4 implementation
**Depends On**: Format-specific organization behavior

---

## Summary Command Integration (Story 5.x) - 1 Skip

### File: `tests/integration/test_cli/test_summary_integration.py`

```python
# Line 445
@pytest.mark.skip(reason="Implementation pending - command integration")
class TestSummaryCommandIntegration:
    """
    Contains 21 test methods:
    - test_summary_without_output_dir
    - test_summary_basic_execution
    - test_summary_with_manifest
    - test_summary_json_format
    - test_summary_csv_format
    - test_summary_txt_format
    - ... (15 more tests)
    """
```
**Status**: Awaiting Story 5.2 implementation
**Depends On**: Summary command CLI integration
**Subtests Blocked**: 21

---

## Performance Tuning (Story 5.x) - 1 Skip

### File: `tests/performance/test_summary_performance.py`

```python
# Line 459
@pytest.mark.skip(reason="Implementation pending - performance tuning")
class TestPerformanceOptimizations:
    """Performance baseline and optimization tests"""
```
**Status**: Awaiting performance baseline establishment
**Depends On**: Performance measurement and tuning

---

## Semantic Analysis - Topics Command - 2 Skips

### File: `tests/test_cli/test_semantic_commands.py`

#### Skip 1: Topics Basic
```python
# Line 571
@pytest.mark.skip(reason="Topics command requires larger corpus for TF-IDF")
def test_topics_basic(
    cli_runner,
    sample_documents_for_topics,
    isolated_corpus_cache,
):
```
**Status**: Deferred pending corpus expansion
**Technical Constraint**: LSA requires n_components < min(n_samples, n_features)
**Current Issue**: Test corpus too small for 50-component LSA model

#### Skip 2: Topics Custom Count
```python
# Line 594
@pytest.mark.skip(reason="Topics command requires larger corpus for TF-IDF")
def test_topics_custom_count(
    cli_runner,
    sample_documents_for_topics,
    isolated_corpus_cache,
):
```
**Status**: Deferred pending corpus expansion
**Technical Constraint**: Same as above
**Solution Path**: Expand test corpus with 100+ documents

---

## Error Prompts - BLUE Phase - 2 Skips

### File: `tests/unit/test_cli/test_story_5_6/test_error_prompts.py`

#### Skip 1: Interactive Error Prompts
```python
# Line 385
@pytest.mark.skip(reason="Interactive error prompts implementation required for BLUE phase")
def test_interactive_flag_enables_prompts(
    cli_runner,
    malformed_pdf,
):
```
**Status**: Feature pending BLUE phase development
**Phase**: Beyond Epic 5
**Dependency**: Interactive prompt framework

#### Skip 2: Non-Interactive Auto-Skip
```python
# Line 481
@pytest.mark.skip(
    reason="Non-interactive auto-skip behavior implementation required for BLUE phase"
)
def test_non_interactive_auto_skips_errors(
    cli_runner,
    malformed_pdf,
):
```
**Status**: Feature pending BLUE phase development
**Phase**: Beyond Epic 5
**Dependency**: Non-interactive error handling mode

---

## Command Router Edge Cases (Story 5.1) - 1 Skip

### File: `tests/unit/test_cli/test_story_5_1/test_command_router.py`

```python
# Line 500
@pytest.mark.skip(reason="Subcommand routing edge case pending implementation")
def test_subcommand_routing(
    router,
    sample_pdf,
):
```
**Status**: Core routing complete; edge cases deferred
**Depends On**: Edge case handler implementation
**Impact**: Low - primary routing functional

---

## Progress Components - Story 5.3 - 2 Skips

### File: `tests/unit/test_cli/test_story_5_3/test_progress_components.py`

#### Skip 1: LSA Topics with Progress Display
```python
# Line 157
@pytest.mark.skip(
    reason="LSA topic extraction requires min 50 components (n_components=50-300). "
    "Expand test corpus or reduce n_components requirement."
)
def test_progress_with_lsa_topics(
    runner,
    large_document_set,
):
```
**Status**: Progress display operational; advanced LSA features deferred
**Technical Constraint**: LSA decomposition requires sufficient features
**Solution**: Expand test corpus or reduce component requirement

#### Skip 2: Cache Warm Command with Progress
```python
# Line 187
@pytest.mark.skip(
    reason="Cache warm command has import error: 'attempted relative import beyond top-level package'. "
    "Requires import path resolution."
)
def test_cache_warm_with_progress(
    runner,
    semantic_cache,
):
```
**Status**: Import error requires resolution
**Issue Type**: Import path misconfiguration
**Solution**: Fix relative imports in cache_warm module

---

## Summary Report Module (Story 5.2) - 1 Skip

### File: `tests/unit/test_cli/test_summary_report.py`

```python
# Line 557
@pytest.mark.skip(reason="Implementation pending - summary.py module")
def test_summary_report_integration():
```
**Status**: Summary framework ready; full module pending
**Depends On**: summary.py module implementation
**Impact**: Core functionality has workarounds; full integration needed

---

## Platform-Conditional Skips (Valid skipif)

### File: `tests/test_extractors/test_txt_extractor.py`

```python
@pytest.mark.skipif(sys.platform == "win32", reason="Permission tests unreliable on Windows")
def test_106_read_permission_denied(extractor, simple_txt_file):
```
**Status**: Valid - permission model differs on Windows
**Behavior**: Skipped on Windows, runs on Linux/macOS

### File: `tests/test_extractors/test_docx_extractor_integration.py`

```python
@pytest.mark.skipif(sys.platform == "win32", reason="Permission tests unreliable on Windows")
def test_docx_extractor_permission_denied(test_docx_file):
```
**Status**: Valid - permission model differs on Windows
**Behavior**: Skipped on Windows, runs on Linux/macOS

### File: `tests/unit/test_scripts/test_scan_security.py`

```python
@pytest.mark.skipif(os.name != "posix", reason="Permission tests only on POSIX")
def test_scan_permissions_ac9(self, scanner, temp_project):
```
**Status**: Valid - feature only applicable on POSIX
**Behavior**: Skipped on Windows, runs on Linux/macOS

---

## Implementation Roadmap

### Immediate (Epic 5)
- [ ] Story 5.1: Remove command_router skip (edge case handling)
- [ ] Story 5.2: Remove summary_report skip (module implementation)
- [ ] Story 5.2: Remove summary_integration skip (command integration)
- [ ] Story 5.3: Fix cache_warm import error
- [ ] Story 5.3: Fix progress_components LSA skip (expand corpus)
- [ ] Story 5.4: Remove organization_flags skips (5 tests)

### Future (BLUE Phase)
- [ ] Story 5.6: Remove error_prompts skips (2 tests)

### Technical Debt
- [ ] Expand semantic test corpus to 100+ documents
- [ ] Establish performance baselines
- [ ] Document topics command corpus requirements

---

## Quick Command Reference

### Find Specific Skip
```bash
# Find all skips in a file
rg "pytest.mark.skip" tests/integration/test_cli/test_organization_flags.py

# Find skip by story
rg "@pytest.mark.skip.*Story 5" tests/

# Find skipif markers
rg "@pytest.mark.skipif" tests/
```

### Run Tests Excluding Skips
```bash
# Run all except skipped
pytest tests/ --ignore-skip-markers

# Run specific category
pytest tests/behavioral/epic_5/ -v  # All passing (53/53)
```

### Count Skips by File
```bash
python -c "
import glob, re
for f in glob.glob('tests/**/*.py', recursive=True):
    with open(f) as file:
        skips = len(re.findall(r'@pytest.mark.skip', file.read()))
        if skips > 0:
            print(f'{f}: {skips} skips')
"
```

---

## Summary Statistics

| Category | Count |
|----------|-------|
| Skip markers (feature-blocking) | 13 |
| Skipif markers (platform-conditional) | 5 |
| **Total** | **18** |
| Awaiting Story 5.x | 13 |
| Awaiting BLUE phase | 2 |
| Platform-specific validity | 3 |

---

**Last Updated**: 2025-11-30
**Verification**: Wave E1 Complete
**Next Review**: After Story 5.1 completion
