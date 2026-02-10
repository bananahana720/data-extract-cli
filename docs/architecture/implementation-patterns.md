# Implementation Patterns

These patterns ensure consistent implementation across all AI agents:

## Pipeline Stage Pattern
**MUST use for all processing stages** (extract, normalize, chunk, semantic, output)

**Implementation:** `src/data_extract/core/pipeline.py` (Story 1.4)

```python
from typing import Protocol, Generic, TypeVar, List, Any
from data_extract.core.models import ProcessingContext

Input = TypeVar('Input', contravariant=True)
Output = TypeVar('Output', covariant=True)

class PipelineStage(Protocol, Generic[Input, Output]):
    """All pipeline stages implement this interface"""

    def process(self, input_data: Input, context: ProcessingContext) -> Output:
        """
        Process input and return output.

        Args:
            input_data: Data from previous stage
            context: Shared processing context (config, logger, metrics)

        Returns:
            Processed output for next stage

        Raises:
            ProcessingError: On recoverable errors (logged, continue batch)
            CriticalError: On unrecoverable errors (halt processing)
        """
        ...

class Pipeline:
    """Pipeline orchestrator that chains multiple stages"""

    def __init__(self, stages: List[PipelineStage]) -> None:
        """Initialize pipeline with list of stages."""
        self.stages = stages

    def process(self, initial_input: Any, context: ProcessingContext) -> Any:
        """Execute all pipeline stages in sequence."""
        current_data = initial_input
        for stage in self.stages:
            current_data = stage.process(current_data, context)
        return current_data
```

**Example: All stages follow this pattern**
```python
class Normalizer(PipelineStage[Document, Document]):
    def process(self, document: Document, context: ProcessingContext) -> Document:
        # Apply cleaning rules
        cleaned_text = self._clean_text(document.text)
        # Normalize entities
        entities = self._normalize_entities(document.entities)
        # Return normalized document
        return Document(text=cleaned_text, entities=entities, metadata=document.metadata)
```

## Error Handling Pattern
**MUST use for all file processing operations**

**Implementation:** `src/data_extract/core/exceptions.py` (Story 1.4)

```python
# In batch processing loop
for file_path in files:
    try:
        result = process_file(file_path)
        successful_results.append(result)
    except ProcessingError as e:
        # Recoverable error - log, quarantine, continue
        logger.warning(f"Processing failed: {file_path}", error=str(e))
        quarantine_file(file_path, error=e)
        failed_files.append((file_path, e))
        continue  # CRITICAL: Continue processing other files
    except CriticalError as e:
        # Unrecoverable error - halt immediately
        logger.error(f"Critical failure: {file_path}", error=str(e))
        raise

# After loop: Report summary of successes and failures
report_summary(successful_results, failed_files)
```

**Exception Hierarchy:**
```python
class DataExtractError(Exception):
    """Base exception for all tool errors"""

class ProcessingError(DataExtractError):
    """Recoverable error - continue batch processing"""

class CriticalError(DataExtractError):
    """Unrecoverable error - halt processing"""

class ConfigurationError(CriticalError):
    """Invalid configuration - cannot proceed"""

class ExtractionError(ProcessingError):
    """File extraction failed - skip file, continue batch"""

class ValidationError(ProcessingError):
    """Quality validation failed - flag file, continue"""
```

## Logging Pattern
**MUST use structured logging for audit trail**

```python
import structlog

logger = structlog.get_logger()

# Log with context (automatically includes timestamps, levels)
logger.info("processing_started",
            file=file_path,
            file_hash=file_hash,
            config_version=config.version)

logger.debug("chunk_created",
             chunk_id=chunk.id,
             chunk_size=len(chunk.text),
             entity_count=len(chunk.entities),
             quality_score=chunk.quality_score)

logger.warning("quality_threshold_failed",
               file=file_path,
               ocr_confidence=0.87,
               threshold=0.95,
               action="quarantined")
```

## Configuration Cascade Pattern
**MUST implement three-tier precedence**

```python
def load_config() -> Config:
    # 1. Load defaults (hardcoded in code)
    config = DEFAULT_CONFIG.copy()

    # 2. Overlay YAML file config (if exists)
    if yaml_config_exists():
        yaml_config = load_yaml_config()
        config.update(yaml_config)

    # 3. Overlay environment variables (DATA_EXTRACT_*)
    env_config = load_from_env_vars()
    config.update(env_config)

    # 4. CLI flags applied last (highest precedence)
    # (Handled by Typer when function is called)

    return Config(**config)  # Pydantic validates
```

**Environment Variable Naming:**
- Prefix: `DATA_EXTRACT_`
- Example: `DATA_EXTRACT_CHUNK_SIZE=512`
- Example: `DATA_EXTRACT_OUTPUT_DIR=/path/to/output`
