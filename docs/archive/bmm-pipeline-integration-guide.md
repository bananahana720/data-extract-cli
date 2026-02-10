# Pipeline Integration Guide - For Semantic Analysis Enhancement

**Generated**: 2025-11-07
**Audience**: Developers adding semantic analysis features
**Focus**: Pipeline architecture and integration points
**Priority**: 1 (User-requested focus area)

---

## Table of Contents

1. [Pipeline Architecture Overview](#pipeline-architecture-overview)
2. [Core Pipeline Components](#core-pipeline-components)
3. [Processing Flow Deep Dive](#processing-flow-deep-dive)
4. [Integration Points for Semantic Analysis](#integration-points-for-semantic-analysis)
5. [Processor Chain Analysis](#processor-chain-analysis)
6. [Adding a Custom Processor](#adding-a-custom-processor)
7. [Data Flow and Transformations](#data-flow-and-transformations)
8. [Configuration and Dependency Injection](#configuration-and-dependency-injection)
9. [Error Handling and Recovery](#error-handling-and-recovery)
10. [Performance Considerations](#performance-considerations)

---

## Pipeline Architecture Overview

### Design Philosophy

The extraction pipeline follows a **staged processing architecture** with clear separation of concerns:

1. **Validation Stage**: File exists, format detected, extractor available
2. **Extraction Stage**: Format-specific content extraction
3. **Processing Stage**: Content enrichment (hierarchy, metadata, quality)
4. **Formatting Stage**: Output generation (JSON, Markdown, etc.)

**Key Principles**:
- **Immutability**: Each stage creates new data structures (no mutations)
- **Composability**: Components are independent and composable
- **Error Isolation**: Errors in one stage don't corrupt others
- **Progressive Enhancement**: Each stage adds value to previous stage's output

### Pipeline State Machine

```
┌──────────────┐
│ VALIDATION   │  Check file exists, detect format, verify extractor
└──────┬───────┘
       │ ✓ File valid
       ▼
┌──────────────┐
│ EXTRACTION   │  Extract content blocks from document
└──────┬───────┘
       │ ✓ ExtractionResult
       ▼
┌──────────────┐
│ PROCESSING   │  Enrich content blocks (hierarchy, metadata, quality)
│              │  → ContextLinker (build hierarchy)
│              │  → MetadataAggregator (compute statistics)
│              │  → QualityValidator (score quality)
│              │  **→ SemanticAnalyzer** ← INTEGRATION POINT
└──────┬───────┘
       │ ✓ ProcessingResult
       ▼
┌──────────────┐
│ FORMATTING   │  Generate output formats (parallel execution)
│              │  → JsonFormatter
│              │  → MarkdownFormatter
│              │  → ChunkedTextFormatter
│              │  **→ RagOptimizedFormatter** ← INTEGRATION POINT
└──────┬───────┘
       │ ✓ FormattedOutput[]
       ▼
┌──────────────┐
│   COMPLETE   │  Return PipelineResult
└──────────────┘
```

---

## Core Pipeline Components

### ExtractionPipeline Class

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

## Processing Flow Deep Dive

### Validation Stage (Lines 334-395)

**Purpose**: Ensure file can be processed before attempting extraction

**Checks Performed**:
1. File exists (`file_path.exists()`)
2. Format detected from extension
3. Extractor registered for format

**Failure Handling**:
- Returns `PipelineResult` with `success=False`
- Sets `failed_stage=ProcessingStage.VALIDATION`
- Includes descriptive error messages

**Integration Note**: Validation stage is complete and rarely needs modification.

### Extraction Stage (Lines 397-434)

**Purpose**: Extract raw content from document

**Process**:
1. Get registered extractor for detected format
2. Call `extractor.extract(file_path)`
3. Collect errors and warnings
4. Return `ExtractionResult` with content blocks

**Data Structures Created**:
```python
ExtractionResult(
    content_blocks=(ContentBlock, ...),  # Extracted content
    document_metadata=DocumentMetadata(...),  # File properties
    images=(ImageMetadata, ...),  # Extracted images
    tables=(TableMetadata, ...),  # Extracted tables
    success=True,
    errors=(),
    warnings=()
)
```

**Integration Note**: Extractors are stable. For semantic analysis, focus on processing stage.

### Processing Stage (Lines 436-550) ⭐ PRIMARY INTEGRATION POINT

**Purpose**: Enrich extracted content with hierarchy, metadata, and quality scores

**Process**:
1. Order processors by dependencies (topological sort)
2. Run each processor in sequence
3. Each processor transforms `ExtractionResult` → `ProcessingResult`
4. Output of one processor becomes input of next

**Current Processor Chain**:

```python
# Automatic ordering based on dependencies
ordered_processors = self._order_processors()  # Returns:
# [ContextLinker, MetadataAggregator, QualityValidator]

for processor in ordered_processors:
    # Convert ExtractionResult to ProcessingResult (first processor)
    if isinstance(current_input, ExtractionResult):
        processing_result = processor.process(current_input)
    else:
        # Adapt ProcessingResult to ExtractionResult (subsequent processors)
        pseudo_extraction = ExtractionResult(
            content_blocks=current_input.content_blocks,
            document_metadata=current_input.document_metadata,
            images=current_input.images,
            tables=current_input.tables,
            success=True
        )
        processing_result = processor.process(pseudo_extraction)

    # Check success
    if not processing_result.success:
        if processor.is_optional():
            # Continue if processor is optional
            pass
        else:
            # Fail pipeline if processor is required
            return PipelineResult(success=False, ...)

    # Use output as input for next processor
    current_input = processing_result
```

**Media Asset Preservation** (Lines 469-477):
- **Critical**: Images and tables must be preserved through processor chain
- Each processor receives and returns media assets unchanged
- Processors enrich `content_blocks` but preserve `images` and `tables`

**Where Semantic Analyzer Fits**:
```python
# After MetadataAggregator, before QualityValidator
pipeline.add_processor(ContextLinker())       # Dependency 1
pipeline.add_processor(MetadataAggregator()) # Dependency 2
pipeline.add_processor(SemanticAnalyzer())   # NEW ← Your processor
pipeline.add_processor(QualityValidator())   # Runs after semantic analysis
```

### Formatting Stage (Lines 552-591)

**Purpose**: Generate output in multiple formats (parallel execution)

**Process**:
1. Loop through all registered formatters
2. Call `formatter.format(processing_result)` for each
3. Collect `FormattedOutput` from successful formatters
4. Continue even if some formatters fail (best effort)

**Data Structures Created**:
```python
FormattedOutput(
    content=str,  # Formatted content (JSON, Markdown, etc.)
    format_type=str,  # "json", "markdown", "chunked_text"
    source_document=Path,
    success=True,
    errors=(),
    warnings=()
)
```

**Integration Note**: Add `RagOptimizedFormatter` here for RAG-specific output.

---

## Integration Points for Semantic Analysis

### Option 1: Semantic Analysis Processor (RECOMMENDED)

**Best for**: Journey B (semantic analysis and knowledge base curation)

**Implementation Pattern**:

```python
# src/processors/semantic_analyzer.py
from core import BaseProcessor, ExtractionResult, ProcessingResult, ProcessingStage

class SemanticAnalyzer(BaseProcessor):
    """
    Semantic analysis processor for knowledge base curation.

    Capabilities:
    - Entity extraction (processes, risks, controls, regulations, policies)
    - Semantic standardization
    - Domain classification (cybersecurity audit)
    - Relationship mapping (GRC entities)
    - Context enrichment
    """

    def get_processor_name(self) -> str:
        return "SemanticAnalyzer"

    def get_dependencies(self) -> list[str]:
        # Run after ContextLinker (need hierarchy) and MetadataAggregator (need stats)
        return ["ContextLinker", "MetadataAggregator"]

    def is_optional(self) -> bool:
        # Optional - don't block pipeline if semantic analysis fails
        return True

    def process(self, extraction_result: ExtractionResult) -> ProcessingResult:
        """
        Enrich content blocks with semantic analysis.

        Available Data:
        - content_blocks[i].content: Text content
        - content_blocks[i].metadata["depth"]: Hierarchy depth (from ContextLinker)
        - content_blocks[i].metadata["document_path"]: Breadcrumb trail
        - content_blocks[i].metadata["word_count"]: Word count (from MetadataAggregator)
        - content_blocks[i].block_type: HEADING, PARAGRAPH, LIST, TABLE, etc.
        - content_blocks[i].parent_id: Parent block ID
        - extraction_result.document_metadata: File properties
        - extraction_result.images: Image metadata
        - extraction_result.tables: Table metadata

        Returns:
        - ProcessingResult with enriched metadata:
          - entities: List[str] (extracted entities)
          - entity_types: Dict[str, str] (entity → type mapping)
          - semantic_tags: List[str] (domain-specific tags)
          - relationships: List[Dict] (entity relationships)
          - domain_classification: str (cybersecurity_audit, etc.)
          - quality_indicators: Dict (RAG quality metrics)
        """
        enriched_blocks = []

        for block in extraction_result.content_blocks:
            # Semantic analysis
            entities = self._extract_entities(block.content)
            entity_types = self._classify_entities(entities)
            semantic_tags = self._generate_semantic_tags(block.content)
            relationships = self._map_relationships(block.content, entities)

            # Quality indicators for RAG
            quality_indicators = {
                "semantic_clarity": self._compute_clarity(block.content),
                "entity_density": len(entities) / max(1, block.metadata.get("word_count", 1)),
                "domain_relevance": self._compute_relevance(semantic_tags),
            }

            # Enrich metadata
            enriched_metadata = {
                **block.metadata,  # Preserve existing metadata
                "entities": entities,
                "entity_types": entity_types,
                "semantic_tags": semantic_tags,
                "relationships": relationships,
                "domain_classification": "cybersecurity_audit",
                "quality_indicators": quality_indicators,
            }

            # Create enriched block (PRESERVE ALL ORIGINAL DATA)
            enriched_block = ContentBlock(
                block_id=block.block_id,  # Same ID
                block_type=block.block_type,  # Same type
                content=block.content,  # Same content
                raw_content=block.raw_content,  # Same raw content
                position=block.position,  # Same position
                parent_id=block.parent_id,  # Same parent
                related_ids=block.related_ids,  # Same relations
                metadata=enriched_metadata,  # ENRICHED metadata
                confidence=block.confidence,  # Same confidence
                style=block.style,  # Same style
            )

            enriched_blocks.append(enriched_block)

        # Compute aggregate statistics
        total_entities = sum(len(block.metadata["entities"]) for block in enriched_blocks)
        unique_entities = len(set(e for block in enriched_blocks for e in block.metadata["entities"]))

        # Return ProcessingResult
        return ProcessingResult(
            content_blocks=tuple(enriched_blocks),
            document_metadata=extraction_result.document_metadata,
            images=extraction_result.images,  # PRESERVE images
            tables=extraction_result.tables,  # PRESERVE tables
            processing_stage=ProcessingStage.SEMANTIC_ANALYSIS,  # New stage (add to enum)
            stage_metadata={
                "total_entities_found": total_entities,
                "unique_entities": unique_entities,
                "entity_types": entity_types,
                "processing_time_seconds": ...,
            },
            success=True,
        )

    def _extract_entities(self, text: str) -> List[str]:
        """
        Extract domain-specific entities.

        For cybersecurity audit domain:
        - Processes
        - Risks
        - Controls
        - Regulations (NIST, COBIT, ISO 27001, SOC2, etc.)
        - Policies/Standards/Procedures
        - GRC platform entities (Archer)
        """
        # Implementation using NLP libraries
        # (spaCy, NLTK, regex patterns, domain lexicons)
        pass

    def _classify_entities(self, entities: List[str]) -> Dict[str, str]:
        """Map entities to types (process, risk, control, regulation, policy)."""
        pass

    def _generate_semantic_tags(self, text: str) -> List[str]:
        """Generate semantic tags based on content."""
        pass

    def _map_relationships(self, text: str, entities: List[str]) -> List[Dict]:
        """Map relationships between entities."""
        pass
```

**Registration**:
```python
# In src/pipeline/__init__.py
from processors import (
    ContextLinker,
    MetadataAggregator,
    SemanticAnalyzer,  # NEW
    QualityValidator
)

# Register all processors
pipeline = ExtractionPipeline()
pipeline.add_processor(ContextLinker())
pipeline.add_processor(MetadataAggregator())
pipeline.add_processor(SemanticAnalyzer())  # Automatically ordered after dependencies
pipeline.add_processor(QualityValidator())
```

### Option 2: RAG-Optimized Formatter

**Best for**: Journey A (RAG optimization and output formatting)

**Implementation Pattern**:

```python
# src/formatters/rag_optimized_formatter.py
from core import BaseFormatter, ProcessingResult, FormattedOutput

class RagOptimizedFormatter(BaseFormatter):
    """
    Format content for RAG pipeline optimization.

    Features:
    - Semantic chunking with context preservation
    - Metadata enrichment for retrieval
    - Schema standardization
    - Quality indicators
    - Embedding preparation
    """

    def format(self, processing_result: ProcessingResult) -> FormattedOutput:
        """
        Generate RAG-optimized output.

        Output Schema:
        {
            "chunks": [
                {
                    "chunk_id": "doc123_chunk_001",
                    "content": "chunk text with context",
                    "context": {
                        "document_path": ["Chapter 1", "Section 1.1"],
                        "parent_heading": "Section 1.1",
                        "depth": 2
                    },
                    "metadata": {
                        "source_file": "document.docx",
                        "page_number": 5,
                        "word_count": 150,
                        "entities": ["NIST SP 800-53", "access control"],
                        "semantic_tags": ["regulation", "control"]
                    },
                    "quality_score": 85.2,
                    "embedding_ready": true
                },
                ...
            ],
            "document_metadata": {...},
            "chunk_statistics": {
                "total_chunks": 42,
                "average_chunk_size": 512,
                "overlap_tokens": 50
            }
        }
        """
        chunks = self._create_semantic_chunks(processing_result)
        standardized_chunks = self._standardize_schema(chunks)

        output_data = {
            "chunks": standardized_chunks,
            "document_metadata": processing_result.document_metadata,
            "chunk_statistics": self._compute_chunk_stats(chunks)
        }

        return FormattedOutput(
            content=json.dumps(output_data, indent=2),
            format_type="rag_optimized",
            source_document=processing_result.document_metadata.source_file,
            success=True
        )

    def _create_semantic_chunks(self, processing_result: ProcessingResult) -> List[Dict]:
        """
        Create semantically meaningful chunks.

        Strategy:
        - Respect document hierarchy (don't split mid-section)
        - Preserve context boundaries
        - Target chunk size: 512 tokens (configurable)
        - Overlap: 50 tokens (configurable)
        - Include parent context in each chunk
        """
        pass

    def get_format_type(self) -> str:
        return "rag_optimized"
```

---

## Processor Chain Analysis

### Current Processor Execution Order

**1. ContextLinker** (REQUIRED, no dependencies)
- **Purpose**: Build document hierarchy
- **Input**: Flat list of content blocks
- **Output**: Content blocks with parent_id, depth, document_path
- **Runtime**: O(n) where n = number of blocks
- **Key Output**: `metadata["depth"]`, `metadata["document_path"]`, `parent_id`

**2. MetadataAggregator** (OPTIONAL, no dependencies)
- **Purpose**: Compute statistics
- **Input**: Content blocks (with or without hierarchy)
- **Output**: Content blocks with word_count, char_count, entities (placeholder)
- **Runtime**: O(n)
- **Key Output**: `metadata["word_count"]`, `metadata["char_count"]`, `stage_metadata`

**3. QualityValidator** (OPTIONAL, no dependencies but benefits from MetadataAggregator)
- **Purpose**: Score extraction quality
- **Input**: Content blocks with metadata
- **Output**: Same blocks + quality_score, quality_issues, needs_review
- **Runtime**: O(n)
- **Key Output**: `quality_score`, `quality_issues`, `needs_review`

### Dependency Graph

```
ContextLinker (no deps)
    │
    ├──────► MetadataAggregator (no deps, but can run after ContextLinker)
    │            │
    │            └──────► QualityValidator (no deps, benefits from MetadataAggregator)
    │                         │
    └────────────────────────► SemanticAnalyzer (deps: ContextLinker, MetadataAggregator)
                                   │
                                   └──────► [Future processors can depend on SemanticAnalyzer]
```

### Adding SemanticAnalyzer to the Chain

**Recommended Position**: After MetadataAggregator, before QualityValidator

**Why This Order?**
1. **After ContextLinker**: Semantic analysis benefits from document hierarchy
   - Use `document_path` for context
   - Use `depth` for importance weighting
   - Use `parent_id` for relationship mapping

2. **After MetadataAggregator**: Semantic analysis benefits from statistics
   - Use `word_count` for normalization
   - Use `content_type_distribution` for content analysis
   - Use `summary` for document overview

3. **Before QualityValidator**: Quality validation can use semantic results
   - Semantic quality indicators
   - Entity-based quality metrics
   - Domain relevance scoring

**Dependency Declaration**:
```python
def get_dependencies(self) -> list[str]:
    return ["ContextLinker", "MetadataAggregator"]
```

**Resulting Execution Order**:
```
1. ContextLinker
2. MetadataAggregator
3. SemanticAnalyzer ← NEW
4. QualityValidator
```

---

## Adding a Custom Processor

### Step-by-Step Guide

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

## Data Flow and Transformations

### Data Structure Evolution

```
INPUT: document.docx
    │
    │ ┌─────────────────────────────────────┐
    ├─► EXTRACTION STAGE                    │
    │ └─────────────────────────────────────┘
    ▼
ExtractionResult(
    content_blocks=(
        ContentBlock(
            block_id="abc123",
            block_type=ContentType.PARAGRAPH,
            content="This is a paragraph.",
            metadata={},  # Empty metadata
            parent_id=None,  # No hierarchy yet
        ),
        ...
    ),
    document_metadata=DocumentMetadata(...),
    images=(...),
    tables=(...),
)
    │
    │ ┌─────────────────────────────────────┐
    ├─► PROCESSING: ContextLinker           │
    │ └─────────────────────────────────────┘
    ▼
ProcessingResult(
    content_blocks=(
        ContentBlock(
            block_id="abc123",  # Same ID
            content="This is a paragraph.",  # Same content
            metadata={
                "depth": 2,  # NEW: Hierarchy depth
                "document_path": ["Chapter 1", "Section 1.1"],  # NEW: Breadcrumb
            },
            parent_id="heading123",  # NEW: Parent reference
        ),
        ...
    ),
)
    │
    │ ┌─────────────────────────────────────┐
    ├─► PROCESSING: MetadataAggregator      │
    │ └─────────────────────────────────────┘
    ▼
ProcessingResult(
    content_blocks=(
        ContentBlock(
            block_id="abc123",
            content="This is a paragraph.",
            metadata={
                "depth": 2,  # Preserved
                "document_path": ["Chapter 1", "Section 1.1"],  # Preserved
                "word_count": 4,  # NEW: Word count
                "char_count": 19,  # NEW: Character count
            },
            parent_id="heading123",  # Preserved
        ),
        ...
    ),
    stage_metadata={
        "total_words": 1234,
        "average_words_per_block": 42.3,
        ...
    },
)
    │
    │ ┌─────────────────────────────────────┐
    ├─► PROCESSING: SemanticAnalyzer        │ ← YOUR PROCESSOR
    │ └─────────────────────────────────────┘
    ▼
ProcessingResult(
    content_blocks=(
        ContentBlock(
            block_id="abc123",
            content="This is a paragraph.",
            metadata={
                "depth": 2,  # Preserved
                "document_path": ["Chapter 1", "Section 1.1"],  # Preserved
                "word_count": 4,  # Preserved
                "char_count": 19,  # Preserved
                "entities": ["example entity"],  # NEW: Extracted entities
                "semantic_tags": ["process", "control"],  # NEW: Domain tags
                "entity_types": {"example entity": "process"},  # NEW: Entity classification
                "domain_classification": "cybersecurity_audit",  # NEW: Domain
            },
            parent_id="heading123",  # Preserved
        ),
        ...
    ),
    stage_metadata={
        "entities_found": 42,
        "unique_entities": 28,
        ...
    },
)
    │
    │ ┌─────────────────────────────────────┐
    ├─► PROCESSING: QualityValidator        │
    │ └─────────────────────────────────────┘
    ▼
ProcessingResult(
    content_blocks=(...),  # All metadata preserved + quality_checked flag
    quality_score=85.2,  # NEW: Quality score
    quality_issues=(...),  # NEW: Quality issues
    needs_review=False,  # NEW: Review flag
)
    │
    │ ┌─────────────────────────────────────┐
    ├─► FORMATTING: JsonFormatter           │
    │ └─────────────────────────────────────┘
    ▼
FormattedOutput(
    content='{"content_blocks": [...], ...}',  # JSON string
    format_type="json",
)
    │
    ▼
OUTPUT: document.json (with all enriched metadata)
```

### Metadata Preservation Pattern

**Critical Rule**: Each processor must preserve metadata from previous processors

```python
# ✅ CORRECT: Preserve existing metadata
enriched_metadata = {
    **block.metadata,  # Spread existing metadata
    "new_field": new_value,  # Add new fields
}

# ❌ WRONG: Overwrites existing metadata
enriched_metadata = {
    "new_field": new_value,  # Loses all previous enrichments!
}
```

---

## Configuration and Dependency Injection

### Processor Configuration

**Pattern 1: Constructor Injection**
```python
class SemanticAnalyzer(BaseProcessor):
    def __init__(self, config: Optional[dict] = None):
        super().__init__(config)
        self.entity_extraction_enabled = self.config.get("entity_extraction", True)
        self.domain_model = self.config.get("domain_model", "general")
```

**Pattern 2: ConfigManager Integration**
```python
# config.yaml
processors:
  semantic_analyzer:
    enabled: true
    entity_extraction: true
    domain_model: "cybersecurity_audit"
    grc_entities:
      - processes
      - risks
      - controls
      - regulations
    confidence_threshold: 0.7
    nlp_library: "spacy"  # or "nltk"
    spacy_model: "en_core_web_sm"
```

```python
# In processor
from infrastructure import ConfigManager

class SemanticAnalyzer(BaseProcessor):
    def __init__(self, config: Optional[dict] = None, config_manager: Optional[ConfigManager] = None):
        super().__init__(config)
        self.config_manager = config_manager

        # Load from ConfigManager if available
        if config_manager:
            self.processor_config = config_manager.get("processors.semantic_analyzer", default={})
        else:
            self.processor_config = self.config
```

### Logging Integration

```python
from infrastructure import get_logger

class SemanticAnalyzer(BaseProcessor):
    def __init__(self, config: Optional[dict] = None):
        super().__init__(config)
        self.logger = get_logger(__name__)

    def process(self, extraction_result: ExtractionResult) -> ProcessingResult:
        self.logger.info("Starting semantic analysis", extra={
            "processor": self.get_processor_name(),
            "block_count": len(extraction_result.content_blocks),
        })

        # Processing logic...

        self.logger.info("Semantic analysis complete", extra={
            "entities_found": total_entities,
            "processing_time_seconds": elapsed_time,
        })
```

---

## Error Handling and Recovery

### Error Handling Patterns

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

### Error Handler Integration

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

## Performance Considerations

### Benchmarking Guidelines

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

### Memory Management

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

## Summary: Integration Checklist

✅ **Before You Start**:
- [ ] Read `docs/architecture/FOUNDATION.md` (data models and interfaces)
- [ ] Review current processor implementations (`src/processors/*.py`)
- [ ] Understand processor ordering mechanism (`_order_processors()`)
- [ ] Study data flow through pipeline (this doc)

✅ **Implementing Your Processor**:
- [ ] Create `src/processors/semantic_analyzer.py`
- [ ] Implement `BaseProcessor` interface
- [ ] Declare dependencies via `get_dependencies()`
- [ ] Set `is_optional()` appropriately
- [ ] Preserve all existing metadata in enriched blocks
- [ ] Preserve media assets (images, tables)
- [ ] Add new `ProcessingStage` enum value
- [ ] Implement error handling (graceful degradation or partial processing)
- [ ] Add logging with structured context

✅ **Configuration**:
- [ ] Define configuration schema (Pydantic model recommended)
- [ ] Add config section to `config.yaml.example`
- [ ] Support constructor injection
- [ ] Support ConfigManager integration
- [ ] Document all configuration options

✅ **Testing**:
- [ ] Write unit tests for semantic extraction logic
- [ ] Write integration tests with real audit documents
- [ ] Test dependency ordering
- [ ] Test error handling (missing libraries, malformed input)
- [ ] Test performance with large documents
- [ ] Verify metadata preservation

✅ **Integration**:
- [ ] Register processor in `src/pipeline/__init__.py`
- [ ] Update CLI to include new processor (if configurable)
- [ ] Update documentation (`README.md`, `USER_GUIDE.md`)
- [ ] Add examples to `examples/` directory

✅ **Validation**:
- [ ] Run full test suite (ensure no regressions)
- [ ] Test on real audit documents (COBIT, NIST, OWASP, GRC exports)
- [ ] Verify pipeline ordering (check logs)
- [ ] Measure performance impact
- [ ] Review output quality

---

## Next Steps

**Recommended Reading Order**:
1. `docs/bmm-project-overview.md` - Project context
2. `docs/bmm-processor-chain-analysis.md` - Detailed processor analysis
3. `docs/architecture/FOUNDATION.md` - Core interfaces and data models
4. `src/processors/context_linker.py` - Example processor implementation
5. `src/processors/metadata_aggregator.py` - Example with metadata enrichment

**Prototyping**:
1. Start with a simple proof-of-concept processor
2. Test entity extraction on sample audit documents
3. Iterate on entity classification accuracy
4. Expand to full semantic analysis features

**Planning**:
1. Run BMM `brainstorm-project` workflow for ideation
2. Research semantic analysis libraries (Python 3.12 compatible, no LLMs)
3. Create PRD defining Journey A and Journey B features
4. Design detailed architecture for semantic integration

---

**Document Status**: ✅ Complete | **Generated**: 2025-11-07 | **Priority**: 1 (User-requested)
