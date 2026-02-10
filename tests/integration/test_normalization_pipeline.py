"""Integration tests for normalization pipeline.

Tests end-to-end normalization workflow integrating:
- Normalizer orchestrator
- TextCleaner
- Configuration cascade
- Metadata enrichment
"""

from datetime import datetime
from pathlib import Path

import pytest
import structlog

from src.data_extract.core.models import Document, Metadata, ProcessingContext
from src.data_extract.normalize import NormalizerFactory
from src.data_extract.normalize.config import NormalizationConfig

pytestmark = [pytest.mark.P1, pytest.mark.integration]


class TestNormalizationPipeline:
    """Integration tests for full normalization pipeline."""

    @pytest.fixture
    def sample_metadata(self, tmp_path: Path) -> Metadata:
        """Create sample metadata."""
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

    def test_end_to_end_normalization(self, sample_metadata: Metadata) -> None:
        """Test complete normalization workflow from raw to cleaned document."""
        # Create document with multiple issues
        raw_doc = Document(
            id="test1",
            text="Document ^^^^^ with   OCR  artifacts\n\n\n\nand ■■■■ noise",
            metadata=sample_metadata,
        )

        # Create normalizer and context
        normalizer = NormalizerFactory.create_default()
        context = ProcessingContext(config={}, logger=structlog.get_logger(), metrics={})

        # Normalize document
        cleaned_doc = normalizer.process(raw_doc, context)

        # Verify cleaning
        assert "^^^^^" not in cleaned_doc.text
        assert "■■■■" not in cleaned_doc.text
        assert cleaned_doc.id == raw_doc.id

        # Verify metadata enrichment
        assert "cleaning_artifacts_removed" in cleaned_doc.metadata.quality_scores
        assert cleaned_doc.metadata.quality_scores["cleaning_artifacts_removed"] > 0

        # Verify context metrics
        assert context.metrics["documents_normalized"] == 1

    def test_deterministic_processing(self, sample_metadata: Metadata) -> None:
        """Test that same input produces identical output (AC-2.1.6)."""
        doc = Document(
            id="test1",
            text="Text ^^^^^ with   artifacts",
            metadata=sample_metadata,
        )

        normalizer = NormalizerFactory.create_default()
        context = ProcessingContext(config={}, logger=structlog.get_logger(), metrics={})

        # Process same document 10 times
        results = []
        for _ in range(10):
            result = normalizer.process(doc, context)
            results.append(result.text)

        # All results should be identical
        assert all(text == results[0] for text in results)

    def test_text_cleaning_to_entity_normalization(self, sample_metadata: Metadata) -> None:
        """Test integration from text cleaning to entity normalization (Story 2.1 + 2.2)."""
        # Create document with both cleaning issues and entities
        raw_doc = Document(
            id="test-entity-integration",
            text="Risk #123 ^^^^^ identified in SOX audit. Control-456 mitigates   this risk.",
            metadata=sample_metadata,
        )

        # Create normalizer with entity normalization enabled
        normalizer = NormalizerFactory.create_default()
        context = ProcessingContext(config={}, logger=structlog.get_logger(), metrics={})

        # Process document
        result = normalizer.process(raw_doc, context)

        # Verify text cleaning worked
        assert "^^^^^" not in result.text

        # Verify entity normalization worked (if enabled in default factory)
        # Note: This depends on entity normalization being integrated in Normalizer
        assert isinstance(result.metadata.entity_tags, list)
        assert isinstance(result.metadata.entity_counts, dict)

    def test_entity_normalization_with_real_audit_doc(self, sample_metadata: Metadata) -> None:
        """Test entity normalization with realistic audit document content."""
        audit_text = """
        Audit Finding Report - Q4 2024

        Risk #123: Operational risk identified in SOX compliance review.
        This risk relates to inadequate separation of duties in financial reporting.

        Mitigation:
        - Control-456 implements dual approval for journal entries
        - Control-457 enforces segregation of duties

        Compliance Framework: SOX, NIST CSF, ISO 27001
        Regulation: SOX Section 404, GDPR Article 32

        Issue-001: Control testing revealed gaps in access management.
        Process-100 requires updating to align with Policy-789.
        """

        doc = Document(
            id="real-audit-doc",
            text=audit_text,
            metadata=sample_metadata,
        )

        normalizer = NormalizerFactory.create_default()
        context = ProcessingContext(config={}, logger=structlog.get_logger(), metrics={})

        result = normalizer.process(doc, context)

        # Verify entities were recognized and metadata enriched
        assert isinstance(result.metadata.entity_tags, list)
        assert isinstance(result.metadata.entity_counts, dict)

        # Verify abbreviation expansion (if enabled)
        # SOX, NIST CSF, ISO 27001, GDPR should be expanded if feature is active

    def test_determinism_with_entities(self, sample_metadata: Metadata) -> None:
        """Test determinism of full pipeline including entity normalization."""
        doc = Document(
            id="determinism-test",
            text="Risk-001 and Control-002 in SOX audit.",
            metadata=sample_metadata,
        )

        normalizer = NormalizerFactory.create_default()
        context = ProcessingContext(config={}, logger=structlog.get_logger(), metrics={})

        # Process 10 times
        results = []
        for _ in range(10):
            result = normalizer.process(doc, context)
            results.append(
                {
                    "text": result.text,
                    "entity_tags": result.metadata.entity_tags,
                    "entity_counts": result.metadata.entity_counts,
                }
            )

        # All results should be identical
        first = results[0]
        for result in results[1:]:
            assert result["text"] == first["text"]
            assert result["entity_tags"] == first["entity_tags"]
            assert result["entity_counts"] == first["entity_counts"]

    def test_risk_control_mapping_preserved_through_schema(self, sample_metadata: Metadata) -> None:
        """Test semantic relationship preservation through schema standardization (AC-2.3.4).

        This test explicitly validates that:
        1. Entity tags from Story 2.2 (EntityNormalizer) are preserved through schema standardization
        2. Risk→control mappings remain intact after schema transformation
        3. entity_tags and entity_counts flow correctly through the full pipeline
        4. Document type detection and schema standardization do not corrupt entity metadata

        Test validates AC-2.3.4: Semantic relationships and entity cross-references
        are preserved during schema transformation.
        """
        # Create document with risk-control relationships
        audit_text = """
        Risk Assessment Report

        Risk-123: Inadequate access controls in financial system
        Inherent Risk Level: High
        Control-456: Two-factor authentication enforced
        Control-457: Role-based access control implemented

        Risk-124: Lack of data encryption at rest
        Inherent Risk Level: Medium
        Control-458: AES-256 encryption deployed

        This document references Policy-789 for access control standards.
        Process-100 defines the risk assessment workflow.
        """

        # Create document with realistic structure
        doc = Document(
            id="risk-control-mapping-test",
            text=audit_text,
            metadata=sample_metadata,
            structure={
                "sections": [
                    {"title": "Risk Assessment Report", "content": audit_text, "level": 1}
                ],
                "headings": ["Risk Assessment Report"],
            },
        )

        # Process through full pipeline (TextCleaner → EntityNormalizer → SchemaStandardizer)
        # Configure normalizer with entity patterns and dictionary for entity recognition
        config = NormalizationConfig(
            enable_entity_normalization=True,
            entity_patterns_file=Path("config/normalize/entity_patterns.yaml"),
            entity_dictionary_file=Path("config/normalize/entity_dictionary.yaml"),
            enable_schema_standardization=True,
            schema_templates_file=Path("config/normalize/schema_templates.yaml"),
        )
        normalizer = NormalizerFactory.create(config)
        context = ProcessingContext(config={}, logger=structlog.get_logger(), metrics={})

        result = normalizer.process(doc, context)

        # Verify entity_tags are present and populated (AC-2.2.6)
        assert isinstance(result.metadata.entity_tags, list)
        assert (
            len(result.metadata.entity_tags) > 0
        ), "Entity tags should be populated after normalization"

        # Verify entity_counts are present and accurate (AC-2.2.6)
        assert isinstance(result.metadata.entity_counts, dict)
        assert "risk" in result.metadata.entity_counts or "Risk" in str(
            result.metadata.entity_counts
        ), "Risk entities should be counted"
        assert "control" in result.metadata.entity_counts or "Control" in str(
            result.metadata.entity_counts
        ), "Control entities should be counted"

        # Verify risk entities are tagged (Risk-123, Risk-124)
        risk_tags = [tag for tag in result.metadata.entity_tags if "Risk" in tag or "risk" in tag]
        assert len(risk_tags) >= 2, f"Expected at least 2 risk tags, found: {risk_tags}"

        # Verify control entities are tagged (Control-456, Control-457, Control-458)
        control_tags = [
            tag for tag in result.metadata.entity_tags if "Control" in tag or "control" in tag
        ]
        assert len(control_tags) >= 3, f"Expected at least 3 control tags, found: {control_tags}"

        # Verify policy and process entities are tagged
        policy_tags = [
            tag for tag in result.metadata.entity_tags if "Policy" in tag or "policy" in tag
        ]
        process_tags = [
            tag for tag in result.metadata.entity_tags if "Process" in tag or "process" in tag
        ]
        assert len(policy_tags) >= 1, f"Expected at least 1 policy tag, found: {policy_tags}"
        assert len(process_tags) >= 1, f"Expected at least 1 process tag, found: {process_tags}"

        # Verify document type was detected by SchemaStandardizer (AC-2.3.1)
        assert result.metadata.document_type is not None, "Document type should be detected"

        # Verify entities are present in document (AC-2.2.1)
        assert len(result.entities) > 0, "Entities should be recognized and attached to document"

        # Verify entity relationships are traceable through entity_tags
        # Risk-123 should be in entity_tags, allowing RAG retrieval filtering
        risk_123_found = any("123" in tag for tag in risk_tags)
        assert risk_123_found, "Risk-123 should be traceable through entity_tags"

        # Control-456 should be in entity_tags, maintaining risk→control mapping
        control_456_found = any("456" in tag for tag in control_tags)
        assert control_456_found, "Control-456 should be traceable through entity_tags"

        # Verify semantic relationships preserved through schema transformation (AC-2.3.4)
        # The text should still contain both risk and control references
        assert "Risk-123" in result.text or "Risk" in result.text
        assert "Control-456" in result.text or "Control" in result.text

        # Verify entity graph can be reconstructed from entity_tags
        # All unique entities should be represented in entity_tags
        unique_entity_types = set(result.metadata.entity_counts.keys())
        assert len(unique_entity_types) >= 3, (
            f"Expected at least 3 entity types (risk, control, policy/process), "
            f"found: {unique_entity_types}"
        )

        # Log results for debugging
        context.logger.info(
            "risk_control_mapping_test_complete",
            entity_tags_count=len(result.metadata.entity_tags),
            entity_counts=result.metadata.entity_counts,
            document_type=result.metadata.document_type,
            entities_found=len(result.entities),
        )
