# Dependency Resolution Mechanism

## Topological Sort Algorithm

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

## Example Dependency Resolution

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
