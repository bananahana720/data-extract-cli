# CLI Entry Points Analysis

## Summary
- Files scanned: 17 CLI-related files
- Key findings:
  - Main CLI entry point is placeholder (Epic 5 implementation pending)
  - 15 utility scripts for development, testing, and maintenance
  - Brownfield CLI exists but being replaced
  - Entry point registered in pyproject.toml as `data-extract`
  - Comprehensive script ecosystem for pipeline profiling and testing

## Detailed Analysis

### CLI Entry Points

#### Main Entry Point (`src/data_extract/cli.py`)

**Status**: Placeholder for Epic 5 implementation

**Current Implementation** (23 lines):
```python
"""CLI entry point for data-extract command.

Epic 5 will implement Typer-based CLI with:
- Command structure (extract, batch, config, version)
- Configuration cascade (CLI flags → env vars → YAML → defaults)
- Progress indicators and error handling

Temporary stub for pyproject.toml entry point definition.
"""

def app() -> None:
    """CLI application entry point (placeholder).

    Epic 5 will replace this with Typer app.
    """
    print("data-extract CLI (placeholder - Epic 5 will implement)")
    print("Current version: 0.1.0")

if __name__ == "__main__":
    app()
```

**Planned Epic 5 Features**:
1. **Command Structure**:
   - `data-extract extract <file>` - Single file extraction
   - `data-extract batch <directory>` - Batch processing
   - `data-extract config show` - Display active configuration
   - `data-extract config validate` - Validate configuration
   - `data-extract version` - Version information

2. **Configuration Cascade**:
   - CLI flags (highest precedence)
   - Environment variables (`DATA_EXTRACTOR_*`)
   - YAML config file (~/.data-extract/config.yaml or project-local)
   - Hardcoded defaults (lowest precedence)

3. **User Experience**:
   - Progress indicators (Rich library)
   - Colored output and formatting
   - Error handling with user-friendly messages
   - Verbose/quiet modes

**pyproject.toml Registration**:
```toml
[project.scripts]
data-extract = "data_extract.cli:app"
```

#### Brownfield CLI (`src/cli/__main__.py`)

**Status**: Existing implementation, being replaced by greenfield

**Purpose**: Legacy CLI entry point for brownfield architecture

**Note**: This module is in brownfield codebase (`src/cli/`) which is excluded from mypy type checking and being gradually replaced by greenfield implementation (`src/data_extract/cli.py`).

### Utility Scripts Ecosystem

**Total Scripts**: 15 development and maintenance scripts

#### Performance & Profiling Scripts (5 scripts)

**1. `scripts/profile_pipeline.py`** - Pipeline performance profiling
```python
# Key features:
- Process batch with ProcessPoolExecutor (parallelization)
- Memory tracking (main + worker processes)
- OCR confidence aggregation
- Performance metrics (throughput, duration, success rate)
- get_total_memory() function (9.6ms overhead)

# Usage:
python scripts/profile_pipeline.py
```

**Functions**:
- `get_total_memory()` - Aggregate memory (main + workers) in MB
- `process_batch(files, worker_count=4)` - Parallel batch processing
- `BatchResult` - Performance metrics data class

**2. `scripts/run_performance_suite.py`** - Run all performance tests
```python
# Purpose:
- Execute all performance tests in tests/performance/
- Generate performance reports
- Validate NFR-P1 and NFR-P2 targets

# Usage:
python scripts/run_performance_suite.py
```

**3. `scripts/measure_progress_overhead.py`** - Measure Rich progress overhead
```python
# Purpose:
- Measure Rich progress bar performance impact
- Compare with/without progress indicators
- Validate progress overhead is minimal

# Usage:
python scripts/measure_progress_overhead.py
```

**4. `scripts/test_progress_display.py`** - Test progress display
```python
# Purpose:
- Visual test of Rich progress bars
- Validate progress indicator behavior
- Demo for UI development

# Usage:
python scripts/test_progress_display.py
```

**5. `scripts/create_performance_batch.py`** - Generate 100-file test batch
```python
# Purpose:
- Create 100-file batch for NFR-P1 testing
- Mixed formats: 40 PDFs, 30 DOCX, 20 XLSX, 10 mixed
- Output: tests/performance/batch_100_files/

# Usage:
python scripts/create_performance_batch.py
```

#### Test Fixture Generation Scripts (3 scripts)

**6. `scripts/generate_large_pdf_fixture.py`** - Large PDF generation
```python
# Purpose:
- Generate multi-page PDF fixtures for stress testing
- Configurable page count, content density
- Used for memory and performance testing

# Usage:
python scripts/generate_large_pdf_fixture.py --pages 100 --output tests/fixtures/large.pdf
```

**7. `scripts/generate_large_excel_fixture.py`** - Large Excel generation
```python
# Purpose:
- Generate large workbooks for memory testing
- Configurable row count, sheet count
- Validate memory handling for large files

# Usage:
python scripts/generate_large_excel_fixture.py --rows 10000 --sheets 5
```

**8. `scripts/generate_scanned_pdf_fixture.py`** - Scanned PDF generation
```python
# Purpose:
- Generate scanned PDF for OCR testing
- Simulate real scanned documents
- Test OCR confidence tracking

# Usage:
python scripts/generate_scanned_pdf_fixture.py --output tests/fixtures/scanned.pdf
```

#### Testing & Validation Scripts (3 scripts)

**9. `scripts/run_test_extractions.py`** - Run extraction tests
```python
# Purpose:
- Execute extraction workflows on sample files
- Validate extractor functionality
- Quick smoke test for extractors

# Usage:
python scripts/run_test_extractions.py
```

**10. `scripts/regenerate_gold_standard.py`** - Regenerate expected outputs
```python
# Purpose:
- Regenerate "gold standard" expected outputs
- Used for regression test maintenance
- Update after intentional behavior changes

# Usage:
python scripts/regenerate_gold_standard.py
```

**11. `scripts/validate_installation.py`** - Installation validation
```python
# Purpose:
- Post-install validation checks
- Verify all dependencies installed
- Check CLI entry point registration

# Usage:
python scripts/validate_installation.py
```

#### Development Utility Scripts (4 scripts)

**12. `scripts/test_installation.py`** - Installation smoke tests
```python
# Purpose:
- Quick smoke tests post-install
- Verify basic functionality
- Import validation

# Usage:
python scripts/test_installation.py
```

**13. `scripts/check_package_contents.py`** - Package content verification
```python
# Purpose:
- Verify package data files included in distribution
- Check YAML, JSON, TXT files packaged
- Validate setuptools configuration

# Usage:
python scripts/check_package_contents.py
```

**14. `scripts/diagnose_ocr.py`** - OCR troubleshooting
```python
# Purpose:
- Diagnose OCR issues (Tesseract, pytesseract)
- Check Tesseract installation
- Validate OCR configuration

# Usage:
python scripts/diagnose_ocr.py
```

**15. `scripts/fix_import_paths.py`** - Import path correction
```python
# Purpose:
- Fix import paths during brownfield → greenfield migration
- Automated refactoring support
- Codebase maintenance

# Usage:
python scripts/fix_import_paths.py
```

### CLI Architecture Analysis

#### Current State (Epic 1)

**Entry Point**:
- Registered in pyproject.toml: `data-extract = "data_extract.cli:app"`
- Placeholder implementation (23 lines)
- Prints version and Epic 5 notice

**Dual Codebase Structure**:
- **Greenfield**: `src/data_extract/cli.py` (future)
- **Brownfield**: `src/cli/__main__.py` (legacy)

**Status**: Infrastructure ready, implementation deferred to Epic 5

#### Epic 5 CLI Design

**Technology Stack**:
- **Typer**: Type-safe CLI framework (planned)
- **Rich**: Progress bars and colored output (planned)
- **Click**: Underlying framework (already in dependencies)

**Command Structure** (planned):

```bash
# Extract commands
data-extract extract <file> [options]
data-extract extract --format json --output result.json document.pdf

# Batch commands
data-extract batch <directory> [options]
data-extract batch --format markdown --workers 4 ./documents/

# Configuration commands
data-extract config show
data-extract config show --section extractors
data-extract config validate
data-extract config validate --file custom-config.yaml

# Utility commands
data-extract version
data-extract version --verbose
```

**CLI Flags** (planned):
- `--format` / `-f`: Output format (json, markdown, chunked)
- `--output` / `-o`: Output file path
- `--config` / `-c`: Configuration file path
- `--workers` / `-w`: Worker count for batch processing
- `--verbose` / `-v`: Verbose output
- `--quiet` / `-q`: Quiet mode (minimal output)
- `--log-level`: Logging level (DEBUG, INFO, WARNING, ERROR)

**Progress Indicators** (Rich):
- File-level progress bar
- Batch progress overview
- ETA and throughput display
- Memory usage monitoring (optional)

**Error Handling**:
- User-friendly error messages (from error_codes.yaml)
- Suggested actions for common errors
- Exit codes (0 = success, 1 = error, 2 = validation error)

### Script Dependency Graph

**Performance Scripts**:
```
run_performance_suite.py
    ├── pytest performance tests
    │   └── test_throughput.py
    │       └── profile_pipeline.py (process_batch, get_total_memory)
    └── create_performance_batch.py (fixture generation)
```

**Profiling Workflow**:
```
profile_pipeline.py (core profiling utilities)
    ├── Used by: test_throughput.py
    ├── Used by: run_performance_suite.py
    └── Provides: BatchResult, get_total_memory(), process_batch()
```

**Fixture Generation Chain**:
```
Test Execution
    ├── create_performance_batch.py → 100-file batch
    ├── generate_large_pdf_fixture.py → Large PDFs
    ├── generate_large_excel_fixture.py → Large Excel files
    └── generate_scanned_pdf_fixture.py → Scanned PDFs
```

**Development Workflow**:
```
Development → Test → Validate
    ├── run_test_extractions.py (quick validation)
    ├── test_installation.py (post-install)
    ├── validate_installation.py (comprehensive check)
    └── check_package_contents.py (distribution validation)
```

### Script Usage Patterns

#### Common Script Patterns

**1. Performance Profiling Pattern**:
```bash
# Generate test batch
python scripts/create_performance_batch.py

# Run performance tests
pytest -m performance tests/performance/test_throughput.py -v

# Or use suite runner
python scripts/run_performance_suite.py
```

**2. Fixture Generation Pattern**:
```bash
# Generate all fixtures
python scripts/generate_large_pdf_fixture.py
python scripts/generate_large_excel_fixture.py
python scripts/generate_scanned_pdf_fixture.py
python scripts/create_performance_batch.py
```

**3. Installation Validation Pattern**:
```bash
# After pip install -e ".[dev]"
python scripts/test_installation.py
python scripts/validate_installation.py
python scripts/check_package_contents.py
```

**4. Development Testing Pattern**:
```bash
# Quick extractor smoke test
python scripts/run_test_extractions.py

# Regenerate gold standard after changes
python scripts/regenerate_gold_standard.py

# Full test suite
pytest
```

#### Script Organization

**scripts/ Directory Structure**:
```
scripts/
├── Performance & Profiling (5 scripts)
│   ├── profile_pipeline.py              # Core profiling utilities
│   ├── run_performance_suite.py         # Performance test runner
│   ├── create_performance_batch.py      # 100-file batch generator
│   ├── measure_progress_overhead.py     # Rich overhead measurement
│   └── test_progress_display.py         # Progress display testing
│
├── Fixture Generation (3 scripts)
│   ├── generate_large_pdf_fixture.py    # Large PDF generator
│   ├── generate_large_excel_fixture.py  # Large Excel generator
│   └── generate_scanned_pdf_fixture.py  # Scanned PDF generator
│
├── Testing & Validation (3 scripts)
│   ├── run_test_extractions.py          # Extractor smoke tests
│   ├── regenerate_gold_standard.py      # Expected output regeneration
│   └── validate_installation.py         # Installation validator
│
└── Development Utilities (4 scripts)
    ├── test_installation.py             # Post-install smoke tests
    ├── check_package_contents.py        # Package verification
    ├── diagnose_ocr.py                  # OCR troubleshooting
    └── fix_import_paths.py              # Import path fixer
```

## Recommendations

### CLI Implementation (Epic 5)

1. **Typer Migration**
   - Implement Typer-based CLI in `src/data_extract/cli.py`
   - Use type hints for automatic validation
   - Leverage Typer's automatic help generation
   - Add shell completion support (bash, zsh, fish)

2. **Command Structure**
   - Keep flat command structure (avoid deep nesting)
   - Use consistent naming (extract, batch, config, version)
   - Add command aliases for common operations
   - Implement `--help` for all commands with examples

3. **Configuration Cascade**
   - Implement 4-tier precedence (CLI → env → YAML → defaults)
   - Show final configuration with `data-extract config show`
   - Validate configuration with `data-extract config validate`
   - Add `--config-override` flag for one-off settings

4. **Progress Indicators**
   - Use Rich Progress for file-level progress
   - Add batch overview (files processed, ETA, throughput)
   - Show memory usage optionally (`--show-memory`)
   - Add quiet mode for scripting (`--quiet`)

5. **Error Handling**
   - Map error codes to user-friendly messages
   - Show suggested actions for common errors
   - Add `--debug` flag for detailed error output
   - Return appropriate exit codes (0, 1, 2)

### Script Improvements

1. **Script Consolidation**
   - Consider consolidating related scripts into CLI subcommands
   - Example: `data-extract dev test-extraction` (instead of run_test_extractions.py)
   - Keep scripts for development, but add CLI equivalents for users

2. **Script Documentation**
   - Add docstrings with usage examples to all scripts
   - Create `scripts/README.md` with script inventory
   - Add `--help` flags to all scripts
   - Document script dependencies and prerequisites

3. **Script Testing**
   - Add unit tests for script functions
   - Add integration tests for script workflows
   - Validate script exit codes
   - Test script error handling

### Development Workflow Integration

1. **CLI Development Tools**
   - Add `data-extract dev` namespace for development commands
   - Example: `data-extract dev profile <file>` (run profiler)
   - Example: `data-extract dev generate-fixtures` (fixture generation)
   - Example: `data-extract dev validate` (installation validation)

2. **Script to CLI Migration**
   - Migrate script functionality to CLI commands:
     - `profile_pipeline.py` → `data-extract dev profile`
     - `run_test_extractions.py` → `data-extract dev test-extraction`
     - `validate_installation.py` → `data-extract dev validate-install`

3. **Pre-commit Integration**
   - Add pre-commit hook for CLI tests
   - Run `data-extract config validate` before commit
   - Ensure CLI entry point is functional

### User Experience Improvements

1. **Interactive Mode**
   - Add interactive mode for batch processing
   - Prompt for configuration values if not provided
   - Show configuration preview before processing

2. **Dry Run Mode**
   - Add `--dry-run` flag to preview actions
   - Show what would be processed without actually processing
   - Estimate time and memory requirements

3. **Output Formatting**
   - Support multiple output formats (JSON, YAML, table)
   - Add `--format` flag for command output
   - Colorize output based on severity (errors, warnings, info)

4. **Shell Completion**
   - Generate shell completion scripts
   - Support bash, zsh, fish
   - Include dynamic completion (file paths, config options)

### Testing Strategy for CLI

1. **CLI Integration Tests**
   - Test all CLI commands (extract, batch, config, version)
   - Test configuration cascade (CLI → env → YAML → defaults)
   - Test progress indicators (Rich integration)
   - Test error handling and exit codes

2. **CLI Usability Tests**
   - Test help text clarity and completeness
   - Validate error messages are user-friendly
   - Test examples in help text are accurate
   - Validate CLI responsiveness (startup time <1s)

3. **CLI Automation Tests**
   - Test CLI in scripting scenarios (quiet mode, exit codes)
   - Test CLI with various input combinations
   - Test CLI with invalid inputs (error handling)

### Documentation Requirements

1. **CLI User Guide**
   - Create comprehensive CLI user guide
   - Include examples for common workflows
   - Document all commands and flags
   - Add troubleshooting section

2. **Script Reference**
   - Document all development scripts in `scripts/README.md`
   - Include usage examples and prerequisites
   - Add script dependency graph
   - Document when to use scripts vs CLI

3. **Developer Guide**
   - Document CLI architecture and design decisions
   - Add guide for adding new CLI commands
   - Document testing strategy for CLI
   - Include contribution guidelines for CLI changes

### Epic 5 Readiness Checklist

**CLI Implementation**:
- [ ] Implement Typer-based CLI in `src/data_extract/cli.py`
- [ ] Add `extract` command with all options
- [ ] Add `batch` command with parallelization
- [ ] Add `config show` and `config validate` commands
- [ ] Add `version` command with detailed info
- [ ] Implement configuration cascade (4-tier)
- [ ] Add Rich progress indicators
- [ ] Implement error handling with user-friendly messages
- [ ] Add shell completion support
- [ ] Write CLI integration tests (8+ test files)

**Script Migration**:
- [ ] Migrate `profile_pipeline.py` to `data-extract dev profile`
- [ ] Migrate `validate_installation.py` to `data-extract dev validate`
- [ ] Keep scripts for development workflow
- [ ] Document CLI equivalents in `scripts/README.md`

**Documentation**:
- [ ] Write CLI user guide with examples
- [ ] Document configuration cascade
- [ ] Add CLI troubleshooting guide
- [ ] Create script reference document
