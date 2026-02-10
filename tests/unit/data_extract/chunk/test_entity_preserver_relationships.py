"""Unit tests for EntityPreserver relationship detection (Story 3.2).

Tests entity relationship extraction from text patterns.

Test Coverage:
    - AC-3.2-3: Entity relationship detection
    - AC-3.2-5: Entity ID cross-references

Part 3 of 3: Entity relationship detection.
"""

import pytest

# These imports WILL FAIL in RED phase - this is expected
try:
    from data_extract.chunk.entity_preserver import EntityPreserver, EntityReference
except ImportError:
    EntityPreserver = None
    EntityReference = None

pytestmark = [pytest.mark.P2, pytest.mark.unit, pytest.mark.chunking, pytest.mark.entity_aware]


class TestEntityPreserverRelationships:
    """Test EntityPreserver.detect_entity_relationships() method (AC-3.2-3)."""

    def test_detect_entity_relationships_mitigated_by(self):
        """Should detect 'mitigated by' relationship pattern (AC-3.2-3)."""
        # GIVEN: Text with "RISK-001 mitigated by CTRL-042" pattern
        text = "RISK-001 is mitigated by CTRL-042 encryption control."
        entity_refs = [
            EntityReference(
                entity_type="RISK",
                entity_id="RISK-001",
                start_pos=0,
                end_pos=8,
                is_partial=False,
                context_snippet="RISK-001 is mitigated",
            ),
            EntityReference(
                entity_type="CONTROL",
                entity_id="CTRL-042",
                start_pos=25,
                end_pos=33,
                is_partial=False,
                context_snippet="by CTRL-042 encryption",
            ),
        ]

        # WHEN: detect_entity_relationships() called
        preserver = EntityPreserver()
        relationships = preserver.detect_entity_relationships(text, entity_refs)

        # THEN: Returns triple ("RISK-001", "mitigated_by", "CTRL-042")
        assert len(relationships) >= 1
        assert isinstance(relationships, list)
        # Find the mitigated_by relationship
        mitigated_rel = [r for r in relationships if r[1] == "mitigated_by"]
        assert len(mitigated_rel) >= 1
        assert mitigated_rel[0] == ("RISK-001", "mitigated_by", "CTRL-042")

    def test_detect_entity_relationships_multiple_patterns(self):
        """Should detect various relationship keywords (AC-3.2-3)."""
        # GIVEN: Text with "maps to", "implements", "addresses" patterns
        text = (
            "CTRL-001 maps to REQ-001. "
            "PROC-002 implements CTRL-001. "
            "POLICY-003 addresses RISK-005."
        )
        entity_refs = [
            EntityReference(
                entity_type="CONTROL",
                entity_id="CTRL-001",
                start_pos=0,
                end_pos=8,
                is_partial=False,
                context_snippet="CTRL-001 maps",
            ),
            EntityReference(
                entity_type="REQUIREMENT",
                entity_id="REQ-001",
                start_pos=17,
                end_pos=24,
                is_partial=False,
                context_snippet="to REQ-001",
            ),
            EntityReference(
                entity_type="PROCESS",
                entity_id="PROC-002",
                start_pos=26,
                end_pos=34,
                is_partial=False,
                context_snippet="PROC-002 implements",
            ),
            EntityReference(
                entity_type="POLICY",
                entity_id="POLICY-003",
                start_pos=57,
                end_pos=67,
                is_partial=False,
                context_snippet="POLICY-003 addresses",
            ),
            EntityReference(
                entity_type="RISK",
                entity_id="RISK-005",
                start_pos=78,
                end_pos=86,
                is_partial=False,
                context_snippet="addresses RISK-005",
            ),
        ]

        # WHEN: detect_entity_relationships() called
        preserver = EntityPreserver()
        relationships = preserver.detect_entity_relationships(text, entity_refs)

        # THEN: Returns triples for all detected relationships
        assert len(relationships) >= 3
        # Should find maps_to, implements, addresses relationships
        relationship_types = [r[1] for r in relationships]
        assert "maps_to" in relationship_types or "maps to" in relationship_types
        assert "implements" in relationship_types
        assert "addresses" in relationship_types

    def test_detect_entity_relationships_no_relationships(self):
        """Should return empty list when no relationships detected."""
        # GIVEN: Text with entities but no relationship keywords
        text = "RISK-001 exists. CTRL-002 exists separately."
        entity_refs = [
            EntityReference(
                entity_type="RISK",
                entity_id="RISK-001",
                start_pos=0,
                end_pos=8,
                is_partial=False,
                context_snippet="RISK-001 exists",
            ),
            EntityReference(
                entity_type="CONTROL",
                entity_id="CTRL-002",
                start_pos=17,
                end_pos=25,
                is_partial=False,
                context_snippet="CTRL-002 exists",
            ),
        ]

        # WHEN: detect_entity_relationships() called
        preserver = EntityPreserver()
        relationships = preserver.detect_entity_relationships(text, entity_refs)

        # THEN: Returns empty list
        assert relationships == []


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
