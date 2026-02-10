# Story 5-7 ATDD Test Skeleton Summary

**Date**: 2025-11-26
**Task**: Create comprehensive test skeletons for Story 5-7 (Batch Processing Optimization and Incremental Updates)
**Status**: Complete - All 6 test files created with full test coverage

## Files Created

### 1. Core Fixtures & Setup
**File**: `tests/behavioral/epic_5/conftest.py`
**Type**: Shared fixtures for all Epic 5 behavioral tests
**Contents**:
- Pytest marker configuration
- `incremental_state_file` fixture - empty state initialization
- `processed_corpus_with_state` fixture - pre-processed files with state tracking
- `orphan_corpus` fixture - deleted files detection setup
- `mixed_corpus` fixture - mixed file change states (new/modified/unchanged)

**Key Features**:
- All fixtures use `tmp_path` for isolation
- State files follow incremental state schema (v1.0)
- Realistic test data with SHA256 hashes
- Datetime tracking for file modifications

### 2. Behavioral Tests - Change Detection
**File**: `tests/behavioral/epic_5/test_incremental_behavior.py`
**Type**: Behavioral validation tests
**Test Count**: 10 tests
**Test Classes**: 4

#### TestChangeDetectionBehavior (5 tests)
- `test_unchanged_files_not_reprocessed` - Files with matching hash skipped
- `test_modified_files_detected_by_hash` - Hash mismatch detected
- `test_new_files_detected_not_in_state` - New files identified
- `test_deleted_files_detected_as_orphans` - Missing source files detected
- `test_config_change_detected_and_invalidates_cache` - Config mismatch triggers full reprocess

#### TestStateFilePersistence (3 tests)
- `test_state_file_persists_across_sessions` - State survives between CLI runs
- `test_state_file_atomic_writes` - No partial writes left behind
- `test_state_file_schema_validation` - Corrupted files raise SessionCorruptedError

#### TestIncrementalModeIntegration (2 tests)
- `test_incremental_flag_activates_change_detection` - Flag routing
- `test_force_flag_bypasses_incremental_skip` - Force override behavior

**Markers**: `@pytest.mark.behavioral`, `@pytest.mark.story_5_7`, `@pytest.mark.cli`, `@pytest.mark.incremental`

### 3. Unit Tests - Components
**File**: `tests/unit/test_cli/test_incremental_processor.py`
**Type**: Unit tests for individual components
**Test Count**: 17 tests
**Test Classes**: 4

#### TestFileHasher (4 tests)
- `test_sha256_hash_deterministic` - Same content produces same hash
- `test_different_content_produces_different_hash` - Content changes cause hash changes
- `test_large_file_hash_calculation` - 100MB+ file hashing
- `test_binary_file_hash` - PDF binary content hashing

#### TestStateFile (4 tests)
- `test_state_file_schema_valid` - Required JSON fields present
- `test_state_file_read_write` - Persistence and recall
- `test_state_file_atomic_writes` - No temp files left behind
- `test_state_file_corruption_handling` - SessionCorruptedError on bad JSON

#### TestChangeDetector (5 tests)
- `test_detects_new_files` - Files not in state identified
- `test_detects_modified_files` - Hash mismatch detected
- `test_detects_unchanged_files` - Hash match identified
- `test_detects_deleted_files` - Missing files marked as orphans
- `test_change_summary_totals` - Accurate count summaries

#### TestGlobPatternExpansion (4 tests)
- `test_simple_extension_pattern` - `*.pdf` pattern matching
- `test_recursive_pattern` - `**/*.pdf` recursive matching
- `test_pattern_no_matches_error` - GlobPatternError on no matches
- `test_multiple_patterns_union` - Combined pattern handling

**Markers**: `@pytest.mark.unit`, `@pytest.mark.story_5_7`, `@pytest.mark.cli`

### 4. Integration Tests - CLI Commands
**File**: `tests/integration/test_cli/test_batch_incremental.py`
**Type**: Integration tests for CLI flag/command handling
**Test Count**: 12 tests
**Test Classes**: 4

#### TestProcessIncrementalFlag (4 tests)
- `test_incremental_flag_accepted_by_process_command` - Flag parsing
- `test_incremental_mode_creates_state_file` - State file creation
- `test_incremental_skips_unchanged_files` - Skip logic works
- `test_incremental_processes_new_files_only` - Selective processing

#### TestProcessForceFlag (2 tests)
- `test_force_flag_reprocesses_all_files` - Force overrides skip
- `test_force_flag_updates_state_with_new_timestamps` - State updated

#### TestStatusCommand (4 tests)
- `test_status_command_displays_panel` - Panel formatting
- `test_status_shows_processed_file_count` - File count display
- `test_status_shows_sync_state` - New/Modified/Unchanged counts
- `test_status_offers_cleanup_option_for_orphans` - Orphan cleanup suggestion

#### TestGlobPatternCLI (2 tests)
- `test_process_accepts_glob_pattern_argument` - Pattern argument parsing
- `test_glob_pattern_displays_match_count` - Match count feedback

**Markers**: `@pytest.mark.integration`, `@pytest.mark.story_5_7`, `@pytest.mark.cli`

### 5. UAT Journey Tests - User Workflows
**File**: `tests/uat/journeys/test_journey_7_incremental_batch.py`
**Type**: User acceptance tests for complete workflows
**Test Count**: 10 tests
**Test Classes**: 2

#### TestJourney7IncrementalBatch (7 tests)
- `test_change_detection_panel_displays` - Panel with New/Modified/Unchanged counts
- `test_incremental_processes_only_changes` - Only changed files processed
- `test_time_savings_displayed` - "Time saved: ~X minutes" message
- `test_force_flag_reprocesses_all` - --force enables full reprocess
- `test_status_command_shows_sync_state` - Sync state panel
- `test_orphan_detection_and_cleanup` - Orphan detection and cleanup option
- `test_glob_pattern_support` - Pattern matching in process command

#### TestJourney7Assertions (3 tests)
- `test_change_panel_assertion` - Change panel output validation
- `test_time_savings_assertion` - Time savings message validation
- `test_orphan_cleanup_assertion` - Orphan cleanup suggestion validation

**Markers**: `@pytest.mark.uat`, `@pytest.mark.journey`
**Framework**: Uses `TmuxSession`, `assert_contains`, `assert_panel_displayed`, `assert_command_success`

### 6. Performance Tests - Benchmarks
**File**: `tests/performance/test_incremental_performance.py`
**Type**: Performance regression tests
**Test Count**: 3 tests
**Test Classes**: 1

#### TestIncrementalPerformance (3 tests)
- `test_state_check_startup_under_2_seconds` - 1000+ files checked in <2s
- `test_hash_calculation_reasonable_for_large_files` - 100MB file in <5s
- `test_state_file_load_under_100ms` - 1000 entries loaded in <100ms

**Markers**: `@pytest.mark.performance`, `@pytest.mark.story_5_7`

## Test Statistics

| Layer | File | Tests | Classes |
|-------|------|-------|---------|
| **Behavioral** | test_incremental_behavior.py | 10 | 4 |
| **Unit** | test_incremental_processor.py | 17 | 4 |
| **Integration** | test_batch_incremental.py | 12 | 4 |
| **UAT** | test_journey_7_incremental_batch.py | 10 | 2 |
| **Performance** | test_incremental_performance.py | 3 | 1 |
| **TOTAL** | 6 files | **52 tests** | 15 classes |

## Test Coverage by Feature

### Incremental Processing Core
- ✅ File change detection (new/modified/unchanged/orphan)
- ✅ SHA256 hash calculation and verification
- ✅ Configuration change detection
- ✅ State file persistence and recovery

### State Management
- ✅ Atomic state file writes
- ✅ Corruption detection and recovery
- ✅ Cross-session state persistence
- ✅ File entry tracking (hash, timestamp, output path)

### CLI Integration
- ✅ `--incremental` flag parsing
- ✅ `--force` flag override
- ✅ `status` command output
- ✅ Glob pattern expansion
- ✅ Incremental mode startup <2s
- ✅ State check performance

### User Workflows (Journeys)
- ✅ Change detection panel display
- ✅ Processing only changes
- ✅ Time savings calculation and display
- ✅ Orphan detection and cleanup
- ✅ Glob pattern support

### Performance Requirements
- ✅ Startup check <2 seconds (1000+ files)
- ✅ SHA256 hashing <5 seconds (100MB)
- ✅ State load <100ms (1000+ entries)

## Fixture Architecture

### State File Fixtures
All fixtures create realistic state files following the incremental state schema:

```json
{
  "version": "1.0",
  "source_dir": "/path/to/source",
  "output_dir": "/path/to/output",
  "config_hash": "sha256...",
  "processed_at": "ISO datetime",
  "files": {
    "/path/to/file.pdf": {
      "hash": "sha256...",
      "processed_at": "ISO datetime",
      "output_path": "/path/to/output.json",
      "size_bytes": 1024
    }
  }
}
```

### Corpus Fixtures
- `incremental_state_file` - Empty state template
- `processed_corpus_with_state` - 3 files previously processed
- `orphan_corpus` - 2 existing + 3 deleted files
- `mixed_corpus` - 2 unchanged + 2 modified + 2 new files

## Implementation Notes

### Anticipated Implementation Patterns

**FileHasher Component**:
```python
class FileHasher:
    def calculate_hash(self, file_path: str) -> str:
        # Streaming SHA256 for large files
        # Return 64-char hex string
```

**StateFile Component**:
```python
class StateFile:
    @classmethod
    def load(cls, path: str) -> 'StateFile':
        # Load and validate JSON schema
        # Raise SessionCorruptedError on invalid

    def save(self) -> None:
        # Atomic write: temp file + rename
```

**ChangeDetector Component**:
```python
class ChangeDetector:
    def detect(self, source_dir: Path) -> dict:
        # Returns: {
        #   'new': int, 'new_files': list,
        #   'modified': int, 'modified_files': list,
        #   'unchanged': int,
        #   'orphans': int, 'orphan_files': list,
        #   'reprocess_all': bool, 'reason': str
        # }
```

**GlobPatternExpander Component**:
```python
class GlobPatternExpander:
    def expand(self, pattern: str, base_dir: str) -> list[Path]:
        # Use pathlib.Path.glob()
        # Raise GlobPatternError if no matches
```

**IncrementalProcessor (Main Orchestrator)**:
```python
class IncrementalProcessor:
    def __init__(self, source_dir: str, state_file_path: str, config: dict = None):
        pass

    def detect_changes(self) -> dict:
        # Use FileHasher, StateFile, ChangeDetector
        # Return change summary
```

## Red Phase Test Design

All tests use:
- `pytest.skip("Implementation pending")` before assertions
- Try/except with `pytest.fail()` for import errors
- GIVEN-WHEN-THEN comment structure
- Descriptive docstrings with "Expected RED failure"

This ensures tests will fail cleanly when implementation is pending.

## Next Steps for Implementation

1. **Create incremental module**: `src/data_extract/cli/batch.py`
2. **Implement components** in order:
   - FileHasher (lowest-level)
   - StateFile (persistence)
   - ChangeDetector (logic)
   - GlobPatternExpander (utility)
   - IncrementalProcessor (orchestrator)
3. **Run unit tests** → fix component-level issues
4. **Run behavioral tests** → fix behavior-level issues
5. **Run integration tests** → fix CLI integration issues
6. **Run UAT tests** → validate user workflows
7. **Run performance tests** → validate performance requirements

## Quality Assurance Notes

- All tests use `tmp_path` fixture for isolation
- No mocking of file I/O (tests use real files)
- Tests follow existing project patterns (Story 5-1, Epic 4)
- Consistent with CLAUDE.md conventions
- Ready for pre-commit hook validation
