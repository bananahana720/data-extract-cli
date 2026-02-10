# Processor Chain Overview

## What is a Processor?

A **processor** is a modular component that enriches content blocks with additional metadata without modifying the original content. Think of processors as stages in an enrichment pipeline:

```
Raw Content → Context → Statistics → Quality → Semantics → Output
              ├─────┴─────┴──────┴──────────┘
              Processor Chain (ordered by dependencies)
```

## Key Characteristics

1. **Immutable Operations**: Create new ContentBlocks, never modify existing ones
2. **Dependency-Ordered**: Automatically sorted based on `get_dependencies()`
3. **Composable**: Each processor builds on previous processors' enrichments
4. **Optional/Required**: Can be marked as optional (pipeline continues on failure)
5. **Metadata Enrichment**: Add fields to `metadata` dict without removing existing fields

## Current Processor Chain (v1.0.6)

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
