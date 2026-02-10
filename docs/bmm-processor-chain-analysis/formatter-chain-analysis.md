# Formatter Chain Analysis

## Current Formatter Implementations

**Formatters run in PARALLEL** (unlike processors which run sequentially).

**1. JsonFormatter** (`src/formatters/json_formatter.py`)
- Purpose: Generate hierarchical or flat JSON output
- Config: `hierarchical`, `pretty_print`, `indent`
- Performance: Fast (no heavy processing)

**2. MarkdownFormatter** (`src/formatters/markdown_formatter.py`)
- Purpose: Generate human-readable Markdown output
- Config: `include_metadata`, `include_images`
- Performance: Fast

**3. ChunkedTextFormatter** (`src/formatters/chunked_text_formatter.py`)
- Purpose: Generate token-limited chunks for AI consumption
- Config: `chunk_size`, `chunk_overlap`, `preserve_structure`
- Performance: Fast

## Formatter Interface

```python
class BaseFormatter(ABC):
    """Abstract base class for output formatters."""

    @abstractmethod
    def format(self, processing_result: ProcessingResult) -> FormattedOutput:
        """
        Format processing result to specific output format.

        Args:
            processing_result: Result from processing stage

        Returns:
            FormattedOutput with formatted content
        """
        pass

    @abstractmethod
    def get_format_type(self) -> str:
        """
        Return format type identifier.

        Returns:
            Format type (e.g., "json", "markdown", "chunked_text")
        """
        pass
```

---
