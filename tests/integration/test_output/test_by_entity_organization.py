"""Integration tests for BY_ENTITY organization strategy (Story 3.7).

Tests the complete BY_ENTITY organization workflow including folder creation,
entity-based routing, and manifest generation with real file system operations.

Test Coverage:
    - Entity-based folder creation (risks/, controls/, policies/)
    - Multi-entity type routing
    - Unclassified folder for chunks without entities
    - Manifest entity summary validation
"""

import json
from pathlib import Path

import pytest

pytestmark = [pytest.mark.P1, pytest.mark.integration, pytest.mark.output]

from data_extract.chunk.entity_preserver import EntityReference  # noqa: E402
from data_extract.chunk.models import Chunk, ChunkMetadata  # noqa: E402
from data_extract.output.organization import OrganizationStrategy, Organizer  # noqa: E402

pytestmark = [pytest.mark.integration, pytest.mark.output, pytest.mark.organization]


class TestByEntityOrganization:
    """Integration tests for BY_ENTITY organization strategy."""

    @pytest.fixture
    def chunks_with_multiple_entity_types(self) -> list:
        """Create chunks with multiple entity types for comprehensive testing."""
        chunks = []

        # Risk entity chunk
        risk_entity = EntityReference(
            entity_type="risk",
            entity_id="RISK-001",
            start_pos=0,
            end_pos=20,
            is_partial=False,
            context_snippet="risk context",
        )
        risk_metadata = ChunkMetadata(
            source_file=Path("audit_report.pdf"),
            entity_tags=[risk_entity],
            section_context="Risk Section",
        )
        chunks.append(
            Chunk(
                id="chunk_001",
                text="Risk content about RISK-001",
                document_id="doc_001",
                position_index=0,
                token_count=50,
                word_count=40,
                entities=[],
                section_context="Risk Section",
                quality_score=0.9,
                readability_scores={},
                metadata=risk_metadata,
            )
        )

        # Control entity chunk
        control_entity = EntityReference(
            entity_type="control",
            entity_id="CTRL-001",
            start_pos=0,
            end_pos=20,
            is_partial=False,
            context_snippet="control context",
        )
        control_metadata = ChunkMetadata(
            source_file=Path("audit_report.pdf"),
            entity_tags=[control_entity],
            section_context="Control Section",
        )
        chunks.append(
            Chunk(
                id="chunk_002",
                text="Control content about CTRL-001",
                document_id="doc_001",
                position_index=1,
                token_count=50,
                word_count=40,
                entities=[],
                section_context="Control Section",
                quality_score=0.9,
                readability_scores={},
                metadata=control_metadata,
            )
        )

        # Policy entity chunk
        policy_entity = EntityReference(
            entity_type="policy",
            entity_id="POL-001",
            start_pos=0,
            end_pos=20,
            is_partial=False,
            context_snippet="policy context",
        )
        policy_metadata = ChunkMetadata(
            source_file=Path("policies.pdf"),
            entity_tags=[policy_entity],
            section_context="Policy Section",
        )
        chunks.append(
            Chunk(
                id="chunk_003",
                text="Policy content about POL-001",
                document_id="doc_002",
                position_index=0,
                token_count=50,
                word_count=40,
                entities=[],
                section_context="Policy Section",
                quality_score=0.9,
                readability_scores={},
                metadata=policy_metadata,
            )
        )

        # Chunk without entities (should go to unclassified)
        no_entity_metadata = ChunkMetadata(
            source_file=Path("general.pdf"),
            entity_tags=[],
            section_context="General Section",
        )
        chunks.append(
            Chunk(
                id="chunk_004",
                text="General content without entities",
                document_id="doc_003",
                position_index=0,
                token_count=50,
                word_count=40,
                entities=[],
                section_context="General Section",
                quality_score=0.9,
                readability_scores={},
                metadata=no_entity_metadata,
            )
        )

        return chunks

    def test_creates_entity_type_folders(self, chunks_with_multiple_entity_types, tmp_path):
        """Should create separate folders for each entity type."""
        organizer = Organizer()
        output_dir = tmp_path / "output"

        result = organizer.organize(
            chunks_with_multiple_entity_types,
            output_dir,
            OrganizationStrategy.BY_ENTITY,
        )

        # Verify all entity type folders were created
        assert (output_dir / "risk").exists()
        assert (output_dir / "risk").is_dir()

        assert (output_dir / "control").exists()
        assert (output_dir / "control").is_dir()

        assert (output_dir / "policy").exists()
        assert (output_dir / "policy").is_dir()

        assert (output_dir / "unclassified").exists()
        assert (output_dir / "unclassified").is_dir()

        # Verify result metadata
        assert result.folders_created == 4  # risk, control, policy, unclassified
        assert result.files_written == 4  # Total chunks

    def test_routes_chunks_to_correct_folders(self, chunks_with_multiple_entity_types, tmp_path):
        """Should route chunks to folders based on entity type."""
        organizer = Organizer()
        output_dir = tmp_path / "output"

        result = organizer.organize(
            chunks_with_multiple_entity_types,
            output_dir,
            OrganizationStrategy.BY_ENTITY,
        )

        # Load and verify manifest routing
        with open(result.manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        folders = manifest["folders"]

        # Verify chunk routing in manifest
        assert "risk" in folders
        assert "chunk_001" in folders["risk"]["chunk_ids"]

        assert "control" in folders
        assert "chunk_002" in folders["control"]["chunk_ids"]

        assert "policy" in folders
        assert "chunk_003" in folders["policy"]["chunk_ids"]

        assert "unclassified" in folders
        assert "chunk_004" in folders["unclassified"]["chunk_ids"]

    def test_manifest_entity_summary_accuracy(self, chunks_with_multiple_entity_types, tmp_path):
        """Should generate accurate entity summary in manifest."""
        organizer = Organizer()
        output_dir = tmp_path / "output"

        result = organizer.organize(
            chunks_with_multiple_entity_types,
            output_dir,
            OrganizationStrategy.BY_ENTITY,
        )

        # Load and verify entity summary
        with open(result.manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        entity_summary = manifest["entity_summary"]

        # Verify total count
        assert entity_summary["total_entities"] == 3  # RISK-001, CTRL-001, POL-001

        # Verify entity types breakdown
        assert entity_summary["entity_types"]["risk"] == 1
        assert entity_summary["entity_types"]["control"] == 1
        assert entity_summary["entity_types"]["policy"] == 1

        # Verify unique entity IDs
        assert "RISK-001" in entity_summary["unique_entity_ids"]
        assert "CTRL-001" in entity_summary["unique_entity_ids"]
        assert "POL-001" in entity_summary["unique_entity_ids"]
        assert len(entity_summary["unique_entity_ids"]) == 3

    def test_by_entity_with_config_snapshot(self, chunks_with_multiple_entity_types, tmp_path):
        """Should include config snapshot in BY_ENTITY manifest."""
        organizer = Organizer()
        output_dir = tmp_path / "output"

        config = {
            "chunk_size": 512,
            "overlap_pct": 0.15,
            "entity_aware": True,
        }

        result = organizer.organize(
            chunks_with_multiple_entity_types,
            output_dir,
            OrganizationStrategy.BY_ENTITY,
            config_snapshot=config,
        )

        # Verify config is in manifest
        with open(result.manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        assert manifest["config_snapshot"] == config
        assert manifest["config_snapshot"]["entity_aware"] is True
        assert manifest["organization_strategy"] == "by_entity"
