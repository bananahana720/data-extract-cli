# Story 5-7 Fixtures - Quick Reference Guide

**Location**: `/tests/integration/test_cli/conftest.py`
**Tests Using These Fixtures**: 12 integration tests in `test_batch_incremental.py`

## Quick Start

### Using `processed_corpus_with_state` Fixture

```python
def test_my_incremental_test(self, processed_corpus_with_state: dict) -> None:
    """Test incremental processing with existing state."""
    # Access fixture data
    source_dir = processed_corpus_with_state["source_dir"]
    state_file = processed_corpus_with_state["state_file"]
    file_list = processed_corpus_with_state["file_list"]

    # Files already exist and are tracked in state
    assert source_dir.exists()
    assert state_file.exists()
    assert len(file_list) == 3
```

### Using `mixed_corpus` Fixture

```python
def test_mixed_files(self, mixed_corpus: dict) -> None:
    """Test processing with mixed file states."""
    # Access different file categories
    new_files = mixed_corpus["new_files"]          # Not in state
    modified_files = mixed_corpus["modified_files"]  # In state, changed
    unchanged_files = mixed_corpus["unchanged_files"]  # In state, same

    # Verify state tracking
    assert len(new_files) == 2
    assert len(modified_files) == 1
    assert len(unchanged_files) == 2
```

### Using `orphan_corpus` Fixture

```python
def test_orphan_cleanup(self, orphan_corpus: dict) -> None:
    """Test orphan detection and cleanup."""
    existing_files = orphan_corpus["existing_files"]
    orphaned_paths = orphan_corpus["orphaned_file_paths"]
    orphaned_outputs = orphan_corpus["orphaned_output_files"]

    # Orphaned paths are in state but not on disk
    assert all(not f.exists() for f in orphaned_paths)
    # Orphaned outputs exist without corresponding source
    assert all(f.exists() for f in orphaned_outputs)
```

## Fixture Features

| Feature | processed_corpus_with_state | mixed_corpus | orphan_corpus |
|---------|-------|-----------|--------|
| Source directory | ✓ | ✓ | ✓ |
| Output directory | ✓ | ✓ | ✓ |
| State file | ✓ | ✓ | ✓ |
| Test files | 3 files | 5 files (mixed) | 1 file + orphans |
| Hash computation | ✓ | ✓ | ✓ |
| File modifications | - | ✓ (1 modified) | - |
| Orphan simulation | - | - | ✓ |

## State File Structure

All fixtures generate JSON state files in `.data-extract-session/incremental-state.json`:

```python
{
    "version": "1.0",
    "source_dir": "<absolute_path>",
    "output_dir": "<absolute_path>",
    "processed_at": "ISO_8601_timestamp",
    "files": {
        "<file_path>": {
            "hash": "<sha256_hex>",
            "processed_at": "ISO_8601_timestamp",
            "output_path": "<output_file_path>",
            "size_bytes": 12345
        }
    }
}
```

## Fixture Data Access

### Dictionary Keys by Fixture

**processed_corpus_with_state:**
- `source_dir` - Path to source directory
- `output_dir` - Path to output directory
- `state_file` - Path to state file
- `file_list` - List of all files created

**mixed_corpus:**
- `source_dir` - Path to source directory
- `output_dir` - Path to output directory
- `state_file` - Path to state file
- `unchanged_files` - Files with same hash as in state
- `modified_files` - Files with different hash than in state
- `new_files` - Files not in state

**orphan_corpus:**
- `source_dir` - Path to source directory
- `output_dir` - Path to output directory
- `state_file` - Path to state file
- `existing_files` - Files that still exist on disk
- `orphaned_file_paths` - File paths in state but not on disk
- `orphaned_output_files` - Output files without corresponding source

## Common Test Patterns

### Pattern 1: Verify Incremental Processing Skips Unchanged Files

```python
def test_incremental_skips(self, processed_corpus_with_state: dict) -> None:
    source_dir = processed_corpus_with_state["source_dir"]
    state_file = processed_corpus_with_state["state_file"]

    # Verify all files are in initial state
    import json
    state = json.loads(state_file.read_text())
    assert len(state["files"]) == 3

    # Run incremental processing (unchanged)
    # ... CLI invocation ...

    # Verify no changes detected
    # ... assertions ...
```

### Pattern 2: Detect and Process New Files

```python
def test_new_files_processed(self, mixed_corpus: dict) -> None:
    source_dir = mixed_corpus["source_dir"]
    new_files = mixed_corpus["new_files"]

    # New files exist on disk but not in state
    assert len(new_files) == 2
    assert all(f.exists() for f in new_files)

    # Verify they're not in state
    state_file = mixed_corpus["state_file"]
    import json
    state = json.loads(state_file.read_text())

    for new_file in new_files:
        assert str(new_file) not in state["files"]
```

### Pattern 3: Detect Modifications

```python
def test_detect_modifications(self, mixed_corpus: dict) -> None:
    modified_files = mixed_corpus["modified_files"]
    state_file = mixed_corpus["state_file"]

    # Modified files exist with different content
    assert len(modified_files) == 1

    import json
    state = json.loads(state_file.read_text())

    for modified_file in modified_files:
        # File is in state
        assert str(modified_file) in state["files"]
        # But hash differs
        old_hash = state["files"][str(modified_file)]["hash"]
        # ... recompute hash ...
```

## Test Markers

All tests using these fixtures have markers:
```python
@pytest.mark.integration    # Integration test suite
@pytest.mark.story_5_7      # Story 5-7 specific tests
@pytest.mark.cli            # CLI testing
```

Run fixture-dependent tests:
```bash
pytest tests/integration/test_cli/test_batch_incremental.py -m story_5_7
```

## Fixture State Files

State files are ISO-8601 timestamped and include:
- **Version**: "1.0" (for schema validation)
- **Paths**: Absolute paths to source and output directories
- **Timestamps**: ISO format (e.g., "2025-11-29T15:42:30.123456")
- **File Hashes**: SHA256 hex strings (64 characters)
- **Sizes**: File size in bytes

## Cleanup

Fixtures use pytest's `tmp_path` mechanism, so all temporary files are automatically cleaned up after each test. No manual cleanup required.

## Troubleshooting

### Tests Can't Find Fixtures

**Error**: `Fixture 'processed_corpus_with_state' not found`

**Solution**: Ensure conftest.py is in the same directory or parent:
```
tests/integration/test_cli/
  ├── conftest.py          ← Fixtures here
  ├── test_batch_incremental.py
  └── test_fixtures_verification.py
```

### State File Not Found

**Error**: `FileNotFoundError: .data-extract-session/incremental-state.json`

**Solution**: Access the state file from fixture dict:
```python
state_file = processed_corpus_with_state["state_file"]
state = json.loads(state_file.read_text())
```

### Hash Mismatch in mixed_corpus

**Expect**: Modified files have different hash than in state

**Verify**: Use the `_compute_file_hash()` helper to check:
```python
from tests.integration.test_cli.conftest import _compute_file_hash
current_hash = _compute_file_hash(file_path)
# Compare against state["files"][str(file_path)]["hash"]
```

## Performance Notes

- **Fixture creation time**: <100ms per fixture
- **State file size**: ~1-2KB (typical)
- **Hash computation**: <50ms per file (for test files)

Fixtures use temporary directories and are isolated per test, ensuring no cross-test contamination.

## References

- **Fixture Implementation**: `/tests/integration/test_cli/conftest.py`
- **State File Schema**: `src/data_extract/cli/batch.py` (StateFile class)
- **Story Specification**: `docs/stories/5-7-batch-processing-optimization.md`
- **Complete Report**: `docs/artifacts/STORY_5_7_FIXTURE_CREATION_REPORT.md`
