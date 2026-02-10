# Adding a Custom Processor

## Step-by-Step Guide

**Step 1: Create Processor Module**

```python
# src/processors/semantic_analyzer.py
from typing import List, Dict, Optional
from core import BaseProcessor, ExtractionResult, ProcessingResult, ProcessingStage, ContentBlock

class SemanticAnalyzer(BaseProcessor):
    """Semantic analysis processor for knowledge base curation."""

    def __init__(self, config: Optional[dict] = None):
        """Initialize with configuration."""
        super().__init__(config)
        # Load domain models, NLP libraries, etc.

    def get_processor_name(self) -> str:
        """Return unique processor name."""
        return "SemanticAnalyzer"

    def get_dependencies(self) -> list[str]:
        """Declare dependencies on other processors."""
        return ["ContextLinker", "MetadataAggregator"]

    def is_optional(self) -> bool:
        """Return whether this processor is optional."""
        return True  # Don't block pipeline if semantic analysis fails

    def process(self, extraction_result: ExtractionResult) -> ProcessingResult:
        """Main processing logic."""
        # Your semantic analysis implementation
        pass
```

**Step 2: Implement Processing Logic**

```python
def process(self, extraction_result: ExtractionResult) -> ProcessingResult:
    """Enrich content with semantic analysis."""

    # Handle empty input
    if not extraction_result.content_blocks:
        return ProcessingResult(
            content_blocks=tuple(),
            document_metadata=extraction_result.document_metadata,
            images=extraction_result.images,
            tables=extraction_result.tables,
            processing_stage=ProcessingStage.SEMANTIC_ANALYSIS,
            stage_metadata={"entities_found": 0},
            success=True
        )

    # Process each block
    enriched_blocks = []
    for block in extraction_result.content_blocks:
        # Extract semantic information
        entities = self._extract_entities(block.content)
        semantic_tags = self._generate_tags(block.content)

        # Enrich metadata (PRESERVE existing metadata)
        enriched_metadata = {
            **block.metadata,  # Keep existing metadata
            "entities": entities,
            "semantic_tags": semantic_tags,
        }

        # Create new block (immutable pattern)
        enriched_block = ContentBlock(
            block_id=block.block_id,
            block_type=block.block_type,
            content=block.content,
            raw_content=block.raw_content,
            position=block.position,
            parent_id=block.parent_id,
            related_ids=block.related_ids,
            metadata=enriched_metadata,  # Updated metadata
            confidence=block.confidence,
            style=block.style,
        )

        enriched_blocks.append(enriched_block)

    # Return result
    return ProcessingResult(
        content_blocks=tuple(enriched_blocks),
        document_metadata=extraction_result.document_metadata,
        images=extraction_result.images,  # PRESERVE
        tables=extraction_result.tables,  # PRESERVE
        processing_stage=ProcessingStage.SEMANTIC_ANALYSIS,
        stage_metadata={
            "entities_found": sum(len(b.metadata["entities"]) for b in enriched_blocks),
        },
        success=True
    )
```

**Step 3: Register with Pipeline**

```python
# In src/pipeline/__init__.py
from processors.semantic_analyzer import SemanticAnalyzer

# Export for public API
__all__ = [
    "ExtractionPipeline",
    "BatchProcessor",
    "SemanticAnalyzer",  # NEW
]
```

```python
# In CLI or application setup
from pipeline import ExtractionPipeline
from processors import ContextLinker, MetadataAggregator, SemanticAnalyzer, QualityValidator

pipeline = ExtractionPipeline()
pipeline.add_processor(ContextLinker())
pipeline.add_processor(MetadataAggregator())
pipeline.add_processor(SemanticAnalyzer(config={
    "entity_extraction": True,
    "domain_model": "cybersecurity_audit",
}))
pipeline.add_processor(QualityValidator())
```

**Step 4: Add ProcessingStage Enum Value**

```python
# In src/core/models.py
from enum import Enum

class ProcessingStage(str, Enum):
    """Processing stage identifiers."""
    VALIDATION = "validation"
    EXTRACTION = "extraction"
    CONTEXT_LINKING = "context_linking"
    METADATA_AGGREGATION = "metadata_aggregation"
    SEMANTIC_ANALYSIS = "semantic_analysis"  # NEW
    QUALITY_VALIDATION = "quality_validation"
    FORMATTING = "formatting"
```

**Step 5: Write Tests**

```python
# tests/test_processors/test_semantic_analyzer.py
import pytest
from processors.semantic_analyzer import SemanticAnalyzer
from core import ExtractionResult, ContentBlock, ContentType, DocumentMetadata

def test_semantic_analyzer_extracts_entities():
    """Test entity extraction from content."""
    analyzer = SemanticAnalyzer(config={"entity_extraction": True})

    # Create test input
    blocks = (
        ContentBlock(
            block_type=ContentType.PARAGRAPH,
            content="NIST SP 800-53 requires access control policies.",
            metadata={},
        ),
    )

    extraction_result = ExtractionResult(
        content_blocks=blocks,
        document_metadata=DocumentMetadata(source_file=Path("test.docx")),
        success=True
    )

    # Process
    result = analyzer.process(extraction_result)

    # Verify
    assert result.success
    assert len(result.content_blocks) == 1
    assert "entities" in result.content_blocks[0].metadata
    assert "NIST SP 800-53" in result.content_blocks[0].metadata["entities"]
```

---
