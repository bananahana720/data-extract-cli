"""Unit tests for Normalizer orchestrator.

Tests cover:
- Document processing (single text field)
- ProcessingContext integration (config, logger, metrics)
- Error handling (ProcessingError, CriticalError)
- Metadata enrichment with cleaning metrics
- Factory methods for Normalizer creation

Target: >85% coverage for normalizer.py
"""

from datetime import datetime
from pathlib import Path
from unittest.mock import Mock

import pytest
import structlog

from src.data_extract.core.exceptions import ProcessingError
from src.data_extract.core.models import Document, Metadata, ProcessingContext
from src.data_extract.normalize.config import NormalizationConfig
from src.data_extract.normalize.normalizer import Normalizer, NormalizerFactory

pytestmark = [pytest.mark.P1, pytest.mark.unit]


class TestNormalizer:
    """Test Normalizer orchestrator."""

    @pytest.fixture
    def sample_metadata(self, tmp_path: Path) -> Metadata:
        """Create sample metadata for testing."""
        source_file = tmp_path / "test.pdf"
        source_file.write_text("test")

        return Metadata(
            source_file=source_file,
            file_hash="abc123",
            processing_timestamp=datetime.now(),
            tool_version="0.1.0",
            config_version="1.0",
            document_type="pdf",
        )

    @pytest.fixture
    def sample_document(self, sample_metadata: Metadata) -> Document:
        """Create sample document for testing."""
        return Document(
            id="doc1",
            text="Text with ^^^^^ artifacts and   multiple  spaces",
            metadata=sample_metadata,
        )

    @pytest.fixture
    def normalizer(self) -> Normalizer:
        """Create Normalizer with default config."""
        config = NormalizationConfig()
        return Normalizer(config)

    @pytest.fixture
    def processing_context(self) -> ProcessingContext:
        """Create processing context with logger."""
        logger = structlog.get_logger()
        return ProcessingContext(config={}, logger=logger, metrics={})

    def test_normalizer_initialization(self) -> None:
        """Test Normalizer instantiation."""
        config = NormalizationConfig()
        normalizer = Normalizer(config)

        assert normalizer.config == config
        assert normalizer.text_cleaner is not None

    def test_process_document_removes_artifacts(
        self,
        normalizer: Normalizer,
        sample_document: Document,
        processing_context: ProcessingContext,
    ) -> None:
        """Test that process() removes OCR artifacts."""
        result = normalizer.process(sample_document, processing_context)

        assert "^^^^^" not in result.text
        assert result.id == sample_document.id

    def test_process_document_normalizes_whitespace(
        self,
        normalizer: Normalizer,
        sample_document: Document,
        processing_context: ProcessingContext,
    ) -> None:
        """Test that process() normalizes whitespace."""
        result = normalizer.process(sample_document, processing_context)

        assert "  " not in result.text  # Multiple spaces removed

    def test_process_document_preserves_id(
        self,
        normalizer: Normalizer,
        sample_document: Document,
        processing_context: ProcessingContext,
    ) -> None:
        """Test that document ID is preserved."""
        result = normalizer.process(sample_document, processing_context)

        assert result.id == sample_document.id

    def test_process_document_enriches_metadata(
        self,
        normalizer: Normalizer,
        sample_document: Document,
        processing_context: ProcessingContext,
    ) -> None:
        """Test that metadata is enriched with cleaning metrics."""
        result = normalizer.process(sample_document, processing_context)

        # Check quality scores added
        assert "cleaning_artifacts_removed" in result.metadata.quality_scores
        assert "cleaning_length_reduction" in result.metadata.quality_scores

    def test_process_document_updates_context_metrics(
        self,
        normalizer: Normalizer,
        sample_document: Document,
        processing_context: ProcessingContext,
    ) -> None:
        """Test that context metrics are updated."""
        assert processing_context.metrics.get("documents_normalized", 0) == 0

        normalizer.process(sample_document, processing_context)

        assert processing_context.metrics["documents_normalized"] == 1
        assert "total_artifacts_removed" in processing_context.metrics

    def test_process_multiple_documents_accumulates_metrics(
        self,
        normalizer: Normalizer,
        sample_metadata: Metadata,
        processing_context: ProcessingContext,
    ) -> None:
        """Test that metrics accumulate across multiple documents."""
        doc1 = Document(id="doc1", text="Text ^^^^^ with artifacts", metadata=sample_metadata)
        doc2 = Document(id="doc2", text="More ■■■■ noise", metadata=sample_metadata)

        normalizer.process(doc1, processing_context)
        normalizer.process(doc2, processing_context)

        assert processing_context.metrics["documents_normalized"] == 2
        assert processing_context.metrics["total_artifacts_removed"] > 0

    def test_process_document_without_artifacts(
        self,
        normalizer: Normalizer,
        sample_metadata: Metadata,
        processing_context: ProcessingContext,
    ) -> None:
        """Test processing clean document (no artifacts)."""
        clean_doc = Document(
            id="clean1", text="This is perfectly clean text.", metadata=sample_metadata
        )

        result = normalizer.process(clean_doc, processing_context)

        assert result.text == "This is perfectly clean text."
        assert result.metadata.quality_scores["cleaning_artifacts_removed"] == 0.0

    def test_process_document_with_high_artifact_count(
        self,
        normalizer: Normalizer,
        sample_metadata: Metadata,
        processing_context: ProcessingContext,
    ) -> None:
        """Test that high artifact count adds quality flag."""
        dirty_doc = Document(
            id="dirty1",
            text="Text " + ("^^^^^ " * 15) + "with many artifacts",
            metadata=sample_metadata,
        )

        result = normalizer.process(dirty_doc, processing_context)

        assert "high_ocr_artifact_count" in result.metadata.quality_flags

    def test_process_empty_document(
        self,
        normalizer: Normalizer,
        sample_metadata: Metadata,
        processing_context: ProcessingContext,
    ) -> None:
        """Test processing empty document."""
        empty_doc = Document(id="empty1", text="", metadata=sample_metadata)

        result = normalizer.process(empty_doc, processing_context)

        assert result.text == ""
        assert result.id == "empty1"

    def test_process_document_with_doc_type(
        self,
        normalizer: Normalizer,
        sample_metadata: Metadata,
        processing_context: ProcessingContext,
    ) -> None:
        """Test that document type is passed to TextCleaner."""
        doc = Document(id="doc1", text="Text with noise", metadata=sample_metadata)

        # Document type comes from metadata
        assert doc.metadata.document_type == "pdf"

        result = normalizer.process(doc, processing_context)

        # Should process successfully
        assert result.id == doc.id

    def test_process_without_logger_uses_fallback(
        self, normalizer: Normalizer, sample_document: Document
    ) -> None:
        """Test that Normalizer works without logger in context."""
        context = ProcessingContext(config={}, logger=None, metrics={})

        result = normalizer.process(sample_document, context)

        # Should still process successfully
        assert result.id == sample_document.id

    def test_process_document_length_reduction(
        self,
        normalizer: Normalizer,
        sample_document: Document,
        processing_context: ProcessingContext,
    ) -> None:
        """Test that length reduction is tracked."""
        original_length = len(sample_document.text)

        result = normalizer.process(sample_document, processing_context)

        cleaned_length = len(result.text)
        expected_reduction = original_length - cleaned_length

        assert result.metadata.quality_scores["cleaning_length_reduction"] == float(
            expected_reduction
        )

    def test_process_preserves_original_metadata_fields(
        self,
        normalizer: Normalizer,
        sample_document: Document,
        processing_context: ProcessingContext,
    ) -> None:
        """Test that original metadata fields are preserved."""
        result = normalizer.process(sample_document, processing_context)

        assert result.metadata.source_file == sample_document.metadata.source_file
        assert result.metadata.file_hash == sample_document.metadata.file_hash
        assert result.metadata.tool_version == sample_document.metadata.tool_version


class TestNormalizerErrorHandling:
    """Test Normalizer error handling."""

    @pytest.fixture
    def sample_metadata(self, tmp_path: Path) -> Metadata:
        """Create sample metadata for testing."""
        source_file = tmp_path / "test.pdf"
        source_file.write_text("test")

        return Metadata(
            source_file=source_file,
            file_hash="abc123",
            processing_timestamp=datetime.now(),
            tool_version="0.1.0",
            config_version="1.0",
            document_type="pdf",
        )

    def test_process_handles_unexpected_errors(self, sample_metadata: Metadata) -> None:
        """Test that unexpected errors are wrapped in ProcessingError."""
        config = NormalizationConfig()
        normalizer = Normalizer(config)

        # Create document with problematic data
        doc = Document(id="bad1", text="Text", metadata=sample_metadata)

        # Mock TextCleaner to raise exception
        normalizer.text_cleaner = Mock()
        normalizer.text_cleaner.clean_text = Mock(side_effect=ValueError("Test error"))

        context = ProcessingContext(config={}, logger=structlog.get_logger(), metrics={})

        with pytest.raises(ProcessingError, match="Text cleaning failed"):
            normalizer.process(doc, context)


class TestNormalizerFactory:
    """Test NormalizerFactory convenience methods."""

    def test_create_default(self) -> None:
        """Test creating normalizer with default config."""
        normalizer = NormalizerFactory.create_default()

        assert isinstance(normalizer, Normalizer)
        assert normalizer.config.remove_ocr_artifacts is True
        assert normalizer.config.remove_headers_footers is True

    def test_create_with_custom_config(self) -> None:
        """Test creating normalizer with custom config."""
        config = NormalizationConfig(remove_ocr_artifacts=False, header_repetition_threshold=5)

        normalizer = NormalizerFactory.create(config)

        assert isinstance(normalizer, Normalizer)
        assert normalizer.config.remove_ocr_artifacts is False
        assert normalizer.config.header_repetition_threshold == 5

    def test_create_from_yaml(self, tmp_path: Path) -> None:
        """Test creating normalizer from YAML file."""
        yaml_file = tmp_path / "config.yaml"
        yaml_content = """
remove_ocr_artifacts: false
header_repetition_threshold: 7
whitespace_max_consecutive_newlines: 3
"""
        yaml_file.write_text(yaml_content)

        normalizer = NormalizerFactory.create_from_yaml(str(yaml_file))

        assert isinstance(normalizer, Normalizer)
        assert normalizer.config.remove_ocr_artifacts is False
        assert normalizer.config.header_repetition_threshold == 7
        assert normalizer.config.whitespace_max_consecutive_newlines == 3


class TestNormalizerIntegration:
    """Integration tests for Normalizer with real workflow."""

    @pytest.fixture
    def sample_metadata(self, tmp_path: Path) -> Metadata:
        """Create sample metadata for testing."""
        source_file = tmp_path / "test.pdf"
        source_file.write_text("test")

        return Metadata(
            source_file=source_file,
            file_hash="abc123",
            processing_timestamp=datetime.now(),
            tool_version="0.1.0",
            config_version="1.0",
            document_type="pdf",
        )

    def test_full_normalization_workflow(self, sample_metadata: Metadata) -> None:
        """Test complete normalization workflow with realistic document."""
        # Create document with multiple issues
        doc = Document(
            id="test1",
            text="Doc ^^^^^ with   multiple  issues\n\n\n\nand ■■■■ noise __________",
            metadata=sample_metadata,
        )

        # Create normalizer and context
        normalizer = NormalizerFactory.create_default()
        context = ProcessingContext(config={}, logger=structlog.get_logger(), metrics={})

        # Process document
        result = normalizer.process(doc, context)

        # Verify cleaning
        assert "^^^^^" not in result.text
        assert "■■■■" not in result.text
        assert "__________" not in result.text
        assert "  " not in result.text  # Multiple spaces removed

        # Verify metadata
        assert result.metadata.quality_scores["cleaning_artifacts_removed"] > 0
        assert "cleaning_length_reduction" in result.metadata.quality_scores

        # Verify context metrics
        assert context.metrics["documents_normalized"] == 1
        assert context.metrics["total_artifacts_removed"] > 0

    def test_pipeline_stage_protocol_compliance(self, sample_metadata: Metadata) -> None:
        """Test that Normalizer implements PipelineStage protocol."""
        doc = Document(id="test1", text="Test text", metadata=sample_metadata)
        normalizer = NormalizerFactory.create_default()
        context = ProcessingContext(config={}, logger=structlog.get_logger(), metrics={})

        # Should have process() method
        assert hasattr(normalizer, "process")
        assert callable(normalizer.process)

        # process() should accept Document and ProcessingContext
        result = normalizer.process(doc, context)

        # process() should return Document
        assert isinstance(result, Document)
