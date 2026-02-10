# Performance Considerations

## Benchmarking Guidelines

**Target Performance**:
- Current pipeline: <2s/MB for text, <15s/page for OCR
- Semantic analysis budget: +3-5s per document (acceptable)
- Total target: <10s for typical audit document (20-50 pages)

**Optimization Strategies**:

**1. Batch Entity Extraction**
```python
# ❌ SLOW: Process each block individually
for block in blocks:
    entities = nlp(block.content)  # Separate NLP call per block

# ✅ FAST: Batch processing
all_text = "\n\n".join(block.content for block in blocks)
doc = nlp(all_text)  # Single NLP call
# Then map entities back to blocks
```

**2. Lazy Loading**
```python
class SemanticAnalyzer(BaseProcessor):
    def __init__(self, config: Optional[dict] = None):
        super().__init__(config)
        self._nlp_model = None  # Don't load until needed

    @property
    def nlp_model(self):
        """Lazy load NLP model."""
        if self._nlp_model is None:
            import spacy
            self._nlp_model = spacy.load("en_core_web_sm")
        return self._nlp_model
```

**3. Caching**
```python
from functools import lru_cache

class SemanticAnalyzer(BaseProcessor):
    @lru_cache(maxsize=1000)
    def _classify_entity(self, entity_text: str) -> str:
        """Cache entity classifications."""
        # Classification logic
        pass
```

**4. Progress Reporting for Long Operations**
```python
def process(self, extraction_result: ExtractionResult) -> ProcessingResult:
    total_blocks = len(extraction_result.content_blocks)

    for i, block in enumerate(extraction_result.content_blocks):
        # Process block...

        # Report progress (useful for CLI progress bars)
        if i % 10 == 0:  # Every 10 blocks
            self.logger.debug(f"Processed {i}/{total_blocks} blocks")
```

## Memory Management

**Considerations**:
- Current pipeline: <500MB per file, <2GB for batch
- NLP models: spaCy models ~50-500MB in memory
- Strategy: Load model once, reuse across all files

**Example**:
```python
class SemanticAnalyzer(BaseProcessor):
    # Class-level model (shared across instances)
    _shared_nlp_model = None

    def __init__(self, config: Optional[dict] = None):
        super().__init__(config)
        # Use shared model
        if SemanticAnalyzer._shared_nlp_model is None:
            import spacy
            SemanticAnalyzer._shared_nlp_model = spacy.load("en_core_web_sm")
        self.nlp = SemanticAnalyzer._shared_nlp_model
```

---
