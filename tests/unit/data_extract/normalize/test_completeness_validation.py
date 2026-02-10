"""Unit tests for completeness validation (Story 2.5).

Tests for QualityValidator methods:
- detect_missing_images() - AC 2.5.1, 2.5.4
- detect_complex_objects() - AC 2.5.2, 2.5.4
- calculate_completeness_ratio() - AC 2.5.3
- log_extraction_gap() - AC 2.5.4, 2.5.6
- process() integration - All ACs
"""

from datetime import datetime
from pathlib import Path

import pytest

from src.data_extract.core.models import Document, Metadata, ProcessingContext
from src.data_extract.normalize.validation import QualityValidator

pytestmark = [pytest.mark.P1, pytest.mark.unit]


class TestDetectMissingImages:
    """Test missing images detection (Story 2.5 - AC 2.5.1, 2.5.4)."""

    def test_detect_missing_images_no_images(self):
        """Test detect_missing_images with document containing no images."""
        metadata = Metadata(
            source_file=Path("test.pdf"),
            file_hash="abc123",
            processing_timestamp=datetime.now(),
            tool_version="1.0.0",
            config_version="1.0",
        )
        document = Document(
            id="DOC-001", text="Test content", metadata=metadata, structure={"content_blocks": []}
        )

        validator = QualityValidator()
        gaps = validator.detect_missing_images(document)

        assert gaps == []

    def test_detect_missing_images_with_alt_text(self):
        """Test detect_missing_images when all images have alt text."""
        metadata = Metadata(
            source_file=Path("test.pdf"),
            file_hash="abc123",
            processing_timestamp=datetime.now(),
            tool_version="1.0.0",
            config_version="1.0",
        )
        content_blocks = [
            {
                "block_type": "image",
                "content": "",
                "metadata": {"alt_text": "Company logo", "section": "Header"},
                "position": {"page": 1},
            }
        ]
        document = Document(
            id="DOC-001",
            text="Test content",
            metadata=metadata,
            structure={"content_blocks": content_blocks},
        )

        validator = QualityValidator()
        gaps = validator.detect_missing_images(document)

        assert gaps == []

    def test_detect_missing_images_without_alt_text(self):
        """Test detect_missing_images flags images without alt text."""
        metadata = Metadata(
            source_file=Path("test.pdf"),
            file_hash="abc123",
            processing_timestamp=datetime.now(),
            tool_version="1.0.0",
            config_version="1.0",
        )
        content_blocks = [
            {
                "block_type": "image",
                "content": "",
                "metadata": {"section": "Risk Summary"},
                "position": {"page": 5},
            }
        ]
        document = Document(
            id="DOC-001",
            text="Test content",
            metadata=metadata,
            structure={"content_blocks": content_blocks},
        )

        validator = QualityValidator()
        gaps = validator.detect_missing_images(document)

        assert len(gaps) == 1
        assert gaps[0]["gap_type"] == "missing_image"
        assert gaps[0]["location"]["page"] == 5
        assert gaps[0]["location"]["section"] == "Risk Summary"
        assert gaps[0]["severity"] == "warning"
        assert "no alt text" in gaps[0]["description"]

    def test_detect_missing_images_empty_alt_text(self):
        """Test detect_missing_images flags images with empty alt text."""
        metadata = Metadata(
            source_file=Path("test.pdf"),
            file_hash="abc123",
            processing_timestamp=datetime.now(),
            tool_version="1.0.0",
            config_version="1.0",
        )
        content_blocks = [
            {
                "block_type": "image",
                "content": "",
                "metadata": {"alt_text": "   ", "section": "Controls"},
                "position": {"page": 3},
            }
        ]
        document = Document(
            id="DOC-001",
            text="Test content",
            metadata=metadata,
            structure={"content_blocks": content_blocks},
        )

        validator = QualityValidator()
        gaps = validator.detect_missing_images(document)

        assert len(gaps) == 1
        assert gaps[0]["gap_type"] == "missing_image"

    def test_detect_missing_images_mixed_scenario(self):
        """Test detect_missing_images with mix of images with/without alt text."""
        metadata = Metadata(
            source_file=Path("test.pdf"),
            file_hash="abc123",
            processing_timestamp=datetime.now(),
            tool_version="1.0.0",
            config_version="1.0",
        )
        content_blocks = [
            {
                "block_type": "image",
                "content": "",
                "metadata": {"alt_text": "Logo", "section": "Header"},
                "position": {"page": 1},
            },
            {
                "block_type": "image",
                "content": "",
                "metadata": {"section": "Body"},
                "position": {"page": 2},
            },
            {
                "block_type": "text",
                "content": "Some text",
                "metadata": {},
                "position": {"page": 2},
            },
            {
                "block_type": "image",
                "content": "",
                "metadata": {"section": "Footer"},
                "position": {"page": 3},
            },
        ]
        document = Document(
            id="DOC-001",
            text="Test content",
            metadata=metadata,
            structure={"content_blocks": content_blocks},
        )

        validator = QualityValidator()
        gaps = validator.detect_missing_images(document)

        assert len(gaps) == 2
        assert all(gap["gap_type"] == "missing_image" for gap in gaps)


class TestDetectComplexObjects:
    """Test complex objects detection (Story 2.5 - AC 2.5.2, 2.5.4)."""

    def test_detect_complex_objects_none(self):
        """Test detect_complex_objects with no complex objects."""
        metadata = Metadata(
            source_file=Path("test.pdf"),
            file_hash="abc123",
            processing_timestamp=datetime.now(),
            tool_version="1.0.0",
            config_version="1.0",
        )
        content_blocks = [
            {"block_type": "text", "content": "Text", "metadata": {}, "position": {"page": 1}}
        ]
        document = Document(
            id="DOC-001",
            text="Test content",
            metadata=metadata,
            structure={"content_blocks": content_blocks},
        )

        validator = QualityValidator()
        gaps = validator.detect_complex_objects(document)

        assert gaps == []

    def test_detect_complex_objects_ole_object(self):
        """Test detect_complex_objects detects OLE objects."""
        metadata = Metadata(
            source_file=Path("test.pdf"),
            file_hash="abc123",
            processing_timestamp=datetime.now(),
            tool_version="1.0.0",
            config_version="1.0",
        )
        content_blocks = [
            {
                "block_type": "ole_object",
                "content": "",
                "metadata": {"section": "Compliance", "object_id": "OLE-123"},
                "position": {"page": 4},
            }
        ]
        document = Document(
            id="DOC-001",
            text="Test content",
            metadata=metadata,
            structure={"content_blocks": content_blocks},
        )

        validator = QualityValidator()
        gaps = validator.detect_complex_objects(document)

        assert len(gaps) == 1
        assert gaps[0]["gap_type"] == "complex_object"
        assert gaps[0]["location"]["page"] == 4
        assert gaps[0]["location"]["object_type"] == "ole_object"
        assert gaps[0]["severity"] == "info"
        assert "manual extraction required" in gaps[0]["description"]
        assert "suggested_action" in gaps[0]

    def test_detect_complex_objects_chart(self):
        """Test detect_complex_objects detects charts."""
        metadata = Metadata(
            source_file=Path("test.pdf"),
            file_hash="abc123",
            processing_timestamp=datetime.now(),
            tool_version="1.0.0",
            config_version="1.0",
        )
        content_blocks = [
            {
                "block_type": "chart",
                "content": "",
                "metadata": {"section": "Risk Analysis"},
                "position": {"page": 7},
            }
        ]
        document = Document(
            id="DOC-001",
            text="Test content",
            metadata=metadata,
            structure={"content_blocks": content_blocks},
        )

        validator = QualityValidator()
        gaps = validator.detect_complex_objects(document)

        assert len(gaps) == 1
        assert gaps[0]["location"]["object_type"] == "chart"

    def test_detect_complex_objects_multiple_types(self):
        """Test detect_complex_objects with multiple object types."""
        metadata = Metadata(
            source_file=Path("test.pdf"),
            file_hash="abc123",
            processing_timestamp=datetime.now(),
            tool_version="1.0.0",
            config_version="1.0",
        )
        content_blocks = [
            {
                "block_type": "ole_object",
                "content": "",
                "metadata": {"section": "A"},
                "position": {"page": 1},
            },
            {
                "block_type": "chart",
                "content": "",
                "metadata": {"section": "B"},
                "position": {"page": 2},
            },
            {
                "block_type": "diagram",
                "content": "",
                "metadata": {"section": "C"},
                "position": {"page": 3},
            },
            {
                "block_type": "drawing",
                "content": "",
                "metadata": {"section": "D"},
                "position": {"page": 4},
            },
        ]
        document = Document(
            id="DOC-001",
            text="Test content",
            metadata=metadata,
            structure={"content_blocks": content_blocks},
        )

        validator = QualityValidator()
        gaps = validator.detect_complex_objects(document)

        assert len(gaps) == 4
        object_types = [gap["location"]["object_type"] for gap in gaps]
        assert set(object_types) == {"ole_object", "chart", "diagram", "drawing"}


class TestCompletenessRatioCalculation:
    """Test completeness ratio calculation (Story 2.5 - AC 2.5.3)."""

    def test_calculate_completeness_ratio_no_elements(self):
        """Test calculate_completeness_ratio with 0 total elements (edge case)."""
        metadata = Metadata(
            source_file=Path("test.pdf"),
            file_hash="abc123",
            processing_timestamp=datetime.now(),
            tool_version="1.0.0",
            config_version="1.0",
        )
        document = Document(
            id="DOC-001", text="", metadata=metadata, structure={"content_blocks": []}
        )

        validator = QualityValidator()
        ratio = validator.calculate_completeness_ratio(document)

        assert ratio == 1.0  # No elements = 100% complete by default

    def test_calculate_completeness_ratio_all_extracted(self):
        """Test calculate_completeness_ratio with 100% extraction."""
        metadata = Metadata(
            source_file=Path("test.pdf"),
            file_hash="abc123",
            processing_timestamp=datetime.now(),
            tool_version="1.0.0",
            config_version="1.0",
        )
        content_blocks = [
            {"block_type": "text", "content": "Block 1", "metadata": {}, "position": {}},
            {"block_type": "text", "content": "Block 2", "metadata": {}, "position": {}},
        ]
        document = Document(
            id="DOC-001",
            text="Test content",
            metadata=metadata,
            structure={"content_blocks": content_blocks},
        )

        validator = QualityValidator()
        ratio = validator.calculate_completeness_ratio(document)

        assert ratio == 1.0

    def test_calculate_completeness_ratio_partial_extraction(self):
        """Test calculate_completeness_ratio with partial extraction (8/10 = 0.8)."""
        metadata = Metadata(
            source_file=Path("test.pdf"),
            file_hash="abc123",
            processing_timestamp=datetime.now(),
            tool_version="1.0.0",
            config_version="1.0",
        )
        content_blocks = [
            {"block_type": "text", "content": "Block 1", "metadata": {}, "position": {}},
            {"block_type": "text", "content": "Block 2", "metadata": {}, "position": {}},
            {"block_type": "text", "content": "", "metadata": {}, "position": {}},  # Empty
            {"block_type": "text", "content": "Block 4", "metadata": {}, "position": {}},
            {"block_type": "text", "content": "   ", "metadata": {}, "position": {}},  # Whitespace
            {"block_type": "text", "content": "Block 6", "metadata": {}, "position": {}},
            {"block_type": "text", "content": "Block 7", "metadata": {}, "position": {}},
            {"block_type": "text", "content": "Block 8", "metadata": {}, "position": {}},
            {"block_type": "text", "content": "Block 9", "metadata": {}, "position": {}},
            {"block_type": "text", "content": "Block 10", "metadata": {}, "position": {}},
        ]
        document = Document(
            id="DOC-001",
            text="Test content",
            metadata=metadata,
            structure={"content_blocks": content_blocks},
        )

        validator = QualityValidator()
        ratio = validator.calculate_completeness_ratio(document)

        assert ratio == 0.8

    def test_calculate_completeness_ratio_threshold_boundary(self):
        """Test calculate_completeness_ratio at exactly 0.90 threshold."""
        metadata = Metadata(
            source_file=Path("test.pdf"),
            file_hash="abc123",
            processing_timestamp=datetime.now(),
            tool_version="1.0.0",
            config_version="1.0",
        )
        # 9 out of 10 = 0.9
        content_blocks = [
            {"block_type": "text", "content": f"Block {i}", "metadata": {}, "position": {}}
            for i in range(1, 10)
        ]
        content_blocks.append({"block_type": "text", "content": "", "metadata": {}, "position": {}})
        document = Document(
            id="DOC-001",
            text="Test content",
            metadata=metadata,
            structure={"content_blocks": content_blocks},
        )

        validator = QualityValidator()
        ratio = validator.calculate_completeness_ratio(document)

        assert ratio == 0.9


class TestGapLogging:
    """Test gap logging with structured output (Story 2.5 - AC 2.5.4, 2.5.6)."""

    def test_log_extraction_gap_structure(self):
        """Test log_extraction_gap returns correct structure."""
        validator = QualityValidator()
        gap = validator.log_extraction_gap(
            gap_type="missing_image",
            location={"page": 3, "section": "Summary"},
            description="Image missing alt text",
            severity="warning",
        )

        assert gap["gap_type"] == "missing_image"
        assert gap["location"] == {"page": 3, "section": "Summary"}
        assert gap["description"] == "Image missing alt text"
        assert gap["severity"] == "warning"
        assert "suggested_action" not in gap

    def test_log_extraction_gap_with_suggested_action(self):
        """Test log_extraction_gap includes suggested_action when provided."""
        validator = QualityValidator()
        gap = validator.log_extraction_gap(
            gap_type="complex_object",
            location={"page": 5, "section": "Analysis"},
            description="OLE object detected",
            severity="info",
            suggested_action="Manually extract OLE content",
        )

        assert gap["suggested_action"] == "Manually extract OLE content"


class TestCompletenessValidationIntegration:
    """Test completeness validation integration into process() (Story 2.5 - all ACs)."""

    def test_process_with_completeness_validation(self, tmp_path):
        """Test process() integrates completeness validation correctly."""
        metadata = Metadata(
            source_file=Path("test.pdf"),
            file_hash="abc123",
            processing_timestamp=datetime.now(),
            tool_version="1.0.0",
            config_version="1.0",
        )
        content_blocks = [
            {"block_type": "text", "content": "Block 1", "metadata": {}, "position": {"page": 1}},
            {
                "block_type": "image",
                "content": "",
                "metadata": {"section": "Header"},
                "position": {"page": 1},
            },  # Missing alt text
            {
                "block_type": "chart",
                "content": "",
                "metadata": {"section": "Data"},
                "position": {"page": 2},
            },
        ]
        document = Document(
            id="DOC-001",
            text="Test content",
            metadata=metadata,
            structure={"content_blocks": content_blocks},
        )
        context = ProcessingContext(config={"output_dir": tmp_path})

        validator = QualityValidator(completeness_threshold=0.90)
        result = validator.process(document, context)

        # Check completeness ratio in metadata
        assert result.metadata.completeness_ratio is not None
        assert 0.0 <= result.metadata.completeness_ratio <= 1.0

        # Check quality flags added
        assert any(
            flag in result.metadata.quality_flags for flag in ["missing_images", "complex_objects"]
        )

    def test_process_quarantine_on_low_completeness(self, tmp_path):
        """Test process() quarantines document with completeness < 0.85."""
        metadata = Metadata(
            source_file=Path("test.pdf"),
            file_hash="abc123",
            processing_timestamp=datetime.now(),
            tool_version="1.0.0",
            config_version="1.0",
        )
        # Create 10 blocks, only 8 with content = 0.8 ratio (< 0.85 quarantine threshold)
        content_blocks = [
            {"block_type": "text", "content": f"Block {i}", "metadata": {}, "position": {}}
            for i in range(1, 9)
        ]
        content_blocks.extend(
            [
                {"block_type": "text", "content": "", "metadata": {}, "position": {}},
                {"block_type": "text", "content": "", "metadata": {}, "position": {}},
            ]
        )
        document = Document(
            id="DOC-001",
            text="Test content",
            metadata=metadata,
            structure={"content_blocks": content_blocks},
        )
        context = ProcessingContext(config={"output_dir": tmp_path})

        validator = QualityValidator(completeness_threshold=0.90, quarantine_low_confidence=True)
        result = validator.process(document, context)

        # Quarantine should have been triggered
        assert result.metadata.completeness_ratio == 0.8
        # Check quarantine file created (in quarantine/YYYY-MM-DD/ subfolder)
        quarantine_files = list(tmp_path.glob("quarantine/**/*.json"))
        assert len(quarantine_files) > 0
