# Core Pipeline Components

## ExtractionPipeline Class

**Location**: `src/pipeline/extraction_pipeline.py`
**Responsibility**: Orchestrate the entire extraction workflow

**Key Methods**:

```python
class ExtractionPipeline(BasePipeline):
    def detect_format(self, file_path: Path) -> Optional[str]:
        """Detect file format from extension."""
        # Maps extensions to format identifiers
        # .docx → 'docx', .pdf → 'pdf', etc.

    def register_extractor(self, format_type: str, extractor: BaseExtractor):
        """Register format-specific extractor."""
        # Stores extractors in registry: self._extractors[format_type]

    def add_processor(self, processor: BaseProcessor):
        """Add processor to processing chain."""
        # Appends to self._processors list
        # Ordering happens automatically via topological sort

    def add_formatter(self, formatter: BaseFormatter):
        """Add output formatter."""
        # Appends to self._formatters list
        # Formatters run in parallel

    def process_file(self, file_path: Path) -> PipelineResult:
        """Process single file through complete pipeline."""
        # Orchestrates: validation → extraction → processing → formatting
```

**Important Implementation Details**:

1. **Format Detection** (lines 142-153):
   ```python
   FORMAT_EXTENSIONS = {
       '.docx': 'docx',
       '.pdf': 'pdf',
       '.pptx': 'pptx',
       '.xlsx': 'xlsx',
       '.csv': 'csv',
       '.tsv': 'csv',  # TSV uses CSV extractor
       '.txt': 'txt',
   }
   ```

2. **Processor Ordering** (lines 213-266):
   ```python
   def _order_processors(self) -> list[BaseProcessor]:
       """Order processors based on dependencies using topological sort."""
       # Uses Kahn's algorithm for dependency resolution
       # Prevents circular dependencies
       # Ensures correct execution order
   ```

   **Why This Matters for Semantic Analysis**:
   - Your semantic processor can declare dependencies
   - Pipeline will automatically order it correctly
   - Example: `get_dependencies() → ["ContextLinker", "MetadataAggregator"]`

3. **Progress Reporting** (lines 268-296):
   ```python
   def _report_progress(self, callback, stage, percentage, message):
       """Report progress to callback if provided."""
       # Enables CLI progress bars
       # Useful for long-running semantic analysis
   ```

---
