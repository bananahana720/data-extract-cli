"""Unit tests for core data models.

Tests cover:
- Valid model instantiation
- Field validation constraints
- Pydantic ValidationError for invalid data
- Edge cases (empty values, boundary conditions)
- EntityType enum validation (Story 2.2)
- Entity location field (Story 2.2)
- Metadata entity_tags and entity_counts (Story 2.2)
"""

from datetime import datetime
from pathlib import Path

import pytest
import structlog
from pydantic import ValidationError

from src.data_extract.core.models import (
    Chunk,
    Document,
    Entity,
    EntityType,
    Metadata,
    ProcessingContext,
    QualityFlag,
    ValidationReport,
)


class TestEntityType:
    """Test EntityType enum (Story 2.2 - AC 2.2.1)."""

    def test_entity_type_enum_has_all_six_types(self):
        """Test EntityType enum contains all 6 required audit entity types."""
        assert EntityType.PROCESS.value == "process"
        assert EntityType.RISK.value == "risk"
        assert EntityType.CONTROL.value == "control"
        assert EntityType.REGULATION.value == "regulation"
        assert EntityType.POLICY.value == "policy"
        assert EntityType.ISSUE.value == "issue"

    def test_entity_type_enum_count(self):
        """Test EntityType enum has exactly 6 types."""
        assert len(EntityType) == 6

    def test_entity_type_string_values(self):
        """Test EntityType enum values are lowercase strings."""
        for entity_type in EntityType:
            assert isinstance(entity_type.value, str)
            assert entity_type.value.islower()


class TestQualityFlag:
    """Test QualityFlag enum (Story 2.4 - AC 2.4.6, 2.4.7)."""

    def test_quality_flag_enum_has_all_flags(self):
        """Test QualityFlag enum contains all required quality flags."""
        assert QualityFlag.LOW_OCR_CONFIDENCE.value == "low_ocr_confidence"
        assert QualityFlag.MISSING_IMAGES.value == "missing_images"
        assert QualityFlag.INCOMPLETE_EXTRACTION.value == "incomplete_extraction"
        assert QualityFlag.COMPLEX_OBJECTS.value == "complex_objects"

    def test_quality_flag_enum_count(self):
        """Test QualityFlag enum has exactly 4 flags (Story 2.5)."""
        assert len(QualityFlag) == 4

    def test_quality_flag_string_values(self):
        """Test QualityFlag enum values are lowercase strings with underscores."""
        for quality_flag in QualityFlag:
            assert isinstance(quality_flag.value, str)
            assert quality_flag.value.islower()
            assert " " not in quality_flag.value  # No spaces, use underscores

    def test_quality_flag_usage_in_list(self):
        """Test QualityFlag enum can be used in lists for quality tracking."""
        flags = [QualityFlag.LOW_OCR_CONFIDENCE, QualityFlag.MISSING_IMAGES]
        assert len(flags) == 2
        assert QualityFlag.LOW_OCR_CONFIDENCE in flags
        assert QualityFlag.INCOMPLETE_EXTRACTION not in flags

    def test_quality_flag_serialization(self):
        """Test QualityFlag enum serializes to string value."""
        flag = QualityFlag.LOW_OCR_CONFIDENCE
        assert flag.value == "low_ocr_confidence"


class TestEntity:
    """Test Entity model validation and instantiation."""

    def test_entity_valid_creation(self):
        """Test Entity instantiation with valid data."""
        entity = Entity(
            type=EntityType.RISK,
            id="RISK-001",
            text="High operational risk identified",
            confidence=0.85,
            location={"start": 100, "end": 136},
        )
        assert entity.type == EntityType.RISK
        assert entity.id == "RISK-001"
        assert entity.text == "High operational risk identified"
        assert entity.confidence == 0.85
        assert entity.location == {"start": 100, "end": 136}

    def test_entity_confidence_boundary_valid(self):
        """Test Entity confidence at boundary values (0.0 and 1.0)."""
        entity_min = Entity(
            type=EntityType.CONTROL,
            id="C-001",
            text="Control",
            confidence=0.0,
            location={"start": 0, "end": 7},
        )
        assert entity_min.confidence == 0.0

        entity_max = Entity(
            type=EntityType.POLICY,
            id="P-001",
            text="Policy",
            confidence=1.0,
            location={"start": 0, "end": 6},
        )
        assert entity_max.confidence == 1.0

    def test_entity_confidence_below_zero_invalid(self):
        """Test Entity with confidence < 0.0 raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            Entity(
                type=EntityType.RISK,
                id="R-001",
                text="Risk",
                confidence=-0.1,
                location={"start": 0, "end": 4},
            )
        assert "greater than or equal to 0" in str(exc_info.value).lower()

    def test_entity_confidence_above_one_invalid(self):
        """Test Entity with confidence > 1.0 raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            Entity(
                type=EntityType.RISK,
                id="R-001",
                text="Risk",
                confidence=1.5,
                location={"start": 0, "end": 4},
            )
        assert "less than or equal to 1" in str(exc_info.value).lower()

    def test_entity_missing_required_fields(self):
        """Test Entity with missing required fields raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            Entity(type=EntityType.RISK, id="R-001")  # Missing text, confidence, location
        assert "field required" in str(exc_info.value).lower()

    def test_entity_empty_text_valid(self):
        """Test Entity with empty text is valid (edge case)."""
        entity = Entity(
            type=EntityType.ISSUE,
            id="I-001",
            text="",
            confidence=0.5,
            location={"start": 0, "end": 0},
        )
        assert entity.text == ""

    def test_entity_location_field(self):
        """Test Entity location field stores character positions (Story 2.2)."""
        entity = Entity(
            type=EntityType.PROCESS,
            id="PROC-001",
            text="Document review process",
            confidence=0.95,
            location={"start": 50, "end": 73},
        )
        assert entity.location["start"] == 50
        assert entity.location["end"] == 73

    def test_entity_type_enum_usage(self):
        """Test Entity type field accepts EntityType enum values (Story 2.2)."""
        for entity_type in EntityType:
            entity = Entity(
                type=entity_type,
                id=f"{entity_type.value.upper()}-001",
                text=f"Sample {entity_type.value}",
                confidence=0.8,
                location={"start": 0, "end": 10},
            )
            assert entity.type == entity_type

    def test_entity_serialization_with_enum(self):
        """Test Entity serializes EntityType enum correctly."""
        entity = Entity(
            type=EntityType.CONTROL,
            id="CTRL-123",
            text="Access control policy",
            confidence=0.92,
            location={"start": 200, "end": 221},
        )
        entity_dict = entity.model_dump()
        assert entity_dict["type"] == "control"  # Enum serializes to string value


class TestMetadata:
    """Test Metadata model validation and instantiation."""

    def test_metadata_valid_creation(self):
        """Test Metadata instantiation with all required fields."""
        metadata = Metadata(
            source_file=Path("/path/to/document.pdf"),
            file_hash="abc123def456",
            processing_timestamp=datetime(2025, 11, 10, 10, 30),
            tool_version="1.0.0",
            config_version="v1",
            document_type="pdf",
        )
        assert metadata.source_file == Path("/path/to/document.pdf")
        assert metadata.file_hash == "abc123def456"
        assert metadata.tool_version == "1.0.0"
        assert metadata.config_version == "v1"
        assert metadata.document_type == "pdf"
        assert metadata.quality_scores == {}
        assert metadata.quality_flags == []
        assert metadata.entity_tags == []  # Story 2.2
        assert metadata.entity_counts == {}  # Story 2.2

    def test_metadata_with_quality_metrics(self):
        """Test Metadata with quality scores and flags."""
        metadata = Metadata(
            source_file=Path("document.pdf"),
            file_hash="hash123",
            processing_timestamp=datetime.now(),
            tool_version="1.0.0",
            config_version="v1",
            document_type="pdf",
            quality_scores={"ocr_confidence": 0.95, "text_density": 0.8},
            quality_flags=["low_contrast", "skewed_image"],
        )
        assert metadata.quality_scores["ocr_confidence"] == 0.95
        assert metadata.quality_scores["text_density"] == 0.8
        assert "low_contrast" in metadata.quality_flags
        assert "skewed_image" in metadata.quality_flags

    def test_metadata_missing_required_fields(self):
        """Test Metadata with missing required fields raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            Metadata(
                source_file=Path("doc.pdf"),
                file_hash="hash",
            )  # Missing other required fields
        assert "field required" in str(exc_info.value).lower()

    def test_metadata_with_entity_tags(self):
        """Test Metadata with entity_tags for RAG retrieval (Story 2.2 - AC 2.2.6)."""
        metadata = Metadata(
            source_file=Path("audit_report.pdf"),
            file_hash="hash123",
            processing_timestamp=datetime.now(),
            tool_version="1.0.0",
            config_version="v1",
            document_type="pdf",
            entity_tags=["Risk-123", "Control-456", "Policy-789"],
        )
        assert len(metadata.entity_tags) == 3
        assert "Risk-123" in metadata.entity_tags
        assert "Control-456" in metadata.entity_tags
        assert "Policy-789" in metadata.entity_tags

    def test_metadata_with_entity_counts(self):
        """Test Metadata with entity_counts by type (Story 2.2 - AC 2.2.6)."""
        metadata = Metadata(
            source_file=Path("audit_report.pdf"),
            file_hash="hash123",
            processing_timestamp=datetime.now(),
            tool_version="1.0.0",
            config_version="v1",
            document_type="pdf",
            entity_counts={"risk": 5, "control": 3, "policy": 2, "regulation": 1},
        )
        assert metadata.entity_counts["risk"] == 5
        assert metadata.entity_counts["control"] == 3
        assert metadata.entity_counts["policy"] == 2
        assert metadata.entity_counts["regulation"] == 1

    def test_metadata_entity_fields_optional(self):
        """Test Metadata entity fields are optional with empty defaults."""
        metadata = Metadata(
            source_file=Path("doc.pdf"),
            file_hash="hash",
            processing_timestamp=datetime.now(),
            tool_version="1.0.0",
            config_version="v1",
            document_type="pdf",
        )
        # entity_tags and entity_counts should default to empty
        assert metadata.entity_tags == []
        assert metadata.entity_counts == {}

    def test_metadata_with_ocr_confidence_scores(self):
        """Test Metadata with per-page OCR confidence scores (Story 2.4 - AC 2.4.6)."""
        metadata = Metadata(
            source_file=Path("scanned_doc.pdf"),
            file_hash="hash456",
            processing_timestamp=datetime.now(),
            tool_version="1.0.0",
            config_version="v1",
            document_type="pdf",
            ocr_confidence={1: 0.98, 2: 0.95, 3: 0.92},
        )
        assert len(metadata.ocr_confidence) == 3
        assert metadata.ocr_confidence[1] == 0.98
        assert metadata.ocr_confidence[2] == 0.95
        assert metadata.ocr_confidence[3] == 0.92

    def test_metadata_ocr_confidence_empty_by_default(self):
        """Test Metadata ocr_confidence field defaults to empty dict."""
        metadata = Metadata(
            source_file=Path("native_doc.pdf"),
            file_hash="hash789",
            processing_timestamp=datetime.now(),
            tool_version="1.0.0",
            config_version="v1",
            document_type="pdf",
        )
        assert metadata.ocr_confidence == {}

    def test_metadata_ocr_confidence_with_quality_flags(self):
        """Test Metadata with both OCR confidence scores and quality flags (Story 2.4)."""
        metadata = Metadata(
            source_file=Path("low_quality_scan.pdf"),
            file_hash="hash999",
            processing_timestamp=datetime.now(),
            tool_version="1.0.0",
            config_version="v1",
            document_type="pdf",
            ocr_confidence={1: 0.85, 2: 0.82},
            quality_flags=["low_ocr_confidence"],  # String values from QualityFlag enum
        )
        assert metadata.ocr_confidence[1] == 0.85
        assert metadata.ocr_confidence[2] == 0.82
        assert "low_ocr_confidence" in metadata.quality_flags

    def test_metadata_completeness_ratio_valid(self):
        """Test Metadata.completeness_ratio accepts valid 0.0-1.0 values (Story 2.5 - AC 2.5.3)."""
        metadata = Metadata(
            source_file=Path("test.pdf"),
            file_hash="abc123",
            processing_timestamp=datetime.now(),
            tool_version="1.0.0",
            config_version="1.0",
            completeness_ratio=0.95,
        )
        assert metadata.completeness_ratio == 0.95

    def test_metadata_completeness_ratio_boundary_values(self):
        """Test Metadata.completeness_ratio at boundary values 0.0 and 1.0 (Story 2.5)."""
        # Test 0.0 (0% complete)
        metadata_zero = Metadata(
            source_file=Path("test.pdf"),
            file_hash="abc123",
            processing_timestamp=datetime.now(),
            tool_version="1.0.0",
            config_version="1.0",
            completeness_ratio=0.0,
        )
        assert metadata_zero.completeness_ratio == 0.0

        # Test 1.0 (100% complete)
        metadata_one = Metadata(
            source_file=Path("test.pdf"),
            file_hash="abc123",
            processing_timestamp=datetime.now(),
            tool_version="1.0.0",
            config_version="1.0",
            completeness_ratio=1.0,
        )
        assert metadata_one.completeness_ratio == 1.0

    def test_metadata_completeness_ratio_none_default(self):
        """Test Metadata.completeness_ratio defaults to None when not provided (Story 2.5)."""
        metadata = Metadata(
            source_file=Path("test.pdf"),
            file_hash="abc123",
            processing_timestamp=datetime.now(),
            tool_version="1.0.0",
            config_version="1.0",
        )
        assert metadata.completeness_ratio is None

    def test_metadata_completeness_ratio_invalid_above_1(self):
        """Test Metadata.completeness_ratio rejects values > 1.0 (Story 2.5)."""
        with pytest.raises(ValidationError) as exc_info:
            Metadata(
                source_file=Path("test.pdf"),
                file_hash="abc123",
                processing_timestamp=datetime.now(),
                tool_version="1.0.0",
                config_version="1.0",
                completeness_ratio=1.5,
            )
        assert "completeness_ratio" in str(exc_info.value).lower()

    def test_metadata_completeness_ratio_invalid_below_0(self):
        """Test Metadata.completeness_ratio rejects values < 0.0 (Story 2.5)."""
        with pytest.raises(ValidationError) as exc_info:
            Metadata(
                source_file=Path("test.pdf"),
                file_hash="abc123",
                processing_timestamp=datetime.now(),
                tool_version="1.0.0",
                config_version="1.0",
                completeness_ratio=-0.1,
            )
        assert "completeness_ratio" in str(exc_info.value).lower()

    def test_metadata_with_entity_relationships(self):
        """Test Metadata with entity_relationships triples (Story 3.2 - AC 3.2-3)."""
        metadata = Metadata(
            source_file=Path("audit_report.pdf"),
            file_hash="hash123",
            processing_timestamp=datetime.now(),
            tool_version="1.0.0",
            config_version="v1",
            entity_relationships=[
                ("RISK-001", "mitigated_by", "CTRL-042"),
                ("POL-001", "implements", "REG-2024-001"),
            ],
        )
        assert len(metadata.entity_relationships) == 2
        assert ("RISK-001", "mitigated_by", "CTRL-042") in metadata.entity_relationships

    def test_metadata_with_empty_entity_relationships(self):
        """Test Metadata with empty entity_relationships (default case)."""
        metadata = Metadata(
            source_file=Path("doc.pdf"),
            file_hash="hash456",
            processing_timestamp=datetime.now(),
            tool_version="1.0.0",
            config_version="v1",
        )
        assert metadata.entity_relationships == []

    def test_metadata_with_section_context(self):
        """Test Metadata with section_context breadcrumb (Story 3.2 - AC 3.2-7)."""
        metadata = Metadata(
            source_file=Path("policy.pdf"),
            file_hash="hash789",
            processing_timestamp=datetime.now(),
            tool_version="1.0.0",
            config_version="v1",
            section_context="Risk Assessment > Identified Risks > Critical Risks",
        )
        assert metadata.section_context == "Risk Assessment > Identified Risks > Critical Risks"

    def test_metadata_with_none_section_context(self):
        """Test Metadata with section_context None (default case)."""
        metadata = Metadata(
            source_file=Path("doc.pdf"),
            file_hash="hash000",
            processing_timestamp=datetime.now(),
            tool_version="1.0.0",
            config_version="v1",
        )
        assert metadata.section_context is None


class TestValidationReport:
    """Test ValidationReport model (Story 2.4 - AC 2.4.5, 2.4.6, 2.4.7)."""

    def test_validation_report_valid_creation(self):
        """Test ValidationReport instantiation with valid data."""
        report = ValidationReport(
            quarantine_recommended=True,
            confidence_scores={1: 0.85, 2: 0.88, 3: 0.90},
            quality_flags=[QualityFlag.LOW_OCR_CONFIDENCE],
            extraction_gaps=["Page 1: Low confidence text detection"],
            document_average_confidence=0.8767,
            scanned_pdf_detected=True,
        )
        assert report.quarantine_recommended is True
        assert len(report.confidence_scores) == 3
        assert report.confidence_scores[1] == 0.85
        assert report.quality_flags == [QualityFlag.LOW_OCR_CONFIDENCE]
        assert len(report.extraction_gaps) == 1
        assert report.document_average_confidence == 0.8767
        assert report.scanned_pdf_detected is True

    def test_validation_report_no_quarantine_needed(self):
        """Test ValidationReport for high-quality document (no quarantine)."""
        report = ValidationReport(
            quarantine_recommended=False,
            confidence_scores={1: 0.98, 2: 0.97, 3: 0.99},
            quality_flags=[],
            extraction_gaps=[],
            document_average_confidence=0.98,
            scanned_pdf_detected=True,
        )
        assert report.quarantine_recommended is False
        assert all(score >= 0.95 for score in report.confidence_scores.values())
        assert report.quality_flags == []
        assert report.extraction_gaps == []
        assert report.document_average_confidence >= 0.95

    def test_validation_report_multiple_quality_flags(self):
        """Test ValidationReport with multiple quality flags."""
        report = ValidationReport(
            quarantine_recommended=True,
            confidence_scores={1: 0.80},
            quality_flags=[
                QualityFlag.LOW_OCR_CONFIDENCE,
                QualityFlag.MISSING_IMAGES,
                QualityFlag.INCOMPLETE_EXTRACTION,
            ],
            extraction_gaps=["Low OCR confidence", "Missing image references"],
        )
        assert len(report.quality_flags) == 3
        assert QualityFlag.LOW_OCR_CONFIDENCE in report.quality_flags
        assert QualityFlag.MISSING_IMAGES in report.quality_flags
        assert QualityFlag.INCOMPLETE_EXTRACTION in report.quality_flags

    def test_validation_report_optional_fields_none(self):
        """Test ValidationReport with optional fields set to None."""
        report = ValidationReport(
            quarantine_recommended=False,
            confidence_scores={},
            quality_flags=[],
            extraction_gaps=[],
            document_average_confidence=None,
            scanned_pdf_detected=None,
        )
        assert report.document_average_confidence is None
        assert report.scanned_pdf_detected is None
        assert report.confidence_scores == {}
        assert report.quality_flags == []

    def test_validation_report_average_confidence_boundary_values(self):
        """Test ValidationReport average confidence at boundary values (0.0 and 1.0)."""
        report_min = ValidationReport(
            quarantine_recommended=True,
            confidence_scores={1: 0.0},
            quality_flags=[QualityFlag.LOW_OCR_CONFIDENCE],
            extraction_gaps=["Completely failed OCR"],
            document_average_confidence=0.0,
            scanned_pdf_detected=True,
        )
        assert report_min.document_average_confidence == 0.0

        report_max = ValidationReport(
            quarantine_recommended=False,
            confidence_scores={1: 1.0},
            quality_flags=[],
            extraction_gaps=[],
            document_average_confidence=1.0,
            scanned_pdf_detected=True,
        )
        assert report_max.document_average_confidence == 1.0

    def test_validation_report_average_confidence_invalid_below_zero(self):
        """Test ValidationReport with average confidence < 0.0 raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            ValidationReport(
                quarantine_recommended=True,
                confidence_scores={},
                quality_flags=[],
                extraction_gaps=[],
                document_average_confidence=-0.1,
            )
        assert "greater than or equal to 0" in str(exc_info.value).lower()

    def test_validation_report_average_confidence_invalid_above_one(self):
        """Test ValidationReport with average confidence > 1.0 raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            ValidationReport(
                quarantine_recommended=False,
                confidence_scores={},
                quality_flags=[],
                extraction_gaps=[],
                document_average_confidence=1.5,
            )
        assert "less than or equal to 1" in str(exc_info.value).lower()

    def test_validation_report_serialization_with_enum_flags(self):
        """Test ValidationReport serializes QualityFlag enums correctly."""
        report = ValidationReport(
            quarantine_recommended=True,
            confidence_scores={1: 0.85},
            quality_flags=[QualityFlag.LOW_OCR_CONFIDENCE, QualityFlag.MISSING_IMAGES],
            extraction_gaps=["Low quality scan"],
        )
        report_dict = report.model_dump()
        # QualityFlag enums should serialize to string values
        assert report_dict["quality_flags"] == ["low_ocr_confidence", "missing_images"]

    def test_validation_report_completeness_passed_default(self):
        """Test ValidationReport.completeness_passed defaults to True (Story 2.5 - AC 2.5.3)."""
        report = ValidationReport(quarantine_recommended=False)
        assert report.completeness_passed is True

    def test_validation_report_completeness_passed_explicit(self):
        """Test ValidationReport.completeness_passed can be set explicitly (Story 2.5)."""
        report = ValidationReport(quarantine_recommended=True, completeness_passed=False)
        assert report.completeness_passed is False

    def test_validation_report_missing_images_count_default(self):
        """Test ValidationReport.missing_images_count defaults to 0 (Story 2.5 - AC 2.5.1)."""
        report = ValidationReport(quarantine_recommended=False)
        assert report.missing_images_count == 0

    def test_validation_report_missing_images_count_positive(self):
        """Test ValidationReport.missing_images_count accepts positive values (Story 2.5)."""
        report = ValidationReport(quarantine_recommended=True, missing_images_count=5)
        assert report.missing_images_count == 5

    def test_validation_report_missing_images_count_invalid_negative(self):
        """Test ValidationReport.missing_images_count rejects negative values (Story 2.5)."""
        with pytest.raises(ValidationError) as exc_info:
            ValidationReport(quarantine_recommended=False, missing_images_count=-1)
        assert "missing_images_count" in str(exc_info.value).lower()

    def test_validation_report_complex_objects_count_default(self):
        """Test ValidationReport.complex_objects_count defaults to 0 (Story 2.5 - AC 2.5.2)."""
        report = ValidationReport(quarantine_recommended=False)
        assert report.complex_objects_count == 0

    def test_validation_report_complex_objects_count_positive(self):
        """Test ValidationReport.complex_objects_count accepts positive values (Story 2.5)."""
        report = ValidationReport(quarantine_recommended=True, complex_objects_count=3)
        assert report.complex_objects_count == 3

    def test_validation_report_complex_objects_count_invalid_negative(self):
        """Test ValidationReport.complex_objects_count rejects negative values (Story 2.5)."""
        with pytest.raises(ValidationError) as exc_info:
            ValidationReport(quarantine_recommended=False, complex_objects_count=-1)
        assert "complex_objects_count" in str(exc_info.value).lower()

    def test_validation_report_all_completeness_fields(self):
        """Test ValidationReport with all completeness fields populated (Story 2.5)."""
        report = ValidationReport(
            quarantine_recommended=True,
            completeness_passed=False,
            missing_images_count=2,
            complex_objects_count=1,
            extraction_gaps=["Missing image on page 3", "OLE object on page 5"],
        )
        assert report.completeness_passed is False
        assert report.missing_images_count == 2
        assert report.complex_objects_count == 1
        assert len(report.extraction_gaps) == 2


class TestDocument:
    """Test Document model validation and instantiation."""

    def test_document_valid_creation(self):
        """Test Document instantiation with valid data."""
        metadata = Metadata(
            source_file=Path("doc.pdf"),
            file_hash="hash123",
            processing_timestamp=datetime.now(),
            tool_version="1.0.0",
            config_version="v1",
            document_type="pdf",
        )
        document = Document(
            id="DOC-001",
            text="Document text content",
            metadata=metadata,
        )
        assert document.id == "DOC-001"
        assert document.text == "Document text content"
        assert document.entities == []
        assert document.structure == {}
        assert document.metadata.document_type == "pdf"

    def test_document_with_entities(self):
        """Test Document with embedded entities."""
        metadata = Metadata(
            source_file=Path("doc.pdf"),
            file_hash="hash",
            processing_timestamp=datetime.now(),
            tool_version="1.0.0",
            config_version="v1",
            document_type="pdf",
        )
        entities = [
            Entity(
                type=EntityType.RISK,
                id="R-001",
                text="Risk 1",
                confidence=0.9,
                location={"start": 0, "end": 6},
            ),
            Entity(
                type=EntityType.CONTROL,
                id="C-001",
                text="Control 1",
                confidence=0.85,
                location={"start": 10, "end": 19},
            ),
        ]
        document = Document(
            id="DOC-001",
            text="Document with entities",
            entities=entities,
            metadata=metadata,
        )
        assert len(document.entities) == 2
        assert document.entities[0].type == EntityType.RISK
        assert document.entities[1].type == EntityType.CONTROL

    def test_document_with_structure(self):
        """Test Document with structure metadata."""
        metadata = Metadata(
            source_file=Path("doc.pdf"),
            file_hash="hash",
            processing_timestamp=datetime.now(),
            tool_version="1.0.0",
            config_version="v1",
            document_type="pdf",
        )
        document = Document(
            id="DOC-001",
            text="Structured document",
            metadata=metadata,
            structure={"pages": 10, "sections": ["intro", "body", "conclusion"]},
        )
        assert document.structure["pages"] == 10
        assert len(document.structure["sections"]) == 3

    def test_document_empty_text_valid(self):
        """Test Document with empty text (edge case)."""
        metadata = Metadata(
            source_file=Path("doc.pdf"),
            file_hash="hash",
            processing_timestamp=datetime.now(),
            tool_version="1.0.0",
            config_version="v1",
            document_type="pdf",
        )
        document = Document(id="DOC-001", text="", metadata=metadata)
        assert document.text == ""


class TestChunk:
    """Test Chunk model validation and instantiation."""

    def test_chunk_valid_creation(self):
        """Test Chunk instantiation with valid data."""
        metadata = Metadata(
            source_file=Path("doc.pdf"),
            file_hash="hash",
            processing_timestamp=datetime.now(),
            tool_version="1.0.0",
            config_version="v1",
            document_type="pdf",
        )
        chunk = Chunk(
            id="doc_001",
            text="Chunk text content",
            document_id="DOC-001",
            position_index=0,
            token_count=100,
            word_count=80,
            quality_score=0.85,
            metadata=metadata,
        )
        assert chunk.id == "doc_001"
        assert chunk.text == "Chunk text content"
        assert chunk.document_id == "DOC-001"
        assert chunk.position_index == 0
        assert chunk.token_count == 100
        assert chunk.word_count == 80
        assert chunk.quality_score == 0.85
        assert chunk.entities == []
        assert chunk.section_context == ""
        assert chunk.readability_scores == {}

    def test_chunk_quality_score_boundary_valid(self):
        """Test Chunk quality_score at boundary values (0.0 and 1.0)."""
        metadata = Metadata(
            source_file=Path("doc.pdf"),
            file_hash="hash",
            processing_timestamp=datetime.now(),
            tool_version="1.0.0",
            config_version="v1",
            document_type="pdf",
        )
        chunk_min = Chunk(
            id="doc_001",
            text="Low quality",
            document_id="DOC-001",
            position_index=0,
            token_count=10,
            word_count=8,
            quality_score=0.0,
            metadata=metadata,
        )
        assert chunk_min.quality_score == 0.0

        chunk_max = Chunk(
            id="doc_002",
            text="High quality",
            document_id="DOC-001",
            position_index=1,
            token_count=10,
            word_count=8,
            quality_score=1.0,
            metadata=metadata,
        )
        assert chunk_max.quality_score == 1.0

    def test_chunk_quality_score_below_zero_invalid(self):
        """Test Chunk with quality_score < 0.0 raises ValidationError."""
        metadata = Metadata(
            source_file=Path("doc.pdf"),
            file_hash="hash",
            processing_timestamp=datetime.now(),
            tool_version="1.0.0",
            config_version="v1",
            document_type="pdf",
        )
        with pytest.raises(ValidationError) as exc_info:
            Chunk(
                id="doc_001",
                text="Chunk",
                document_id="DOC-001",
                position_index=0,
                token_count=10,
                word_count=8,
                quality_score=-0.1,
                metadata=metadata,
            )
        assert "greater than or equal to 0" in str(exc_info.value).lower()

    def test_chunk_quality_score_above_one_invalid(self):
        """Test Chunk with quality_score > 1.0 raises ValidationError."""
        metadata = Metadata(
            source_file=Path("doc.pdf"),
            file_hash="hash",
            processing_timestamp=datetime.now(),
            tool_version="1.0.0",
            config_version="v1",
            document_type="pdf",
        )
        with pytest.raises(ValidationError) as exc_info:
            Chunk(
                id="doc_001",
                text="Chunk",
                document_id="DOC-001",
                position_index=0,
                token_count=10,
                word_count=8,
                quality_score=1.5,
                metadata=metadata,
            )
        assert "less than or equal to 1" in str(exc_info.value).lower()

    def test_chunk_with_entities_and_readability(self):
        """Test Chunk with entities and readability scores."""
        metadata = Metadata(
            source_file=Path("doc.pdf"),
            file_hash="hash",
            processing_timestamp=datetime.now(),
            tool_version="1.0.0",
            config_version="v1",
            document_type="pdf",
        )
        entities = [
            Entity(
                type=EntityType.RISK,
                id="R-001",
                text="Risk",
                confidence=0.9,
                location={"start": 0, "end": 4},
            )
        ]
        chunk = Chunk(
            id="doc_001",
            text="Chunk with metrics",
            document_id="DOC-001",
            position_index=0,
            token_count=50,
            word_count=40,
            quality_score=0.9,
            entities=entities,
            section_context="Section 1: Introduction",
            readability_scores={"flesch_reading_ease": 65.0, "grade_level": 8.5},
            metadata=metadata,
        )
        assert len(chunk.entities) == 1
        assert chunk.section_context == "Section 1: Introduction"
        assert chunk.readability_scores["flesch_reading_ease"] == 65.0
        assert chunk.readability_scores["grade_level"] == 8.5

    def test_chunk_position_index_negative_invalid(self):
        """Test Chunk with negative position_index raises ValidationError."""
        metadata = Metadata(
            source_file=Path("doc.pdf"),
            file_hash="hash",
            processing_timestamp=datetime.now(),
            tool_version="1.0.0",
            config_version="v1",
            document_type="pdf",
        )
        with pytest.raises(ValidationError) as exc_info:
            Chunk(
                id="doc_001",
                text="Chunk",
                document_id="DOC-001",
                position_index=-1,
                token_count=10,
                word_count=8,
                quality_score=0.5,
                metadata=metadata,
            )
        assert "greater than or equal to 0" in str(exc_info.value).lower()

    def test_chunk_token_count_negative_invalid(self):
        """Test Chunk with negative token_count raises ValidationError."""
        metadata = Metadata(
            source_file=Path("doc.pdf"),
            file_hash="hash",
            processing_timestamp=datetime.now(),
            tool_version="1.0.0",
            config_version="v1",
            document_type="pdf",
        )
        with pytest.raises(ValidationError) as exc_info:
            Chunk(
                id="doc_001",
                text="Chunk",
                document_id="DOC-001",
                position_index=0,
                token_count=-10,
                word_count=8,
                quality_score=0.5,
                metadata=metadata,
            )
        assert "greater than or equal to 0" in str(exc_info.value).lower()

    def test_chunk_to_dict_with_entity_relationships(self):
        """Test Chunk.to_dict() serializes entity_relationships correctly (Story 3.2)."""
        metadata = Metadata(
            source_file=Path("doc.pdf"),
            file_hash="hash",
            processing_timestamp=datetime.now(),
            tool_version="1.0.0",
            config_version="v1",
            entity_relationships=[("RISK-001", "mitigates", "CTRL-001")],
        )
        chunk = Chunk(
            id="doc_001",
            text="Chunk text",
            document_id="DOC-001",
            position_index=0,
            token_count=10,
            word_count=8,
            quality_score=0.9,
            metadata=metadata,
        )
        chunk_dict = chunk.to_dict()
        # Verify tuple serialized as list (JSON compatible)
        assert "entity_relationships" in chunk_dict["metadata"]
        assert isinstance(chunk_dict["metadata"]["entity_relationships"], list)


class TestProcessingContext:
    """Test ProcessingContext model validation and instantiation."""

    def test_processing_context_valid_creation(self):
        """Test ProcessingContext instantiation with config dict."""
        context = ProcessingContext(
            config={"batch_size": 100, "max_workers": 4},
            metrics={"processed_files": 0, "errors": 0},
        )
        assert context.config["batch_size"] == 100
        assert context.config["max_workers"] == 4
        assert context.metrics["processed_files"] == 0
        assert context.logger is None

    def test_processing_context_with_logger(self):
        """Test ProcessingContext with structlog logger."""
        logger = structlog.get_logger().bind(component="test")
        context = ProcessingContext(
            config={"mode": "batch"},
            logger=logger,
            metrics={},
        )
        assert context.logger is not None
        assert context.config["mode"] == "batch"

    def test_processing_context_empty_config(self):
        """Test ProcessingContext with empty config (edge case)."""
        context = ProcessingContext()
        assert context.config == {}
        assert context.metrics == {}
        assert context.logger is None

    def test_processing_context_metrics_accumulation(self):
        """Test ProcessingContext metrics can be mutated (for accumulation)."""
        context = ProcessingContext(metrics={"count": 0})
        assert context.metrics["count"] == 0

        # Metrics should be mutable for accumulation
        context.metrics["count"] += 1
        assert context.metrics["count"] == 1

        context.metrics["errors"] = 5
        assert context.metrics["errors"] == 5
