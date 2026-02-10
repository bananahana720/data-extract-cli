"""Unit tests for EntityPreserver gap finding functionality (Story 3.2).

Tests entity gap detection for safe chunk boundary placement.

Test Coverage:
    - AC-3.2-1: Entity preservation within chunks
    - AC-3.2-4: Entity definition boundary detection

Part 2 of 3: Entity gap detection.
"""

import pytest

# These imports WILL FAIL in RED phase - this is expected
try:
    from data_extract.chunk.entity_preserver import EntityPreserver, EntityReference
except ImportError:
    EntityPreserver = None
    EntityReference = None

pytestmark = [pytest.mark.P2, pytest.mark.unit, pytest.mark.chunking, pytest.mark.entity_aware]


class TestEntityPreserverGaps:
    """Test EntityPreserver.find_entity_gaps() method (AC-3.2-1)."""

    def test_find_entity_gaps(self):
        """Should identify character offsets between entities (AC-3.2-1)."""
        # GIVEN: Text with multiple entities
        text = "RISK-001 description. CTRL-002 mitigates. POLICY-003 governs."
        entity_refs = [
            EntityReference(
                entity_type="RISK",
                entity_id="RISK-001",
                start_pos=0,
                end_pos=8,
                is_partial=False,
                context_snippet="RISK-001 description",
            ),
            EntityReference(
                entity_type="CONTROL",
                entity_id="CTRL-002",
                start_pos=22,
                end_pos=30,
                is_partial=False,
                context_snippet="CTRL-002 mitigates",
            ),
            EntityReference(
                entity_type="POLICY",
                entity_id="POLICY-003",
                start_pos=43,
                end_pos=53,
                is_partial=False,
                context_snippet="POLICY-003 governs",
            ),
        ]

        # WHEN: find_entity_gaps() called
        preserver = EntityPreserver()
        gaps = preserver.find_entity_gaps(entity_refs, text)

        # THEN: Returns character offsets between entities (safe split zones)
        assert isinstance(gaps, list)
        assert len(gaps) >= 2  # At least gaps between the 3 entities
        # Gaps should be in positions between entities
        for gap in gaps:
            # Gap should not be within any entity span
            for ref in entity_refs:
                assert not (ref.start_pos <= gap <= ref.end_pos)

    def test_find_entity_gaps_no_entities(self):
        """Should return empty list when no entities (AC-3.2-1 edge case)."""
        # GIVEN: Text with no entities
        text = "Plain text with no entity markers."
        entity_refs = []

        # WHEN: find_entity_gaps() called
        preserver = EntityPreserver()
        gaps = preserver.find_entity_gaps(entity_refs, text)

        # THEN: Returns empty list (no gaps to find)
        assert gaps == []

    def test_overlapping_entities_handling(self):
        """Should handle overlapping entity spans gracefully (AC-3.2-1 edge case)."""
        # GIVEN: Entities with overlapping start/end positions
        text = "RISK-CTRL-001 combined entity reference"
        entity_refs = [
            EntityReference(
                entity_type="RISK",
                entity_id="RISK-001",
                start_pos=0,
                end_pos=9,
                is_partial=False,
                context_snippet="RISK-CTRL-001",
            ),
            EntityReference(
                entity_type="CONTROL",
                entity_id="CTRL-001",
                start_pos=5,
                end_pos=13,
                is_partial=False,
                context_snippet="CTRL-001 combined",
            ),
        ]

        # WHEN: find_entity_gaps() called
        preserver = EntityPreserver()
        gaps = preserver.find_entity_gaps(entity_refs, text)

        # THEN: Handles gracefully (prefer earlier entity or flag both)
        # Should not crash, returns valid gap list (may be empty for overlaps)
        assert isinstance(gaps, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
