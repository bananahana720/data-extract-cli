# Current Processor Implementations

## 1. ContextLinker (REQUIRED)

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

## 2. MetadataAggregator (OPTIONAL)

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

## 3. QualityValidator (OPTIONAL)

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
