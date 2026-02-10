# Error Handling and Recovery

## Error Handling Patterns

**Pattern 1: Graceful Degradation (Optional Processor)**
```python
def process(self, extraction_result: ExtractionResult) -> ProcessingResult:
    try:
        # Semantic analysis logic
        enriched_blocks = self._process_blocks(extraction_result.content_blocks)
        return ProcessingResult(
            content_blocks=enriched_blocks,
            ...,
            success=True
        )
    except Exception as e:
        self.logger.exception("Semantic analysis failed", exc_info=e)

        # Return original blocks (no enrichment, but pipeline continues)
        return ProcessingResult(
            content_blocks=extraction_result.content_blocks,
            document_metadata=extraction_result.document_metadata,
            images=extraction_result.images,
            tables=extraction_result.tables,
            processing_stage=ProcessingStage.SEMANTIC_ANALYSIS,
            success=False,  # Mark as failed
            errors=(f"Semantic analysis failed: {str(e)}",),
        )
```

**Pattern 2: Partial Processing (Best Effort)**
```python
def process(self, extraction_result: ExtractionResult) -> ProcessingResult:
    enriched_blocks = []
    errors = []

    for block in extraction_result.content_blocks:
        try:
            # Try to process this block
            enriched_block = self._process_single_block(block)
            enriched_blocks.append(enriched_block)
        except Exception as e:
            self.logger.warning(f"Failed to process block {block.block_id}: {e}")
            errors.append(f"Block {block.block_id}: {str(e)}")
            # Add original block (no enrichment for this one)
            enriched_blocks.append(block)

    return ProcessingResult(
        content_blocks=tuple(enriched_blocks),
        ...,
        success=True,  # Overall success (partial processing)
        errors=tuple(errors),  # Log errors for inspection
    )
```

## Error Handler Integration

```python
from infrastructure import ErrorHandler, RecoveryAction

class SemanticAnalyzer(BaseProcessor):
    def __init__(self, config: Optional[dict] = None):
        super().__init__(config)
        self.error_handler = ErrorHandler()

    def process(self, extraction_result: ExtractionResult) -> ProcessingResult:
        try:
            # Processing logic
            pass
        except ImportError as e:
            # Handle missing NLP library
            recovery = self.error_handler.handle_error(
                error_code="SEMANTIC_001",
                error_message=f"NLP library not available: {e}",
                context={"processor": "SemanticAnalyzer"},
            )

            if recovery.action == RecoveryAction.FAIL:
                return ProcessingResult(..., success=False, errors=(recovery.message,))
            elif recovery.action == RecoveryAction.SKIP:
                return ProcessingResult(..., success=True, warnings=(recovery.message,))
```

---
