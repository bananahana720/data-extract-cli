# Consistency Rules

## Naming Conventions

**Files and Modules:**
- Python files: `lowercase_with_underscores.py`
- Classes: `PascalCase` (e.g., `DocumentExtractor`, `SemanticChunker`)
- Functions/methods: `lowercase_with_underscores` (e.g., `process_batch`, `calculate_similarity`)
- Constants: `UPPERCASE_WITH_UNDERSCORES` (e.g., `DEFAULT_CHUNK_SIZE`, `MAX_FILE_SIZE`)
- Private methods: `_leading_underscore` (e.g., `_clean_text`, `_validate_chunk`)

**Variables:**
- Local variables: `lowercase_with_underscores`
- Type variables: `PascalCase` (e.g., `Input`, `Output`, `T`)
- Pydantic models: `PascalCase` (e.g., `Document`, `Chunk`, `Metadata`)

**CLI Commands:**
- Main commands: single words lowercase (e.g., `process`, `similarity`, `validate`)
- Sub-commands: hyphenated lowercase (e.g., `config-show`, `config-init`)
- Flags: full words with hyphens (e.g., `--chunk-size`, `--output-dir`, `--no-validate`)

**Output Files:**
- JSON: `{source_filename}_chunks.json`
- TXT chunks: `{source_filename}_chunk_{001}.txt`
- CSV index: `{batch_name}_chunk_index.csv`
- Logs: `processing_{YYYY-MM-DD-HH-MM-SS}.log`
- Manifest: `.processing_manifest.json` (hidden file)

## Code Organization

**Module Structure:**
```python
# Standard import order (enforced by ruff)
# 1. Standard library imports
import json
import logging
from pathlib import Path
from typing import List, Optional

# 2. Third-party imports
import spacy
from pydantic import BaseModel
from rich.progress import Progress

# 3. Local application imports
from data_extract.core.models import Document, Chunk
from data_extract.core.pipeline import PipelineStage
from data_extract.utils.logging import get_logger
```

**Function Organization:**
```python
class Normalizer(PipelineStage):
    # 1. Class docstring
    """Normalizes extracted text for RAG optimization."""

    # 2. Class-level constants
    DEFAULT_ENTITY_TYPES = ["process", "risk", "control", "regulation", "policy", "issue"]

    # 3. __init__ and setup methods
    def __init__(self, config: NormalizerConfig):
        self.config = config
        self.logger = get_logger(__name__)

    # 4. Public interface methods
    def process(self, document: Document, context: ProcessingContext) -> Document:
        """Main processing method (implements PipelineStage)."""
        ...

    # 5. Private helper methods (alphabetical)
    def _clean_text(self, text: str) -> str:
        ...

    def _normalize_entities(self, entities: List[Entity]) -> List[Entity]:
        ...

    def _validate_output(self, document: Document) -> bool:
        ...
```

**Testing Organization:**
```python
# tests/unit/test_normalize/test_cleaning.py
import pytest
from data_extract.normalize.cleaning import TextCleaner

class TestTextCleaner:
    """Test suite for TextCleaner class"""

    @pytest.fixture
    def cleaner(self):
        return TextCleaner()

    def test_removes_ocr_artifacts(self, cleaner):
        """Should remove common OCR artifacts like ^^^^"""
        ...

    def test_normalizes_whitespace(self, cleaner):
        """Should collapse multiple spaces to single space"""
        ...

    def test_preserves_intentional_formatting(self, cleaner):
        """Should keep lists and emphasis intact"""
        ...
```

## Error Handling

**Always Catch Specific Exceptions:**
```python
# GOOD: Specific exception handling
try:
    document = extract_pdf(file_path)
except FileNotFoundError as e:
    logger.error("file_not_found", file=file_path)
    raise ProcessingError(f"File not found: {file_path}") from e
except PermissionError as e:
    logger.error("permission_denied", file=file_path)
    raise ProcessingError(f"Permission denied: {file_path}") from e

# BAD: Bare except
try:
    document = extract_pdf(file_path)
except:  # NEVER DO THIS
    pass
```

**Provide Actionable Error Messages:**
```python
# GOOD: Actionable error message
raise ConfigurationError(
    f"Invalid chunk size: {chunk_size}. "
    f"Must be between 128 and 2048 tokens. "
    f"Update config file or use --chunk-size flag."
)

# BAD: Vague error message
raise ConfigurationError("Invalid config")
```

**No Silent Failures:**
```python
# GOOD: Flag issues, don't skip silently
if ocr_confidence < threshold:
    logger.warning("low_ocr_confidence",
                   file=file_path,
                   confidence=ocr_confidence,
                   threshold=threshold)
    metadata["quality_flags"].append("low_ocr_confidence")
    # Continue processing, but flag the issue

# BAD: Silent skip
if ocr_confidence < threshold:
    return None  # NEVER RETURN NONE SILENTLY
```

## Logging Strategy

**Structured Logging Levels:**
- **DEBUG**: Detailed information for diagnosing problems (chunk boundaries, entity matches, config values)
- **INFO**: Confirmation of expected behavior (processing started/completed, files processed, chunks created)
- **WARNING**: Unexpected but recoverable (low OCR confidence, quality threshold not met, file skipped)
- **ERROR**: Serious problems (file processing failed, invalid configuration, missing dependencies)
- **CRITICAL**: System-level failures (database corruption, out of disk space, Python version mismatch)

**What to Log:**
```python
# START of operations (with context)
logger.info("batch_processing_started",
            input_dir=input_dir,
            file_count=len(files),
            config_version=config.version)

# DECISIONS made during processing
logger.debug("chunk_split_decision",
             reason="sentence_boundary",
             position=char_index,
             chunk_size=current_size)

# QUALITY issues (with threshold values)
logger.warning("quality_threshold_failed",
               metric="ocr_confidence",
               value=0.87,
               threshold=0.95,
               action="flagged_for_review")

# END of operations (with results)
logger.info("batch_processing_completed",
            successful=len(successful),
            failed=len(failed),
            duration_seconds=elapsed_time)
```

**Structured Format (JSON for audit trail):**
```json
{
  "timestamp": "2025-11-09T14:23:45.123Z",
  "level": "info",
  "event": "processing_completed",
  "file": "audit-report-2024.pdf",
  "file_hash": "sha256:abc123...",
  "chunks_created": 47,
  "quality_score": 0.96,
  "config_version": "1.0.0",
  "processing_time_ms": 2340
}
```
