# Story 5-7 Test Quick Reference

## Running the Tests

```bash
# All Story 5-7 tests
pytest -m story_5_7

# By layer
pytest tests/behavioral/epic_5/              # Behavioral (10)
pytest tests/unit/test_cli/test_incremental_processor.py  # Unit (17)
pytest tests/integration/test_cli/test_batch_incremental.py  # Integration (12)
pytest tests/uat/journeys/test_journey_7_incremental_batch.py  # UAT (10)
pytest tests/performance/test_incremental_performance.py  # Performance (3)

# Specific test class
pytest tests/unit/test_cli/test_incremental_processor.py::TestFileHasher -v

# With coverage
pytest -m story_5_7 --cov=src/data_extract/cli/batch

# Verbose output
pytest tests/behavioral/epic_5/test_incremental_behavior.py -vv
```

## Test Fixtures Available

### From `tests/behavioral/epic_5/conftest.py`

```python
# Empty state file template
def test_something(incremental_state_file: Path):
    assert incremental_state_file.exists()

# Corpus with processed files
def test_something(processed_corpus_with_state: dict):
    source_dir = processed_corpus_with_state["source_dir"]
    state_file = processed_corpus_with_state["state_file"]
    file_list = processed_corpus_with_state["file_list"]

# Corpus with deleted files
def test_something(orphan_corpus: dict):
    source_dir = orphan_corpus["source_dir"]
    deleted_files = orphan_corpus["deleted_files"]

# Corpus with all change types
def test_something(mixed_corpus: dict):
    new_files = mixed_corpus["new_files"]          # 2 files
    modified_files = mixed_corpus["modified_files"]  # 2 files
    unchanged_files = mixed_corpus["unchanged_files"] # 2 files
```

## Expected Implementation Structure

```python
# src/data_extract/cli/batch.py

class FileHasher:
    """Calculate SHA256 hashes for change detection."""
    def calculate_hash(self, file_path: str) -> str:
        """Return 64-char hex SHA256 hash."""

class StateFile:
    """Persist and load incremental processing state."""
    @classmethod
    def load(cls, path: str) -> 'StateFile':
        """Load state from JSON, raise SessionCorruptedError on invalid."""

    def save(self) -> None:
        """Atomically save state (temp file + rename)."""

    def add_file(self, path: str, hash: str, output: str, size: int):
        """Track a processed file."""

class ChangeDetector:
    """Detect file changes (new/modified/unchanged/orphan)."""
    def detect(self, source_dir: Path) -> dict:
        """Return change summary with counts and file lists."""

class GlobPatternExpander:
    """Expand glob patterns to matching files."""
    def expand(self, pattern: str, base_dir: str) -> list[Path]:
        """Match pattern, raise GlobPatternError if no matches."""

class IncrementalProcessor:
    """Main orchestrator for incremental processing."""
    def __init__(self, source_dir: str, state_file_path: str, config: dict = None):
        pass

    def detect_changes(self) -> dict:
        """Analyze changes since last processing."""

    def load_state(self) -> dict:
        """Load and validate state file."""
```

## Test Design Patterns Used

### GIVEN-WHEN-THEN Structure
```python
def test_example(fixture: Path):
    """
    RED: Brief description.

    Given: Initial state/setup
    When: Action performed
    Then: Expected outcome

    Expected RED failure: Why test fails before implementation
    """
    pytest.skip("Implementation pending")

    # Given
    setup_code()

    # When
    try:
        from module import Component
        result = Component().do_something()
    except ImportError:
        pytest.fail("Cannot import Component")

    # Then
    assert result == expected
```

### Fixture Patterns
```python
# Using tmp_path for isolation
def test_with_files(tmp_path: Path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "file.pdf").write_bytes(b"content")

# Using corpus fixtures
def test_with_processed_files(processed_corpus_with_state: dict):
    source_dir = processed_corpus_with_state["source_dir"]
    # Files already exist in tmp_path
```

## Common Test Scenarios

### Testing Change Detection
```python
def test_change_detection(mixed_corpus: dict):
    """Test that changes are properly detected."""
    source_dir = mixed_corpus["source_dir"]

    # Corpus contains:
    # - 2 unchanged files (same hash)
    # - 2 modified files (different hash)
    # - 2 new files (not in state)
```

### Testing State Persistence
```python
def test_state_persistence(processed_corpus_with_state: dict):
    """Test state survives between sessions."""
    state_file = processed_corpus_with_state["state_file"]

    # Load, verify, modify, save, reload, verify again
```

### Testing CLI Integration
```python
def test_cli_flag(tmp_path: Path):
    """Test CLI accepts flags."""
    from typer.testing import CliRunner
    from data_extract.cli.app import app

    runner = CliRunner()
    result = runner.invoke(app, ["process", str(tmp_path), "--incremental"])
    assert result.exit_code == 0
```

### Testing Performance
```python
def test_performance_baseline(tmp_path: Path):
    """Test meets performance requirement."""
    # Create large test data
    # Measure time
    # Assert elapsed < threshold

    start = time.perf_counter()
    # ... do work
    elapsed = time.perf_counter() - start
    assert elapsed < 2.0  # Must complete in 2 seconds
```

## State File Schema Reference

```json
{
  "version": "1.0",
  "source_dir": "/absolute/path/to/source",
  "output_dir": "/absolute/path/to/output",
  "config_hash": "sha256_hex_string",
  "processed_at": "2025-11-26T12:00:00",
  "files": {
    "/absolute/path/to/file.pdf": {
      "hash": "sha256_hex_string",
      "processed_at": "2025-11-26T12:00:00",
      "output_path": "/absolute/path/to/output/file.json",
      "size_bytes": 102400
    }
  }
}
```

## Implementation Checklist

- [ ] Create `src/data_extract/cli/batch.py`
- [ ] Implement `FileHasher` class
  - [ ] Run `pytest tests/unit/test_cli/test_incremental_processor.py::TestFileHasher -v`
- [ ] Implement `StateFile` class
  - [ ] Run `pytest tests/unit/test_cli/test_incremental_processor.py::TestStateFile -v`
- [ ] Implement `ChangeDetector` class
  - [ ] Run `pytest tests/unit/test_cli/test_incremental_processor.py::TestChangeDetector -v`
- [ ] Implement `GlobPatternExpander` class
  - [ ] Run `pytest tests/unit/test_cli/test_incremental_processor.py::TestGlobPatternExpansion -v`
- [ ] Implement `IncrementalProcessor` orchestrator
- [ ] Add CLI flag support (`--incremental`, `--force`)
  - [ ] Run `pytest tests/integration/test_cli/test_batch_incremental.py -v`
- [ ] Implement `status` command
- [ ] Run behavioral tests
  - [ ] Run `pytest tests/behavioral/epic_5/test_incremental_behavior.py -v`
- [ ] Run UAT tests
  - [ ] Run `pytest tests/uat/journeys/test_journey_7_incremental_batch.py -v`
- [ ] Run performance tests
  - [ ] Run `pytest tests/performance/test_incremental_performance.py -v`
- [ ] Run all Story 5-7 tests
  - [ ] Run `pytest -m story_5_7 --cov=src/data_extract/cli/batch`

## Debugging Tips

### Import Errors
If tests skip with "Cannot import", the module/class doesn't exist yet:
```
Implementation pending - create the import path first
```

### Test Failures (After Implementation)
```bash
# Show detailed output
pytest tests/.../test_file.py::TestClass::test_method -vv

# Show print statements
pytest tests/.../test_file.py::TestClass::test_method -s

# Drop into debugger on failure
pytest tests/.../test_file.py::TestClass::test_method --pdb

# Run only failed tests from last run
pytest --lf tests/...
```

### Fixture Issues
```bash
# Show available fixtures
pytest --fixtures tests/behavioral/epic_5/

# Show fixture usage
pytest tests/behavioral/epic_5/test_incremental_behavior.py::TestChangeDetectionBehavior::test_unchanged_files_not_reprocessed --setup-show
```

## Common Assertions

```python
# File operations
assert state_file.exists()
assert (source_dir / "file.pdf").stat().st_size > 0

# Change detection
assert change_summary["new"] == 2
assert change_summary["modified"] == 1
assert change_summary["unchanged"] == 5
assert change_summary["orphans"] == 0

# State file
assert "version" in state
assert state["files"] is not None
assert isinstance(state["files"], dict)

# Performance
assert elapsed < 2.0
assert len(file_hash) == 64

# CLI
assert result.exit_code == 0
assert "error" not in result.stdout.lower()
```

## Files & Locations Quick Links

| Test Type | File | Tests | Fixture Deps |
|-----------|------|-------|--------------|
| Behavioral | `tests/behavioral/epic_5/test_incremental_behavior.py` | 10 | conftest.py |
| Unit | `tests/unit/test_cli/test_incremental_processor.py` | 17 | tmp_path |
| Integration | `tests/integration/test_cli/test_batch_incremental.py` | 12 | tmp_path |
| UAT | `tests/uat/journeys/test_journey_7_incremental_batch.py` | 10 | tmux_session |
| Performance | `tests/performance/test_incremental_performance.py` | 3 | tmp_path |
| Fixtures | `tests/behavioral/epic_5/conftest.py` | - | tmp_path |
