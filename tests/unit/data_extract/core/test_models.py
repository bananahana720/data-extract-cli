"""Tests for core.models module.

Comprehensive tests for all 13 classes/enums in models.py:
- Enums: ContentType, EntityType, DocumentType, QualityFlag
- Frozen models: Position, Entity, Metadata
- Mutable models: ContentBlock, ValidationReport, Document, Chunk, ProcessingResult, ProcessingContext
"""

from datetime import datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from src.data_extract.core.models import (
    Chunk,
    ContentBlock,
    ContentType,
    Document,
    DocumentType,
    Entity,
    EntityType,
    Metadata,
    Position,
    ProcessingContext,
    ProcessingResult,
    QualityFlag,
    ValidationReport,
)

pytestmark = [pytest.mark.P0, pytest.mark.unit]


# ============================================================================
# Enum Completeness Tests
# ============================================================================


class TestEnumCompleteness:
    """Test that all enum values exist and are correct."""

    def test_content_type_enum_has_all_values(self) -> None:
        """Verify ContentType enum has all 7 expected values."""
        expected_values = {"heading", "paragraph", "table", "list", "image", "code", "unknown"}
        actual_values = {ct.value for ct in ContentType}
        assert actual_values == expected_values

    def test_entity_type_enum_has_all_values(self) -> None:
        """Verify EntityType enum has all 6 expected values."""
        expected_values = {"process", "risk", "control", "regulation", "policy", "issue"}
        actual_values = {et.value for et in EntityType}
        assert actual_values == expected_values

    def test_document_type_enum_has_all_values(self) -> None:
        """Verify DocumentType enum has all 4 expected values."""
        expected_values = {"report", "matrix", "export", "image"}
        actual_values = {dt.value for dt in DocumentType}
        assert actual_values == expected_values

    def test_quality_flag_enum_has_all_values(self) -> None:
        """Verify QualityFlag enum has all 4 expected values."""
        expected_values = {
            "low_ocr_confidence",
            "missing_images",
            "incomplete_extraction",
            "complex_objects",
        }
        actual_values = {qf.value for qf in QualityFlag}
        assert actual_values == expected_values


# ============================================================================
# Frozen Model Immutability Tests
# ============================================================================


class TestFrozenModelImmutability:
    """Test that frozen models cannot be modified after creation."""

    def test_position_is_frozen(self) -> None:
        """Verify Position model is frozen and cannot be modified."""
        position = Position(page=1, sequence_index=0)

        with pytest.raises(ValidationError, match="frozen"):
            position.page = 2  # type: ignore

    def test_entity_is_frozen(self) -> None:
        """Verify Entity model is frozen and cannot be modified."""
        entity = Entity(
            type=EntityType.RISK,
            id="RISK-001",
            text="High risk of data breach",
            confidence=0.95,
            location={"start": 0, "end": 25},
        )

        with pytest.raises(ValidationError, match="frozen"):
            entity.confidence = 0.99  # type: ignore

    def test_metadata_is_frozen(self) -> None:
        """Verify Metadata model is frozen and cannot be modified."""
        metadata = Metadata(
            source_file=Path("/docs/report.pdf"),
            file_hash="abc123",
            processing_timestamp=datetime.now(),
            tool_version="1.0.0",
            config_version="v1",
        )

        with pytest.raises(ValidationError, match="frozen"):
            metadata.tool_version = "2.0.0"  # type: ignore


# ============================================================================
# Field Validation Tests
# ============================================================================


class TestFieldValidation:
    """Test field validators and constraints."""

    @pytest.mark.parametrize("confidence", [0.0, 0.5, 1.0])
    def test_entity_confidence_accepts_valid_range(self, confidence: float) -> None:
        """Verify Entity confidence accepts values in [0.0, 1.0]."""
        entity = Entity(
            type=EntityType.CONTROL,
            id="CTRL-042",
            text="Access control policy",
            confidence=confidence,
            location={"start": 0, "end": 22},
        )
        assert entity.confidence == confidence

    @pytest.mark.parametrize("confidence", [-0.1, 1.1, 2.0])
    def test_entity_confidence_rejects_invalid_range(self, confidence: float) -> None:
        """Verify Entity confidence rejects values outside [0.0, 1.0]."""
        with pytest.raises(ValidationError):
            Entity(
                type=EntityType.CONTROL,
                id="CTRL-042",
                text="Access control policy",
                confidence=confidence,
                location={"start": 0, "end": 22},
            )

    @pytest.mark.parametrize("completeness_ratio", [0.0, 0.5, 1.0])
    def test_metadata_completeness_ratio_accepts_valid_range(
        self, completeness_ratio: float
    ) -> None:
        """Verify Metadata completeness_ratio accepts values in [0.0, 1.0]."""
        metadata = Metadata(
            source_file=Path("/docs/report.pdf"),
            file_hash="abc123",
            processing_timestamp=datetime.now(),
            tool_version="1.0.0",
            config_version="v1",
            completeness_ratio=completeness_ratio,
        )
        assert metadata.completeness_ratio == completeness_ratio

    @pytest.mark.parametrize("completeness_ratio", [-0.1, 1.1])
    def test_metadata_completeness_ratio_rejects_invalid_range(
        self, completeness_ratio: float
    ) -> None:
        """Verify Metadata completeness_ratio rejects values outside [0.0, 1.0]."""
        with pytest.raises(ValidationError):
            Metadata(
                source_file=Path("/docs/report.pdf"),
                file_hash="abc123",
                processing_timestamp=datetime.now(),
                tool_version="1.0.0",
                config_version="v1",
                completeness_ratio=completeness_ratio,
            )

    @pytest.mark.parametrize("avg_confidence", [0.0, 0.95, 1.0])
    def test_validation_report_average_confidence_accepts_valid_range(
        self, avg_confidence: float
    ) -> None:
        """Verify ValidationReport document_average_confidence accepts values in [0.0, 1.0]."""
        report = ValidationReport(
            quarantine_recommended=False,
            document_average_confidence=avg_confidence,
        )
        assert report.document_average_confidence == avg_confidence

    @pytest.mark.parametrize("avg_confidence", [-0.1, 1.1])
    def test_validation_report_average_confidence_rejects_invalid_range(
        self, avg_confidence: float
    ) -> None:
        """Verify ValidationReport document_average_confidence rejects values outside [0.0, 1.0]."""
        with pytest.raises(ValidationError):
            ValidationReport(
                quarantine_recommended=False,
                document_average_confidence=avg_confidence,
            )

    @pytest.mark.parametrize("position_index", [0, 5, 100])
    def test_chunk_position_index_accepts_non_negative(self, position_index: int) -> None:
        """Verify Chunk position_index accepts non-negative integers."""
        metadata = Metadata(
            source_file=Path("/docs/report.pdf"),
            file_hash="abc123",
            processing_timestamp=datetime.now(),
            tool_version="1.0.0",
            config_version="v1",
        )
        chunk = Chunk(
            id="doc_001",
            text="Sample chunk text",
            document_id="doc_id",
            position_index=position_index,
            token_count=10,
            word_count=3,
            quality_score=0.9,
            metadata=metadata,
        )
        assert chunk.position_index == position_index

    def test_chunk_position_index_rejects_negative(self) -> None:
        """Verify Chunk position_index rejects negative values."""
        metadata = Metadata(
            source_file=Path("/docs/report.pdf"),
            file_hash="abc123",
            processing_timestamp=datetime.now(),
            tool_version="1.0.0",
            config_version="v1",
        )
        with pytest.raises(ValidationError):
            Chunk(
                id="doc_001",
                text="Sample chunk text",
                document_id="doc_id",
                position_index=-1,
                token_count=10,
                word_count=3,
                quality_score=0.9,
                metadata=metadata,
            )

    @pytest.mark.parametrize("quality_score", [0.0, 0.5, 1.0])
    def test_chunk_quality_score_accepts_valid_range(self, quality_score: float) -> None:
        """Verify Chunk quality_score accepts values in [0.0, 1.0]."""
        metadata = Metadata(
            source_file=Path("/docs/report.pdf"),
            file_hash="abc123",
            processing_timestamp=datetime.now(),
            tool_version="1.0.0",
            config_version="v1",
        )
        chunk = Chunk(
            id="doc_001",
            text="Sample chunk text",
            document_id="doc_id",
            position_index=0,
            token_count=10,
            word_count=3,
            quality_score=quality_score,
            metadata=metadata,
        )
        assert chunk.quality_score == quality_score

    @pytest.mark.parametrize("quality_score", [-0.1, 1.1])
    def test_chunk_quality_score_rejects_invalid_range(self, quality_score: float) -> None:
        """Verify Chunk quality_score rejects values outside [0.0, 1.0]."""
        metadata = Metadata(
            source_file=Path("/docs/report.pdf"),
            file_hash="abc123",
            processing_timestamp=datetime.now(),
            tool_version="1.0.0",
            config_version="v1",
        )
        with pytest.raises(ValidationError):
            Chunk(
                id="doc_001",
                text="Sample chunk text",
                document_id="doc_id",
                position_index=0,
                token_count=10,
                word_count=3,
                quality_score=quality_score,
                metadata=metadata,
            )

    @pytest.mark.parametrize("count", [0, 5, 100])
    def test_validation_report_counts_accept_non_negative(self, count: int) -> None:
        """Verify ValidationReport counts accept non-negative integers."""
        report = ValidationReport(
            quarantine_recommended=False,
            missing_images_count=count,
            complex_objects_count=count,
        )
        assert report.missing_images_count == count
        assert report.complex_objects_count == count

    def test_validation_report_counts_reject_negative(self) -> None:
        """Verify ValidationReport counts reject negative values."""
        with pytest.raises(ValidationError):
            ValidationReport(
                quarantine_recommended=False,
                missing_images_count=-1,
            )

        with pytest.raises(ValidationError):
            ValidationReport(
                quarantine_recommended=False,
                complex_objects_count=-1,
            )


# ============================================================================
# Metadata Validator Tests
# ============================================================================


class TestMetadataValidators:
    """Test Metadata field validators."""

    def test_document_type_accepts_enum(self) -> None:
        """Verify document_type validator accepts DocumentType enum."""
        metadata = Metadata(
            source_file=Path("/docs/report.pdf"),
            file_hash="abc123",
            processing_timestamp=datetime.now(),
            tool_version="1.0.0",
            config_version="v1",
            document_type=DocumentType.REPORT,
        )
        assert metadata.document_type == DocumentType.REPORT

    def test_document_type_accepts_string_for_legacy_support(self) -> None:
        """Verify document_type validator accepts string for backwards compatibility."""
        metadata = Metadata(
            source_file=Path("/docs/report.pdf"),
            file_hash="abc123",
            processing_timestamp=datetime.now(),
            tool_version="1.0.0",
            config_version="v1",
            document_type="custom_type",  # type: ignore
        )
        assert metadata.document_type == "custom_type"

    def test_document_type_accepts_none(self) -> None:
        """Verify document_type validator accepts None."""
        metadata = Metadata(
            source_file=Path("/docs/report.pdf"),
            file_hash="abc123",
            processing_timestamp=datetime.now(),
            tool_version="1.0.0",
            config_version="v1",
            document_type=None,
        )
        assert metadata.document_type is None


# ============================================================================
# Chunk Serialization Tests
# ============================================================================


class TestChunkSerialization:
    """Test Chunk.to_dict() method for JSON serialization."""

    def test_chunk_to_dict_basic(self) -> None:
        """Verify Chunk.to_dict() produces valid dictionary."""
        metadata = Metadata(
            source_file=Path("/docs/report.pdf"),
            file_hash="abc123",
            processing_timestamp=datetime(2025, 11, 30, 12, 0, 0),
            tool_version="1.0.0",
            config_version="v1",
        )
        chunk = Chunk(
            id="doc_001",
            text="Sample chunk text",
            document_id="doc_id",
            position_index=0,
            token_count=10,
            word_count=3,
            quality_score=0.9,
            metadata=metadata,
        )

        result = chunk.to_dict()

        assert isinstance(result, dict)
        assert result["id"] == "doc_001"
        assert result["text"] == "Sample chunk text"
        assert result["document_id"] == "doc_id"
        assert result["position_index"] == 0

    def test_chunk_to_dict_serializes_path_to_string(self) -> None:
        """Verify Chunk.to_dict() converts Path to string."""
        metadata = Metadata(
            source_file=Path("/docs/report.pdf"),
            file_hash="abc123",
            processing_timestamp=datetime.now(),
            tool_version="1.0.0",
            config_version="v1",
        )
        chunk = Chunk(
            id="doc_001",
            text="Sample chunk",
            document_id="doc_id",
            position_index=0,
            token_count=5,
            word_count=2,
            quality_score=0.9,
            metadata=metadata,
        )

        result = chunk.to_dict()

        # Path should be serialized to string
        assert isinstance(result["metadata"]["source_file"], str)
        assert result["metadata"]["source_file"] == "/docs/report.pdf"

    def test_chunk_to_dict_serializes_datetime_to_isoformat(self) -> None:
        """Verify Chunk.to_dict() converts datetime to ISO format string."""
        test_timestamp = datetime(2025, 11, 30, 12, 0, 0)
        metadata = Metadata(
            source_file=Path("/docs/report.pdf"),
            file_hash="abc123",
            processing_timestamp=test_timestamp,
            tool_version="1.0.0",
            config_version="v1",
        )
        chunk = Chunk(
            id="doc_001",
            text="Sample chunk",
            document_id="doc_id",
            position_index=0,
            token_count=5,
            word_count=2,
            quality_score=0.9,
            metadata=metadata,
        )

        result = chunk.to_dict()

        # Datetime should be serialized to ISO format
        assert isinstance(result["metadata"]["processing_timestamp"], str)
        assert result["metadata"]["processing_timestamp"] == test_timestamp.isoformat()

    def test_chunk_to_dict_serializes_enum_to_value(self) -> None:
        """Verify Chunk.to_dict() converts enum to value string."""
        metadata = Metadata(
            source_file=Path("/docs/report.pdf"),
            file_hash="abc123",
            processing_timestamp=datetime.now(),
            tool_version="1.0.0",
            config_version="v1",
            document_type=DocumentType.REPORT,
        )
        chunk = Chunk(
            id="doc_001",
            text="Sample chunk",
            document_id="doc_id",
            position_index=0,
            token_count=5,
            word_count=2,
            quality_score=0.9,
            metadata=metadata,
        )

        result = chunk.to_dict()

        # Enum should be serialized to value
        assert result["metadata"]["document_type"] == "report"

    def test_chunk_to_dict_with_entities(self) -> None:
        """Verify Chunk.to_dict() handles entities list correctly."""
        metadata = Metadata(
            source_file=Path("/docs/report.pdf"),
            file_hash="abc123",
            processing_timestamp=datetime.now(),
            tool_version="1.0.0",
            config_version="v1",
        )
        entity = Entity(
            type=EntityType.RISK,
            id="RISK-001",
            text="Data breach risk",
            confidence=0.95,
            location={"start": 0, "end": 16},
        )
        chunk = Chunk(
            id="doc_001",
            text="Data breach risk",
            document_id="doc_id",
            position_index=0,
            token_count=5,
            word_count=3,
            quality_score=0.9,
            entities=[entity],
            metadata=metadata,
        )

        result = chunk.to_dict()

        # Entities should be serialized
        assert len(result["entities"]) == 1
        assert result["entities"][0]["type"] == "risk"
        assert result["entities"][0]["id"] == "RISK-001"


# ============================================================================
# Edge Case Tests
# ============================================================================


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_content_block_with_empty_content(self) -> None:
        """Verify ContentBlock accepts empty content string."""
        position = Position(page=1, sequence_index=0)
        block = ContentBlock(
            block_type=ContentType.PARAGRAPH,
            content="",
            position=position,
        )
        assert block.content == ""

    def test_content_block_with_empty_metadata(self) -> None:
        """Verify ContentBlock metadata defaults to empty dict."""
        position = Position(page=1, sequence_index=0)
        block = ContentBlock(
            block_type=ContentType.PARAGRAPH,
            content="Sample text",
            position=position,
        )
        assert block.metadata == {}

    def test_metadata_with_empty_quality_scores(self) -> None:
        """Verify Metadata quality_scores defaults to empty dict."""
        metadata = Metadata(
            source_file=Path("/docs/report.pdf"),
            file_hash="abc123",
            processing_timestamp=datetime.now(),
            tool_version="1.0.0",
            config_version="v1",
        )
        assert metadata.quality_scores == {}

    def test_metadata_with_empty_quality_flags(self) -> None:
        """Verify Metadata quality_flags defaults to empty list."""
        metadata = Metadata(
            source_file=Path("/docs/report.pdf"),
            file_hash="abc123",
            processing_timestamp=datetime.now(),
            tool_version="1.0.0",
            config_version="v1",
        )
        assert metadata.quality_flags == []

    def test_validation_report_with_empty_confidence_scores(self) -> None:
        """Verify ValidationReport confidence_scores defaults to empty dict."""
        report = ValidationReport(quarantine_recommended=False)
        assert report.confidence_scores == {}

    def test_validation_report_with_empty_quality_flags(self) -> None:
        """Verify ValidationReport quality_flags defaults to empty list."""
        report = ValidationReport(quarantine_recommended=False)
        assert report.quality_flags == []

    def test_document_with_empty_entities(self) -> None:
        """Verify Document entities defaults to empty list."""
        metadata = Metadata(
            source_file=Path("/docs/report.pdf"),
            file_hash="abc123",
            processing_timestamp=datetime.now(),
            tool_version="1.0.0",
            config_version="v1",
        )
        document = Document(
            id="doc_001",
            text="Sample text",
            metadata=metadata,
        )
        assert document.entities == []

    def test_document_with_empty_structure(self) -> None:
        """Verify Document structure defaults to empty dict."""
        metadata = Metadata(
            source_file=Path("/docs/report.pdf"),
            file_hash="abc123",
            processing_timestamp=datetime.now(),
            tool_version="1.0.0",
            config_version="v1",
        )
        document = Document(
            id="doc_001",
            text="Sample text",
            metadata=metadata,
        )
        assert document.structure == {}

    def test_chunk_with_empty_section_context(self) -> None:
        """Verify Chunk section_context defaults to empty string."""
        metadata = Metadata(
            source_file=Path("/docs/report.pdf"),
            file_hash="abc123",
            processing_timestamp=datetime.now(),
            tool_version="1.0.0",
            config_version="v1",
        )
        chunk = Chunk(
            id="doc_001",
            text="Sample chunk",
            document_id="doc_id",
            position_index=0,
            token_count=5,
            word_count=2,
            quality_score=0.9,
            metadata=metadata,
        )
        assert chunk.section_context == ""

    def test_chunk_with_empty_readability_scores(self) -> None:
        """Verify Chunk readability_scores defaults to empty dict."""
        metadata = Metadata(
            source_file=Path("/docs/report.pdf"),
            file_hash="abc123",
            processing_timestamp=datetime.now(),
            tool_version="1.0.0",
            config_version="v1",
        )
        chunk = Chunk(
            id="doc_001",
            text="Sample chunk",
            document_id="doc_id",
            position_index=0,
            token_count=5,
            word_count=2,
            quality_score=0.9,
            metadata=metadata,
        )
        assert chunk.readability_scores == {}

    def test_processing_result_with_empty_content_blocks(self) -> None:
        """Verify ProcessingResult content_blocks defaults to empty list."""
        metadata = Metadata(
            source_file=Path("/docs/report.pdf"),
            file_hash="abc123",
            processing_timestamp=datetime.now(),
            tool_version="1.0.0",
            config_version="v1",
        )
        result = ProcessingResult(
            file_path=Path("/docs/report.pdf"),
            document_type=DocumentType.REPORT,
            metadata=metadata,
        )
        assert result.content_blocks == []

    def test_processing_context_with_empty_config(self) -> None:
        """Verify ProcessingContext config defaults to empty dict."""
        context = ProcessingContext()
        assert context.config == {}

    def test_processing_context_with_empty_metrics(self) -> None:
        """Verify ProcessingContext metrics defaults to empty dict."""
        context = ProcessingContext()
        assert context.metrics == {}

    def test_processing_context_with_none_logger(self) -> None:
        """Verify ProcessingContext logger defaults to None."""
        context = ProcessingContext()
        assert context.logger is None


# ============================================================================
# Integration Tests (Model Composition)
# ============================================================================


class TestModelComposition:
    """Test that models compose correctly."""

    def test_content_block_with_position(self) -> None:
        """Verify ContentBlock correctly embeds Position model."""
        position = Position(page=5, sequence_index=10)
        block = ContentBlock(
            block_type=ContentType.TABLE,
            content="| Header | Value |",
            position=position,
        )
        assert block.position.page == 5
        assert block.position.sequence_index == 10

    def test_document_with_entities_and_metadata(self) -> None:
        """Verify Document correctly embeds Entity and Metadata models."""
        metadata = Metadata(
            source_file=Path("/docs/report.pdf"),
            file_hash="abc123",
            processing_timestamp=datetime.now(),
            tool_version="1.0.0",
            config_version="v1",
        )
        entity = Entity(
            type=EntityType.CONTROL,
            id="CTRL-042",
            text="Access control",
            confidence=0.98,
            location={"start": 0, "end": 14},
        )
        document = Document(
            id="doc_001",
            text="Access control policy document",
            entities=[entity],
            metadata=metadata,
        )

        assert len(document.entities) == 1
        assert document.entities[0].id == "CTRL-042"
        assert document.metadata.tool_version == "1.0.0"

    def test_chunk_with_entities_and_metadata(self) -> None:
        """Verify Chunk correctly embeds Entity and Metadata models."""
        metadata = Metadata(
            source_file=Path("/docs/report.pdf"),
            file_hash="abc123",
            processing_timestamp=datetime.now(),
            tool_version="1.0.0",
            config_version="v1",
        )
        entity = Entity(
            type=EntityType.ISSUE,
            id="ISSUE-007",
            text="Compliance gap",
            confidence=0.92,
            location={"start": 0, "end": 14},
        )
        chunk = Chunk(
            id="doc_001",
            text="Compliance gap identified",
            document_id="doc_id",
            position_index=0,
            token_count=10,
            word_count=3,
            quality_score=0.88,
            entities=[entity],
            metadata=metadata,
        )

        assert len(chunk.entities) == 1
        assert chunk.entities[0].type == EntityType.ISSUE
        assert chunk.metadata.source_file == Path("/docs/report.pdf")

    def test_processing_result_with_content_blocks_and_entities(self) -> None:
        """Verify ProcessingResult correctly embeds ContentBlock, Entity, and Metadata."""
        metadata = Metadata(
            source_file=Path("/docs/report.pdf"),
            file_hash="abc123",
            processing_timestamp=datetime.now(),
            tool_version="1.0.0",
            config_version="v1",
        )
        position = Position(page=1, sequence_index=0)
        block = ContentBlock(
            block_type=ContentType.HEADING,
            content="Risk Assessment",
            position=position,
        )
        entity = Entity(
            type=EntityType.RISK,
            id="RISK-123",
            text="Financial risk",
            confidence=0.97,
            location={"start": 0, "end": 14},
        )
        result = ProcessingResult(
            file_path=Path("/docs/report.pdf"),
            document_type=DocumentType.REPORT,
            content_blocks=[block],
            entities=[entity],
            metadata=metadata,
        )

        assert len(result.content_blocks) == 1
        assert result.content_blocks[0].block_type == ContentType.HEADING
        assert len(result.entities) == 1
        assert result.entities[0].type == EntityType.RISK

    def test_validation_report_with_quality_flags(self) -> None:
        """Verify ValidationReport correctly embeds QualityFlag enum values."""
        report = ValidationReport(
            quarantine_recommended=True,
            quality_flags=[QualityFlag.LOW_OCR_CONFIDENCE, QualityFlag.MISSING_IMAGES],
            document_average_confidence=0.82,
        )

        assert len(report.quality_flags) == 2
        assert QualityFlag.LOW_OCR_CONFIDENCE in report.quality_flags
        assert QualityFlag.MISSING_IMAGES in report.quality_flags
        assert report.quarantine_recommended is True
