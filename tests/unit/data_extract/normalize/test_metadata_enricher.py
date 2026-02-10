"""Integration tests for MetadataEnricher class (AC-2.6.1-2.6.8)."""

import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from src.data_extract.core.exceptions import ProcessingError
from src.data_extract.core.models import Entity, EntityType, QualityFlag, ValidationReport
from src.data_extract.normalize.config import NormalizationConfig
from src.data_extract.normalize.metadata import MetadataEnricher

pytestmark = [pytest.mark.P1, pytest.mark.unit]


class TestMetadataEnricher:
    """Tests for MetadataEnricher class (AC-2.6.1-2.6.8)."""

    def test_enrich_metadata_full_workflow(self):
        """Test full metadata enrichment workflow with all components (AC-all)."""
        # Create temporary test file
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("Test document content")
            temp_path = Path(f.name)

        try:
            # Setup test data
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
                    confidence=0.88,
                    location={"start": 20, "end": 30},
                ),
            ]

            validation_report = ValidationReport(
                quarantine_recommended=False,
                document_average_confidence=0.95,
                completeness_passed=True,
                quality_flags=[],
            )

            config = NormalizationConfig(
                tool_version="2.0.0",
                ocr_confidence_threshold=0.95,
                completeness_threshold=0.90,
            )

            # Enrich metadata
            enricher = MetadataEnricher()
            metadata = enricher.enrich_metadata(
                source_file=temp_path,
                entities=entities,
                validation_report=validation_report,
                config=config,
            )

            # Verify all enrichment fields (AC-2.6.1-2.6.8)
            assert len(metadata.file_hash) == 64  # SHA-256 (AC-2.6.1)
            assert metadata.processing_timestamp is not None  # AC-2.6.3
            assert metadata.tool_version == "2.0.0"  # AC-2.6.3
            assert metadata.entity_tags == ["Risk-123", "Control-456"]  # AC-2.6.4
            assert metadata.entity_counts == {"risk": 1, "control": 1}  # AC-2.6.4
            assert metadata.quality_scores["ocr_confidence"] == 0.95  # AC-2.6.5
            assert metadata.config_snapshot["tool_version"] == "2.0.0"  # AC-2.6.6
            assert metadata.validation_report["quarantine_recommended"] is False  # AC-2.6.5

        finally:
            temp_path.unlink()

    def test_enrich_metadata_with_readability(self):
        """Test metadata enrichment with readability scores (AC-2.6.5)."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("Test content")
            temp_path = Path(f.name)

        try:
            validation_report = ValidationReport(
                quarantine_recommended=False,
                document_average_confidence=0.96,
                completeness_passed=True,
                quality_flags=[],
            )

            config = NormalizationConfig(tool_version="2.0.0")

            readability = {"flesch_reading_ease": 70.5, "coleman_liau_index": 10.2}

            enricher = MetadataEnricher()
            metadata = enricher.enrich_metadata(
                source_file=temp_path,
                entities=[],
                validation_report=validation_report,
                config=config,
                readability_scores=readability,
            )

            assert metadata.quality_scores["flesch_reading_ease"] == 70.5
            assert metadata.quality_scores["coleman_liau_index"] == 10.2

        finally:
            temp_path.unlink()

    def test_enrich_metadata_empty_entities(self):
        """Test metadata enrichment with no entities (edge case, AC-2.6.4)."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("Test content")
            temp_path = Path(f.name)

        try:
            validation_report = ValidationReport(
                quarantine_recommended=False,
                document_average_confidence=0.95,
                completeness_passed=True,
                quality_flags=[],
            )

            config = NormalizationConfig(tool_version="2.0.0")

            enricher = MetadataEnricher()
            metadata = enricher.enrich_metadata(
                source_file=temp_path,
                entities=[],
                validation_report=validation_report,
                config=config,
            )

            assert metadata.entity_tags == []
            assert metadata.entity_counts == {}

        finally:
            temp_path.unlink()

    def test_enrich_metadata_json_serialization(self):
        """Test enriched metadata is JSON serializable (AC-2.6.7)."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("Test content")
            temp_path = Path(f.name)

        try:
            validation_report = ValidationReport(
                quarantine_recommended=False,
                document_average_confidence=0.95,
                completeness_passed=True,
                quality_flags=[],
            )

            config = NormalizationConfig(tool_version="2.0.0")

            enricher = MetadataEnricher()
            metadata = enricher.enrich_metadata(
                source_file=temp_path,
                entities=[],
                validation_report=validation_report,
                config=config,
            )

            # Test JSON serialization (AC-2.6.7)
            json_str = metadata.model_dump_json()
            assert json_str is not None
            assert "file_hash" in json_str
            assert "config_snapshot" in json_str
            assert "validation_report" in json_str

        finally:
            temp_path.unlink()

    def test_enrich_metadata_with_quality_flags(self):
        """Test metadata enrichment with quality flags (AC-2.6.5)."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("Test content")
            temp_path = Path(f.name)

        try:
            validation_report = ValidationReport(
                quarantine_recommended=True,
                document_average_confidence=0.85,
                completeness_passed=False,
                quality_flags=[QualityFlag.LOW_OCR_CONFIDENCE, QualityFlag.MISSING_IMAGES],
            )

            config = NormalizationConfig(tool_version="2.0.0")

            enricher = MetadataEnricher()
            metadata = enricher.enrich_metadata(
                source_file=temp_path,
                entities=[],
                validation_report=validation_report,
                config=config,
            )

            assert len(metadata.quality_flags) == 2
            assert "low_ocr_confidence" in metadata.quality_flags
            assert "missing_images" in metadata.quality_flags

        finally:
            temp_path.unlink()

    def test_enrich_metadata_missing_file_error(self):
        """Test metadata enrichment with missing file raises ProcessingError (AC-2.6.1)."""
        missing_path = Path("/nonexistent/file.pdf")

        validation_report = ValidationReport(
            quarantine_recommended=False,
            document_average_confidence=0.95,
            completeness_passed=True,
            quality_flags=[],
        )

        config = NormalizationConfig(tool_version="2.0.0")

        enricher = MetadataEnricher()

        with pytest.raises(ProcessingError, match="File not found"):
            enricher.enrich_metadata(
                source_file=missing_path,
                entities=[],
                validation_report=validation_report,
                config=config,
            )

    def test_enrich_metadata_iso8601_timestamp(self):
        """Test processing timestamp is valid datetime (AC-2.6.3)."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("Test content")
            temp_path = Path(f.name)

        try:
            validation_report = ValidationReport(
                quarantine_recommended=False,
                completeness_passed=True,
                quality_flags=[],
            )

            config = NormalizationConfig(tool_version="2.0.0")

            enricher = MetadataEnricher()
            metadata = enricher.enrich_metadata(
                source_file=temp_path,
                entities=[],
                validation_report=validation_report,
                config=config,
            )

            # Verify timestamp is datetime and recent
            assert isinstance(metadata.processing_timestamp, datetime)
            from datetime import timezone

            assert (datetime.now(timezone.utc) - metadata.processing_timestamp).seconds < 5

        finally:
            temp_path.unlink()
