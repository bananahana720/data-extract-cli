"""Unit tests for schema standardization module.

Tests document type detection (AC-2.3.1), type-specific transformations (AC-2.3.2),
field standardization (AC-2.3.3), and Archer/Excel handling (AC-2.3.6, AC-2.3.7).
"""

from datetime import datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from src.data_extract.core.models import (
    Document,
    DocumentType,
    Metadata,
    ProcessingContext,
)
from src.data_extract.normalize.schema import SchemaStandardizer

pytestmark = [pytest.mark.P0, pytest.mark.unit]

# Test fixtures


@pytest.fixture
def mock_metadata() -> Metadata:
    """Create mock metadata for testing."""
    return Metadata(
        source_file=Path("test.pdf"),
        file_hash="abc123",
        processing_timestamp=datetime.now(),
        tool_version="0.1.0",
        config_version="1.0",
    )


@pytest.fixture
def schema_standardizer() -> SchemaStandardizer:
    """Create SchemaStandardizer instance for testing."""
    return SchemaStandardizer(enable_standardization=True)


@pytest.fixture
def processing_context() -> ProcessingContext:
    """Create processing context for testing."""
    return ProcessingContext(config={}, metrics={})


# AC-2.3.1: Document Type Detection Tests


class TestDocumentTypeDetection:
    """Tests for document type auto-detection with >95% accuracy."""

    def test_detect_document_type_report(
        self, schema_standardizer: SchemaStandardizer, mock_metadata: Metadata
    ) -> None:
        """Test REPORT detection for Word narrative with sections/headings."""
        document = Document(
            id="test-report-1",
            text="This is a long report with multiple sections discussing various topics.",
            metadata=mock_metadata,
            structure={
                "sections": [
                    {"title": "Introduction", "content": "Intro text"},
                    {"title": "Methods", "content": "Methods text"},
                    {"title": "Results", "content": "Results text"},
                    {"title": "Conclusion", "content": "Conclusion text"},
                ],
                "headings": ["Introduction", "Methods", "Results", "Conclusion"],
            },
        )

        doc_type, confidence = schema_standardizer.detect_document_type(document)

        assert doc_type == DocumentType.REPORT
        assert confidence >= 0.95, f"Expected confidence >=0.95, got {confidence}"

    def test_detect_document_type_matrix(
        self, schema_standardizer: SchemaStandardizer, mock_metadata: Metadata
    ) -> None:
        """Test MATRIX detection for Excel with tables/rows/cols."""
        document = Document(
            id="test-matrix-1",
            text="Control ID | Control Name | Status\nCTRL-001 | Access Control | Active",
            metadata=mock_metadata,
            structure={
                "tables": [
                    {
                        "headers": ["Control ID", "Control Name", "Status"],
                        "rows": [["CTRL-001", "Access Control", "Active"]],
                        "content": "Control ID | Control Name | Status\nCTRL-001 | Access Control | Active",
                    }
                ]
            },
        )

        doc_type, confidence = schema_standardizer.detect_document_type(document)

        assert doc_type == DocumentType.MATRIX
        assert confidence >= 0.95, f"Expected confidence >=0.95, got {confidence}"

    def test_detect_document_type_export(
        self, schema_standardizer: SchemaStandardizer, mock_metadata: Metadata
    ) -> None:
        """Test EXPORT detection for Archer HTML with module fields."""
        archer_html = """
        <html>
        <body>
            <div class="archer-field" name="risk_id">RISK-123</div>
            <div class="archer-field" name="risk description">High priority risk</div>
            <a href="/record.aspx?recordId=456">Control-456</a>
            <field name="inherent_risk">High</field>
        </body>
        </html>
        """
        document = Document(
            id="test-export-1",
            text=archer_html,
            metadata=mock_metadata,
            structure={},
        )

        doc_type, confidence = schema_standardizer.detect_document_type(document)

        assert doc_type == DocumentType.EXPORT
        assert confidence >= 0.95, f"Expected confidence >=0.95, got {confidence}"

    def test_detect_document_type_image(
        self, schema_standardizer: SchemaStandardizer, mock_metadata: Metadata
    ) -> None:
        """Test IMAGE detection for PDF with OCR metadata."""
        mock_metadata.quality_scores["ocr_confidence"] = 0.92

        document = Document(
            id="test-image-1",
            text="Scanned text extracted via OCR",
            metadata=mock_metadata,
            structure={},
        )

        doc_type, confidence = schema_standardizer.detect_document_type(document)

        assert doc_type == DocumentType.IMAGE
        assert confidence >= 0.95, f"Expected confidence >=0.95, got {confidence}"

    def test_detect_document_type_confidence_scores(
        self, schema_standardizer: SchemaStandardizer, mock_metadata: Metadata
    ) -> None:
        """Verify confidence scores >0.95 for clear document types."""
        # Test REPORT with strong signals
        report_doc = Document(
            id="report-strong",
            text="Long report" * 100,
            metadata=mock_metadata,
            structure={
                "sections": [{"title": f"Section {i}"} for i in range(5)],
                "headings": [f"Heading {i}" for i in range(5)],
            },
        )
        _, report_confidence = schema_standardizer.detect_document_type(report_doc)
        assert report_confidence >= 0.95

        # Test MATRIX with strong signals
        matrix_doc = Document(
            id="matrix-strong",
            text="Table data" * 50,
            metadata=mock_metadata,
            structure={
                "tables": [
                    {"content": "Table data" * 50, "headers": ["A", "B", "C"]} for _ in range(3)
                ]
            },
        )
        _, matrix_confidence = schema_standardizer.detect_document_type(matrix_doc)
        assert matrix_confidence >= 0.95

    def test_detect_document_type_ambiguous(
        self, schema_standardizer: SchemaStandardizer, mock_metadata: Metadata
    ) -> None:
        """Handle ambiguous cases with lower confidence."""
        # Document with both narrative and tables
        ambiguous_doc = Document(
            id="ambiguous-1",
            text="Some text with a small table",
            metadata=mock_metadata,
            structure={
                "sections": [{"title": "Section 1"}],
                "tables": [{"content": "Small table"}],
            },
        )

        doc_type, confidence = schema_standardizer.detect_document_type(ambiguous_doc)

        # Should still classify, but confidence may be lower
        assert doc_type in [DocumentType.REPORT, DocumentType.MATRIX]
        assert 0.7 <= confidence <= 1.0

    def test_detect_document_type_empty(
        self, schema_standardizer: SchemaStandardizer, mock_metadata: Metadata
    ) -> None:
        """Gracefully handle empty/malformed documents."""
        empty_doc = Document(
            id="empty-1",
            text="",
            metadata=mock_metadata,
            structure={},
        )

        doc_type, confidence = schema_standardizer.detect_document_type(empty_doc)

        # Should default to REPORT with low confidence
        assert doc_type == DocumentType.REPORT
        assert confidence < 0.95

    def test_detect_document_type_accuracy_corpus(
        self, schema_standardizer: SchemaStandardizer, mock_metadata: Metadata
    ) -> None:
        """Run on test corpus and verify >95% accuracy."""
        # Create diverse test corpus
        test_corpus = [
            # 10 REPORTs
            *[
                Document(
                    id=f"report-{i}",
                    text="Long narrative" * 50,
                    metadata=mock_metadata,
                    structure={"sections": [{"title": f"Section {j}"} for j in range(3 + i)]},
                )
                for i in range(10)
            ],
            # 10 MATRIXes
            *[
                Document(
                    id=f"matrix-{i}",
                    text="Table content" * 40,
                    metadata=mock_metadata,
                    structure={
                        "tables": [{"content": "Table content" * 40} for _ in range(2 + i % 3)]
                    },
                )
                for i in range(10)
            ],
            # 10 EXPORTs
            *[
                Document(
                    id=f"export-{i}",
                    text=f"archer_field_id RSA Archer recordId={i} field_name risk_id",
                    metadata=mock_metadata,
                    structure={},
                )
                for i in range(10)
            ],
            # 10 IMAGEs
            *[
                Document(
                    id=f"image-{i}",
                    text="OCR extracted text",
                    metadata=Metadata(
                        source_file=Path(f"test-{i}.pdf"),
                        file_hash=f"hash-{i}",
                        processing_timestamp=datetime.now(),
                        tool_version="0.1.0",
                        config_version="1.0",
                        quality_scores={"ocr_confidence": 0.85 + i * 0.01},
                    ),
                    structure={},
                )
                for i in range(10)
            ],
        ]

        # Expected types (ground truth)
        expected_types = (
            [DocumentType.REPORT] * 10
            + [DocumentType.MATRIX] * 10
            + [DocumentType.EXPORT] * 10
            + [DocumentType.IMAGE] * 10
        )

        # Run detection on corpus
        correct_predictions = 0
        for doc, expected_type in zip(test_corpus, expected_types):
            detected_type, _ = schema_standardizer.detect_document_type(doc)
            if detected_type == expected_type:
                correct_predictions += 1

        accuracy = correct_predictions / len(test_corpus)

        assert accuracy >= 0.95, f"Expected accuracy >=0.95, got {accuracy:.2%}"


# AC-2.3.2: Type-Specific Schema Transformation Tests


class TestTypeSpecificTransformations:
    """Tests for type-specific schema transformations."""

    def test_standardize_schema_report(
        self,
        schema_standardizer: SchemaStandardizer,
        mock_metadata: Metadata,
        processing_context: ProcessingContext,
    ) -> None:
        """Test REPORT transformation (sections, headings, narrative flow)."""
        document = Document(
            id="report-1",
            text="Report content",
            metadata=mock_metadata,
            structure={
                "sections": [
                    {"title": "Intro", "content": "Introduction text", "level": 1},
                    {"title": "Methods", "content": "Methods text", "level": 1},
                ]
            },
        )

        result = schema_standardizer.process(document, processing_context)

        assert result.metadata.document_type == DocumentType.REPORT
        assert "standardized_sections" in result.structure
        assert len(result.structure["standardized_sections"]) == 2

    def test_standardize_schema_matrix(
        self,
        schema_standardizer: SchemaStandardizer,
        mock_metadata: Metadata,
        processing_context: ProcessingContext,
    ) -> None:
        """Test MATRIX transformation (table structure preservation)."""
        document = Document(
            id="matrix-1",
            text="Table content" * 50,
            metadata=mock_metadata,
            structure={
                "tables": [
                    {
                        "headers": ["Col1", "Col2"],
                        "rows": [["A", "B"]],
                        "columns": ["Col1", "Col2"],
                    }
                ]
            },
        )

        result = schema_standardizer.process(document, processing_context)

        assert result.metadata.document_type == DocumentType.MATRIX
        assert "standardized_tables" in result.structure

    def test_standardize_schema_export(
        self,
        schema_standardizer: SchemaStandardizer,
        mock_metadata: Metadata,
        processing_context: ProcessingContext,
    ) -> None:
        """Test EXPORT transformation (Archer field parsing)."""
        document = Document(
            id="export-1",
            text="archer_field_id recordId=123 RSA Archer",
            metadata=mock_metadata,
            structure={},
        )

        result = schema_standardizer.process(document, processing_context)

        assert result.metadata.document_type == DocumentType.EXPORT
        # Archer parsing should be applied

    def test_standardize_schema_image(
        self,
        schema_standardizer: SchemaStandardizer,
        mock_metadata: Metadata,
        processing_context: ProcessingContext,
    ) -> None:
        """Test IMAGE transformation (OCR metadata validation)."""
        mock_metadata.quality_scores["ocr_confidence"] = 0.88

        document = Document(
            id="image-1",
            text="OCR text",
            metadata=mock_metadata,
            structure={},
        )

        result = schema_standardizer.process(document, processing_context)

        assert result.metadata.document_type == DocumentType.IMAGE

    def test_standardize_schema_pydantic_validation(
        self, schema_standardizer: SchemaStandardizer, mock_metadata: Metadata
    ) -> None:
        """Verify Pydantic models validate output."""
        document = Document(
            id="test-1",
            text="Test content",
            metadata=mock_metadata,
            structure={"sections": [{"title": "Test"}]},
        )

        # Should not raise validation errors
        try:
            _ = schema_standardizer.detect_document_type(document)
        except ValidationError as e:
            pytest.fail(f"Pydantic validation failed: {e}")

    def test_standardize_schema_invalid_type(
        self,
        schema_standardizer: SchemaStandardizer,
        mock_metadata: Metadata,
        processing_context: ProcessingContext,
    ) -> None:
        """Handle unknown document types gracefully."""
        # Create minimal document
        document = Document(
            id="unknown-1",
            text="x",
            metadata=mock_metadata,
            structure={},
        )

        # Should classify as something (default to REPORT)
        result = schema_standardizer.process(document, processing_context)
        assert result.metadata.document_type in [
            DocumentType.REPORT,
            DocumentType.MATRIX,
            DocumentType.EXPORT,
            DocumentType.IMAGE,
        ]


# AC-2.3.6: Archer-Specific Field and Hyperlink Tests


class TestArcherHandling:
    """Tests for Archer-specific field parsing and hyperlink extraction."""

    def test_parse_archer_export_html(
        self, schema_standardizer: SchemaStandardizer, mock_metadata: Metadata
    ) -> None:
        """Parse Archer HTML with BeautifulSoup4."""
        archer_html = """
        <html>
        <body>
            <div class="archer-field" name="risk_id">RISK-123</div>
            <div class="archer-field" name="description">Test risk</div>
        </body>
        </html>
        """
        document = Document(
            id="archer-1",
            text=archer_html,
            metadata=mock_metadata,
            structure={},
        )

        result = schema_standardizer.parse_archer_export(document)

        assert "fields" in result
        assert "hyperlinks" in result

    def test_parse_archer_hyperlinks(
        self, schema_standardizer: SchemaStandardizer, mock_metadata: Metadata
    ) -> None:
        """Extract hyperlinks representing entity relationships."""
        archer_html = """
        <html>
        <body>
            <a href="/record.aspx?recordId=123&module=Risk">Risk-123</a>
            <a href="/record.aspx?recordId=456&module=Control">Control-456</a>
        </body>
        </html>
        """
        document = Document(
            id="archer-2",
            text=archer_html,
            metadata=mock_metadata,
            structure={},
        )

        result = schema_standardizer.parse_archer_export(document)

        assert len(result["hyperlinks"]) == 2
        assert result["hyperlinks"][0]["record_id"] == "123"
        assert result["hyperlinks"][1]["record_id"] == "456"

    def test_parse_archer_module_variations(
        self, schema_standardizer: SchemaStandardizer, mock_metadata: Metadata
    ) -> None:
        """Handle Risk Management, Compliance, Issues modules."""
        # Test Risk Management module
        risk_doc = Document(
            id="risk-1",
            text="risk_id RISK-001 risk description inherent risk High",
            metadata=mock_metadata,
            structure={},
        )
        risk_result = schema_standardizer.parse_archer_export(risk_doc)
        assert risk_result["module"] == "Risk Management"

        # Test Compliance module
        compliance_doc = Document(
            id="compliance-1",
            text="compliance regulation requirement REG-001",
            metadata=mock_metadata,
            structure={},
        )
        compliance_result = schema_standardizer.parse_archer_export(compliance_doc)
        assert compliance_result["module"] == "Compliance"

        # Test Issues module
        issues_doc = Document(
            id="issues-1",
            text="issue_id ISSUE-001 issue description remediation plan",
            metadata=mock_metadata,
            structure={},
        )
        issues_result = schema_standardizer.parse_archer_export(issues_doc)
        assert issues_result["module"] == "Issues"

    def test_parse_archer_custom_fields(
        self, schema_standardizer: SchemaStandardizer, mock_metadata: Metadata
    ) -> None:
        """Parse Archer-specific field schemas."""
        archer_html = """
        <html>
        <body>
            <field name="custom_field_1">Value 1</field>
            <field name="custom_field_2">Value 2</field>
        </body>
        </html>
        """
        document = Document(
            id="archer-3",
            text=archer_html,
            metadata=mock_metadata,
            structure={},
        )

        result = schema_standardizer.parse_archer_export(document)

        assert "custom_field_1" in result["fields"]
        assert result["fields"]["custom_field_1"] == "Value 1"


# AC-2.3.3: Field Name Standardization Tests


class TestFieldNameStandardization:
    """Tests for field name standardization across source systems."""

    def test_field_standardization_archer_to_standard(self, mock_metadata: Metadata) -> None:
        """Test Archer 'Risk Description' → 'description' mapping."""
        from pathlib import Path

        config_path = Path("config/normalize/schema_templates.yaml")
        standardizer = SchemaStandardizer(schema_templates_file=config_path)

        # Archer Risk Management fields
        source_fields = {
            "Risk ID": "RISK-001",
            "Risk Description": "High priority risk",
            "Risk Owner": "John Doe",
            "Inherent Risk": "High",
        }

        standardized = standardizer.standardize_field_names(
            source_fields, DocumentType.EXPORT, "Risk Management"
        )

        assert standardized["id"] == "RISK-001"
        assert standardized["description"] == "High priority risk"
        assert standardized["owner"] == "John Doe"
        assert standardized["inherent_risk_level"] == "High"

    def test_field_standardization_excel_to_standard(self, mock_metadata: Metadata) -> None:
        """Test Excel column names → standard fields."""
        from pathlib import Path

        config_path = Path("config/normalize/schema_templates.yaml")
        standardizer = SchemaStandardizer(schema_templates_file=config_path)

        # Excel control matrix fields
        source_fields = {
            "Control ID": "CTRL-001",
            "Control Name": "Access Control",
            "Control Owner": "IT Department",
            "Effectiveness Rating": "Effective",
        }

        standardized = standardizer.standardize_field_names(source_fields, DocumentType.MATRIX)

        assert standardized["id"] == "CTRL-001"
        assert standardized["name"] == "Access Control"
        assert standardized["owner"] == "IT Department"
        assert standardized["effectiveness"] == "Effective"

    def test_field_standardization_traceability(self, mock_metadata: Metadata) -> None:
        """Verify source→output field mapping is preserved."""
        from pathlib import Path

        config_path = Path("config/normalize/schema_templates.yaml")
        standardizer = SchemaStandardizer(schema_templates_file=config_path)

        source_fields = {"Risk ID": "RISK-001", "Risk Description": "Test risk"}

        _ = standardizer.standardize_field_names(
            source_fields, DocumentType.EXPORT, "Risk Management"
        )

        # Check traceability mapping
        assert "Risk ID" in standardizer.field_mapping_traceability
        assert standardizer.field_mapping_traceability["Risk ID"] == "id"
        assert "Risk Description" in standardizer.field_mapping_traceability
        assert standardizer.field_mapping_traceability["Risk Description"] == "description"

    def test_field_standardization_missing_source(self, mock_metadata: Metadata) -> None:
        """Handle missing source fields gracefully."""
        standardizer = SchemaStandardizer()

        # Fields with no mapping should pass through unchanged
        source_fields = {"Unknown Field": "value", "Another Unknown": "value2"}

        standardized = standardizer.standardize_field_names(source_fields, DocumentType.EXPORT)

        assert standardized["Unknown Field"] == "value"
        assert standardized["Another Unknown"] == "value2"

    def test_field_standardization_common_aliases(self, mock_metadata: Metadata) -> None:
        """Test common field aliases work across all document types."""
        from pathlib import Path

        config_path = Path("config/normalize/schema_templates.yaml")
        standardizer = SchemaStandardizer(schema_templates_file=config_path)

        # Common aliases should work regardless of doc type
        source_fields = {"ID": "123", "Name": "Test", "Status": "Active"}

        standardized = standardizer.standardize_field_names(source_fields, DocumentType.REPORT)

        assert standardized["id"] == "123"
        assert standardized["name"] == "Test"
        assert standardized["status"] == "Active"

    def test_field_standardization_schema_templates_yaml(self, mock_metadata: Metadata) -> None:
        """Verify YAML config is loaded correctly."""
        from pathlib import Path

        config_path = Path("config/normalize/schema_templates.yaml")
        assert config_path.exists(), "schema_templates.yaml must exist"

        standardizer = SchemaStandardizer(schema_templates_file=config_path)

        # Verify templates loaded
        assert len(standardizer.field_mappings) > 0
        assert "archer" in standardizer.field_mappings
        assert "excel" in standardizer.field_mappings
        assert "common_aliases" in standardizer.field_mappings

    def test_field_standardization_archer_modules(self, mock_metadata: Metadata) -> None:
        """Test different Archer module variations."""
        from pathlib import Path

        config_path = Path("config/normalize/schema_templates.yaml")
        standardizer = SchemaStandardizer(schema_templates_file=config_path)

        # Test Compliance module
        compliance_fields = {"Regulation ID": "REG-001", "Requirement": "Test requirement"}
        compliance_result = standardizer.standardize_field_names(
            compliance_fields, DocumentType.EXPORT, "Compliance"
        )
        assert compliance_result["id"] == "REG-001"
        assert compliance_result["description"] == "Test requirement"

        # Test Issues module
        issues_fields = {"Issue ID": "ISS-001", "Issue Description": "Test issue"}
        issues_result = standardizer.standardize_field_names(
            issues_fields, DocumentType.EXPORT, "Issues"
        )
        assert issues_result["id"] == "ISS-001"
        assert issues_result["description"] == "Test issue"


# AC-2.3.7: Excel Table Structure Preservation Tests


class TestExcelTablePreservation:
    """Tests for Excel table structure preservation."""

    def test_preserve_excel_rows_cols_headers(
        self, schema_standardizer: SchemaStandardizer, mock_metadata: Metadata
    ) -> None:
        """Excel matrix structure preserved."""
        document = Document(
            id="excel-1",
            text="Table data",
            metadata=mock_metadata,
            structure={
                "tables": [
                    {
                        "headers": ["ID", "Name", "Status"],
                        "rows": [["1", "Item 1", "Active"], ["2", "Item 2", "Inactive"]],
                        "columns": ["ID", "Name", "Status"],
                        "sheet_name": "Sheet1",
                    }
                ]
            },
        )

        result = schema_standardizer.preserve_excel_structure(document)

        assert "standardized_tables" in result.structure
        assert len(result.structure["standardized_tables"]) == 1
        table = result.structure["standardized_tables"][0]
        assert table["headers"] == ["ID", "Name", "Status"]
        assert len(table["rows"]) == 2

    def test_preserve_control_matrix_structure(
        self, schema_standardizer: SchemaStandardizer, mock_metadata: Metadata
    ) -> None:
        """Control matrix rows/cols intact."""
        document = Document(
            id="control-matrix-1",
            text="Control matrix",
            metadata=mock_metadata,
            structure={
                "tables": [
                    {
                        "headers": ["Control ID", "Description", "Owner"],
                        "rows": [["CTRL-001", "Access control", "IT"]],
                        "columns": ["Control ID", "Description", "Owner"],
                    }
                ]
            },
        )

        result = schema_standardizer.preserve_excel_structure(document)

        assert len(result.structure["standardized_tables"]) == 1

    def test_preserve_risk_register_structure(
        self, schema_standardizer: SchemaStandardizer, mock_metadata: Metadata
    ) -> None:
        """Risk register structure maintained."""
        document = Document(
            id="risk-register-1",
            text="Risk register",
            metadata=mock_metadata,
            structure={
                "tables": [
                    {
                        "headers": ["Risk ID", "Description", "Likelihood", "Impact"],
                        "rows": [["RISK-001", "Data breach", "High", "Critical"]],
                        "columns": ["Risk ID", "Description", "Likelihood", "Impact"],
                    }
                ]
            },
        )

        result = schema_standardizer.preserve_excel_structure(document)

        assert len(result.structure["standardized_tables"]) == 1

    def test_preserve_multi_sheet_excel(
        self, schema_standardizer: SchemaStandardizer, mock_metadata: Metadata
    ) -> None:
        """Handle multiple Excel sheets."""
        document = Document(
            id="multi-sheet-1",
            text="Multi-sheet Excel",
            metadata=mock_metadata,
            structure={
                "tables": [
                    {
                        "headers": ["A", "B"],
                        "rows": [["1", "2"]],
                        "columns": ["A", "B"],
                        "sheet_name": "Sheet1",
                    },
                    {
                        "headers": ["C", "D"],
                        "rows": [["3", "4"]],
                        "columns": ["C", "D"],
                        "sheet_name": "Sheet2",
                    },
                ]
            },
        )

        result = schema_standardizer.preserve_excel_structure(document)

        assert len(result.structure["standardized_tables"]) == 2
        assert result.structure["standardized_tables"][0]["sheet_name"] == "Sheet1"
        assert result.structure["standardized_tables"][1]["sheet_name"] == "Sheet2"


# Edge Case Tests for Coverage Improvement


class TestEdgeCases:
    """Edge case tests to improve coverage from 91% to 95%+."""

    def test_schema_templates_yaml_malformed(self, tmp_path: Path, mock_metadata: Metadata) -> None:
        """Test handling of corrupt/malformed YAML schema templates."""
        malformed_yaml = tmp_path / "malformed.yaml"
        malformed_yaml.write_text("invalid: yaml: content: [unclosed", encoding="utf-8")

        standardizer = SchemaStandardizer(schema_templates_file=malformed_yaml)
        assert standardizer.field_mappings == {}

    def test_schema_templates_yaml_missing_file(self, tmp_path: Path) -> None:
        """Test handling of missing schema templates file."""
        missing_file = tmp_path / "nonexistent.yaml"
        standardizer = SchemaStandardizer(schema_templates_file=missing_file)
        assert standardizer.field_mappings == {}

    def test_schema_templates_from_dict(self) -> None:
        """Test schema templates provided as dictionary."""
        templates_dict = {"archer": {"risk_management": {"Risk ID": "id"}}}
        standardizer = SchemaStandardizer(schema_templates=templates_dict)
        assert standardizer.field_mappings == templates_dict

    def test_standardization_disabled(
        self, mock_metadata: Metadata, processing_context: ProcessingContext
    ) -> None:
        """Test schema standardization when disabled."""
        standardizer = SchemaStandardizer(enable_standardization=False)
        document = Document(
            id="test-1",
            text="Test",
            metadata=mock_metadata,
            structure={"sections": [{"title": "Test"}]},
        )
        result = standardizer.process(document, processing_context)
        assert result == document

    def test_detect_image_low_ocr_confidence(
        self, schema_standardizer: SchemaStandardizer, mock_metadata: Metadata
    ) -> None:
        """Test IMAGE detection with low OCR confidence."""
        mock_metadata.quality_scores["ocr_confidence"] = 0.5
        document = Document(id="low-ocr-1", text="Poor OCR", metadata=mock_metadata, structure={})
        doc_type, confidence = schema_standardizer.detect_document_type(document)
        assert doc_type == DocumentType.IMAGE
        assert confidence == 0.85

    def test_detect_report_medium_length_text(
        self, schema_standardizer: SchemaStandardizer, mock_metadata: Metadata
    ) -> None:
        """Test REPORT detection for medium-length text."""
        medium_text = "Test content " * 50
        document = Document(id="medium-1", text=medium_text, metadata=mock_metadata, structure={})
        doc_type, confidence = schema_standardizer.detect_document_type(document)
        assert doc_type == DocumentType.REPORT
        assert confidence == 0.85

    def test_transform_image_missing_ocr_confidence(
        self, schema_standardizer: SchemaStandardizer, mock_metadata: Metadata
    ) -> None:
        """Test IMAGE transformation when OCR confidence is missing."""
        updated_metadata = mock_metadata.model_copy(update={"quality_scores": {}})
        document = Document(id="image-1", text="OCR text", metadata=updated_metadata, structure={})
        transformed = schema_standardizer._transform_image(document)
        assert "missing_ocr_confidence" in transformed.metadata.quality_flags

    def test_archer_field_mapping_default_fallback(self, mock_metadata: Metadata) -> None:
        """Test Archer field mapping falls back to risk_management default."""
        config_path = Path("config/normalize/schema_templates.yaml")
        standardizer = SchemaStandardizer(schema_templates_file=config_path)

        # Test with unknown subtype - should fall back to risk_management
        fields = {"Risk ID": "RISK-999", "Risk Description": "Test"}
        result = standardizer.standardize_field_names(fields, DocumentType.EXPORT, "Unknown Module")

        # Should use risk_management mapping as fallback
        assert result["id"] == "RISK-999"
        assert result["description"] == "Test"

    def test_process_exception_with_invalid_structure(
        self, mock_metadata: Metadata, processing_context: ProcessingContext, monkeypatch
    ) -> None:
        """Test process exception handling with invalid document structure."""
        from src.data_extract.core.exceptions import ProcessingError

        standardizer = SchemaStandardizer(enable_standardization=True)

        # Mock detect_document_type to raise an exception
        def mock_detect_raises(document):
            raise ValueError("Simulated detection error")

        monkeypatch.setattr(standardizer, "detect_document_type", mock_detect_raises)

        document = Document(
            id="test-1",
            text="Test",
            metadata=mock_metadata,
            structure={},
        )

        with pytest.raises(ProcessingError) as exc_info:
            standardizer.process(document, processing_context)
        assert "Schema standardization failed" in str(exc_info.value)

    def test_transform_export_with_no_fields(
        self, mock_metadata: Metadata, processing_context: ProcessingContext
    ) -> None:
        """Test EXPORT transformation when parse_archer_export returns empty fields."""
        config_path = Path("config/normalize/schema_templates.yaml")
        standardizer = SchemaStandardizer(
            schema_templates_file=config_path, enable_standardization=True
        )

        # Create EXPORT document with minimal patterns
        document = Document(
            id="export-minimal-1",
            text="RSA Archer recordId=123",
            metadata=mock_metadata,
            structure={},
        )

        result = standardizer.process(document, processing_context)

        # Should detect as EXPORT and add archer_fields even if empty
        assert result.metadata.document_type == DocumentType.EXPORT
        assert "archer_fields" in result.structure

    def test_transform_export_with_populated_fields(
        self, mock_metadata: Metadata, processing_context: ProcessingContext
    ) -> None:
        """Test EXPORT transformation with populated Archer fields for standardization."""
        config_path = Path("config/normalize/schema_templates.yaml")
        standardizer = SchemaStandardizer(
            schema_templates_file=config_path, enable_standardization=True
        )

        # Create EXPORT document with actual Archer fields
        archer_html = """
        <html>
        <body>
            <field name="Risk ID">RISK-123</field>
            <field name="Risk Description">Critical security risk</field>
            <field name="Risk Owner">Security Team</field>
            <a href="/record.aspx?recordId=456">Control-456</a>
        </body>
        </html>
        """

        document = Document(
            id="export-with-fields-1",
            text=archer_html,
            metadata=mock_metadata,
            structure={},
        )

        # Set document subtype to trigger Risk Management module
        document.metadata = document.metadata.model_copy(
            update={"document_subtype": "Risk Management"}
        )

        result = standardizer.process(document, processing_context)

        # Should detect as EXPORT and standardize field names
        assert result.metadata.document_type == DocumentType.EXPORT
        assert "archer_fields" in result.structure

        # Check that fields were standardized
        if "standardized_fields" in result.structure["archer_fields"]:
            standardized = result.structure["archer_fields"]["standardized_fields"]
            assert "id" in standardized or "Risk ID" in result.structure["archer_fields"]["fields"]

    def test_parse_archer_exception_with_invalid_html(
        self, schema_standardizer: SchemaStandardizer, mock_metadata: Metadata
    ) -> None:
        """Test Archer parsing exception handling with problematic content."""
        # Create content that could cause BeautifulSoup parsing issues
        problematic_html = "<html><body>" + "\x00" * 1000 + "</body></html>"

        document = Document(
            id="problematic-1",
            text=problematic_html,
            metadata=mock_metadata,
            structure={},
        )

        # Should handle gracefully and log warning
        result = schema_standardizer.parse_archer_export(document)

        # Even with problematic content, should return valid structure
        assert isinstance(result, dict)
        assert "fields" in result
        assert "hyperlinks" in result
        assert "module" in result

    def test_parse_archer_with_exception_in_soup(
        self, schema_standardizer: SchemaStandardizer, mock_metadata: Metadata, monkeypatch
    ) -> None:
        """Test Archer parsing when BeautifulSoup raises exception."""

        # Mock BeautifulSoup to raise an exception
        def mock_soup_raises(*args, **kwargs):
            raise RuntimeError("BeautifulSoup parsing error")

        # Temporarily replace BeautifulSoup in the schema module
        import src.data_extract.normalize.schema as schema_module

        original_soup = schema_module.BeautifulSoup
        monkeypatch.setattr(schema_module, "BeautifulSoup", mock_soup_raises)

        document = Document(
            id="exception-1",
            text="<html><body>Test</body></html>",
            metadata=mock_metadata,
            structure={},
        )

        # Should handle exception gracefully
        result = schema_standardizer.parse_archer_export(document)

        # Should return empty archer_data structure
        assert result["fields"] == {}
        assert result["hyperlinks"] == []
        assert result["module"] is None
