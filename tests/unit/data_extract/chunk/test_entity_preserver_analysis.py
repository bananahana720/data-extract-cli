"""Unit tests for EntityPreserver analysis functionality (Story 3.2).

Tests entity-aware boundary detection, entity reference management,
and deterministic entity analysis.

Test Coverage:
    - AC-3.2-1: Entity preservation within chunks
    - AC-3.2-6: Entity metadata tags
    - AC-3.2-8: Deterministic entity analysis

Part 1 of 3: Entity reference model and analysis.
"""

import json

import pytest

# These imports WILL FAIL in RED phase - this is expected
try:
    from data_extract.chunk.entity_preserver import EntityPreserver, EntityReference
    from data_extract.core.models import Entity, EntityType
except ImportError:
    EntityPreserver = None
    EntityReference = None
    Entity = None
    EntityType = None

pytestmark = [pytest.mark.P1, pytest.mark.unit, pytest.mark.chunking, pytest.mark.entity_aware]


class TestEntityReferenceModel:
    """Test EntityReference dataclass creation and serialization (AC-3.2-6)."""

    def test_entity_reference_creation(self):
        """Should create EntityReference with all required fields."""
        # GIVEN: Entity data
        entity_type = "RISK"
        entity_id = "RISK-2024-001"
        start_pos = 100
        end_pos = 150
        is_partial = False
        context_snippet = "...Data breach risk involving..."

        # WHEN: EntityReference instantiated
        entity_ref = EntityReference(
            entity_type=entity_type,
            entity_id=entity_id,
            start_pos=start_pos,
            end_pos=end_pos,
            is_partial=is_partial,
            context_snippet=context_snippet,
        )

        # THEN: All fields populated correctly
        assert entity_ref.entity_type == entity_type
        assert entity_ref.entity_id == entity_id
        assert entity_ref.start_pos == start_pos
        assert entity_ref.end_pos == end_pos
        assert entity_ref.is_partial == is_partial
        assert entity_ref.context_snippet == context_snippet

    def test_entity_reference_frozen(self):
        """Should enforce immutability with frozen=True."""
        # GIVEN: EntityReference
        entity_ref = EntityReference(
            entity_type="CONTROL",
            entity_id="CTRL-001",
            start_pos=200,
            end_pos=220,
            is_partial=False,
            context_snippet="...Encryption control...",
        )

        # WHEN/THEN: Attempting to modify raises error
        with pytest.raises(AttributeError):
            entity_ref.entity_id = "CTRL-002"

    def test_entity_reference_to_dict(self):
        """Should serialize to JSON-compatible dict (AC-3.2-6)."""
        # GIVEN: EntityReference with all fields
        entity_ref = EntityReference(
            entity_type="POLICY",
            entity_id="POL-001",
            start_pos=500,
            end_pos=550,
            is_partial=True,
            context_snippet="...Data protection policy...",
        )

        # WHEN: to_dict() called
        result = entity_ref.to_dict()

        # THEN: Returns dict with all fields
        assert isinstance(result, dict)
        assert result["entity_type"] == "POLICY"
        assert result["entity_id"] == "POL-001"
        assert result["start_pos"] == 500
        assert result["end_pos"] == 550
        assert result["is_partial"] is True
        assert result["context_snippet"] == "...Data protection policy..."

        # AND: Dict is JSON serializable
        json_str = json.dumps(result)
        assert json_str is not None


class TestEntityPreserverAnalysis:
    """Test EntityPreserver.analyze_entities() method (AC-3.2-1, AC-3.2-6, AC-3.2-8)."""

    def test_analyze_entities_sorting(self):
        """Should sort entities by start_pos for determinism (AC-3.2-8)."""
        # GIVEN: Entities in random order
        text = "Risk RISK-003 affects system. Control CTRL-001 mitigates. Risk RISK-001 identified."
        entities = [
            Entity(
                type=EntityType.RISK,
                id="RISK-003",
                text="RISK-003",
                confidence=0.95,
                location={"start": 5, "end": 14},
            ),
            Entity(
                type=EntityType.CONTROL,
                id="CTRL-001",
                text="CTRL-001",
                confidence=0.92,
                location={"start": 37, "end": 45},
            ),
            Entity(
                type=EntityType.RISK,
                id="RISK-001",
                text="RISK-001",
                confidence=0.93,
                location={"start": 63, "end": 71},
            ),
        ]

        # WHEN: analyze_entities() called
        preserver = EntityPreserver()
        entity_refs = preserver.analyze_entities(text, entities)

        # THEN: Returns EntityReferences sorted by start_pos
        assert len(entity_refs) == 3
        assert entity_refs[0].start_pos == 5  # RISK-003
        assert entity_refs[1].start_pos == 37  # CTRL-001
        assert entity_refs[2].start_pos == 63  # RISK-001
        assert entity_refs[0].entity_id == "RISK-003"
        assert entity_refs[1].entity_id == "CTRL-001"
        assert entity_refs[2].entity_id == "RISK-001"

    def test_analyze_entities_context_snippets(self):
        """Should extract context snippets around entities (AC-3.2-6)."""
        # GIVEN: Entity at various positions in text
        text = "The RISK-2024-001 data breach risk requires immediate attention and mitigation."
        entities = [
            Entity(
                type=EntityType.RISK,
                id="RISK-2024-001",
                text="RISK-2024-001",
                confidence=0.95,
                location={"start": 4, "end": 17},
            )
        ]

        # WHEN: analyze_entities() called
        preserver = EntityPreserver()
        entity_refs = preserver.analyze_entities(text, entities)

        # THEN: context_snippet contains ±20 chars around entity
        snippet = entity_refs[0].context_snippet
        assert "RISK-2024-001" in snippet
        # Should include some surrounding text
        assert len(snippet) > len("RISK-2024-001")

    def test_analyze_entities_empty_list(self):
        """Should handle empty entity list gracefully (AC-3.2-1)."""
        # GIVEN: Text with no entities
        text = "This is plain text with no entity markers."
        entities = []

        # WHEN: analyze_entities() called
        preserver = EntityPreserver()
        entity_refs = preserver.analyze_entities(text, entities)

        # THEN: Returns empty list
        assert entity_refs == []

    def test_entities_at_document_boundaries(self):
        """Should handle entities at start/end of document (AC-3.2-1 edge case)."""
        # GIVEN: Entity at position 0 and end of text
        text = "RISK-001 is critical. CTRL-999"
        entities = [
            Entity(
                type=EntityType.RISK,
                id="RISK-001",
                text="RISK-001",
                confidence=0.95,
                location={"start": 0, "end": 8},
            ),
            Entity(
                type=EntityType.CONTROL,
                id="CTRL-999",
                text="CTRL-999",
                confidence=0.92,
                location={"start": 22, "end": 30},
            ),
        ]

        # WHEN: analyze_entities() called
        preserver = EntityPreserver()
        entity_refs = preserver.analyze_entities(text, entities)

        # THEN: Context snippets truncated appropriately (no negative indices)
        assert len(entity_refs) == 2
        # First entity context should not cause negative index
        assert entity_refs[0].context_snippet is not None
        # Last entity context should not exceed text length
        assert entity_refs[1].context_snippet is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
