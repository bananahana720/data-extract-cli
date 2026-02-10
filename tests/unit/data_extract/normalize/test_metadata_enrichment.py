"""Tests for Story 2.6 metadata enrichment module.

Tests for metadata.py including:
- calculate_file_hash(): SHA-256 file hashing with chunked reading
- aggregate_entity_tags(): Entity extraction and counting
- aggregate_quality_scores(): Quality metrics aggregation
- serialize_config_snapshot(): Configuration serialization
- MetadataEnricher: Main enrichment orchestrator
"""

import tempfile
from pathlib import Path

import pytest

from src.data_extract.core.exceptions import ProcessingError
from src.data_extract.normalize.metadata import calculate_file_hash

pytestmark = [pytest.mark.P1, pytest.mark.unit]


class TestCalculateFileHash:
    """Tests for calculate_file_hash() function (AC-2.6.1, AC-2.6.8)."""

    def test_calculate_file_hash_normal_file(self):
        """Test SHA-256 hash generation for normal file (AC-2.6.1)."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("Test content for hashing")
            temp_path = Path(f.name)

        try:
            file_hash = calculate_file_hash(temp_path)

            # SHA-256 produces 64 hex characters
            assert len(file_hash) == 64
            assert all(c in "0123456789abcdef" for c in file_hash)

        finally:
            temp_path.unlink()

    def test_calculate_file_hash_determinism(self):
        """Test same file produces same hash (determinism, AC-2.6.8)."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("Deterministic content")
            temp_path = Path(f.name)

        try:
            hash1 = calculate_file_hash(temp_path)
            hash2 = calculate_file_hash(temp_path)

            # Same file must produce identical hash
            assert hash1 == hash2

        finally:
            temp_path.unlink()

    def test_calculate_file_hash_different_content(self):
        """Test different content produces different hash (AC-2.6.1)."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f1:
            f1.write("Content A")
            temp_path1 = Path(f1.name)

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f2:
            f2.write("Content B")
            temp_path2 = Path(f2.name)

        try:
            hash1 = calculate_file_hash(temp_path1)
            hash2 = calculate_file_hash(temp_path2)

            # Different content must produce different hashes
            assert hash1 != hash2

        finally:
            temp_path1.unlink()
            temp_path2.unlink()

    def test_calculate_file_hash_large_file(self):
        """Test SHA-256 hash for large file using chunked reading (AC-2.6.1)."""
        # Create 1MB file to test chunked reading
        large_content = "x" * (1024 * 1024)  # 1MB

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write(large_content)
            temp_path = Path(f.name)

        try:
            file_hash = calculate_file_hash(temp_path)

            # Should successfully hash large file
            assert len(file_hash) == 64
            assert all(c in "0123456789abcdef" for c in file_hash)

        finally:
            temp_path.unlink()

    def test_calculate_file_hash_missing_file(self):
        """Test error handling for missing file (AC-2.6.1)."""
        missing_path = Path("/nonexistent/file.txt")

        with pytest.raises(ProcessingError, match="File not found"):
            calculate_file_hash(missing_path)

    def test_calculate_file_hash_directory_not_file(self):
        """Test error handling when path is directory (AC-2.6.1)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            dir_path = Path(tmpdir)

            with pytest.raises(ProcessingError, match="not a file"):
                calculate_file_hash(dir_path)

    def test_calculate_file_hash_empty_file(self):
        """Test SHA-256 hash for empty file (edge case, AC-2.6.1)."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            # Write nothing (empty file)
            temp_path = Path(f.name)

        try:
            file_hash = calculate_file_hash(temp_path)

            # Empty file should produce valid hash
            assert len(file_hash) == 64
            # SHA-256 of empty file is known constant
            assert file_hash == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

        finally:
            temp_path.unlink()

    def test_calculate_file_hash_binary_file(self):
        """Test SHA-256 hash for binary file (AC-2.6.1)."""
        binary_content = bytes([0, 1, 2, 3, 255, 254, 253])

        with tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".bin") as f:
            f.write(binary_content)
            temp_path = Path(f.name)

        try:
            file_hash = calculate_file_hash(temp_path)

            # Binary file should hash successfully
            assert len(file_hash) == 64
            assert all(c in "0123456789abcdef" for c in file_hash)

        finally:
            temp_path.unlink()

    def test_calculate_file_hash_custom_chunk_size(self):
        """Test file hashing with custom chunk size (AC-2.6.1)."""
        content = "Test content for custom chunk size"

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write(content)
            temp_path = Path(f.name)

        try:
            # Hash with different chunk sizes - should produce same result
            hash_8kb = calculate_file_hash(temp_path, chunk_size=8192)
            hash_4kb = calculate_file_hash(temp_path, chunk_size=4096)
            hash_1kb = calculate_file_hash(temp_path, chunk_size=1024)

            # Chunk size should not affect hash result (determinism)
            assert hash_8kb == hash_4kb == hash_1kb

        finally:
            temp_path.unlink()


class TestAggregateEntityTags:
    """Tests for aggregate_entity_tags() function (AC-2.6.4)."""

    def test_aggregate_entity_tags_empty_list(self):
        """Test entity aggregation with empty list (edge case, AC-2.6.4)."""
        from src.data_extract.normalize.metadata import aggregate_entity_tags

        tags, counts = aggregate_entity_tags([])

        assert tags == []
        assert counts == {}

    def test_aggregate_entity_tags_single_entity(self):
        """Test entity aggregation with single entity (AC-2.6.4)."""
        from src.data_extract.core.models import Entity, EntityType
        from src.data_extract.normalize.metadata import aggregate_entity_tags

        entities = [
            Entity(
                type=EntityType.RISK,
                id="Risk-123",
                text="Risk assessment",
                confidence=0.9,
                location={"start": 0, "end": 10},
            )
        ]

        tags, counts = aggregate_entity_tags(entities)

        assert tags == ["Risk-123"]
        assert counts == {"risk": 1}

    def test_aggregate_entity_tags_multiple_types(self):
        """Test entity aggregation with mixed entity types (AC-2.6.4)."""
        from src.data_extract.core.models import Entity, EntityType
        from src.data_extract.normalize.metadata import aggregate_entity_tags

        entities = [
            Entity(
                type=EntityType.RISK,
                id="Risk-123",
                text="Risk A",
                confidence=0.9,
                location={"start": 0, "end": 10},
            ),
            Entity(
                type=EntityType.CONTROL,
                id="Control-456",
                text="Control A",
                confidence=0.9,
                location={"start": 20, "end": 30},
            ),
            Entity(
                type=EntityType.PROCESS,
                id="Process-789",
                text="Process A",
                confidence=0.85,
                location={"start": 40, "end": 50},
            ),
        ]

        tags, counts = aggregate_entity_tags(entities)

        assert tags == ["Risk-123", "Control-456", "Process-789"]
        assert counts == {"risk": 1, "control": 1, "process": 1}

    def test_aggregate_entity_tags_duplicate_types(self):
        """Test entity aggregation with multiple entities of same type (AC-2.6.4)."""
        from src.data_extract.core.models import Entity, EntityType
        from src.data_extract.normalize.metadata import aggregate_entity_tags

        entities = [
            Entity(
                type=EntityType.RISK,
                id="Risk-123",
                text="Risk A",
                confidence=0.9,
                location={"start": 0, "end": 10},
            ),
            Entity(
                type=EntityType.RISK,
                id="Risk-456",
                text="Risk B",
                confidence=0.88,
                location={"start": 20, "end": 30},
            ),
            Entity(
                type=EntityType.RISK,
                id="Risk-789",
                text="Risk C",
                confidence=0.92,
                location={"start": 40, "end": 50},
            ),
        ]

        tags, counts = aggregate_entity_tags(entities)

        assert tags == ["Risk-123", "Risk-456", "Risk-789"]
        assert counts == {"risk": 3}

    def test_aggregate_entity_tags_all_six_types(self):
        """Test entity aggregation with all 6 entity types (AC-2.6.4)."""
        from src.data_extract.core.models import Entity, EntityType
        from src.data_extract.normalize.metadata import aggregate_entity_tags

        entities = [
            Entity(
                type=EntityType.PROCESS,
                id="Process-1",
                text="P",
                confidence=0.9,
                location={"start": 0, "end": 1},
            ),
            Entity(
                type=EntityType.RISK,
                id="Risk-2",
                text="R",
                confidence=0.9,
                location={"start": 0, "end": 1},
            ),
            Entity(
                type=EntityType.CONTROL,
                id="Control-3",
                text="C",
                confidence=0.9,
                location={"start": 0, "end": 1},
            ),
            Entity(
                type=EntityType.REGULATION,
                id="Regulation-4",
                text="Reg",
                confidence=0.9,
                location={"start": 0, "end": 1},
            ),
            Entity(
                type=EntityType.POLICY,
                id="Policy-5",
                text="Pol",
                confidence=0.9,
                location={"start": 0, "end": 1},
            ),
            Entity(
                type=EntityType.ISSUE,
                id="Issue-6",
                text="Iss",
                confidence=0.9,
                location={"start": 0, "end": 1},
            ),
        ]

        tags, counts = aggregate_entity_tags(entities)

        assert len(tags) == 6
        assert "Process-1" in tags
        assert "Risk-2" in tags
        assert "Control-3" in tags
        assert "Regulation-4" in tags
        assert "Policy-5" in tags
        assert "Issue-6" in tags

        assert counts == {
            "process": 1,
            "risk": 1,
            "control": 1,
            "regulation": 1,
            "policy": 1,
            "issue": 1,
        }


class TestAggregateQualityScores:
    """Tests for aggregate_quality_scores() function (AC-2.6.5)."""

    def test_aggregate_quality_scores_all_present(self):
        """Test quality score aggregation with all scores present (AC-2.6.5)."""
        from src.data_extract.core.models import ValidationReport
        from src.data_extract.normalize.metadata import aggregate_quality_scores

        report = ValidationReport(
            quarantine_recommended=False,
            document_average_confidence=0.95,
            completeness_passed=True,
            quality_flags=[],
        )
        readability = {"flesch_reading_ease": 65.5, "coleman_liau_index": 12.3}

        scores, flags = aggregate_quality_scores(report, readability)

        assert scores["ocr_confidence"] == 0.95
        assert scores["flesch_reading_ease"] == 65.5
        assert scores["coleman_liau_index"] == 12.3
        assert flags == []

    def test_aggregate_quality_scores_no_readability(self):
        """Test quality score aggregation without readability metrics (AC-2.6.5)."""
        from src.data_extract.core.models import ValidationReport
        from src.data_extract.normalize.metadata import aggregate_quality_scores

        report = ValidationReport(
            quarantine_recommended=False,
            document_average_confidence=0.92,
            completeness_passed=True,
            quality_flags=[],
        )

        scores, flags = aggregate_quality_scores(report, readability_scores=None)

        assert scores["ocr_confidence"] == 0.92
        assert "flesch_reading_ease" not in scores
        assert flags == []

    def test_aggregate_quality_scores_with_quality_flags(self):
        """Test quality score aggregation with quality flags (AC-2.6.5)."""
        from src.data_extract.core.models import QualityFlag, ValidationReport
        from src.data_extract.normalize.metadata import aggregate_quality_scores

        report = ValidationReport(
            quarantine_recommended=True,
            document_average_confidence=0.85,
            completeness_passed=False,
            quality_flags=[QualityFlag.LOW_OCR_CONFIDENCE, QualityFlag.INCOMPLETE_EXTRACTION],
        )

        scores, flags = aggregate_quality_scores(report)

        assert scores["ocr_confidence"] == 0.85
        assert len(flags) == 2
        assert "low_ocr_confidence" in flags
        assert "incomplete_extraction" in flags

    def test_aggregate_quality_scores_missing_ocr_confidence(self):
        """Test quality score aggregation when OCR confidence is None (AC-2.6.5)."""
        from src.data_extract.core.models import ValidationReport
        from src.data_extract.normalize.metadata import aggregate_quality_scores

        report = ValidationReport(
            quarantine_recommended=False,
            document_average_confidence=None,
            completeness_passed=True,
            quality_flags=[],
        )

        scores, flags = aggregate_quality_scores(report)

        assert "ocr_confidence" not in scores
        assert flags == []

    def test_aggregate_quality_scores_all_quality_flags(self):
        """Test quality score aggregation with all 4 quality flags (AC-2.6.5)."""
        from src.data_extract.core.models import QualityFlag, ValidationReport
        from src.data_extract.normalize.metadata import aggregate_quality_scores

        report = ValidationReport(
            quarantine_recommended=True,
            document_average_confidence=0.80,
            completeness_passed=False,
            quality_flags=[
                QualityFlag.LOW_OCR_CONFIDENCE,
                QualityFlag.MISSING_IMAGES,
                QualityFlag.INCOMPLETE_EXTRACTION,
                QualityFlag.COMPLEX_OBJECTS,
            ],
        )

        scores, flags = aggregate_quality_scores(report)

        assert len(flags) == 4
        assert "low_ocr_confidence" in flags
        assert "missing_images" in flags
        assert "incomplete_extraction" in flags
        assert "complex_objects" in flags

    def test_aggregate_quality_scores_empty_readability(self):
        """Test quality score aggregation with empty readability dict (AC-2.6.5)."""
        from src.data_extract.core.models import ValidationReport
        from src.data_extract.normalize.metadata import aggregate_quality_scores

        report = ValidationReport(
            quarantine_recommended=False,
            document_average_confidence=0.96,
            completeness_passed=True,
            quality_flags=[],
        )

        scores, flags = aggregate_quality_scores(report, readability_scores={})

        assert scores["ocr_confidence"] == 0.96
        assert len(scores) == 2  # OCR confidence + completeness


class TestSerializeConfigSnapshot:
    """Tests for serialize_config_snapshot() function (AC-2.6.6)."""

    def test_serialize_config_snapshot_full_config(self):
        """Test config snapshot with full configuration (AC-2.6.6)."""
        from src.data_extract.normalize.config import NormalizationConfig
        from src.data_extract.normalize.metadata import serialize_config_snapshot

        config = NormalizationConfig(
            tool_version="2.0.0",
            ocr_confidence_threshold=0.95,
            completeness_threshold=0.90,
            remove_ocr_artifacts=True,
            normalize_whitespace=True,
        )

        snapshot = serialize_config_snapshot(config)

        assert snapshot["tool_version"] == "2.0.0"
        assert snapshot["ocr_confidence_threshold"] == 0.95
        assert snapshot["completeness_threshold"] == 0.90
        assert snapshot["remove_ocr_artifacts"] is True
        assert snapshot["normalize_whitespace"] is True

    def test_serialize_config_snapshot_default_config(self):
        """Test config snapshot with default configuration (AC-2.6.6)."""
        from src.data_extract.normalize.config import NormalizationConfig
        from src.data_extract.normalize.metadata import serialize_config_snapshot

        config = NormalizationConfig()  # All defaults

        snapshot = serialize_config_snapshot(config)

        # Verify defaults are captured
        assert "tool_version" in snapshot
        assert "ocr_confidence_threshold" in snapshot
        assert snapshot["ocr_confidence_threshold"] == 0.95  # Default

    def test_serialize_config_snapshot_roundtrip(self):
        """Test config serialization roundtrip (AC-2.6.6)."""
        from src.data_extract.normalize.config import NormalizationConfig
        from src.data_extract.normalize.metadata import serialize_config_snapshot

        config = NormalizationConfig(
            tool_version="2.1.0",
            ocr_confidence_threshold=0.98,
            completeness_threshold=0.85,
        )

        snapshot = serialize_config_snapshot(config)

        # Recreate config from snapshot
        restored_config = NormalizationConfig(**snapshot)

        assert restored_config.tool_version == config.tool_version
        assert restored_config.ocr_confidence_threshold == config.ocr_confidence_threshold
        assert restored_config.completeness_threshold == config.completeness_threshold
