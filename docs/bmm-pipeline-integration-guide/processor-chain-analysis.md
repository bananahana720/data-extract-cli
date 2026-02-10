# Processor Chain Analysis

## Current Processor Execution Order

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

## Dependency Graph

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

## Adding SemanticAnalyzer to the Chain

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
