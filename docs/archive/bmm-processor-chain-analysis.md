# Processor Chain Analysis - Semantic Analysis Integration Points

**Generated**: 2025-11-07
**Audience**: Developers adding semantic analysis features
**Focus**: Processor/formatter chain architecture
**Priority**: 2 (User-requested focus area)

---

## Table of Contents

1. [Processor Chain Overview](#processor-chain-overview)
2. [Current Processor Implementations](#current-processor-implementations)
3. [Processor Interface Contract](#processor-interface-contract)
4. [Dependency Resolution Mechanism](#dependency-resolution-mechanism)
5. [Data Enrichment Patterns](#data-enrichment-patterns)
6. [Semantic Analysis Processor Design](#semantic-analysis-processor-design)
7. [Formatter Chain Analysis](#formatter-chain-analysis)
8. [RAG-Optimized Formatter Design](#rag-optimized-formatter-design)

---

## Processor Chain Overview

### What is a Processor?

A **processor** is a modular component that enriches content blocks with additional metadata without modifying the original content. Think of processors as stages in an enrichment pipeline:

```
Raw Content → Context → Statistics → Quality → Semantics → Output
              ├─────┴─────┴──────┴──────────┘
              Processor Chain (ordered by dependencies)
```

### Key Characteristics

1. **Immutable Operations**: Create new ContentBlocks, never modify existing ones
2. **Dependency-Ordered**: Automatically sorted based on `get_dependencies()`
3. **Composable**: Each processor builds on previous processors' enrichments
4. **Optional/Required**: Can be marked as optional (pipeline continues on failure)
5. **Metadata Enrichment**: Add fields to `metadata` dict without removing existing fields

### Current Processor Chain (v1.0.6)

```python
# Automatic execution order (based on dependencies):
1. ContextLinker       # No dependencies, runs first
2. MetadataAggregator  # No dependencies, runs second
3. QualityValidator    # No dependencies, runs third

# Where semantic analysis fits:
1. ContextLinker       # Provides hierarchy
2. MetadataAggregator  # Provides statistics
3. SemanticAnalyzer    # ← NEW: Uses hierarchy + statistics
4. QualityValidator    # Can use semantic results for quality scoring
```

---

## Current Processor Implementations

### 1. ContextLinker (REQUIRED)

**Location**: `src/processors/context_linker.py`
**Purpose**: Build hierarchical document structure from flat content blocks
**Dependencies**: None (runs first)
**Optional**: No (required for downstream processors)

**What It Does**:
- Tracks heading hierarchy (H1 > H2 > H3 > ...)
- Links paragraphs and content to parent headings
- Computes depth information for each block
- Generates document paths (breadcrumb trails)

**Key Algorithm**:
```python
heading_stack = {}  # Maps level → (block_id, title)

for block in content_blocks:
    if block.block_type == ContentType.HEADING:
        level = block.metadata.get("level", 1)

        # Update stack at this level
        heading_stack[level] = (block.block_id, block.content)

        # Clear deeper levels
        for l in list(heading_stack.keys()):
            if l > level:
                del heading_stack[l]

        # Find parent (closest higher-level heading)
        parent_id = find_parent_heading(heading_stack, level)
        depth = level - 1

    else:  # Content block (PARAGRAPH, LIST, TABLE, etc.)
        # Link to most recent heading
        parent_id = find_current_parent(heading_stack)
        depth = compute_depth(heading_stack)

    # Build document path (breadcrumb trail)
    document_path = build_document_path(heading_stack)

    # Create enriched block with new metadata
    enriched_metadata = {
        **block.metadata,
        "depth": depth,
        "document_path": document_path,
    }
```

**Example Output**:

**Input**:
```python
ContentBlock(
    block_type=ContentType.PARAGRAPH,
    content="This paragraph describes access controls.",
    metadata={},  # Empty
    parent_id=None,  # No parent
)
```

**Output** (after ContextLinker):
```python
ContentBlock(
    block_type=ContentType.PARAGRAPH,
    content="This paragraph describes access controls.",  # Same content
    metadata={
        "depth": 2,  # NEW: Nesting depth
        "document_path": ["Chapter 1", "Section 1.1: Access Controls"],  # NEW: Breadcrumb
    },
    parent_id="heading_abc123",  # NEW: Parent reference
)
```

**Why This Matters for Semantic Analysis**:
- **Document Path**: Use for context (e.g., "This paragraph is under 'Access Controls' in 'Chapter 1'")
- **Depth**: Weight entity importance (deeper content may be less significant)
- **Parent ID**: Build relationship graphs between entities and their containing sections

### 2. MetadataAggregator (OPTIONAL)

**Location**: `src/processors/metadata_aggregator.py`
**Purpose**: Compute statistics and extract entities (placeholder)
**Dependencies**: None (but benefits from ContextLinker output)
**Optional**: Yes (enrichment only, not critical)

**What It Does**:
- Counts words and characters per block
- Computes document-wide statistics (total words, averages, min/max)
- Tracks content type distribution
- Generates document summary (top N headings)
- **Placeholder**: Entity extraction (currently disabled)

**Key Statistics Computed**:

**Block-Level** (added to each block's metadata):
- `word_count`: Number of words in block
- `char_count`: Number of characters in block
- `entities`: List of extracted entities (placeholder, empty by default)

**Document-Level** (added to `stage_metadata`):
- `total_words`: Sum of all words in document
- `total_characters`: Sum of all characters
- `average_words_per_block`: Mean word count
- `min_words_per_block`: Minimum word count (non-empty blocks)
- `max_words_per_block`: Maximum word count
- `content_type_distribution`: Count by type ({"heading": 28, "paragraph": 180, ...})
- `unique_content_types`: Number of unique types
- `summary`: High-level document summary (top headings)

**Example Output**:

**Input** (from ContextLinker):
```python
ContentBlock(
    content="This paragraph describes access controls.",
    metadata={
        "depth": 2,
        "document_path": ["Chapter 1", "Section 1.1"],
    },
    ...
)
```

**Output** (after MetadataAggregator):
```python
ContentBlock(
    content="This paragraph describes access controls.",  # Same content
    metadata={
        "depth": 2,  # Preserved
        "document_path": ["Chapter 1", "Section 1.1"],  # Preserved
        "word_count": 5,  # NEW: Word count
        "char_count": 42,  # NEW: Character count
    },
    ...
)
```

**Stage Metadata**:
```python
{
    "total_words": 5234,
    "total_characters": 32456,
    "average_words_per_block": 21.3,
    "min_words_per_block": 1,
    "max_words_per_block": 287,
    "content_type_distribution": {
        "heading": 28,
        "paragraph": 180,
        "list_item": 42,
        "table": 12,
    },
    "unique_content_types": 4,
    "summary": {
        "headings": ["Chapter 1: Introduction", "Chapter 2: Framework", ...]
    }
}
```

**Why This Matters for Semantic Analysis**:
- **Word Count**: Normalize entity density (entities per 100 words)
- **Content Type Distribution**: Understand document structure (heavy on lists? tables?)
- **Summary**: Quick overview for context
- **Entity Extraction Placeholder**: This is WHERE entity extraction should happen (currently disabled)

**Placeholder Entity Extraction** (lines 210-235):
```python
def _extract_entities(self, text: str) -> list[str]:
    """
    Extract named entities from text.

    This is a placeholder for entity extraction. In production,
    this would use spaCy or another NLP library.

    Note:
        Actual implementation would use:
        ```python
        import spacy
        nlp = spacy.load("en_core_web_sm")
        doc = nlp(text)
        return [ent.text for ent in doc.ents]
        ```
    """
    # Placeholder - entity extraction disabled by default
    # Would require spaCy which may not be available in enterprise env
    return []
```

**Integration Opportunity**: Replace this placeholder or create dedicated SemanticAnalyzer processor.

### 3. QualityValidator (OPTIONAL)

**Location**: `src/processors/quality_validator.py`
**Purpose**: Score extraction quality and identify issues
**Dependencies**: None (but benefits from MetadataAggregator output)
**Optional**: Yes (informational only, doesn't modify content)

**What It Does**:
- Computes multi-dimensional quality score (0-100)
- Identifies specific quality issues
- Sets `needs_review` flag for low-quality extractions
- Provides detailed quality metrics

**Quality Dimensions**:

1. **Completeness** (0-100):
   - Presence of headings (document structure)
   - Content type diversity
   - Empty blocks (penalty)

2. **Consistency** (0-100):
   - Confidence scores present
   - Confidence scores reasonable (not too low)
   - Metadata completeness

3. **Readability** (0-100):
   - Text appears readable (not corrupted)
   - Special character ratio reasonable
   - No abnormally long words (>30 chars = corruption)

**Overall Score**: Average of all dimensions

**Example Output**:

**ProcessingResult**:
```python
ProcessingResult(
    content_blocks=(...),  # Enriched blocks (minimal changes)
    quality_score=85.2,  # NEW: Overall quality
    quality_issues=(  # NEW: Specific issues
        "2 empty blocks found",
        "1 block with low confidence",
    ),
    needs_review=False,  # NEW: Review flag (score >= 60)
    stage_metadata={
        "completeness_score": 90.0,
        "consistency_score": 85.0,
        "readability_score": 80.7,
        "empty_blocks": 2,
        "blocks_without_confidence": 0,
        "low_confidence_blocks": 1,
        "suspicious_blocks": 0,
    },
)
```

**Why This Matters for Semantic Analysis**:
- **Quality Score Baseline**: Semantic analysis can add quality indicators
- **Needs Review Flag**: Low-quality extractions may need manual entity verification
- **Readability Issues**: Skip semantic analysis on corrupted blocks

---

## Processor Interface Contract

### BaseProcessor Abstract Class

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

### ProcessingResult Data Structure

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

## Dependency Resolution Mechanism

### Topological Sort Algorithm

**Location**: `src/pipeline/extraction_pipeline.py` (lines 213-266)

**Purpose**: Automatically order processors based on declared dependencies

**Algorithm**: Kahn's algorithm for topological sorting

**How It Works**:

```python
def _order_processors(self) -> list[BaseProcessor]:
    """Order processors based on dependencies using topological sort."""

    # Build dependency graph
    graph: dict[str, list[str]] = {}
    processor_map: dict[str, BaseProcessor] = {}

    for processor in self._processors:
        name = processor.get_processor_name()
        processor_map[name] = processor
        graph[name] = processor.get_dependencies()  # List of dependency names

    # Calculate in-degrees (number of dependencies per processor)
    in_degree: dict[str, int] = {}
    for name, deps in graph.items():
        in_degree[name] = len(deps)

    # Queue of processors with no dependencies
    queue = [name for name, degree in in_degree.items() if degree == 0]
    ordered = []

    while queue:
        current = queue.pop(0)
        ordered.append(current)

        # Find processors that depend on current
        for name, deps in graph.items():
            if current in deps:
                in_degree[name] -= 1
                if in_degree[name] == 0 and name not in ordered:
                    queue.append(name)

    # Check for circular dependencies
    if len(ordered) != len(graph):
        raise ValueError("Circular dependency detected in processor chain")

    # Convert names back to processor instances
    return [processor_map[name] for name in ordered]
```

### Example Dependency Resolution

**Scenario**: Add SemanticAnalyzer with dependencies

```python
# Registered processors (unordered)
pipeline.add_processor(QualityValidator())       # No deps
pipeline.add_processor(MetadataAggregator())     # No deps
pipeline.add_processor(SemanticAnalyzer())       # Deps: ["ContextLinker", "MetadataAggregator"]
pipeline.add_processor(ContextLinker())          # No deps

# Dependency graph
graph = {
    "QualityValidator": [],
    "MetadataAggregator": [],
    "SemanticAnalyzer": ["ContextLinker", "MetadataAggregator"],
    "ContextLinker": [],
}

# In-degrees (number of dependencies)
in_degree = {
    "QualityValidator": 0,
    "MetadataAggregator": 0,
    "SemanticAnalyzer": 2,  # Depends on 2 processors
    "ContextLinker": 0,
}

# Topological sort execution
# Step 1: Queue = ["QualityValidator", "MetadataAggregator", "ContextLinker"]
#         (all processors with in_degree == 0)
# Step 2: Process "ContextLinker" first (arbitrary choice from queue)
#         → ordered = ["ContextLinker"]
#         → SemanticAnalyzer in_degree reduced: 2 → 1
# Step 3: Process "MetadataAggregator"
#         → ordered = ["ContextLinker", "MetadataAggregator"]
#         → SemanticAnalyzer in_degree reduced: 1 → 0
#         → Add SemanticAnalyzer to queue
# Step 4: Process "SemanticAnalyzer"
#         → ordered = ["ContextLinker", "MetadataAggregator", "SemanticAnalyzer"]
# Step 5: Process "QualityValidator"
#         → ordered = ["ContextLinker", "MetadataAggregator", "SemanticAnalyzer", "QualityValidator"]

# Final execution order
[ContextLinker, MetadataAggregator, SemanticAnalyzer, QualityValidator]
```

**Key Insight**: You don't need to worry about registration order. Declare dependencies and the pipeline handles ordering automatically.

---

## Data Enrichment Patterns

### Pattern 1: Metadata Preservation (CRITICAL)

**Rule**: Always preserve existing metadata from previous processors

```python
# ✅ CORRECT: Spread existing metadata, add new fields
enriched_metadata = {
    **block.metadata,  # Preserve all existing fields
    "entities": extracted_entities,  # Add new field
    "semantic_tags": tags,  # Add new field
}

# ❌ WRONG: Overwrites all existing metadata
enriched_metadata = {
    "entities": extracted_entities,  # Loses depth, document_path, word_count, etc.!
}
```

**Why This Matters**: Each processor builds on previous enrichments. If you overwrite metadata, you break the chain.

### Pattern 2: Immutable Block Creation

**Rule**: Never modify existing ContentBlocks, always create new ones

```python
# ✅ CORRECT: Create new ContentBlock
enriched_block = ContentBlock(
    block_id=block.block_id,  # Same ID (preserve reference)
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

# ❌ WRONG: Modify existing block (ContentBlock is frozen dataclass)
block.metadata["entities"] = extracted_entities  # ERROR: frozen instance
```

### Pattern 3: Media Asset Preservation (CRITICAL)

**Rule**: Always pass through images and tables unchanged

```python
# ✅ CORRECT: Preserve media assets
return ProcessingResult(
    content_blocks=tuple(enriched_blocks),
    document_metadata=extraction_result.document_metadata,
    images=extraction_result.images,  # PRESERVE
    tables=extraction_result.tables,  # PRESERVE
    processing_stage=ProcessingStage.SEMANTIC_ANALYSIS,
    stage_metadata={...},
    success=True,
)

# ❌ WRONG: Drop media assets
return ProcessingResult(
    content_blocks=tuple(enriched_blocks),
    document_metadata=extraction_result.document_metadata,
    # Missing images and tables! They're lost forever!
    processing_stage=ProcessingStage.SEMANTIC_ANALYSIS,
    stage_metadata={...},
    success=True,
)
```

**Why This Matters**: Images and tables are extracted by extractors (DOCX, PDF, etc.). If processors don't preserve them, they're lost from the output.

### Pattern 4: Empty Input Handling

**Rule**: Gracefully handle empty content blocks

```python
def process(self, extraction_result: ExtractionResult) -> ProcessingResult:
    """Process extracted content."""

    # Handle empty input
    if not extraction_result.content_blocks:
        return ProcessingResult(
            content_blocks=tuple(),
            document_metadata=extraction_result.document_metadata,
            images=extraction_result.images,
            tables=extraction_result.tables,
            processing_stage=ProcessingStage.SEMANTIC_ANALYSIS,
            stage_metadata={"entities_found": 0},
            success=True,  # Empty is not an error
        )

    # Normal processing
    ...
```

### Pattern 5: Partial Processing (Best Effort)

**Rule**: Process as many blocks as possible, don't fail entire pipeline on single block error

```python
def process(self, extraction_result: ExtractionResult) -> ProcessingResult:
    """Process with best-effort approach."""

    enriched_blocks = []
    errors = []

    for block in extraction_result.content_blocks:
        try:
            # Try to enrich this block
            enriched_block = self._enrich_block(block)
            enriched_blocks.append(enriched_block)
        except Exception as e:
            # Log error but continue
            self.logger.warning(f"Failed to enrich block {block.block_id}: {e}")
            errors.append(f"Block {block.block_id}: {str(e)}")
            # Add original block (no enrichment for this one)
            enriched_blocks.append(block)

    return ProcessingResult(
        content_blocks=tuple(enriched_blocks),
        ...,
        success=True,  # Overall success (partial processing)
        errors=tuple(errors),  # But log errors for debugging
    )
```

---

## Semantic Analysis Processor Design

### Recommended Architecture

```python
# src/processors/semantic_analyzer.py
from typing import List, Dict, Optional, Set, Tuple
from dataclasses import dataclass
from pathlib import Path

from core import (
    BaseProcessor,
    ExtractionResult,
    ProcessingResult,
    ProcessingStage,
    ContentBlock,
)
from infrastructure import get_logger, ConfigManager


@dataclass
class Entity:
    """Extracted entity with metadata."""
    text: str
    entity_type: str  # "process", "risk", "control", "regulation", "policy"
    confidence: float
    mentions: List[str]  # All text variations found
    block_ids: List[str]  # Blocks where entity appears


@dataclass
class Relationship:
    """Relationship between entities."""
    source_entity: str
    target_entity: str
    relationship_type: str  # "implements", "mitigates", "requires", etc.
    confidence: float
    evidence_block_ids: List[str]  # Blocks providing evidence


class SemanticAnalyzer(BaseProcessor):
    """
    Semantic analysis processor for cybersecurity audit knowledge base curation.

    Capabilities:
    - Domain-specific entity extraction (processes, risks, controls, regulations, policies)
    - Entity classification and normalization
    - Relationship mapping between entities
    - Semantic tagging for GRC domains
    - Context enrichment using document hierarchy
    - Quality indicators for RAG optimization

    Configuration Options:
        entity_extraction (bool): Enable entity extraction (default: True)
        relationship_mapping (bool): Enable relationship extraction (default: False)
        domain_model (str): Domain model to use ("cybersecurity_audit", "general")
        confidence_threshold (float): Minimum confidence for entities (default: 0.7)
        grc_entities (list): List of GRC entity types to extract
        nlp_library (str): NLP library to use ("spacy", "nltk", "regex")
        enable_normalization (bool): Normalize entity names (default: True)

    Dependencies:
        - ContextLinker: Provides document hierarchy for context
        - MetadataAggregator: Provides word counts for normalization

    Performance:
        - Target: +3-5s per document
        - Memory: +50-500MB (NLP model loading)
        - Batch friendly: Reuses loaded models across documents
    """

    def __init__(self, config: Optional[dict] = None):
        """Initialize semantic analyzer with configuration."""
        super().__init__(config)

        self.logger = get_logger(__name__)

        # Configuration
        self.entity_extraction_enabled = self.config.get("entity_extraction", True)
        self.relationship_mapping_enabled = self.config.get("relationship_mapping", False)
        self.domain_model = self.config.get("domain_model", "cybersecurity_audit")
        self.confidence_threshold = self.config.get("confidence_threshold", 0.7)
        self.grc_entities = self.config.get("grc_entities", [
            "processes", "risks", "controls", "regulations", "policies"
        ])

        # NLP model (lazy loaded)
        self._nlp_model = None

        # Domain lexicons (lazy loaded)
        self._entity_lexicons: Optional[Dict[str, Set[str]]] = None

        self.logger.info("SemanticAnalyzer initialized", extra={
            "domain_model": self.domain_model,
            "entity_extraction": self.entity_extraction_enabled,
            "relationship_mapping": self.relationship_mapping_enabled,
        })

    def get_processor_name(self) -> str:
        """Return processor name."""
        return "SemanticAnalyzer"

    def get_dependencies(self) -> list[str]:
        """Declare dependencies on other processors."""
        return ["ContextLinker", "MetadataAggregator"]

    def is_optional(self) -> bool:
        """Semantic analysis is optional (don't block pipeline on failure)."""
        return True

    def process(self, extraction_result: ExtractionResult) -> ProcessingResult:
        """
        Enrich content blocks with semantic analysis.

        Processing Steps:
        1. Handle empty input
        2. Extract entities from all blocks (batch processing for performance)
        3. Classify and normalize entities
        4. Map relationships between entities (if enabled)
        5. Generate semantic tags based on content
        6. Compute quality indicators for RAG optimization
        7. Enrich each block's metadata
        8. Return ProcessingResult with aggregate statistics

        Args:
            extraction_result: Extraction result from previous stage

        Returns:
            ProcessingResult with semantically enriched content blocks
        """
        self.logger.info("Starting semantic analysis", extra={
            "block_count": len(extraction_result.content_blocks),
        })

        start_time = time.time()

        # Handle empty input
        if not extraction_result.content_blocks:
            return ProcessingResult(
                content_blocks=tuple(),
                document_metadata=extraction_result.document_metadata,
                images=extraction_result.images,
                tables=extraction_result.tables,
                processing_stage=ProcessingStage.SEMANTIC_ANALYSIS,
                stage_metadata={"entities_found": 0, "processing_time_seconds": 0},
                success=True,
            )

        try:
            # Step 1: Batch entity extraction (performance optimization)
            all_entities = self._extract_entities_batch(extraction_result.content_blocks)

            # Step 2: Classify and normalize entities
            classified_entities = self._classify_entities(all_entities)

            # Step 3: Map relationships (if enabled)
            relationships = []
            if self.relationship_mapping_enabled:
                relationships = self._map_relationships(
                    extraction_result.content_blocks,
                    classified_entities
                )

            # Step 4: Enrich each block
            enriched_blocks = []
            for block in extraction_result.content_blocks:
                # Get entities for this block
                block_entities = [e for e in all_entities if block.block_id in e.block_ids]

                # Generate semantic tags
                semantic_tags = self._generate_semantic_tags(
                    block.content,
                    block_entities,
                    block.metadata.get("document_path", [])
                )

                # Compute quality indicators
                quality_indicators = self._compute_quality_indicators(
                    block,
                    block_entities,
                    semantic_tags
                )

                # Enrich metadata (PRESERVE existing metadata)
                enriched_metadata = {
                    **block.metadata,  # Preserve all existing fields
                    "entities": [e.text for e in block_entities],
                    "entity_types": {e.text: e.entity_type for e in block_entities},
                    "entity_confidences": {e.text: e.confidence for e in block_entities},
                    "semantic_tags": semantic_tags,
                    "domain_classification": self.domain_model,
                    "semantic_quality_indicators": quality_indicators,
                }

                # Create enriched block
                enriched_block = ContentBlock(
                    block_id=block.block_id,
                    block_type=block.block_type,
                    content=block.content,
                    raw_content=block.raw_content,
                    position=block.position,
                    parent_id=block.parent_id,
                    related_ids=block.related_ids,
                    metadata=enriched_metadata,
                    confidence=block.confidence,
                    style=block.style,
                )

                enriched_blocks.append(enriched_block)

            # Compute aggregate statistics
            elapsed_time = time.time() - start_time
            unique_entities = len(set(e.text for e in all_entities))
            entity_types_dist = {}
            for e in all_entities:
                entity_types_dist[e.entity_type] = entity_types_dist.get(e.entity_type, 0) + 1

            stage_metadata = {
                "total_entities_found": len(all_entities),
                "unique_entities": unique_entities,
                "entity_types_distribution": entity_types_dist,
                "relationships_found": len(relationships),
                "processing_time_seconds": round(elapsed_time, 2),
                "domain_model": self.domain_model,
            }

            self.logger.info("Semantic analysis complete", extra=stage_metadata)

            return ProcessingResult(
                content_blocks=tuple(enriched_blocks),
                document_metadata=extraction_result.document_metadata,
                images=extraction_result.images,  # PRESERVE
                tables=extraction_result.tables,  # PRESERVE
                processing_stage=ProcessingStage.SEMANTIC_ANALYSIS,
                stage_metadata=stage_metadata,
                success=True,
            )

        except Exception as e:
            # Graceful degradation: return original blocks
            self.logger.exception("Semantic analysis failed", exc_info=e)
            return ProcessingResult(
                content_blocks=extraction_result.content_blocks,
                document_metadata=extraction_result.document_metadata,
                images=extraction_result.images,
                tables=extraction_result.tables,
                processing_stage=ProcessingStage.SEMANTIC_ANALYSIS,
                stage_metadata={"error": str(e)},
                success=False,
                errors=(f"Semantic analysis failed: {str(e)}",),
            )

    def _extract_entities_batch(self, blocks: tuple[ContentBlock, ...]) -> List[Entity]:
        """
        Extract entities from all blocks (batch processing for performance).

        This method processes all blocks together for efficiency.
        NLP models are more efficient when processing larger text batches.

        Args:
            blocks: All content blocks

        Returns:
            List of Entity objects with block_ids mapping
        """
        # TODO: Implement batch entity extraction
        # Suggested approach:
        # 1. Combine all block texts (preserve block IDs for mapping)
        # 2. Run NLP model once on combined text
        # 3. Map extracted entities back to block IDs
        # 4. Return Entity objects with block_ids populated
        pass

    def _classify_entities(self, entities: List[Entity]) -> List[Entity]:
        """
        Classify entities into domain-specific types.

        For cybersecurity audit domain:
        - process: Business processes, workflows
        - risk: Risks, threats, vulnerabilities
        - control: Security controls, safeguards
        - regulation: Regulations, standards (NIST, ISO, SOC2, COBIT)
        - policy: Policies, procedures, guidelines

        Args:
            entities: Raw extracted entities

        Returns:
            Entities with classified types
        """
        # TODO: Implement entity classification
        # Suggested approaches:
        # 1. Rule-based: Match against domain lexicons
        # 2. Pattern-based: Regex patterns for each type
        # 3. Context-based: Use surrounding words
        pass

    def _map_relationships(
        self,
        blocks: tuple[ContentBlock, ...],
        entities: List[Entity]
    ) -> List[Relationship]:
        """
        Map relationships between entities.

        Example relationships in cybersecurity audit domain:
        - "Access Control Policy" implements "NIST SP 800-53 AC-2"
        - "Encryption Control" mitigates "Data Breach Risk"
        - "SOC2 Compliance" requires "Access Review Process"

        Args:
            blocks: All content blocks
            entities: Classified entities

        Returns:
            List of Relationship objects
        """
        # TODO: Implement relationship mapping
        # Suggested approaches:
        # 1. Co-occurrence: Entities in same block/section
        # 2. Pattern-based: "X implements Y", "X mitigates Y"
        # 3. Dependency parsing: Use NLP dependency trees
        pass

    def _generate_semantic_tags(
        self,
        content: str,
        entities: List[Entity],
        document_path: List[str]
    ) -> List[str]:
        """
        Generate semantic tags for content.

        Tags examples:
        - GRC domains: "access_control", "risk_management", "compliance"
        - Document sections: "overview", "requirements", "implementation"
        - Content types: "definition", "procedure", "checklist"

        Args:
            content: Block content
            entities: Entities in this block
            document_path: Hierarchical path (from ContextLinker)

        Returns:
            List of semantic tags
        """
        # TODO: Implement semantic tagging
        pass

    def _compute_quality_indicators(
        self,
        block: ContentBlock,
        entities: List[Entity],
        semantic_tags: List[str]
    ) -> Dict[str, float]:
        """
        Compute quality indicators for RAG optimization.

        Indicators:
        - semantic_clarity: How clear/well-defined is the content?
        - entity_density: Entities per 100 words
        - domain_relevance: How relevant to cybersecurity audit domain?
        - context_richness: How much hierarchical context?

        Args:
            block: Content block
            entities: Entities in block
            semantic_tags: Semantic tags

        Returns:
            Dictionary of quality indicators (0.0-1.0)
        """
        word_count = block.metadata.get("word_count", 1)
        depth = block.metadata.get("depth", 0)

        return {
            "entity_density": len(entities) / max(1, word_count / 100),
            "domain_relevance": len(semantic_tags) / max(1, len(semantic_tags)),
            "context_richness": min(1.0, depth / 5.0),  # Normalize depth 0-5
            "semantic_clarity": self._compute_clarity(block.content),
        }

    def _compute_clarity(self, text: str) -> float:
        """
        Compute semantic clarity score (0.0-1.0).

        Factors:
        - Sentence structure (well-formed sentences)
        - Vocabulary (domain-specific terms)
        - Readability (not too complex)

        Args:
            text: Text content

        Returns:
            Clarity score (0.0-1.0)
        """
        # TODO: Implement clarity scoring
        # Suggested approaches:
        # 1. Readability metrics (Flesch-Kincaid, etc.)
        # 2. Sentence structure analysis
        # 3. Domain vocabulary coverage
        return 0.8  # Placeholder
```

### Configuration Example

```yaml
# config.yaml
processors:
  semantic_analyzer:
    enabled: true

    # Entity extraction
    entity_extraction: true
    confidence_threshold: 0.7
    enable_normalization: true

    # Domain model
    domain_model: "cybersecurity_audit"
    grc_entities:
      - processes
      - risks
      - controls
      - regulations
      - policies

    # Relationship mapping (expensive, optional)
    relationship_mapping: false

    # NLP library choice
    nlp_library: "spacy"  # "spacy", "nltk", "regex"
    spacy_model: "en_core_web_sm"

    # Domain lexicons (paths to custom lexicons)
    lexicon_paths:
      regulations: "config/lexicons/regulations.txt"
      controls: "config/lexicons/controls.txt"
```

---

## Formatter Chain Analysis

### Current Formatter Implementations

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

### Formatter Interface

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

## RAG-Optimized Formatter Design

### Recommended Implementation

```python
# src/formatters/rag_optimized_formatter.py
from typing import List, Dict, Optional
import json
from dataclasses import asdict

from core import BaseFormatter, ProcessingResult, FormattedOutput
from infrastructure import get_logger


class RagOptimizedFormatter(BaseFormatter):
    """
    Format content for RAG pipeline optimization.

    Output Features:
    - Semantic chunking with context preservation
    - Metadata enrichment for retrieval
    - Schema standardization for vector DBs
    - Quality indicators per chunk
    - Embedding preparation

    Configuration:
        chunk_size (int): Target chunk size in tokens (default: 512)
        chunk_overlap (int): Overlap between chunks in tokens (default: 50)
        include_context (bool): Include parent headings (default: True)
        include_entities (bool): Include extracted entities (default: True)
        schema_version (str): Output schema version (default: "1.0")
    """

    def __init__(self, config: Optional[dict] = None):
        """Initialize formatter with configuration."""
        super().__init__(config)

        self.chunk_size = self.config.get("chunk_size", 512)
        self.chunk_overlap = self.config.get("chunk_overlap", 50)
        self.include_context = self.config.get("include_context", True)
        self.include_entities = self.config.get("include_entities", True)
        self.schema_version = self.config.get("schema_version", "1.0")

        self.logger = get_logger(__name__)

    def format(self, processing_result: ProcessingResult) -> FormattedOutput:
        """
        Generate RAG-optimized output.

        Output Schema:
        {
            "schema_version": "1.0",
            "chunks": [
                {
                    "chunk_id": "doc123_chunk_001",
                    "content": "chunk text with semantic boundaries respected",
                    "context": {
                        "document_path": ["Chapter 1", "Section 1.1"],
                        "parent_heading": "Section 1.1: Access Controls",
                        "depth": 2,
                        "source_file": "document.docx",
                        "page_number": 5
                    },
                    "metadata": {
                        "word_count": 150,
                        "entities": {
                            "regulations": ["NIST SP 800-53"],
                            "controls": ["Access Control"],
                            "policies": []
                        },
                        "semantic_tags": ["regulation", "control", "access_management"],
                        "domain_classification": "cybersecurity_audit"
                    },
                    "quality_indicators": {
                        "semantic_clarity": 0.85,
                        "entity_density": 0.12,
                        "domain_relevance": 0.92,
                        "context_richness": 0.75,
                        "overall_quality": 85.2
                    },
                    "embedding_ready": true
                },
                ...
            ],
            "document_metadata": {...},
            "chunk_statistics": {
                "total_chunks": 42,
                "average_chunk_size": 487,
                "chunks_with_entities": 38,
                "overall_quality_score": 85.2
            }
        }

        Args:
            processing_result: Processing result with semantic enrichments

        Returns:
            FormattedOutput with RAG-optimized JSON
        """
        try:
            # Create semantic chunks
            chunks = self._create_semantic_chunks(processing_result)

            # Build output structure
            output_data = {
                "schema_version": self.schema_version,
                "chunks": chunks,
                "document_metadata": self._serialize_document_metadata(
                    processing_result.document_metadata
                ),
                "chunk_statistics": self._compute_chunk_statistics(chunks),
            }

            # Serialize to JSON
            content = json.dumps(output_data, indent=2, ensure_ascii=False)

            return FormattedOutput(
                content=content,
                format_type=self.get_format_type(),
                source_document=processing_result.document_metadata.source_file,
                success=True,
            )

        except Exception as e:
            self.logger.exception("RAG formatting failed", exc_info=e)
            return FormattedOutput(
                content="{}",
                format_type=self.get_format_type(),
                source_document=processing_result.document_metadata.source_file,
                success=False,
                errors=(f"RAG formatting failed: {str(e)}",),
            )

    def get_format_type(self) -> str:
        """Return format type identifier."""
        return "rag_optimized"

    def _create_semantic_chunks(
        self,
        processing_result: ProcessingResult
    ) -> List[Dict]:
        """
        Create semantically meaningful chunks.

        Strategy:
        - Respect document hierarchy (don't split mid-section)
        - Preserve semantic boundaries (paragraphs, lists)
        - Target chunk size with overlap
        - Include hierarchical context
        - Preserve entity associations

        Args:
            processing_result: Processing result with enriched blocks

        Returns:
            List of chunk dictionaries
        """
        chunks = []
        chunk_id = 0

        # TODO: Implement semantic chunking algorithm
        # Suggested approach:
        # 1. Group blocks by section (using parent_id, depth)
        # 2. Create chunks respecting semantic boundaries
        # 3. Add overlap between chunks
        # 4. Include context (document_path, parent heading)
        # 5. Attach entities from original blocks
        # 6. Compute quality indicators per chunk

        for block in processing_result.content_blocks:
            chunk = {
                "chunk_id": f"chunk_{chunk_id:03d}",
                "content": block.content,
                "context": {
                    "document_path": block.metadata.get("document_path", []),
                    "depth": block.metadata.get("depth", 0),
                    "source_file": str(processing_result.document_metadata.source_file),
                    "page_number": block.position.page if block.position else None,
                },
                "metadata": {
                    "word_count": block.metadata.get("word_count", 0),
                    "entities": block.metadata.get("entities", []),
                    "entity_types": block.metadata.get("entity_types", {}),
                    "semantic_tags": block.metadata.get("semantic_tags", []),
                    "domain_classification": block.metadata.get("domain_classification", ""),
                },
                "quality_indicators": block.metadata.get("semantic_quality_indicators", {}),
                "embedding_ready": True,
            }

            chunks.append(chunk)
            chunk_id += 1

        return chunks

    def _compute_chunk_statistics(self, chunks: List[Dict]) -> Dict:
        """Compute aggregate statistics across all chunks."""
        total_chunks = len(chunks)
        chunks_with_entities = sum(1 for c in chunks if c["metadata"]["entities"])

        return {
            "total_chunks": total_chunks,
            "chunks_with_entities": chunks_with_entities,
            "entity_coverage": chunks_with_entities / max(1, total_chunks),
        }
```

---

## Summary: Integration Checklist

✅ **Understanding Current Architecture**:
- [ ] Read all 3 processor implementations (ContextLinker, MetadataAggregator, QualityValidator)
- [ ] Understand dependency resolution mechanism (topological sort)
- [ ] Review data enrichment patterns (metadata preservation, immutability, media assets)

✅ **Designing Semantic Processor**:
- [ ] Define entity types for cybersecurity audit domain
- [ ] Choose NLP library (spaCy, NLTK, regex-based)
- [ ] Design entity extraction algorithm
- [ ] Design entity classification logic
- [ ] Plan relationship mapping (optional)
- [ ] Define quality indicators for RAG

✅ **Implementing**:
- [ ] Create `src/processors/semantic_analyzer.py`
- [ ] Implement `BaseProcessor` interface
- [ ] Add configuration schema
- [ ] Implement batch entity extraction
- [ ] Test on real audit documents

✅ **RAG Optimization (Optional)**:
- [ ] Create `src/formatters/rag_optimized_formatter.py`
- [ ] Implement semantic chunking
- [ ] Design output schema
- [ ] Test with RAG pipeline

---

**Document Status**: ✅ Complete | **Generated**: 2025-11-07 | **Priority**: 2 (User-requested)
