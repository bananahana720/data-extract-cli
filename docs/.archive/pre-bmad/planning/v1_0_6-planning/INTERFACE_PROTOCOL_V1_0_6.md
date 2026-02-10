# Interface Protocol v1.0.6

## Overview

**Version**: v1.0.6
**Features**: DOCX image extraction, CSV extractor
**Purpose**: Ensure architectural consistency, code quality, and seamless integration with existing codebase

This document defines mandatory patterns, standards, and contracts that all v1.0.6 implementations must follow.

---

## BaseExtractor Contract

All extractors implement `BaseExtractor` from `src/core/interfaces.py`.

### Required Methods

```python
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any
from ..core.models import ExtractionResult

class BaseExtractor(ABC):
    @abstractmethod
    def extract(self, file_path: Path) -> ExtractionResult:
        """
        Extract content from file.

        Args:
            file_path: Absolute path to file

        Returns:
            ExtractionResult with success status, content blocks, metadata, errors

        Raises:
            ValueError: If file_path is None or empty
            TypeError: If file_path is not Path object
        """
        pass

    @abstractmethod
    def supports_file(self, file_path: Path) -> bool:
        """
        Check if extractor can handle this file.

        Args:
            file_path: Path to check

        Returns:
            True if file extension matches supported types
        """
        pass
```

### Type Hint Requirements

- **ALL** public methods: Full type hints for parameters and return values
- **ALL** class attributes: Type annotations
- Use `typing` module for complex types: `Dict`, `List`, `Optional`, `Union`, `Any`
- Path objects: Always `pathlib.Path`, never `str`

### Docstring Requirements

**Format**: Google style

**Required sections**:
- One-line summary
- `Args`: All parameters with types and descriptions
- `Returns`: Return type and description
- `Raises`: All exceptions with conditions
- `Examples`: For class docstrings

---

## Configuration Pattern

### ConfigManager Detection

```python
from pathlib import Path
from typing import Dict, Any, Optional
from ..infrastructure.config_manager import ConfigManager

class MyExtractor(BaseExtractor):
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize extractor with configuration.

        Args:
            config: Configuration dict or None for defaults
        """
        # Detect ConfigManager vs dict
        if isinstance(config, ConfigManager):
            self.config = config
        else:
            # Fallback to dict
            self.config = config or {}

        # Extract settings with defaults
        if isinstance(self.config, ConfigManager):
            self.setting_a = self.config.get('extractor.setting_a', default=True)
            self.setting_b = self.config.get('extractor.setting_b', default=100)
        else:
            self.setting_a = self.config.get('setting_a', True)
            self.setting_b = self.config.get('setting_b', 100)
```

### Config Keys Pattern

- ConfigManager: `'extractor.setting_name'` (dotted path)
- Dict: `'setting_name'` (flat keys)
- Always provide defaults
- Document all config options in class docstring

---

## Infrastructure Integration

### Availability Check

```python
from ..infrastructure import INFRASTRUCTURE_AVAILABLE

if INFRASTRUCTURE_AVAILABLE:
    from ..infrastructure.logger import get_logger
    from ..infrastructure.error_handler import ErrorHandler
```

### Logger Usage

```python
class MyExtractor(BaseExtractor):
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        # ... config setup ...

        # Initialize logger
        if INFRASTRUCTURE_AVAILABLE:
            self.logger = get_logger(__name__)
        else:
            self.logger = None

    def extract(self, file_path: Path) -> ExtractionResult:
        if self.logger:
            self.logger.debug(f"Extracting from {file_path}")

        # ... extraction logic ...

        if self.logger:
            self.logger.info(f"Extracted {len(blocks)} blocks from {file_path}")
```

### ErrorHandler Usage

```python
def extract(self, file_path: Path) -> ExtractionResult:
    try:
        # ... extraction logic ...
        pass
    except Exception as e:
        if INFRASTRUCTURE_AVAILABLE:
            error_msg = ErrorHandler.handle_extraction_error(
                error=e,
                file_path=file_path,
                extractor_name=self.__class__.__name__
            )
        else:
            error_msg = f"Extraction failed: {str(e)}"

        return ExtractionResult(
            success=False,
            content_blocks=[],
            metadata={},
            errors=(error_msg,)
        )
```

### Complete Example

```python
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from ..core.interfaces import BaseExtractor
from ..core.models import ExtractionResult, ContentBlock
from ..infrastructure import INFRASTRUCTURE_AVAILABLE

if INFRASTRUCTURE_AVAILABLE:
    from ..infrastructure.logger import get_logger
    from ..infrastructure.error_handler import ErrorHandler

class MyExtractor(BaseExtractor):
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        # Config
        if isinstance(config, ConfigManager):
            self.config = config
        else:
            self.config = config or {}

        # Logger
        if INFRASTRUCTURE_AVAILABLE:
            self.logger = get_logger(__name__)
        else:
            self.logger = None

        # Settings
        self._load_settings()

    def _load_settings(self) -> None:
        """Load configuration settings with defaults."""
        if isinstance(self.config, ConfigManager):
            self.my_setting = self.config.get('extractor.my_setting', default=True)
        else:
            self.my_setting = self.config.get('my_setting', True)
```

---

## Error Handling Protocol

### File-Level Errors

**Pattern**: Return `ExtractionResult(success=False)` with error message

**Use for**: File not found, unreadable, corrupted, wrong format

```python
def extract(self, file_path: Path) -> ExtractionResult:
    # Validation
    if not file_path or not isinstance(file_path, Path):
        return ExtractionResult(
            success=False,
            content_blocks=[],
            metadata={},
            errors=("Invalid file path",)
        )

    if not file_path.exists():
        return ExtractionResult(
            success=False,
            content_blocks=[],
            metadata={},
            errors=(f"File not found: {file_path}",)
        )

    try:
        # ... extraction logic ...
        pass
    except Exception as e:
        if INFRASTRUCTURE_AVAILABLE:
            error_msg = ErrorHandler.handle_extraction_error(
                error=e,
                file_path=file_path,
                extractor_name=self.__class__.__name__
            )
        else:
            error_msg = f"Extraction failed: {str(e)}"

        return ExtractionResult(
            success=False,
            content_blocks=[],
            metadata={},
            errors=(error_msg,)
        )
```

### Programming Errors

**Pattern**: Raise exceptions

**Use for**: Invalid arguments, type errors, assertion failures

```python
def extract(self, file_path: Path) -> ExtractionResult:
    if not isinstance(file_path, Path):
        raise TypeError(f"file_path must be Path, got {type(file_path)}")
```

### Per-Item Errors

**Pattern**: Try/except with warnings, continue processing

**Use for**: Individual images fail, single row corrupt, one table malformed

```python
def _extract_images(self, document) -> Tuple[List[ContentBlock], List[str]]:
    """Extract images, collecting warnings for failures."""
    blocks = []
    warnings = []

    for idx, image in enumerate(document.images):
        try:
            block = self._process_image(image, idx)
            blocks.append(block)
        except Exception as e:
            warning = f"Image {idx} extraction failed: {str(e)}"
            warnings.append(warning)
            if self.logger:
                self.logger.warning(warning)
            # Continue processing remaining images
            continue

    return blocks, warnings
```

---

## Data Model Requirements

### ExtractionResult Structure

```python
from dataclasses import dataclass
from typing import List, Dict, Any, Tuple

@dataclass(frozen=True)
class ExtractionResult:
    success: bool
    content_blocks: List[ContentBlock]
    metadata: Dict[str, Any]
    errors: Tuple[str, ...] = ()
    warnings: Tuple[str, ...] = ()
```

**Requirements**:
- `success=True`: Content extracted, may have warnings
- `success=False`: Fatal error, `content_blocks` empty, `errors` populated
- `warnings`: Non-fatal issues, extraction continues
- `errors`: Fatal issues, extraction stops
- Both `errors` and `warnings`: Immutable tuples

### ContentBlock Usage

```python
from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass(frozen=True)
class ContentBlock:
    content_type: str  # 'text', 'table', 'image', etc.
    content: Any       # Type varies by content_type
    metadata: Dict[str, Any]
    source_reference: Optional[str] = None
```

**Content types**:
- `'text'`: `content` is `str`
- `'table'`: `content` is `List[List[str]]`
- `'image'`: `content` is `bytes` (binary data)
- `'metadata'`: `content` is `Dict[str, Any]`

### Metadata Structures

**ImageMetadata**:
```python
{
    'format': 'PNG',           # Image format
    'width': 800,              # Pixels
    'height': 600,             # Pixels
    'size_bytes': 45231,       # File size
    'image_index': 0,          # Position in document
    'source_location': 'slide_1',  # Where found
    'description': 'Chart showing revenue'  # Optional alt text
}
```

**TableMetadata**:
```python
{
    'rows': 10,
    'columns': 5,
    'has_header': True,
    'table_index': 0,
    'source_location': 'page_3'
}
```

### Immutability Requirement

**All data models**: `@dataclass(frozen=True)`

**Rationale**: Thread safety, predictable behavior, cache-friendly

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class MyMetadata:
    field_a: str
    field_b: int
```

### Type Safety

- Use specific types, not `Any` unless truly dynamic
- Prefer `Optional[T]` over `T | None` for clarity
- Use `Tuple[str, ...]` for variable-length immutable sequences
- Use `List[T]` for mutable sequences
- Use `Dict[str, Any]` for metadata dictionaries

---

## Testing Protocol

### Test File Location

**Pattern**: `tests/test_<module>/<test_file>.py`

**Examples**:
- Extractor: `tests/test_extractors/test_csv_extractor.py`
- Processor: `tests/test_processors/test_my_processor.py`
- Formatter: `tests/test_formatters/test_my_formatter.py`

### Minimum Coverage

**Target**: ≥85% for new code

**Command**:
```bash
pytest tests/test_extractors/test_csv_extractor.py --cov=src/extractors/csv_extractor --cov-report=term-missing
```

### Required Test Types

#### 1. Basic Functionality (Happy Path)

```python
def test_extract_valid_file(csv_extractor, tmp_path):
    """Test extraction from valid CSV file."""
    # Arrange
    csv_file = tmp_path / "test.csv"
    csv_file.write_text("Name,Age\nAlice,30\nBob,25")

    # Act
    result = csv_extractor.extract(csv_file)

    # Assert
    assert result.success is True
    assert len(result.content_blocks) > 0
    assert result.errors == ()
```

#### 2. Edge Cases

```python
def test_extract_empty_file(csv_extractor, tmp_path):
    """Test extraction from empty file."""
    csv_file = tmp_path / "empty.csv"
    csv_file.write_text("")

    result = csv_extractor.extract(csv_file)

    # May succeed with no blocks or fail gracefully
    assert result.errors == () or "empty" in result.errors[0].lower()

def test_extract_large_file(csv_extractor, tmp_path):
    """Test extraction from file with 10,000+ rows."""
    # ... test implementation ...
```

#### 3. Error Handling

```python
def test_extract_nonexistent_file(csv_extractor, tmp_path):
    """Test extraction from missing file."""
    result = csv_extractor.extract(tmp_path / "nonexistent.csv")

    assert result.success is False
    assert len(result.errors) > 0
    assert "not found" in result.errors[0].lower()

def test_extract_corrupted_file(csv_extractor, tmp_path):
    """Test extraction from corrupted file."""
    # ... test implementation ...
```

#### 4. Configuration Options

```python
def test_custom_delimiter(tmp_path):
    """Test CSV extraction with tab delimiter."""
    config = {'delimiter': '\t'}
    extractor = CSVExtractor(config)

    csv_file = tmp_path / "test.tsv"
    csv_file.write_text("Name\tAge\nAlice\t30")

    result = extractor.extract(csv_file)

    assert result.success is True
```

#### 5. Integration with Pipeline

```python
def test_pipeline_integration(tmp_path):
    """Test extractor works with ExtractionPipeline."""
    from src.pipeline.extraction_pipeline import ExtractionPipeline

    csv_file = tmp_path / "test.csv"
    csv_file.write_text("Name,Age\nAlice,30")

    pipeline = ExtractionPipeline()
    result = pipeline.process_file(csv_file)

    assert result.success is True
```

### Test Fixture Patterns

```python
import pytest
from pathlib import Path
from src.extractors.csv_extractor import CSVExtractor

@pytest.fixture
def csv_extractor():
    """Provide CSVExtractor instance with default config."""
    return CSVExtractor()

@pytest.fixture
def sample_csv(tmp_path):
    """Provide sample CSV file."""
    csv_file = tmp_path / "sample.csv"
    csv_file.write_text("Name,Age\nAlice,30\nBob,25")
    return csv_file
```

### Assertion Patterns

```python
# Success status
assert result.success is True

# Content blocks
assert len(result.content_blocks) == expected_count
assert result.content_blocks[0].content_type == 'table'

# Metadata
assert 'rows' in result.metadata
assert result.metadata['rows'] == 10

# Errors and warnings
assert result.errors == ()
assert len(result.warnings) == 1
assert "warning text" in result.warnings[0].lower()

# Type checking
assert isinstance(result, ExtractionResult)
assert isinstance(result.content_blocks[0], ContentBlock)
```

---

## Code Quality Standards

### Type Hints

**Requirement**: All public methods and attributes

```python
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path

class MyExtractor(BaseExtractor):
    # Attribute annotations
    config: Dict[str, Any]
    logger: Optional[Any]
    setting_a: bool

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize extractor."""
        pass

    def extract(self, file_path: Path) -> ExtractionResult:
        """Extract content from file."""
        pass

    def _helper_method(self, data: List[str]) -> Tuple[str, ...]:
        """Private helper with type hints."""
        pass
```

### Docstrings

**Format**: Google style

**Class docstring**:
```python
class CSVExtractor(BaseExtractor):
    """
    Extract structured data from CSV files.

    Handles CSV files with configurable delimiters, quoting, and encoding.
    Supports header detection and type inference.

    Configuration:
        delimiter (str): Field delimiter (default: ',')
        encoding (str): File encoding (default: 'utf-8')
        has_header (bool): First row is header (default: True)

    Examples:
        >>> extractor = CSVExtractor()
        >>> result = extractor.extract(Path('data.csv'))
        >>> result.success
        True
    """
```

**Method docstring**:
```python
def extract(self, file_path: Path) -> ExtractionResult:
    """
    Extract content from CSV file.

    Args:
        file_path: Absolute path to CSV file

    Returns:
        ExtractionResult with table content blocks and metadata

    Raises:
        TypeError: If file_path is not Path object
        ValueError: If file_path is None

    Examples:
        >>> result = extractor.extract(Path('data.csv'))
        >>> result.content_blocks[0].content_type
        'table'
    """
```

### Method Organization Order

```python
class MyExtractor(BaseExtractor):
    # 1. Class variables
    SUPPORTED_EXTENSIONS = ['.csv']

    # 2. __init__
    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        pass

    # 3. Public interface methods (alphabetical)
    def extract(self, file_path: Path) -> ExtractionResult:
        pass

    def supports_file(self, file_path: Path) -> bool:
        pass

    # 4. Private helper methods (alphabetical)
    def _load_settings(self) -> None:
        pass

    def _parse_data(self, raw: str) -> List[List[str]]:
        pass
```

### Private Method Naming

**Pattern**: Prefix with single underscore `_`

```python
def _internal_helper(self) -> str:
    """Private method for internal use."""
    pass

def __double_underscore(self):  # Avoid, only for name mangling
    pass
```

### Line Length and Formatting

**Max line length**: 100 characters
**Tool**: `black` formatter with default settings

```bash
black src/extractors/csv_extractor.py --line-length 100
```

### Import Organization

```python
# 1. Standard library
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# 2. Third-party
import pandas as pd
import numpy as np

# 3. Local application
from ..core.interfaces import BaseExtractor
from ..core.models import ExtractionResult, ContentBlock
from ..infrastructure import INFRASTRUCTURE_AVAILABLE

# 4. Conditional imports
if INFRASTRUCTURE_AVAILABLE:
    from ..infrastructure.logger import get_logger
```

---

## Documentation Requirements

### Module Docstring

```python
"""
CSV file extractor for structured data extraction.

This module provides CSVExtractor class for extracting tabular data
from CSV files with support for various delimiters and encodings.

Classes:
    CSVExtractor: Main extraction class

Example:
    >>> from pathlib import Path
    >>> from src.extractors.csv_extractor import CSVExtractor
    >>> extractor = CSVExtractor()
    >>> result = extractor.extract(Path('data.csv'))
"""
```

### Class Docstring

See "Code Quality Standards" → "Docstrings" section above.

**Required sections**:
- One-line summary
- Detailed description
- Configuration options
- Examples

### Method Docstrings

**Required sections**:
- One-line summary
- Args (if any)
- Returns
- Raises (if any)
- Examples (for complex methods)

### Inline Comments

**Use for**:
- Complex algorithms
- Non-obvious business logic
- Workarounds for library limitations
- Performance optimizations

```python
def _parse_row(self, row: str) -> List[str]:
    """Parse CSV row into fields."""
    # Use custom parser instead of csv.reader for better Unicode support
    # Standard library has issues with certain emoji in field values
    fields = []
    # ... implementation ...
    return fields
```

### Configuration Documentation

**Location**: Class docstring

**Format**:
```python
"""
Configuration:
    setting_name (type): Description (default: value)
    another_setting (type): Description (default: value)
"""
```

---

## Pipeline Integration Checklist

### Registration

**File**: `src/pipeline/extraction_pipeline.py`

**Pattern**:
```python
from ..extractors.csv_extractor import CSVExtractor

class ExtractionPipeline:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.extractors = {
            '.csv': CSVExtractor(config),
            # ... other extractors ...
        }
```

### Extension Mapping

**Add to**:
```python
SUPPORTED_EXTENSIONS = {
    '.csv': 'CSV file',
    # ... other extensions ...
}
```

### CLI Support Validation

**Test**:
```bash
cd data-extractor-tool
python -m src.cli extract path/to/file.csv --output output.json
```

**Verify**:
- File detected correctly
- Extraction succeeds
- Output formatted properly

### Batch Processing Compatibility

**Test**:
```bash
python -m src.cli batch input_dir output_dir --format json
```

**Verify**:
- CSV files discovered
- Processed in parallel
- Results written correctly

### Formatter Compatibility

**Test with each formatter**:

```python
def test_json_formatter_compatibility(csv_extractor, tmp_path):
    """Test CSVExtractor output works with JSONFormatter."""
    from src.formatters.json_formatter import JSONFormatter

    csv_file = tmp_path / "test.csv"
    csv_file.write_text("Name,Age\nAlice,30")

    result = csv_extractor.extract(csv_file)
    formatter = JSONFormatter()
    output = formatter.format(result)

    assert '"content_type": "table"' in output

def test_markdown_formatter_compatibility(csv_extractor, tmp_path):
    """Test CSVExtractor output works with MarkdownFormatter."""
    from src.formatters.markdown_formatter import MarkdownFormatter
    # ... similar test ...

def test_chunked_formatter_compatibility(csv_extractor, tmp_path):
    """Test CSVExtractor output works with ChunkedTextFormatter."""
    from src.formatters.chunked_text_formatter import ChunkedTextFormatter
    # ... similar test ...
```

---

## Pre-Implementation Checklist

- [ ] Read `src/core/models.py` - Understand data structures
- [ ] Read `src/core/interfaces.py` - Understand BaseExtractor contract
- [ ] Review reference extractor (`src/extractors/pdf_extractor.py`) - See infrastructure patterns
- [ ] Identify integration points in `src/pipeline/extraction_pipeline.py`
- [ ] Create test file `tests/test_extractors/test_<name>_extractor.py`
- [ ] Write RED tests first (TDD approach)
- [ ] Set up test fixtures and sample data

---

## Implementation Checklist

- [ ] Follow TDD: RED → GREEN → REFACTOR
- [ ] Implement one feature at a time
- [ ] Run tests after each change: `pytest tests/test_extractors/test_<name>_extractor.py -v`
- [ ] Maintain type safety: All methods fully typed
- [ ] Add docstrings as you go: Don't leave for later
- [ ] Use infrastructure correctly: Logger, ErrorHandler, ConfigManager
- [ ] Handle errors properly: File-level vs per-item vs programming errors
- [ ] Keep data models immutable: `@dataclass(frozen=True)`
- [ ] Log at appropriate levels: DEBUG for details, INFO for milestones, WARNING for issues
- [ ] Write clear commit messages: What and why

---

## Post-Implementation Checklist

- [ ] All tests pass: `pytest tests/test_extractors/test_<name>_extractor.py -v`
- [ ] Coverage ≥85%: `pytest --cov=src/extractors/<name>_extractor --cov-report=term-missing`
- [ ] Existing tests still pass: `pytest tests/ -v`
- [ ] Type checking passes: `mypy src/extractors/<name>_extractor.py`
- [ ] No linting errors: `black src/extractors/<name>_extractor.py --check`
- [ ] Documentation complete: Module, class, method docstrings
- [ ] Integration tested: Works with pipeline, CLI, formatters
- [ ] Edge cases handled: Empty files, large files, corrupted data
- [ ] Error messages clear: Users understand what went wrong
- [ ] Configuration documented: All options in class docstring

---

## Validation Commands

### Test Execution

```bash
# Run specific test file
pytest tests/test_extractors/test_csv_extractor.py -v

# Run with coverage
pytest tests/test_extractors/test_csv_extractor.py \
  --cov=src/extractors/csv_extractor \
  --cov-report=term-missing

# Run all tests
pytest tests/ -v

# Run integration tests
pytest tests/integration/ -v
```

### Coverage Check

```bash
# Generate coverage report
pytest tests/test_extractors/test_csv_extractor.py \
  --cov=src/extractors/csv_extractor \
  --cov-report=html \
  --cov-report=term-missing

# View HTML report
open htmlcov/index.html  # macOS
start htmlcov/index.html  # Windows
```

### Type Checking

```bash
# Check specific file
mypy src/extractors/csv_extractor.py

# Check entire package
mypy src/
```

### Linting

```bash
# Format code
black src/extractors/csv_extractor.py --line-length 100

# Check formatting without changes
black src/extractors/csv_extractor.py --check --line-length 100

# Lint with flake8
flake8 src/extractors/csv_extractor.py --max-line-length=100
```

---

## Reference Files

### Core Interfaces
**Path**: `src/core/interfaces.py`
**Purpose**: BaseExtractor contract definition

### Data Models
**Path**: `src/core/models.py`
**Purpose**: ExtractionResult, ContentBlock, metadata structures

### Infrastructure Integration Reference
**Path**: `src/extractors/pdf_extractor.py`
**Lines**: 1-50 (initialization), 100-150 (error handling)
**Purpose**: See how to use Logger, ErrorHandler, ConfigManager

### Table Handling Reference
**Path**: `src/extractors/excel_extractor.py`
**Lines**: 80-120 (table extraction)
**Purpose**: Pattern for extracting tabular data

### Image Handling Reference
**Path**: `src/extractors/pptx_extractor.py`
**Lines**: 150-200 (image extraction)
**Purpose**: Pattern for extracting binary image data

### Pipeline Registration
**Path**: `src/pipeline/extraction_pipeline.py`
**Lines**: 30-50 (extractor registration)
**Purpose**: How to register new extractor

---

## Success Criteria

Implementation is complete when:

1. **All tests pass** with ≥85% coverage
2. **Type checking** passes with no errors
3. **Linting** passes with no errors
4. **Documentation** complete (module, class, methods)
5. **Integration** works (pipeline, CLI, formatters)
6. **Error handling** robust (file-level, per-item, programming)
7. **Configuration** documented and tested
8. **Edge cases** covered in tests
9. **Code review** approved by team
10. **Performance** acceptable (no regressions)

---

**Version**: 1.0
**Last Updated**: 2025-11-06
**Status**: Active
