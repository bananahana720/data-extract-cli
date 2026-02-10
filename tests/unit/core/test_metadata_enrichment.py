"""Tests for Story 2.6 metadata enrichment fields.

Tests the new fields added to Metadata model:
- config_snapshot: Configuration snapshot for reproducibility (AC-2.6.6)
- validation_report: Serialized ValidationReport (AC-2.6.5, AC-2.6.7)
"""

import json
from datetime import datetime
from pathlib import Path

from src.data_extract.core.models import DocumentType, Metadata


class TestMetadataEnrichmentFields:
    """Tests for Story 2.6 metadata enrichment fields."""

    def test_metadata_config_snapshot_default(self):
        """Test config_snapshot defaults to empty dict (AC-2.6.6)."""
        metadata = Metadata(
            source_file=Path("/tmp/test.pdf"),
            file_hash="a" * 64,
            processing_timestamp=datetime.now(),
            tool_version="2.0.0",
            config_version="1.0",
        )
        assert metadata.config_snapshot == {}
        assert isinstance(metadata.config_snapshot, dict)

    def test_metadata_config_snapshot_non_empty(self):
        """Test config_snapshot with actual configuration data (AC-2.6.6)."""
        config_data = {
            "tool_version": "2.0.0",
            "ocr_confidence_threshold": 0.95,
            "completeness_threshold": 0.90,
            "remove_ocr_artifacts": True,
        }
        metadata = Metadata(
            source_file=Path("/tmp/test.pdf"),
            file_hash="a" * 64,
            processing_timestamp=datetime.now(),
            tool_version="2.0.0",
            config_version="1.0",
            config_snapshot=config_data,
        )
        assert metadata.config_snapshot == config_data
        assert metadata.config_snapshot["tool_version"] == "2.0.0"
        assert metadata.config_snapshot["ocr_confidence_threshold"] == 0.95

    def test_metadata_config_snapshot_nested_dict(self):
        """Test config_snapshot with nested configuration (AC-2.6.6)."""
        config_data = {
            "tool_version": "2.0.0",
            "thresholds": {
                "ocr_confidence": 0.95,
                "completeness": 0.90,
            },
            "flags": {
                "remove_ocr_artifacts": True,
                "quarantine_low_confidence": True,
            },
        }
        metadata = Metadata(
            source_file=Path("/tmp/test.pdf"),
            file_hash="a" * 64,
            processing_timestamp=datetime.now(),
            tool_version="2.0.0",
            config_version="1.0",
            config_snapshot=config_data,
        )
        assert metadata.config_snapshot["thresholds"]["ocr_confidence"] == 0.95
        assert metadata.config_snapshot["flags"]["remove_ocr_artifacts"] is True

    def test_metadata_validation_report_default(self):
        """Test validation_report defaults to empty dict (AC-2.6.5)."""
        metadata = Metadata(
            source_file=Path("/tmp/test.pdf"),
            file_hash="a" * 64,
            processing_timestamp=datetime.now(),
            tool_version="2.0.0",
            config_version="1.0",
        )
        assert metadata.validation_report == {}
        assert isinstance(metadata.validation_report, dict)

    def test_metadata_validation_report_non_empty(self):
        """Test validation_report with serialized ValidationReport (AC-2.6.5)."""
        validation_data = {
            "quarantine_recommended": False,
            "confidence_scores": {1: 0.98, 2: 0.97},
            "quality_flags": [],
            "extraction_gaps": [],
            "document_average_confidence": 0.975,
            "completeness_passed": True,
        }
        metadata = Metadata(
            source_file=Path("/tmp/test.pdf"),
            file_hash="a" * 64,
            processing_timestamp=datetime.now(),
            tool_version="2.0.0",
            config_version="1.0",
            validation_report=validation_data,
        )
        assert metadata.validation_report == validation_data
        assert metadata.validation_report["quarantine_recommended"] is False
        assert metadata.validation_report["document_average_confidence"] == 0.975

    def test_metadata_validation_report_with_quality_flags(self):
        """Test validation_report with quality flags (AC-2.6.5)."""
        validation_data = {
            "quarantine_recommended": True,
            "quality_flags": ["low_ocr_confidence", "incomplete_extraction"],
            "extraction_gaps": ["Missing page 3", "Table extraction failed"],
            "document_average_confidence": 0.85,
            "completeness_passed": False,
        }
        metadata = Metadata(
            source_file=Path("/tmp/test.pdf"),
            file_hash="a" * 64,
            processing_timestamp=datetime.now(),
            tool_version="2.0.0",
            config_version="1.0",
            validation_report=validation_data,
        )
        assert metadata.validation_report["quarantine_recommended"] is True
        assert len(metadata.validation_report["quality_flags"]) == 2
        assert len(metadata.validation_report["extraction_gaps"]) == 2

    def test_metadata_both_enrichment_fields(self):
        """Test Metadata with both config_snapshot and validation_report (AC-2.6.6, AC-2.6.5)."""
        config_data = {"tool_version": "2.0.0", "ocr_confidence_threshold": 0.95}
        validation_data = {
            "quarantine_recommended": False,
            "completeness_passed": True,
        }
        metadata = Metadata(
            source_file=Path("/tmp/test.pdf"),
            file_hash="a" * 64,
            processing_timestamp=datetime.now(),
            tool_version="2.0.0",
            config_version="1.0",
            config_snapshot=config_data,
            validation_report=validation_data,
        )
        assert metadata.config_snapshot == config_data
        assert metadata.validation_report == validation_data

    def test_metadata_enrichment_json_serialization(self):
        """Test JSON serialization with enrichment fields (AC-2.6.7)."""
        config_data = {"tool_version": "2.0.0", "threshold": 0.95}
        validation_data = {"quarantine_recommended": False}
        metadata = Metadata(
            source_file=Path("/tmp/test.pdf"),
            file_hash="a" * 64,
            processing_timestamp=datetime.now(),
            tool_version="2.0.0",
            config_version="1.0",
            config_snapshot=config_data,
            validation_report=validation_data,
        )

        # Serialize to JSON
        json_str = metadata.model_dump_json()
        assert json_str is not None
        assert "config_snapshot" in json_str
        assert "validation_report" in json_str

        # Deserialize from JSON
        json_dict = json.loads(json_str)
        assert json_dict["config_snapshot"] == config_data
        assert json_dict["validation_report"] == validation_data

    def test_metadata_enrichment_model_dump(self):
        """Test model_dump() includes enrichment fields (AC-2.6.7)."""
        config_data = {"tool_version": "2.0.0"}
        validation_data = {"quarantine_recommended": False}
        metadata = Metadata(
            source_file=Path("/tmp/test.pdf"),
            file_hash="a" * 64,
            processing_timestamp=datetime.now(),
            tool_version="2.0.0",
            config_version="1.0",
            config_snapshot=config_data,
            validation_report=validation_data,
        )

        dumped = metadata.model_dump()
        assert "config_snapshot" in dumped
        assert "validation_report" in dumped
        assert dumped["config_snapshot"] == config_data
        assert dumped["validation_report"] == validation_data

    def test_metadata_backward_compatibility_without_enrichment(self):
        """Test backward compatibility: old metadata without enrichment fields (AC-2.6.6)."""
        # Create metadata without new fields (simulates old data)
        metadata = Metadata(
            source_file=Path("/tmp/test.pdf"),
            file_hash="a" * 64,
            processing_timestamp=datetime.now(),
            tool_version="2.0.0",
            config_version="1.0",
        )

        # New fields should default to empty dicts
        assert metadata.config_snapshot == {}
        assert metadata.validation_report == {}

        # Old fields should work normally
        assert metadata.source_file == Path("/tmp/test.pdf")
        assert metadata.tool_version == "2.0.0"

    def test_metadata_enrichment_fields_mutable_defaults(self):
        """Test that mutable defaults (dicts) don't share state (AC-2.6.6)."""
        metadata1 = Metadata(
            source_file=Path("/tmp/test1.pdf"),
            file_hash="a" * 64,
            processing_timestamp=datetime.now(),
            tool_version="2.0.0",
            config_version="1.0",
        )
        metadata2 = Metadata(
            source_file=Path("/tmp/test2.pdf"),
            file_hash="b" * 64,
            processing_timestamp=datetime.now(),
            tool_version="2.0.0",
            config_version="1.0",
        )

        # Modify metadata1's config_snapshot
        metadata1.config_snapshot["key"] = "value1"

        # metadata2 should not be affected (separate dict instances)
        assert "key" not in metadata2.config_snapshot
        assert metadata2.config_snapshot == {}

    def test_metadata_enrichment_large_config_snapshot(self):
        """Test config_snapshot with large configuration data (AC-2.6.6)."""
        large_config = {f"setting_{i}": f"value_{i}" for i in range(100)}
        metadata = Metadata(
            source_file=Path("/tmp/test.pdf"),
            file_hash="a" * 64,
            processing_timestamp=datetime.now(),
            tool_version="2.0.0",
            config_version="1.0",
            config_snapshot=large_config,
        )
        assert len(metadata.config_snapshot) == 100
        assert metadata.config_snapshot["setting_0"] == "value_0"
        assert metadata.config_snapshot["setting_99"] == "value_99"

    def test_metadata_enrichment_validation_report_complex(self):
        """Test validation_report with complex nested structure (AC-2.6.5)."""
        validation_data = {
            "quarantine_recommended": True,
            "confidence_scores": {i: 0.9 + (i * 0.01) for i in range(1, 11)},
            "quality_flags": ["low_ocr_confidence", "missing_images"],
            "extraction_gaps": [f"Gap {i}" for i in range(5)],
            "metadata": {
                "document_average_confidence": 0.95,
                "scanned_pdf_detected": True,
            },
        }
        metadata = Metadata(
            source_file=Path("/tmp/test.pdf"),
            file_hash="a" * 64,
            processing_timestamp=datetime.now(),
            tool_version="2.0.0",
            config_version="1.0",
            validation_report=validation_data,
        )
        assert len(metadata.validation_report["confidence_scores"]) == 10
        assert len(metadata.validation_report["extraction_gaps"]) == 5
        assert metadata.validation_report["metadata"]["scanned_pdf_detected"] is True

    def test_metadata_enrichment_serialization_roundtrip(self):
        """Test serialization roundtrip preserves enrichment fields (AC-2.6.7)."""
        config_data = {
            "tool_version": "2.0.0",
            "thresholds": {"ocr": 0.95, "completeness": 0.90},
        }
        validation_data = {
            "quarantine_recommended": False,
            "quality_flags": ["complex_objects"],
        }
        metadata = Metadata(
            source_file=Path("/tmp/test.pdf"),
            file_hash="a" * 64,
            processing_timestamp=datetime(2025, 11, 11, 12, 0, 0),
            tool_version="2.0.0",
            config_version="1.0",
            config_snapshot=config_data,
            validation_report=validation_data,
        )

        # Serialize to dict
        dumped = metadata.model_dump()

        # Deserialize from dict
        restored = Metadata(**dumped)

        # Verify enrichment fields preserved
        assert restored.config_snapshot == config_data
        assert restored.validation_report == validation_data
        assert restored.config_snapshot["thresholds"]["ocr"] == 0.95
        assert restored.validation_report["quality_flags"] == ["complex_objects"]

    def test_metadata_enrichment_with_all_existing_fields(self):
        """Test enrichment fields work with all existing Metadata fields (AC-2.6.1-2.6.8)."""
        config_data = {"tool_version": "2.0.0"}
        validation_data = {"quarantine_recommended": False}

        metadata = Metadata(
            source_file=Path("/tmp/test.pdf"),
            file_hash="a" * 64,
            processing_timestamp=datetime.now(),
            tool_version="2.0.0",
            config_version="1.0",
            document_type=DocumentType.REPORT,
            document_subtype="Audit Report",
            quality_scores={"ocr_confidence": 0.95},
            quality_flags=["low_ocr_confidence"],
            ocr_confidence={1: 0.95, 2: 0.93},
            completeness_ratio=0.92,
            entity_tags=["Risk-123", "Control-456"],
            entity_counts={"risk": 1, "control": 1},
            config_snapshot=config_data,
            validation_report=validation_data,
        )

        # Verify all fields set correctly
        assert metadata.config_snapshot == config_data
        assert metadata.validation_report == validation_data
        assert metadata.entity_tags == ["Risk-123", "Control-456"]
        assert metadata.completeness_ratio == 0.92
        assert metadata.document_type == DocumentType.REPORT
