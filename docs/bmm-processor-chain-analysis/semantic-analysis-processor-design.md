# Semantic Analysis Processor Design

## Recommended Architecture

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

## Configuration Example

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
