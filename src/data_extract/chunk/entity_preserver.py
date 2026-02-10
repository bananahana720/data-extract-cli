"""Entity-aware boundary detection for semantic chunking.

This module implements entity preservation logic to avoid splitting entity
definitions across chunk boundaries in RAG workflows. Analyzes entity positions,
identifies safe split zones, and detects entity relationships.

Type Contract: List[Entity] + Text → EntityReferences + Gaps + Relationships

Compliance:
    - AC-3.2-1: Entity mentions kept within single chunks (>95% intact)
    - AC-3.2-3: Relationship context preserved (entity pairs in same chunk)
    - AC-3.2-4: Chunk boundaries avoid splitting entity definitions
    - AC-3.2-5: Cross-references maintained with entity IDs
    - AC-3.2-6: Entity tags in chunk metadata
    - AC-3.2-8: Deterministic entity analysis (sorted by start_pos)
"""

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

from ..core.models import Entity


@dataclass(frozen=True)
class EntityReference:
    """Immutable reference to entity mention within chunk.

    Tracks entity position, type, and context for chunk metadata enrichment.
    Supports JSON serialization for output formats.

    Attributes:
        entity_type: Entity type as string (e.g., "RISK", "CONTROL", "POLICY")
        entity_id: Canonical entity identifier (e.g., "RISK-2024-001")
        start_pos: Character offset where entity starts in text
        end_pos: Character offset where entity ends in text
        is_partial: True if entity split across chunk boundary
        context_snippet: ±20 chars around entity for context

    Example:
        >>> ref = EntityReference(
        ...     entity_type="RISK",
        ...     entity_id="RISK-001",
        ...     start_pos=100,
        ...     end_pos=120,
        ...     is_partial=False,
        ...     context_snippet="...Data breach risk..."
        ... )
        >>> ref.to_dict()
        {'entity_type': 'RISK', 'entity_id': 'RISK-001', ...}
    """

    entity_type: str
    entity_id: str
    start_pos: int
    end_pos: int
    is_partial: bool = False
    context_snippet: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dictionary.

        Returns:
            Dict with all EntityReference fields
        """
        return {
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "start_pos": self.start_pos,
            "end_pos": self.end_pos,
            "is_partial": self.is_partial,
            "context_snippet": self.context_snippet,
        }


class EntityPreserver:
    """Analyzes entity boundaries to preserve complete entity definitions in chunks.

    Implements entity-aware chunking logic:
    1. analyze_entities(): Build EntityReference map from Epic 2 entities
    2. find_entity_gaps(): Identify safe split zones between entities
    3. detect_entity_relationships(): Find relationship patterns (e.g., "mitigated by")

    Design:
        - Deterministic processing (entities sorted by start_pos)
        - Streaming-compatible (no buffering entire document)
        - Graceful degradation (handles overlapping entities, missing data)

    Example:
        >>> preserver = EntityPreserver()
        >>> entities = [Entity(type="RISK", id="RISK-001", ...)]
        >>> entity_refs = preserver.analyze_entities(text, entities)
        >>> gaps = preserver.find_entity_gaps(entity_refs, text)
        >>> relationships = preserver.detect_entity_relationships(text, entity_refs)
    """

    # Relationship patterns for detection (AC-3.2-3)
    # Pattern: word boundaries + entity ID pattern (allows hyphens)
    # Updated to allow descriptive text between entity ID and relationship keyword
    RELATIONSHIP_PATTERNS = [
        (r"\b([A-Z]+-\d+)\b.*?\b(?:is\s+)?mitigated\s+by\b.*?\b([A-Z]+-\d+)\b", "mitigated_by"),
        (r"\b([A-Z]+-\d+)\b.*?\bmaps\s+to\b.*?\b([A-Z]+-\d+)\b", "maps_to"),
        (r"\b([A-Z]+-\d+)\b.*?\bimplements\b.*?\b([A-Z]+-\d+)\b", "implements"),
        (r"\b([A-Z]+-\d+)\b.*?\baddresses\b.*?\b([A-Z]+-\d+)\b", "addresses"),
        (r"\b([A-Z]+-\d+)\b.*?\bcontrolled\s+by\b.*?\b([A-Z]+-\d+)\b", "controlled_by"),
        (r"\b([A-Z]+-\d+)\b.*?\brelates\s+to\b.*?\b([A-Z]+-\d+)\b", "relates_to"),
    ]

    def __init__(self) -> None:
        """Initialize EntityPreserver."""
        pass

    def analyze_entities(self, text: str, entities: List[Entity]) -> List[EntityReference]:
        """Analyze entity boundaries and build EntityReference map.

        Extracts entity positions, types, and context snippets for chunk metadata.
        Sorts entities by start position for deterministic processing (AC-3.2-8).

        Args:
            text: Full document text
            entities: Entity list from Epic 2 ProcessingResult

        Returns:
            List of EntityReference objects sorted by start_pos

        Example:
            >>> entities = [
            ...     Entity(type=EntityType.RISK, id="RISK-001", text="Data breach",
            ...            confidence=0.95, location={"start": 100, "end": 120})
            ... ]
            >>> entity_refs = preserver.analyze_entities(text, entities)
            >>> len(entity_refs)
            1
        """
        if not entities:
            return []

        entity_refs = []

        for entity in entities:
            # Extract position from location dict
            start_pos = entity.location.get("start", 0)
            end_pos = entity.location.get("end", 0)

            # Extract context snippet (±20 chars around entity)
            context_start = max(0, start_pos - 20)
            context_end = min(len(text), end_pos + 20)
            context_snippet = text[context_start:context_end]

            # Add ellipsis if truncated
            if context_start > 0:
                context_snippet = "..." + context_snippet
            if context_end < len(text):
                context_snippet = context_snippet + "..."

            # Create EntityReference
            entity_ref = EntityReference(
                entity_type=(
                    str(entity.type.value) if hasattr(entity.type, "value") else str(entity.type)
                ),
                entity_id=entity.id,
                start_pos=start_pos,
                end_pos=end_pos,
                is_partial=False,  # Will be set during chunking
                context_snippet=context_snippet,
            )
            entity_refs.append(entity_ref)

        # Sort by start_pos for determinism (AC-3.2-8)
        entity_refs.sort(key=lambda ref: ref.start_pos)

        return entity_refs

    def find_entity_gaps(self, entities: List[EntityReference], text: str) -> List[int]:
        """Identify character positions between entities (safe split zones).

        Analyzes entity positions to find gaps where chunk boundaries can be placed
        without splitting entity definitions. Returns character offsets in text.

        **Integration**: Called by ChunkingEngine._generate_chunks() during entity-aware
        boundary adjustment (line 677). When a chunk reaches target size, the engine
        searches for the nearest entity gap within ±20% of chunk_size to adjust the
        boundary, preventing entity splits (AC-3.2-1, AC-3.2-4).

        Args:
            entities: Sorted list of EntityReference objects
            text: Full document text

        Returns:
            List of character offsets suitable for chunk boundaries

        Example:
            >>> # Entity 1 at 100-120, Entity 2 at 200-220
            >>> gaps = preserver.find_entity_gaps(entity_refs, text)
            >>> # Returns positions between 120 and 200
        """
        if not entities:
            return []

        gaps = []

        # Add gap positions between entities
        for i in range(len(entities) - 1):
            current_entity = entities[i]
            next_entity = entities[i + 1]

            # Gap exists if there's space between current end and next start
            gap_start = current_entity.end_pos
            gap_end = next_entity.start_pos

            if gap_end > gap_start:
                # Add midpoint of gap as potential split position
                gap_midpoint = (gap_start + gap_end) // 2
                gaps.append(gap_midpoint)

        return gaps

    def detect_entity_relationships(
        self, text: str, entities: List[EntityReference]
    ) -> List[Tuple[str, str, str]]:
        """Detect entity relationship patterns in text.

        Searches for relationship keywords connecting entity pairs
        (e.g., "RISK-001 mitigated by CTRL-042"). Returns relationship triples.

        Args:
            text: Full document text
            entities: List of EntityReference objects

        Returns:
            List of (entity1_id, relation_type, entity2_id) triples

        Example:
            >>> # Text: "RISK-001 mitigated by CTRL-042"
            >>> relationships = preserver.detect_entity_relationships(text, entity_refs)
            >>> relationships[0]
            ('RISK-001', 'mitigated_by', 'CTRL-042')
        """
        relationships = []

        # Build entity ID map for lookup
        entity_ids = {entity.entity_id for entity in entities}

        # Search for relationship patterns
        for pattern, relation_type in self.RELATIONSHIP_PATTERNS:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                entity1 = match.group(1)
                entity2 = match.group(2)

                # Verify both entities exist in our entity list
                if entity1 in entity_ids and entity2 in entity_ids:
                    relationships.append((entity1, relation_type, entity2))

        return relationships
