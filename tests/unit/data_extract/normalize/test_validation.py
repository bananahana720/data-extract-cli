"""Unit tests for OCR confidence scoring and quality validation.

Tests cover:
- OCR confidence calculation with mocked pytesseract (AC 2.4.1)
- Confidence threshold flagging (AC 2.4.2)
- Image preprocessing pipeline (AC 2.4.3)
- Scanned vs native PDF detection (AC 2.4.4)
- Quarantine mechanism (AC 2.4.5)
- Metadata population (AC 2.4.6)
- OCR operation logging (AC 2.4.7)
"""

from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.data_extract.core.exceptions import ProcessingError
from src.data_extract.core.models import Document, Metadata, ProcessingContext, QualityFlag
from src.data_extract.normalize.validation import QualityValidator

pytestmark = [pytest.mark.P0, pytest.mark.unit]


class TestOCRConfidenceCalculation:
    """Test OCR confidence calculation (Story 2.4 - AC 2.4.1)."""

    @patch("src.data_extract.normalize.validation.TESSERACT_AVAILABLE", True)
    @patch("src.data_extract.normalize.validation.pytesseract", create=True)
    @patch("src.data_extract.normalize.validation.Image", create=True)
    def test_validate_ocr_confidence_high_quality(self, mock_image_class, mock_pytesseract):
        """Test OCR confidence calculation with high-quality scan (>95%)."""
        # Mock image loading
        mock_image = MagicMock()
        mock_image_class.open.return_value = mock_image

        # Mock pytesseract response with high confidence scores
        mock_pytesseract.Output.DICT = 0
        mock_pytesseract.image_to_data.return_value = {
            "conf": ["98", "97", "99", "96", "98"],
            "text": ["The", "quick", "brown", "fox", "jumps"],
        }

        validator = QualityValidator(ocr_confidence_threshold=0.95, ocr_preprocessing_enabled=False)
        confidence, ocr_data = validator.validate_ocr_confidence(
            Path("test_image.png"), preprocess=False
        )

        # Average confidence: (98+97+99+96+98)/5 / 100 = 0.976
        assert confidence == pytest.approx(0.976, abs=0.001)
        assert "conf" in ocr_data
        assert len(ocr_data["conf"]) == 5

    @patch("src.data_extract.normalize.validation.TESSERACT_AVAILABLE", True)
    @patch("src.data_extract.normalize.validation.pytesseract", create=True)
    @patch("src.data_extract.normalize.validation.Image", create=True)
    def test_validate_ocr_confidence_low_quality(self, mock_image_class, mock_pytesseract):
        """Test OCR confidence calculation with low-quality scan (<85%)."""
        mock_image = MagicMock()
        mock_image_class.open.return_value = mock_image

        mock_pytesseract.Output.DICT = 0
        mock_pytesseract.image_to_data.return_value = {
            "conf": ["75", "80", "82", "78", "85"],
            "text": ["Poor", "quality", "scan", "text", "here"],
        }

        validator = QualityValidator()
        confidence, ocr_data = validator.validate_ocr_confidence(
            Path("low_quality.png"), preprocess=False
        )

        # Average confidence: (75+80+82+78+85)/5 / 100 = 0.80
        assert confidence == pytest.approx(0.80, abs=0.001)

    @patch("src.data_extract.normalize.validation.TESSERACT_AVAILABLE", True)
    @patch("src.data_extract.normalize.validation.pytesseract", create=True)
    @patch("src.data_extract.normalize.validation.Image", create=True)
    def test_validate_ocr_confidence_filters_invalid_scores(
        self, mock_image_class, mock_pytesseract
    ):
        """Test that -1 confidence scores (no OCR) are filtered out."""
        mock_image = MagicMock()
        mock_image_class.open.return_value = mock_image

        mock_pytesseract.Output.DICT = 0
        mock_pytesseract.image_to_data.return_value = {
            "conf": ["-1", "90", "-1", "95", "88", "-1"],
            "text": ["", "Valid", "", "text", "here", ""],
        }

        validator = QualityValidator()
        confidence, ocr_data = validator.validate_ocr_confidence(
            Path("mixed_confidence.png"), preprocess=False
        )

        # Should only average valid scores: (90+95+88)/3 / 100 = 0.91
        assert confidence == pytest.approx(0.91, abs=0.001)

    @patch("src.data_extract.normalize.validation.TESSERACT_AVAILABLE", True)
    @patch("src.data_extract.normalize.validation.pytesseract", create=True)
    @patch("src.data_extract.normalize.validation.Image", create=True)
    def test_validate_ocr_confidence_empty_page(self, mock_image_class, mock_pytesseract):
        """Test OCR confidence calculation with empty page (no text detected)."""
        mock_image = MagicMock()
        mock_image_class.open.return_value = mock_image

        mock_pytesseract.Output.DICT = 0
        mock_pytesseract.image_to_data.return_value = {
            "conf": ["-1", "-1", "-1"],
            "text": ["", "", ""],
        }

        validator = QualityValidator()
        confidence, ocr_data = validator.validate_ocr_confidence(
            Path("empty_page.png"), preprocess=False
        )

        # No valid text - should return 0.0 confidence
        assert confidence == 0.0

    @patch("src.data_extract.normalize.validation.TESSERACT_AVAILABLE", False)
    def test_validate_ocr_confidence_tesseract_not_available(self):
        """Test that ProcessingError is raised when Tesseract not available."""
        validator = QualityValidator()

        with pytest.raises(ProcessingError) as exc_info:
            validator.validate_ocr_confidence(Path("test.png"), preprocess=False)

        assert "pytesseract or Pillow not installed" in str(exc_info.value)

    @patch("src.data_extract.normalize.validation.TESSERACT_AVAILABLE", True)
    @patch("src.data_extract.normalize.validation.Image", create=True)
    def test_validate_ocr_confidence_image_load_failure(self, mock_image_class):
        """Test graceful handling of image load failure."""
        mock_image_class.open.side_effect = IOError("Cannot load image")

        validator = QualityValidator()

        with pytest.raises(ProcessingError) as exc_info:
            validator.validate_ocr_confidence(Path("corrupt.png"), preprocess=False)

        assert "Failed to calculate OCR confidence" in str(exc_info.value)

    @patch("src.data_extract.normalize.validation.TESSERACT_AVAILABLE", True)
    @patch("src.data_extract.normalize.validation.pytesseract", create=True)
    @patch("src.data_extract.normalize.validation.Image", create=True)
    def test_validate_ocr_confidence_boundary_scores(self, mock_image_class, mock_pytesseract):
        """Test OCR confidence calculation with boundary values (0 and 100)."""
        mock_image = MagicMock()
        mock_image_class.open.return_value = mock_image

        mock_pytesseract.Output.DICT = 0
        mock_pytesseract.image_to_data.return_value = {
            "conf": ["0", "100", "50"],
            "text": ["word1", "word2", "word3"],
        }

        validator = QualityValidator()
        confidence, ocr_data = validator.validate_ocr_confidence(
            Path("boundary.png"), preprocess=False
        )

        # Average: (0+100+50)/3 / 100 = 0.50
        assert confidence == pytest.approx(0.50, abs=0.001)

    @patch("src.data_extract.normalize.validation.TESSERACT_AVAILABLE", True)
    @patch("src.data_extract.normalize.validation.pytesseract", create=True)
    @patch("src.data_extract.normalize.validation.Image", create=True)
    @patch("src.data_extract.normalize.validation.ImageFilter", create=True)
    @patch("src.data_extract.normalize.validation.ImageEnhance", create=True)
    def test_validate_ocr_confidence_with_preprocessing(
        self, mock_enhance, mock_filter, mock_image_class, mock_pytesseract
    ):
        """Test OCR confidence calculation with preprocessing enabled."""
        mock_image = MagicMock()
        mock_image.mode = "RGB"
        mock_image.convert.return_value = mock_image
        mock_image.filter.return_value = mock_image
        mock_image_class.open.return_value = mock_image

        mock_pytesseract.Output.DICT = 0
        # Three calls: before preprocessing check, after preprocessing check, final calculation
        mock_pytesseract.image_to_data.side_effect = [
            {
                "conf": ["80", "82", "85"],
                "text": ["low", "quality", "text"],
            },  # Before preprocessing
            {
                "conf": ["90", "92", "95"],
                "text": ["improved", "quality", "text"],
            },  # After preprocessing
            {
                "conf": ["90", "92", "95"],
                "text": ["improved", "quality", "text"],
            },  # Final calculation
        ]

        validator = QualityValidator(ocr_preprocessing_enabled=True)

        # Mock ImageEnhance.Contrast
        mock_enhancer = MagicMock()
        mock_enhancer.enhance.return_value = mock_image
        mock_enhance.Contrast.return_value = mock_enhancer

        confidence, ocr_data = validator.validate_ocr_confidence(
            Path("preprocessed.png"), preprocess=True
        )

        # Should return confidence after preprocessing: (90+92+95)/3 / 100 = 0.923
        assert confidence == pytest.approx(0.923, abs=0.001)


class TestDocumentAverageConfidence:
    """Test document-level average confidence calculation."""

    def test_calculate_document_average_confidence_multiple_pages(self):
        """Test document average confidence with multiple pages."""
        validator = QualityValidator()
        confidence_scores = {1: 0.98, 2: 0.95, 3: 0.92, 4: 0.97}

        avg_confidence = validator.calculate_document_average_confidence(confidence_scores)

        # Average: (0.98+0.95+0.92+0.97)/4 = 0.955
        assert avg_confidence == pytest.approx(0.955, abs=0.001)

    def test_calculate_document_average_confidence_single_page(self):
        """Test document average confidence with single page."""
        validator = QualityValidator()
        confidence_scores = {1: 0.85}

        avg_confidence = validator.calculate_document_average_confidence(confidence_scores)

        assert avg_confidence == 0.85

    def test_calculate_document_average_confidence_empty_scores(self):
        """Test document average confidence with no scores returns None."""
        validator = QualityValidator()
        confidence_scores = {}

        avg_confidence = validator.calculate_document_average_confidence(confidence_scores)

        assert avg_confidence is None


class TestConfidenceThresholdFlagging:
    """Test confidence threshold flagging (Story 2.4 - AC 2.4.2)."""

    def test_check_confidence_threshold_all_above(self):
        """Test threshold check when all pages above threshold (0.95)."""
        validator = QualityValidator(ocr_confidence_threshold=0.95)
        confidence_scores = {1: 0.98, 2: 0.96, 3: 0.97}

        quarantine_needed, pages_below = validator.check_confidence_threshold(confidence_scores)

        assert quarantine_needed is False
        assert pages_below == []

    def test_check_confidence_threshold_some_below(self):
        """Test threshold check when some pages below threshold."""
        validator = QualityValidator(ocr_confidence_threshold=0.95)
        confidence_scores = {1: 0.98, 2: 0.92, 3: 0.94, 4: 0.97}

        quarantine_needed, pages_below = validator.check_confidence_threshold(confidence_scores)

        assert quarantine_needed is True
        assert pages_below == [2, 3]

    def test_check_confidence_threshold_edge_case_exactly_at_threshold(self):
        """Test threshold check with confidence exactly at threshold (0.95)."""
        validator = QualityValidator(ocr_confidence_threshold=0.95)
        confidence_scores = {1: 0.95, 2: 0.96}

        quarantine_needed, pages_below = validator.check_confidence_threshold(confidence_scores)

        # 0.95 should NOT be below threshold (threshold is exclusive)
        assert quarantine_needed is False
        assert pages_below == []

    def test_check_confidence_threshold_edge_case_just_below(self):
        """Test threshold check with confidence just below threshold (0.94)."""
        validator = QualityValidator(ocr_confidence_threshold=0.95)
        confidence_scores = {1: 0.94}

        quarantine_needed, pages_below = validator.check_confidence_threshold(confidence_scores)

        assert quarantine_needed is True
        assert pages_below == [1]

    def test_check_confidence_threshold_edge_case_just_above(self):
        """Test threshold check with confidence just above threshold (0.96)."""
        validator = QualityValidator(ocr_confidence_threshold=0.95)
        confidence_scores = {1: 0.96}

        quarantine_needed, pages_below = validator.check_confidence_threshold(confidence_scores)

        assert quarantine_needed is False
        assert pages_below == []

    def test_create_validation_report_high_confidence(self):
        """Test validation report creation for high-confidence document."""
        validator = QualityValidator(ocr_confidence_threshold=0.95)
        confidence_scores = {1: 0.98, 2: 0.97, 3: 0.99}

        report = validator.create_validation_report(
            confidence_scores, [], scanned_pdf_detected=True
        )

        assert report.quarantine_recommended is False
        assert report.quality_flags == []
        assert report.extraction_gaps == []
        assert report.document_average_confidence == pytest.approx(0.98, abs=0.01)
        assert report.scanned_pdf_detected is True

    def test_create_validation_report_low_confidence(self):
        """Test validation report creation for low-confidence document."""
        validator = QualityValidator(ocr_confidence_threshold=0.95, quarantine_low_confidence=True)
        confidence_scores = {1: 0.92, 2: 0.93}

        report = validator.create_validation_report(
            confidence_scores, [1, 2], scanned_pdf_detected=True
        )

        assert report.quarantine_recommended is True
        assert QualityFlag.LOW_OCR_CONFIDENCE in report.quality_flags
        assert len(report.extraction_gaps) == 2
        assert "Page 1" in report.extraction_gaps[0]
        assert "Page 2" in report.extraction_gaps[1]
        assert report.document_average_confidence == pytest.approx(0.925, abs=0.001)

    def test_create_validation_report_quarantine_disabled(self):
        """Test validation report with quarantine disabled."""
        validator = QualityValidator(ocr_confidence_threshold=0.95, quarantine_low_confidence=False)
        confidence_scores = {1: 0.92}

        report = validator.create_validation_report(confidence_scores, [1])

        # Quality flag should still be set, but quarantine should be False
        assert report.quarantine_recommended is False
        assert QualityFlag.LOW_OCR_CONFIDENCE in report.quality_flags
        assert len(report.extraction_gaps) == 1


class TestQualityValidatorInitialization:
    """Test QualityValidator initialization and configuration."""

    def test_quality_validator_default_config(self):
        """Test QualityValidator initialization with default configuration."""
        validator = QualityValidator()

        assert validator.ocr_confidence_threshold == 0.95
        assert validator.ocr_preprocessing_enabled is True
        assert validator.quarantine_low_confidence is True

    def test_quality_validator_custom_config(self):
        """Test QualityValidator initialization with custom configuration."""
        validator = QualityValidator(
            ocr_confidence_threshold=0.90,
            ocr_preprocessing_enabled=False,
            quarantine_low_confidence=False,
        )

        assert validator.ocr_confidence_threshold == 0.90
        assert validator.ocr_preprocessing_enabled is False
        assert validator.quarantine_low_confidence is False

    def test_quality_validator_with_custom_logger(self):
        """Test QualityValidator initialization with custom logger."""
        mock_logger = MagicMock()
        validator = QualityValidator(logger=mock_logger)

        assert validator.logger == mock_logger


class TestQualityValidatorProcess:
    """Test QualityValidator process() method integration."""

    @patch("src.data_extract.normalize.validation.TESSERACT_AVAILABLE", False)
    def test_process_skips_validation_when_tesseract_unavailable(self):
        """Test that process() gracefully skips validation when Tesseract unavailable."""
        metadata = Metadata(
            source_file=Path("doc.pdf"),
            file_hash="hash123",
            processing_timestamp=datetime.now(),
            tool_version="1.0.0",
            config_version="v1",
        )
        document = Document(id="DOC-001", text="Sample document text", metadata=metadata)
        context = ProcessingContext()

        validator = QualityValidator()
        result = validator.process(document, context)

        # Should return document unchanged
        assert result.id == "DOC-001"
        assert result.text == "Sample document text"

    @patch("src.data_extract.normalize.validation.TESSERACT_AVAILABLE", True)
    def test_process_logs_validation_start(self):
        """Test that process() logs validation start event."""
        metadata = Metadata(
            source_file=Path("doc.pdf"),
            file_hash="hash123",
            processing_timestamp=datetime.now(),
            tool_version="1.0.0",
            config_version="v1",
            document_type="image",  # Mark as scanned to trigger validation
            ocr_confidence={1: 0.96},  # Provide confidence scores
        )
        document = Document(id="DOC-001", text="Sample document text", metadata=metadata)
        context = ProcessingContext()

        mock_logger = MagicMock()
        validator = QualityValidator(logger=mock_logger)
        validator.process(document, context)

        # Should log validation start
        validation_started_calls = [
            call
            for call in mock_logger.info.call_args_list
            if call[0][0] == "ocr_validation_started"
        ]
        assert len(validation_started_calls) == 1
        assert validation_started_calls[0][1]["document_id"] == "DOC-001"
        assert validation_started_calls[0][1]["threshold"] == 0.95


class TestScannedPDFDetection:
    """Test scanned vs native PDF detection (Story 2.4 - AC 2.4.4)."""

    def test_detect_scanned_pdf_with_image_document_type(self):
        """Test detection when document_type is explicitly 'image'."""
        metadata = Metadata(
            source_file=Path("scanned.pdf"),
            file_hash="hash123",
            processing_timestamp=datetime.now(),
            tool_version="1.0.0",
            config_version="v1",
            document_type="image",
        )
        document = Document(id="DOC-001", text="Scanned content", metadata=metadata)

        validator = QualityValidator()
        is_scanned = validator.detect_scanned_pdf(document)

        assert is_scanned is True

    def test_detect_scanned_pdf_with_ocr_confidence_scores(self):
        """Test detection when OCR confidence scores present in metadata."""
        metadata = Metadata(
            source_file=Path("scanned.pdf"),
            file_hash="hash123",
            processing_timestamp=datetime.now(),
            tool_version="1.0.0",
            config_version="v1",
            ocr_confidence={1: 0.95, 2: 0.93, 3: 0.97},
        )
        document = Document(id="DOC-002", text="Scanned content", metadata=metadata)

        validator = QualityValidator()
        is_scanned = validator.detect_scanned_pdf(document)

        assert is_scanned is True

    def test_detect_scanned_pdf_with_high_image_ratio(self):
        """Test detection when >50% of content is from images."""
        metadata = Metadata(
            source_file=Path("mixed.pdf"),
            file_hash="hash123",
            processing_timestamp=datetime.now(),
            tool_version="1.0.0",
            config_version="v1",
        )
        document = Document(
            id="DOC-003",
            text="Mixed content",
            metadata=metadata,
            structure={
                "pages": [
                    {"page_num": 1, "has_images": True, "ocr_applied": True},
                    {"page_num": 2, "has_images": True, "ocr_applied": True},
                    {"page_num": 3, "has_text": True, "text_blocks": 5},
                ]
            },
        )

        validator = QualityValidator()
        is_scanned = validator.detect_scanned_pdf(document)

        # 2 image pages + 1 text page = 2/3 = 66.7% image ratio > 50%
        assert is_scanned is True

    def test_detect_native_pdf_with_high_text_ratio(self):
        """Test detection when >50% of content is native text."""
        metadata = Metadata(
            source_file=Path("native.pdf"),
            file_hash="hash123",
            processing_timestamp=datetime.now(),
            tool_version="1.0.0",
            config_version="v1",
        )
        document = Document(
            id="DOC-004",
            text="Native text content",
            metadata=metadata,
            structure={
                "pages": [
                    {"page_num": 1, "has_text": True, "text_blocks": 10},
                    {"page_num": 2, "has_text": True, "text_blocks": 8},
                    {"page_num": 3, "has_images": True, "ocr_applied": True},
                ]
            },
        )

        validator = QualityValidator()
        is_scanned = validator.detect_scanned_pdf(document)

        # 2 text pages + 1 image page = 1/3 = 33.3% image ratio < 50%
        assert is_scanned is False

    def test_detect_native_pdf_with_rich_fonts(self):
        """Test detection when document has rich font metadata (native indicator)."""
        metadata = Metadata(
            source_file=Path("native.pdf"),
            file_hash="hash123",
            processing_timestamp=datetime.now(),
            tool_version="1.0.0",
            config_version="v1",
        )
        document = Document(
            id="DOC-005",
            text="Native text with rich fonts",
            metadata=metadata,
            structure={"font_count": 8},  # >3 fonts indicates native PDF
        )

        validator = QualityValidator()
        is_scanned = validator.detect_scanned_pdf(document)

        assert is_scanned is False

    def test_detect_pdf_type_edge_case_exactly_50_percent(self):
        """Test detection with exactly 50% image content (edge case)."""
        metadata = Metadata(
            source_file=Path("mixed.pdf"),
            file_hash="hash123",
            processing_timestamp=datetime.now(),
            tool_version="1.0.0",
            config_version="v1",
        )
        document = Document(
            id="DOC-006",
            text="Mixed content",
            metadata=metadata,
            structure={
                "blocks": [
                    {"type": "image"},
                    {"type": "image"},
                    {"type": "text"},
                    {"type": "paragraph"},
                ]
            },
        )

        validator = QualityValidator()
        is_scanned = validator.detect_scanned_pdf(document)

        # 2 image blocks + 2 text blocks = 50% exactly → NOT scanned (threshold is >50%)
        assert is_scanned is False

    def test_detect_pdf_type_indeterminate_no_structure(self):
        """Test detection with no structure metadata (assume native)."""
        metadata = Metadata(
            source_file=Path("unknown.pdf"),
            file_hash="hash123",
            processing_timestamp=datetime.now(),
            tool_version="1.0.0",
            config_version="v1",
        )
        document = Document(id="DOC-007", text="Content", metadata=metadata, structure={})

        validator = QualityValidator()
        is_scanned = validator.detect_scanned_pdf(document)

        # No structure metadata → assume native
        assert is_scanned is False

    def test_detect_scanned_pdf_with_block_types(self):
        """Test detection using block-level type indicators."""
        metadata = Metadata(
            source_file=Path("scanned.pdf"),
            file_hash="hash123",
            processing_timestamp=datetime.now(),
            tool_version="1.0.0",
            config_version="v1",
        )
        document = Document(
            id="DOC-008",
            text="Scanned content",
            metadata=metadata,
            structure={
                "blocks": [
                    {"type": "ocr"},
                    {"type": "scanned"},
                    {"type": "image"},
                    {"type": "text"},
                ]
            },
        )

        validator = QualityValidator()
        is_scanned = validator.detect_scanned_pdf(document)

        # 3 image-type blocks + 1 text block = 3/4 = 75% > 50%
        assert is_scanned is True


class TestQuarantineMechanism:
    """Test quarantine mechanism (Story 2.4 - AC 2.4.5)."""

    def test_quarantine_document_creates_directory_structure(self, tmp_path):
        """Test that quarantine creates proper directory structure."""
        from src.data_extract.normalize.validation import ValidationReport

        metadata = Metadata(
            source_file=Path("low_quality.pdf"),
            file_hash="abc123",
            processing_timestamp=datetime.now(),
            tool_version="1.0.0",
            config_version="v1",
            ocr_confidence={1: 0.85, 2: 0.88},
        )
        document = Document(id="DOC-001", text="Low quality content", metadata=metadata)

        validation_report = ValidationReport(
            quarantine_recommended=True,
            confidence_scores={1: 0.85, 2: 0.88},
            quality_flags=[QualityFlag.LOW_OCR_CONFIDENCE],
            extraction_gaps=["Page 1: OCR confidence 85.00% below threshold 95.00%"],
            document_average_confidence=0.865,
            scanned_pdf_detected=True,
        )

        validator = QualityValidator()
        quarantine_dir = validator.quarantine_document(document, validation_report, tmp_path)

        # Check directory structure: output_dir/quarantine/{date}/
        today = datetime.now().strftime("%Y-%m-%d")
        expected_dir = tmp_path / "quarantine" / today

        assert quarantine_dir == expected_dir
        assert quarantine_dir.exists()
        assert quarantine_dir.is_dir()

    def test_quarantine_document_creates_audit_log(self, tmp_path):
        """Test that quarantine creates JSON audit log with all required fields."""
        from src.data_extract.normalize.validation import ValidationReport

        metadata = Metadata(
            source_file=Path("low_quality.pdf"),
            file_hash="abc123",
            processing_timestamp=datetime.now(),
            tool_version="1.0.0",
            config_version="v1",
            ocr_confidence={1: 0.85, 2: 0.88},
        )
        document = Document(id="DOC-001", text="Low quality content", metadata=metadata)

        validation_report = ValidationReport(
            quarantine_recommended=True,
            confidence_scores={1: 0.85, 2: 0.88},
            quality_flags=[QualityFlag.LOW_OCR_CONFIDENCE],
            extraction_gaps=["Page 1: OCR confidence 85.00% below threshold 95.00%"],
            document_average_confidence=0.865,
            scanned_pdf_detected=True,
        )

        validator = QualityValidator(ocr_confidence_threshold=0.95)
        validator.quarantine_document(document, validation_report, tmp_path)

        # Check audit log exists
        today = datetime.now().strftime("%Y-%m-%d")
        log_path = tmp_path / "quarantine" / today / "quarantine_log.json"

        assert log_path.exists()

        # Check log contents
        import json

        with open(log_path, "r", encoding="utf-8") as f:
            log_entries = json.load(f)

        assert len(log_entries) == 1
        entry = log_entries[0]

        # Verify all required fields
        assert entry["file_path"] == "low_quality.pdf"
        assert entry["file_hash"] == "abc123"
        assert entry["document_id"] == "DOC-001"
        assert entry["quarantine_reason"] == "low_ocr_confidence"
        # Note: JSON converts integer keys to strings
        assert entry["confidence_scores"] == {"1": 0.85, "2": 0.88}
        assert entry["document_average_confidence"] == 0.865
        assert entry["quality_flags"] == ["low_ocr_confidence"]
        assert entry["extraction_gaps"] == ["Page 1: OCR confidence 85.00% below threshold 95.00%"]
        assert "timestamp" in entry
        assert entry["threshold"] == 0.95

    def test_quarantine_document_appends_to_existing_log(self, tmp_path):
        """Test that quarantine appends to existing log (not overwrite)."""
        from src.data_extract.normalize.validation import ValidationReport

        # Create first document
        metadata1 = Metadata(
            source_file=Path("doc1.pdf"),
            file_hash="hash1",
            processing_timestamp=datetime.now(),
            tool_version="1.0.0",
            config_version="v1",
            ocr_confidence={1: 0.85},
        )
        doc1 = Document(id="DOC-001", text="Content 1", metadata=metadata1)
        report1 = ValidationReport(
            quarantine_recommended=True,
            confidence_scores={1: 0.85},
            quality_flags=[QualityFlag.LOW_OCR_CONFIDENCE],
            extraction_gaps=[],
            document_average_confidence=0.85,
        )

        # Create second document
        metadata2 = Metadata(
            source_file=Path("doc2.pdf"),
            file_hash="hash2",
            processing_timestamp=datetime.now(),
            tool_version="1.0.0",
            config_version="v1",
            ocr_confidence={1: 0.90},
        )
        doc2 = Document(id="DOC-002", text="Content 2", metadata=metadata2)
        report2 = ValidationReport(
            quarantine_recommended=True,
            confidence_scores={1: 0.90},
            quality_flags=[QualityFlag.LOW_OCR_CONFIDENCE],
            extraction_gaps=[],
            document_average_confidence=0.90,
        )

        validator = QualityValidator()

        # Quarantine first document
        validator.quarantine_document(doc1, report1, tmp_path)

        # Quarantine second document
        validator.quarantine_document(doc2, report2, tmp_path)

        # Check log has both entries
        today = datetime.now().strftime("%Y-%m-%d")
        log_path = tmp_path / "quarantine" / today / "quarantine_log.json"

        import json

        with open(log_path, "r", encoding="utf-8") as f:
            log_entries = json.load(f)

        assert len(log_entries) == 2
        assert log_entries[0]["document_id"] == "DOC-001"
        assert log_entries[1]["document_id"] == "DOC-002"

    def test_quarantine_document_handles_corrupted_log(self, tmp_path):
        """Test that quarantine handles corrupted existing log gracefully."""
        from src.data_extract.normalize.validation import ValidationReport

        # Create quarantine directory with corrupted log
        today = datetime.now().strftime("%Y-%m-%d")
        quarantine_dir = tmp_path / "quarantine" / today
        quarantine_dir.mkdir(parents=True, exist_ok=True)

        log_path = quarantine_dir / "quarantine_log.json"
        with open(log_path, "w", encoding="utf-8") as f:
            f.write("{ invalid json }")

        # Quarantine a document
        metadata = Metadata(
            source_file=Path("doc.pdf"),
            file_hash="hash",
            processing_timestamp=datetime.now(),
            tool_version="1.0.0",
            config_version="v1",
            ocr_confidence={1: 0.85},
        )
        document = Document(id="DOC-001", text="Content", metadata=metadata)
        report = ValidationReport(
            quarantine_recommended=True,
            confidence_scores={1: 0.85},
            quality_flags=[QualityFlag.LOW_OCR_CONFIDENCE],
            extraction_gaps=[],
            document_average_confidence=0.85,
        )

        validator = QualityValidator()
        validator.quarantine_document(document, report, tmp_path)

        # Check log was recreated with new entry
        import json

        with open(log_path, "r", encoding="utf-8") as f:
            log_entries = json.load(f)

        assert len(log_entries) == 1
        assert log_entries[0]["document_id"] == "DOC-001"

    def test_quarantine_document_failure_raises_processing_error(self, tmp_path):
        """Test that quarantine failure raises ProcessingError."""
        from unittest.mock import patch

        from src.data_extract.core.exceptions import ProcessingError
        from src.data_extract.normalize.validation import ValidationReport

        metadata = Metadata(
            source_file=Path("doc.pdf"),
            file_hash="hash",
            processing_timestamp=datetime.now(),
            tool_version="1.0.0",
            config_version="v1",
        )
        document = Document(id="DOC-001", text="Content", metadata=metadata)
        report = ValidationReport(
            quarantine_recommended=True,
            confidence_scores={1: 0.85},
            quality_flags=[QualityFlag.LOW_OCR_CONFIDENCE],
            extraction_gaps=[],
        )

        validator = QualityValidator()

        # Mock mkdir to raise an exception
        with patch("pathlib.Path.mkdir", side_effect=PermissionError("Permission denied")):
            with pytest.raises(ProcessingError) as exc_info:
                validator.quarantine_document(document, report, tmp_path)

        assert "Failed to quarantine document" in str(exc_info.value)


class TestMetadataPopulation:
    """Test metadata population with confidence scores (Story 2.4 - AC 2.4.6)."""

    @patch("src.data_extract.normalize.validation.TESSERACT_AVAILABLE", True)
    def test_process_populates_metadata_with_confidence_scores(self):
        """Test that process() adds per-page OCR confidence to metadata."""
        metadata = Metadata(
            source_file=Path("scanned.pdf"),
            file_hash="hash123",
            processing_timestamp=datetime.now(),
            tool_version="1.0.0",
            config_version="v1",
            document_type="image",
            ocr_confidence={1: 0.96, 2: 0.98, 3: 0.97},
        )
        document = Document(id="DOC-001", text="Scanned content", metadata=metadata)
        context = ProcessingContext()

        validator = QualityValidator()
        result = validator.process(document, context)

        # Check per-page confidence scores in metadata
        assert result.metadata.ocr_confidence == {1: 0.96, 2: 0.98, 3: 0.97}

    @patch("src.data_extract.normalize.validation.TESSERACT_AVAILABLE", True)
    def test_process_adds_document_average_confidence_to_quality_scores(self):
        """Test that process() calculates and stores document-level average."""
        metadata = Metadata(
            source_file=Path("scanned.pdf"),
            file_hash="hash123",
            processing_timestamp=datetime.now(),
            tool_version="1.0.0",
            config_version="v1",
            document_type="image",
            ocr_confidence={1: 0.96, 2: 0.98, 3: 0.96},
        )
        document = Document(id="DOC-001", text="Scanned content", metadata=metadata)
        context = ProcessingContext()

        validator = QualityValidator()
        result = validator.process(document, context)

        # Check document-level average: (0.96 + 0.98 + 0.96) / 3 = 0.9667
        assert "ocr_average_confidence" in result.metadata.quality_scores
        assert result.metadata.quality_scores["ocr_average_confidence"] == pytest.approx(
            0.9667, abs=0.001
        )

    @patch("src.data_extract.normalize.validation.TESSERACT_AVAILABLE", True)
    def test_process_adds_quality_flags_to_metadata(self):
        """Test that process() adds quality flags to metadata."""
        metadata = Metadata(
            source_file=Path("scanned.pdf"),
            file_hash="hash123",
            processing_timestamp=datetime.now(),
            tool_version="1.0.0",
            config_version="v1",
            document_type="image",
            ocr_confidence={1: 0.92, 2: 0.93},  # Below 0.95 threshold
        )
        document = Document(id="DOC-001", text="Low quality content", metadata=metadata)
        context = ProcessingContext()

        validator = QualityValidator(ocr_confidence_threshold=0.95)
        result = validator.process(document, context)

        # Check quality flags
        assert "low_ocr_confidence" in result.metadata.quality_flags

    @patch("src.data_extract.normalize.validation.TESSERACT_AVAILABLE", True)
    def test_process_metadata_json_serialization(self):
        """Test that metadata with OCR confidence is JSON-serializable."""
        metadata = Metadata(
            source_file=Path("scanned.pdf"),
            file_hash="hash123",
            processing_timestamp=datetime.now(),
            tool_version="1.0.0",
            config_version="v1",
            document_type="image",
            ocr_confidence={1: 0.96, 2: 0.98},
        )
        document = Document(id="DOC-001", text="Scanned content", metadata=metadata)
        context = ProcessingContext()

        validator = QualityValidator()
        result = validator.process(document, context)

        # Test JSON serialization (Pydantic validation)
        metadata_dict = result.metadata.model_dump()
        assert "ocr_confidence" in metadata_dict
        assert metadata_dict["ocr_confidence"] == {1: 0.96, 2: 0.98}

        # Test JSON roundtrip
        import json

        json_str = json.dumps(metadata_dict, default=str)
        parsed = json.loads(json_str)
        assert "ocr_confidence" in parsed


class TestOCROperationLogging:
    """Test OCR operation logging (Story 2.4 - AC 2.4.7)."""

    @patch("src.data_extract.normalize.validation.TESSERACT_AVAILABLE", True)
    def test_process_logs_validation_started(self):
        """Test that process() logs validation start event."""
        metadata = Metadata(
            source_file=Path("scanned.pdf"),
            file_hash="hash123",
            processing_timestamp=datetime.now(),
            tool_version="1.0.0",
            config_version="v1",
            document_type="image",
            ocr_confidence={1: 0.96},
        )
        document = Document(id="DOC-001", text="Content", metadata=metadata)
        context = ProcessingContext()

        mock_logger = MagicMock()
        validator = QualityValidator(logger=mock_logger)
        validator.process(document, context)

        # Check validation started log
        validation_started_calls = [
            call
            for call in mock_logger.info.call_args_list
            if call[0][0] == "ocr_validation_started"
        ]
        assert len(validation_started_calls) == 1
        assert validation_started_calls[0][1]["document_id"] == "DOC-001"
        assert validation_started_calls[0][1]["threshold"] == 0.95

    @patch("src.data_extract.normalize.validation.TESSERACT_AVAILABLE", True)
    def test_process_logs_validation_complete_with_metrics(self):
        """Test that process() logs validation complete with confidence metrics."""
        metadata = Metadata(
            source_file=Path("scanned.pdf"),
            file_hash="hash123",
            processing_timestamp=datetime.now(),
            tool_version="1.0.0",
            config_version="v1",
            document_type="image",
            ocr_confidence={1: 0.92, 2: 0.93},
        )
        document = Document(id="DOC-001", text="Content", metadata=metadata)
        context = ProcessingContext()

        mock_logger = MagicMock()
        validator = QualityValidator(logger=mock_logger, ocr_confidence_threshold=0.95)
        validator.process(document, context)

        # Check validation complete log
        validation_complete_calls = [
            call
            for call in mock_logger.info.call_args_list
            if call[0][0] == "ocr_validation_complete"
        ]
        assert len(validation_complete_calls) == 1
        call_kwargs = validation_complete_calls[0][1]
        assert call_kwargs["document_id"] == "DOC-001"
        assert call_kwargs["document_average_confidence"] == pytest.approx(0.925, abs=0.001)
        assert call_kwargs["pages_below_threshold"] == 2
        assert "low_ocr_confidence" in call_kwargs["quality_flags"]
        assert call_kwargs["quarantine_recommended"] is True

    @patch("src.data_extract.normalize.validation.TESSERACT_AVAILABLE", True)
    def test_process_logs_quarantine_decision(self, tmp_path):
        """Test that process() logs quarantine decision with reason and threshold."""
        metadata = Metadata(
            source_file=Path("scanned.pdf"),
            file_hash="hash123",
            processing_timestamp=datetime.now(),
            tool_version="1.0.0",
            config_version="v1",
            document_type="image",
            ocr_confidence={1: 0.85},
        )
        document = Document(id="DOC-001", text="Low quality", metadata=metadata)
        context = ProcessingContext(config={"output_dir": tmp_path})

        mock_logger = MagicMock()
        validator = QualityValidator(
            logger=mock_logger, ocr_confidence_threshold=0.95, quarantine_low_confidence=True
        )
        validator.process(document, context)

        # Check quarantine log
        quarantine_calls = [
            call for call in mock_logger.info.call_args_list if call[0][0] == "document_quarantined"
        ]
        assert len(quarantine_calls) == 1
        call_kwargs = quarantine_calls[0][1]
        assert call_kwargs["document_id"] == "DOC-001"
        assert call_kwargs["reason"] == "low_ocr_confidence"
        assert call_kwargs["threshold"] == 0.95
        assert call_kwargs["average_confidence"] == 0.85
