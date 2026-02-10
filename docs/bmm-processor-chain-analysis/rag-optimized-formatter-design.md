# RAG-Optimized Formatter Design

## Recommended Implementation

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
