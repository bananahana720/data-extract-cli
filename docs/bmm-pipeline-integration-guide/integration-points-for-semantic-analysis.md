# Integration Points for Semantic Analysis

## Option 1: Semantic Analysis Processor (RECOMMENDED)

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

## Option 2: RAG-Optimized Formatter

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
