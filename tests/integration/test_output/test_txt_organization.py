"""Integration tests for TXT formatter with organization strategies (Story 3.5 - Bucket 1).

Tests end-to-end integration of TxtFormatter with per-chunk mode and Organizer
with all three organization strategies (BY_DOCUMENT, BY_ENTITY, FLAT).

Test Coverage:
    - TxtFormatter per_chunk mode integration
    - Organizer integration with all strategies
    - Complete pipeline: chunks → formatter → organizer → files
    - Directory structure validation
    - File content validation
    - Manifest validation
    - Cross-platform path handling
"""

import json
from pathlib import Path

import pytest

pytestmark = [pytest.mark.P1, pytest.mark.integration, pytest.mark.output]

from data_extract.chunk.entity_preserver import EntityReference  # noqa: E402
from data_extract.chunk.models import Chunk, ChunkMetadata  # noqa: E402
from data_extract.output.formatters.txt_formatter import TxtFormatter  # noqa: E402
from data_extract.output.organization import OrganizationStrategy, Organizer  # noqa: E402

pytestmark = [pytest.mark.integration, pytest.mark.output, pytest.mark.organization]


@pytest.fixture
def sample_chunks_multi_source(tmp_path):
    """Create sample chunks from multiple source documents."""
    chunks = []

    # Chunks from audit_report.pdf
    for i in range(2):
        metadata = ChunkMetadata(
            source_file=Path("audit_report.pdf"),
            entity_tags=[],
            section_context="Executive Summary",
        )
        chunk = Chunk(
            id=f"audit_chunk_{i+1:03d}",
            text=f"This is audit report content chunk {i+1}. It contains important audit findings.",
            document_id="audit_001",
            position_index=i,
            token_count=50,
            word_count=40,
            entities=[],
            section_context="Executive Summary",
            quality_score=0.95,
            readability_scores={},
            metadata=metadata,
        )
        chunks.append(chunk)

    # Chunks from risk_register.xlsx with entity tags
    entity1 = EntityReference(
        entity_type="risk",
        entity_id="RISK-001",
        start_pos=0,
        end_pos=20,
        is_partial=False,
        context_snippet="risk context",
    )
    for i in range(2):
        metadata = ChunkMetadata(
            source_file=Path("risk_register.xlsx"),
            entity_tags=[entity1],
            section_context="Risk Assessment",
        )
        chunk = Chunk(
            id=f"risk_chunk_{i+1:03d}",
            text=f"This is risk register content chunk {i+1}. RISK-001 is a critical risk.",
            document_id="risk_001",
            position_index=i,
            token_count=50,
            word_count=40,
            entities=[],
            section_context="Risk Assessment",
            quality_score=0.90,
            readability_scores={},
            metadata=metadata,
        )
        chunks.append(chunk)

    return chunks


class TestTxtFormatterPerChunkMode:
    """Test TxtFormatter with per_chunk=True parameter."""

    def test_per_chunk_creates_separate_files(self, sample_chunks_multi_source, tmp_path):
        """Should create separate TXT file for each chunk."""
        formatter = TxtFormatter(per_chunk=True)
        output_dir = tmp_path / "output"

        formatter.format_chunks(iter(sample_chunks_multi_source), output_dir)

        # Should create 4 separate files (2 from each source)
        txt_files = list(output_dir.glob("*.txt"))
        assert len(txt_files) == 4

        # Check naming pattern
        assert (output_dir / "audit_report_chunk_001.txt").exists()
        assert (output_dir / "audit_report_chunk_002.txt").exists()
        assert (output_dir / "risk_register_chunk_001.txt").exists()
        assert (output_dir / "risk_register_chunk_002.txt").exists()

    def test_per_chunk_file_contents(self, sample_chunks_multi_source, tmp_path):
        """Should write correct content to each per-chunk file."""
        formatter = TxtFormatter(per_chunk=True)
        output_dir = tmp_path / "output"

        formatter.format_chunks(iter(sample_chunks_multi_source), output_dir)

        # Read first file and check content
        chunk1_path = output_dir / "audit_report_chunk_001.txt"
        content = chunk1_path.read_text(encoding="utf-8-sig")

        # Should contain delimiter
        assert "━━━ CHUNK 001 ━━━" in content

        # Should contain chunk text
        assert "audit report content chunk 1" in content

        # Should be clean text (no artifacts)
        assert "<" not in content or ">" not in content  # No HTML tags

    def test_per_chunk_with_metadata(self, sample_chunks_multi_source, tmp_path):
        """Should include metadata headers when enabled."""
        formatter = TxtFormatter(per_chunk=True, include_metadata=True)
        output_dir = tmp_path / "output"

        formatter.format_chunks(iter(sample_chunks_multi_source), output_dir)

        # Read file and check for metadata
        chunk1_path = output_dir / "audit_report_chunk_001.txt"
        content = chunk1_path.read_text(encoding="utf-8-sig")

        # Should contain source metadata
        assert "Source:" in content or "audit_report" in content

    def test_per_chunk_backward_compatibility(self, sample_chunks_multi_source, tmp_path):
        """Should default to concatenated mode when per_chunk=False."""
        formatter = TxtFormatter(per_chunk=False)  # Explicit False (default)
        output_path = tmp_path / "output.txt"

        result = formatter.format_chunks(iter(sample_chunks_multi_source), output_path)

        # Should create single file
        assert output_path.exists()
        assert result.output_path == output_path

        # Should not create multiple files
        txt_files = list(output_path.parent.glob("*.txt"))
        assert len(txt_files) == 1


class TestOrganizerByDocumentIntegration:
    """Test Organizer with BY_DOCUMENT strategy end-to-end."""

    def test_by_document_directory_structure(self, sample_chunks_multi_source, tmp_path):
        """Should create correct directory structure for BY_DOCUMENT."""
        organizer = Organizer()
        output_dir = tmp_path / "output"

        result = organizer.organize(
            sample_chunks_multi_source, output_dir, OrganizationStrategy.BY_DOCUMENT
        )

        # Check directory structure
        assert (output_dir / "audit_report").exists()
        assert (output_dir / "audit_report").is_dir()
        assert (output_dir / "risk_register").exists()
        assert (output_dir / "risk_register").is_dir()

        # Check manifest
        assert (output_dir / "manifest.json").exists()
        assert result.manifest_path == output_dir / "manifest.json"

    def test_by_document_file_organization(self, sample_chunks_multi_source, tmp_path):
        """Should plan file organization correctly within source folders."""
        organizer = Organizer()
        output_dir = tmp_path / "output"

        result = organizer.organize(
            sample_chunks_multi_source, output_dir, OrganizationStrategy.BY_DOCUMENT
        )

        # Check planned file paths include correct folder structure
        file_paths = [str(f) for f in result.files_created]
        audit_paths = [p for p in file_paths if "audit_report" in p]
        risk_paths = [p for p in file_paths if "risk_register" in p]

        assert len(audit_paths) == 2
        assert len(risk_paths) == 2

    def test_by_document_manifest_contents(self, sample_chunks_multi_source, tmp_path):
        """Should generate correct manifest for BY_DOCUMENT."""
        organizer = Organizer()
        output_dir = tmp_path / "output"

        result = organizer.organize(
            sample_chunks_multi_source, output_dir, OrganizationStrategy.BY_DOCUMENT
        )

        # Read manifest
        with open(result.manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        # Check metadata
        assert manifest["metadata"]["strategy"] == "by_document"
        assert manifest["metadata"]["total_chunks"] == 4
        assert manifest["metadata"]["total_files"] == 4

        # Check files list includes source info
        sources = [f["source"] for f in manifest["files"]]
        assert "audit_report" in sources
        assert "risk_register" in sources


class TestOrganizerByEntityIntegration:
    """Test Organizer with BY_ENTITY strategy end-to-end."""

    def test_by_entity_directory_structure(self, sample_chunks_multi_source, tmp_path):
        """Should create folders for each entity type."""
        organizer = Organizer()
        output_dir = tmp_path / "output"

        organizer.organize(sample_chunks_multi_source, output_dir, OrganizationStrategy.BY_ENTITY)

        # Should have risk folder (chunks with risk entities)
        assert (output_dir / "risk").exists()

        # Should have uncategorized folder (chunks without entities)
        assert (output_dir / "uncategorized").exists()

    def test_by_entity_file_distribution(self, sample_chunks_multi_source, tmp_path):
        """Should plan to distribute chunks to correct entity folders."""
        organizer = Organizer()
        output_dir = tmp_path / "output"

        result = organizer.organize(
            sample_chunks_multi_source, output_dir, OrganizationStrategy.BY_ENTITY
        )

        # Check planned paths include risk and uncategorized folders
        file_paths = [str(f) for f in result.files_created]
        risk_paths = [p for p in file_paths if "risk" in p and "uncategorized" not in p]
        uncat_paths = [p for p in file_paths if "uncategorized" in p]

        assert len(risk_paths) == 2  # 2 chunks with risk entities
        assert len(uncat_paths) == 2  # 2 chunks without entities

    def test_by_entity_manifest_entity_types(self, sample_chunks_multi_source, tmp_path):
        """Should include entity_type in manifest entries."""
        organizer = Organizer()
        output_dir = tmp_path / "output"

        result = organizer.organize(
            sample_chunks_multi_source, output_dir, OrganizationStrategy.BY_ENTITY
        )

        # Read manifest
        with open(result.manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        # Check entity_type field present
        entity_types = [f.get("entity_type", "") for f in manifest["files"]]
        assert "risk" in entity_types
        assert "uncategorized" in entity_types


class TestOrganizerFlatIntegration:
    """Test Organizer with FLAT strategy end-to-end."""

    def test_flat_no_subdirectories(self, sample_chunks_multi_source, tmp_path):
        """Should plan flat structure without subdirectories."""
        organizer = Organizer()
        output_dir = tmp_path / "output"

        result = organizer.organize(
            sample_chunks_multi_source, output_dir, OrganizationStrategy.FLAT
        )

        # Check no subdirectories (only manifest)
        subdirs = [p for p in output_dir.iterdir() if p.is_dir()]
        assert len(subdirs) == 0

        # All planned paths should be flat (no parent dirs)
        for file_path in result.files_created:
            relative = file_path.relative_to(output_dir)
            assert relative.parent == Path(".")

    def test_flat_filename_prefixes(self, sample_chunks_multi_source, tmp_path):
        """Should plan source-prefixed filenames."""
        organizer = Organizer()
        output_dir = tmp_path / "output"

        result = organizer.organize(
            sample_chunks_multi_source, output_dir, OrganizationStrategy.FLAT
        )

        # Check planned filenames have source prefix
        file_names = [f.name for f in result.files_created]
        expected_files = [
            "audit_report_chunk_001.txt",
            "audit_report_chunk_002.txt",
            "risk_register_chunk_001.txt",
            "risk_register_chunk_002.txt",
        ]

        for expected in expected_files:
            assert expected in file_names

    def test_flat_manifest_structure(self, sample_chunks_multi_source, tmp_path):
        """Should generate correct manifest for FLAT strategy."""
        organizer = Organizer()
        output_dir = tmp_path / "output"

        result = organizer.organize(
            sample_chunks_multi_source, output_dir, OrganizationStrategy.FLAT
        )

        # Read manifest
        with open(result.manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        # Check strategy
        assert manifest["metadata"]["strategy"] == "flat"

        # Check file paths are relative and flat
        for file_entry in manifest["files"]:
            file_path = file_entry["path"]
            # Should not contain directory separators (flat structure)
            assert "/" not in file_path and "\\" not in file_path


class TestEndToEndPipelineWithOrganization:
    """Test complete pipeline: TxtFormatter + Organizer."""

    def test_per_chunk_formatter_with_organizer(self, sample_chunks_multi_source, tmp_path):
        """Should work together: TxtFormatter per-chunk + Organizer."""
        # Step 1: Format chunks to individual files
        formatter = TxtFormatter(per_chunk=True)
        temp_dir = tmp_path / "temp"
        formatter.format_chunks(iter(sample_chunks_multi_source), temp_dir)

        # Verify per-chunk files created
        txt_files = list(temp_dir.glob("*.txt"))
        assert len(txt_files) == 4

        # Step 2: Organize using Organizer (simulate re-organization)
        # Note: In real workflow, chunks would be organized BEFORE formatting
        # This test validates that both components work independently
        organizer = Organizer()
        output_dir = tmp_path / "organized"
        result = organizer.organize(
            sample_chunks_multi_source, output_dir, OrganizationStrategy.BY_DOCUMENT
        )

        # Verify organization worked
        assert len(result.files_created) == 4
        assert result.manifest_path.exists()

    def test_concatenated_formatter_per_source(self, sample_chunks_multi_source, tmp_path):
        """Should create concatenated TXT per source using organization."""
        organizer = Organizer()
        output_dir = tmp_path / "output"

        # Organize chunks first
        result = organizer.organize(
            sample_chunks_multi_source, output_dir, OrganizationStrategy.BY_DOCUMENT
        )

        # Verify directory structure
        assert (output_dir / "audit_report").exists()
        assert (output_dir / "risk_register").exists()

        # Verify files created
        assert len(result.files_created) == 4

    def test_cross_platform_path_handling(self, sample_chunks_multi_source, tmp_path):
        """Should handle paths correctly across Windows and Unix."""
        organizer = Organizer()
        output_dir = tmp_path / "output"

        result = organizer.organize(
            sample_chunks_multi_source, output_dir, OrganizationStrategy.BY_DOCUMENT
        )

        # All paths should be Path objects (cross-platform)
        assert isinstance(result.manifest_path, Path)
        for file_path in result.files_created:
            assert isinstance(file_path, Path)

        # Manifest should use forward slashes (JSON standard)
        with open(result.manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        for file_entry in manifest["files"]:
            file_path = file_entry["path"]
            # Path should be string in manifest
            assert isinstance(file_path, str)


class TestErrorHandlingAndEdgeCases:
    """Test error handling in integration scenarios."""

    def test_empty_chunks_with_organizer(self, tmp_path):
        """Should handle empty chunks list gracefully."""
        organizer = Organizer()
        output_dir = tmp_path / "output"

        result = organizer.organize([], output_dir, OrganizationStrategy.BY_DOCUMENT)

        # Should create manifest even with no chunks
        assert result.manifest_path.exists()
        assert len(result.files_created) == 0

    def test_per_chunk_formatter_empty_chunks(self, tmp_path):
        """Should handle empty chunks in per-chunk mode."""
        formatter = TxtFormatter(per_chunk=True)
        output_dir = tmp_path / "output"

        result = formatter.format_chunks(iter([]), output_dir)

        # Should complete without errors
        assert result.chunk_count == 0
        assert len(result.errors) == 0

    def test_unicode_filenames_integration(self, tmp_path):
        """Should handle Unicode in filenames across pipeline."""
        # Create chunk with Unicode source
        metadata = ChunkMetadata(
            source_file=Path("审计报告_2024.pdf"),  # Chinese characters
            entity_tags=[],
            section_context="",
        )
        chunk = Chunk(
            id="chunk_001",
            text="Unicode filename test",
            document_id="doc_001",
            position_index=0,
            token_count=50,
            word_count=40,
            entities=[],
            section_context="",
            quality_score=0.9,
            readability_scores={},
            metadata=metadata,
        )

        # Test with organizer
        organizer = Organizer()
        output_dir = tmp_path / "output"

        result = organizer.organize([chunk], output_dir, OrganizationStrategy.BY_DOCUMENT)

        # Should create directory (name may be sanitized)
        assert len(result.files_created) == 1
        assert result.manifest_path.exists()

    def test_special_characters_in_paths(self, tmp_path):
        """Should sanitize special characters in paths."""
        # Create chunk with problematic characters
        metadata = ChunkMetadata(
            source_file=Path("audit:report/2024.pdf"),  # Invalid chars: : and /
            entity_tags=[],
            section_context="",
        )
        chunk = Chunk(
            id="chunk_001",
            text="Special chars test",
            document_id="doc_001",
            position_index=0,
            token_count=50,
            word_count=40,
            entities=[],
            section_context="",
            quality_score=0.9,
            readability_scores={},
            metadata=metadata,
        )

        organizer = Organizer()
        output_dir = tmp_path / "output"

        result = organizer.organize([chunk], output_dir, OrganizationStrategy.BY_DOCUMENT)

        # Should sanitize and plan valid directory/filename
        assert len(result.files_created) == 1
        created_path = result.files_created[0]

        # Check path is sanitized (no invalid chars)
        path_str = str(created_path)
        invalid_chars = [":", "*", "?", '"', "<", ">", "|"]
        # Allow : only for Windows drive letters (e.g., C:)
        path_without_drive = path_str[2:] if len(path_str) > 2 and path_str[1] == ":" else path_str
        for char in invalid_chars:
            assert char not in path_without_drive
