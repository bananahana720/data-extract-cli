# Processor Interface Contract

## BaseProcessor Abstract Class

**Location**: `src/core/interfaces.py` (lines 122-245)

**Required Methods**:

```python
class BaseProcessor(ABC):
    """Abstract base class for content processors."""

    @abstractmethod
    def get_processor_name(self) -> str:
        """Return unique processor name for dependency resolution."""
        pass

    @abstractmethod
    def get_dependencies(self) -> list[str]:
        """
        Return list of processor names this processor depends on.

        Dependencies are used for automatic ordering via topological sort.
        Return empty list if no dependencies.

        Example:
            >>> def get_dependencies(self) -> list[str]:
            >>>     return ["ContextLinker", "MetadataAggregator"]
        """
        pass

    @abstractmethod
    def is_optional(self) -> bool:
        """
        Whether this processor is optional.

        Optional processors: Pipeline continues if they fail
        Required processors: Pipeline stops if they fail

        Returns:
            True if optional, False if required
        """
        pass

    @abstractmethod
    def process(self, extraction_result: ExtractionResult) -> ProcessingResult:
        """
        Process extracted content and enrich with additional metadata.

        Args:
            extraction_result: Raw extraction result from extractor

        Returns:
            ProcessingResult with enriched content blocks

        Note:
            - Must preserve all existing metadata from previous processors
            - Must preserve images and tables
            - Should be idempotent (safe to run multiple times)
        """
        pass
```

**Constructor Pattern**:
```python
def __init__(self, config: Optional[dict] = None):
    """
    Initialize processor with optional configuration.

    Args:
        config: Processor-specific configuration options
    """
    self.config = config or {}
```

## ProcessingResult Data Structure

**Returns from `process()` method**:

```python
@dataclass(frozen=True)
class ProcessingResult:
    """Result from processing stage."""

    # Enriched content blocks (tuple for immutability)
    content_blocks: tuple[ContentBlock, ...]

    # Document metadata (preserved from extraction)
    document_metadata: DocumentMetadata

    # Media assets (preserved from extraction)
    images: tuple[ImageMetadata, ...] = ()
    tables: tuple[TableMetadata, ...] = ()

    # Processing stage identifier
    processing_stage: ProcessingStage = ProcessingStage.EXTRACTION

    # Stage-specific metadata (statistics, counts, etc.)
    stage_metadata: dict = field(default_factory=dict)

    # Quality metrics (optional, added by QualityValidator)
    quality_score: Optional[float] = None
    quality_issues: tuple[str, ...] = ()
    needs_review: bool = False

    # Success/error tracking
    success: bool = True
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
```

---
