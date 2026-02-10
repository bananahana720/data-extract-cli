"""Schema standardization for document type detection and transformation.

This module implements document type auto-detection and type-specific schema
transformations to ensure consistent structure across Word reports, Excel matrices,
PDF documents, and Archer GRC exports.

Classes:
    SchemaStandardizer: Pipeline stage for document type detection and schema transformation
"""

from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import structlog
import yaml
from bs4 import BeautifulSoup

from ..core.exceptions import ProcessingError
from ..core.models import Document, DocumentType, ProcessingContext
from ..core.pipeline import PipelineStage


class SchemaStandardizer(PipelineStage[Document, Document]):
    """Schema standardizer for document type detection and transformation.

    Implements PipelineStage protocol to detect document types (REPORT, MATRIX,
    EXPORT, IMAGE) with >95% accuracy and apply type-specific schema transformations.

    Attributes:
        logger: Structured logger for audit trail
        schema_templates: Field mapping templates loaded from YAML config
        enable_standardization: Flag to enable/disable schema standardization
    """

    def __init__(
        self,
        schema_templates: Optional[Dict[str, Any]] = None,
        schema_templates_file: Optional[Path] = None,
        enable_standardization: bool = True,
        logger: Optional[Any] = None,
    ) -> None:
        """Initialize schema standardizer.

        Args:
            schema_templates: Field mapping templates for standardization (dict)
            schema_templates_file: Path to schema_templates.yaml file
            enable_standardization: Enable/disable schema standardization
            logger: Structured logger instance
        """
        self.logger = logger or structlog.get_logger(__name__)
        self.enable_standardization = enable_standardization
        self.field_mappings: Dict[str, Any] = {}
        self.field_mapping_traceability: Dict[str, str] = {}  # source -> output mapping

        # Load schema templates from file or dict
        if schema_templates:
            self.field_mappings = schema_templates
        elif schema_templates_file and schema_templates_file.exists():
            try:
                with open(schema_templates_file, "r", encoding="utf-8") as f:
                    self.field_mappings = yaml.safe_load(f) or {}
                self.logger.info(
                    "schema_templates_loaded",
                    file=str(schema_templates_file),
                    template_count=len(self.field_mappings),
                )
            except Exception as e:
                self.logger.error(
                    "schema_templates_load_failed",
                    file=str(schema_templates_file),
                    error=str(e),
                )
                self.field_mappings = {}

    def standardize_field_names(
        self,
        fields: Dict[str, Any],
        doc_type: DocumentType,
        doc_subtype: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Standardize field names using configured mappings.

        Args:
            fields: Dictionary of source fields to standardize
            doc_type: Document type (REPORT, MATRIX, EXPORT, IMAGE)
            doc_subtype: Document subtype (e.g., Archer module name)

        Returns:
            Dictionary with standardized field names
        """
        standardized = {}

        # Get appropriate mapping based on doc_type and doc_subtype
        mapping = self._get_field_mapping(doc_type, doc_subtype)

        for source_field, value in fields.items():
            # Try to find mapping for this field
            standardized_name = mapping.get(source_field, source_field)

            # Also check common aliases
            if standardized_name == source_field and "common_aliases" in self.field_mappings:
                standardized_name = self.field_mappings["common_aliases"].get(
                    source_field, source_field
                )

            standardized[standardized_name] = value

            # Track mapping for traceability
            if standardized_name != source_field:
                self.field_mapping_traceability[source_field] = standardized_name

        return standardized

    def _get_field_mapping(
        self, doc_type: DocumentType, doc_subtype: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get field mapping for document type and subtype.

        Args:
            doc_type: Document type
            doc_subtype: Document subtype (optional)

        Returns:
            Field mapping dictionary
        """
        if doc_type == DocumentType.EXPORT and "archer" in self.field_mappings:
            # Archer exports have module-specific mappings
            if doc_subtype:
                subtype_key = doc_subtype.lower().replace(" ", "_")
                if subtype_key in self.field_mappings["archer"]:
                    return dict(self.field_mappings["archer"][subtype_key])

            # Default to risk_management if subtype not found
            return dict(self.field_mappings["archer"].get("risk_management", {}))

        elif doc_type == DocumentType.MATRIX and "excel" in self.field_mappings:
            # Excel matrices default to control_matrix
            return dict(self.field_mappings["excel"].get("control_matrix", {}))

        elif doc_type == DocumentType.REPORT and "word" in self.field_mappings:
            # Word reports use report_sections mapping
            return dict(self.field_mappings["word"].get("report_sections", {}))

        return {}

    def process(self, document: Document, context: ProcessingContext) -> Document:
        """Apply schema standardization to document.

        Detects document type and applies type-specific transformations to ensure
        consistent schema across all document sources.

        Args:
            document: Document to standardize
            context: Processing context with config and metrics

        Returns:
            Document with standardized schema and updated metadata

        Raises:
            ProcessingError: If schema detection fails (graceful degradation)
        """
        if not self.enable_standardization:
            self.logger.info("schema_standardization_disabled")
            return document

        try:
            # Detect document type with confidence score
            doc_type, confidence = self.detect_document_type(document)
            self.logger.info(
                "document_type_detected",
                doc_type=doc_type.value,
                confidence=confidence,
                document_id=document.id,
            )

            # Update document metadata with document type and quality flags
            quality_flags_update = document.metadata.quality_flags.copy()
            if confidence < 0.95:
                quality_flags_update.append(f"low_type_confidence:{confidence:.2f}")

            document.metadata = document.metadata.model_copy(
                update={
                    "document_type": doc_type,
                    "quality_flags": quality_flags_update,
                }
            )

            # Apply type-specific schema transformation
            document = self.standardize_schema(document, doc_type)

            # Update context metrics
            context.metrics.setdefault("schema_standardization", {})["documents_processed"] = (
                context.metrics.get("schema_standardization", {}).get("documents_processed", 0) + 1
            )

            return document

        except Exception as e:
            self.logger.error(
                "schema_standardization_failed",
                document_id=document.id,
                error=str(e),
            )
            raise ProcessingError(f"Schema standardization failed: {e}") from e

    def detect_document_type(self, document: Document) -> Tuple[DocumentType, float]:
        """Detect document type using structure analysis.

        Analyzes document structure (sections, tables, fields, OCR metadata) to
        determine document type with >95% accuracy.

        Args:
            document: Document to classify

        Returns:
            Tuple of (DocumentType, confidence_score)
        """
        structure = document.structure
        text = document.text
        metadata = document.metadata

        # Calculate structural features
        has_sections = bool(structure.get("sections"))
        has_headings = bool(structure.get("headings"))
        has_tables = bool(structure.get("tables"))
        has_ocr_metadata = "ocr_confidence" in metadata.quality_scores
        text_length = len(text)
        table_count = len(structure.get("tables", []))

        # Archer export detection (HTML/XML with specific field patterns)
        is_archer_export = self._detect_archer_export(text, structure)

        # IMAGE: Has OCR metadata and high OCR confidence
        if has_ocr_metadata:
            ocr_confidence = metadata.quality_scores.get("ocr_confidence", 0.0)
            if ocr_confidence > 0.7:
                return DocumentType.IMAGE, 0.98
            else:
                return DocumentType.IMAGE, 0.85

        # EXPORT: Archer-specific patterns detected
        if is_archer_export:
            return DocumentType.EXPORT, 0.97

        # MATRIX: High table density (tables dominate content)
        if has_tables and table_count > 0:
            # Calculate table text ratio
            table_text_length = sum(
                len(str(table.get("content", ""))) for table in structure.get("tables", [])
            )
            table_ratio = table_text_length / max(text_length, 1)

            # Check if tables have structured data (rows/columns)
            has_structured_tables = any(
                table.get("rows") or table.get("columns") for table in structure.get("tables", [])
            )

            if table_ratio > 0.6:  # Tables are >60% of content
                return DocumentType.MATRIX, 0.96
            elif table_ratio > 0.3:  # Moderate table content
                return DocumentType.MATRIX, 0.88
            elif has_structured_tables and table_count >= 1:  # Has structured table data
                return DocumentType.MATRIX, 0.90

        # REPORT: Narrative text with sections/headings
        if has_sections or has_headings:
            section_count = len(structure.get("sections", []))
            heading_count = len(structure.get("headings", []))

            if section_count >= 3 or heading_count >= 3:
                return DocumentType.REPORT, 0.97
            elif section_count >= 1 or heading_count >= 1:
                return DocumentType.REPORT, 0.90

        # Default: REPORT for text-heavy documents
        if text_length > 500:
            return DocumentType.REPORT, 0.85

        # Fallback: REPORT with low confidence
        return DocumentType.REPORT, 0.70

    def _detect_archer_export(self, text: str, structure: Dict[str, Any]) -> bool:
        """Detect Archer GRC export patterns.

        Args:
            text: Document text content
            structure: Document structure metadata

        Returns:
            True if Archer export patterns detected
        """
        # Check for Archer-specific field patterns
        archer_patterns = [
            "archer_field_id",
            "archer_record_id",
            "field_name",
            "field_value",
            "<field",
            "RSA Archer",
            "recordId=",
        ]

        archer_pattern_count = sum(1 for pattern in archer_patterns if pattern in text)

        # Check structure for Archer metadata
        has_archer_metadata = structure.get(
            "source_system"
        ) == "archer" or "archer" in structure.get("metadata", {})

        return archer_pattern_count >= 2 or has_archer_metadata

    def standardize_schema(self, document: Document, doc_type: DocumentType) -> Document:
        """Apply type-specific schema transformation.

        Args:
            document: Document to transform
            doc_type: Detected document type

        Returns:
            Document with standardized schema
        """
        if doc_type == DocumentType.REPORT:
            document = self._transform_report(document)
        elif doc_type == DocumentType.MATRIX:
            document = self._transform_matrix(document)
        elif doc_type == DocumentType.EXPORT:
            document = self._transform_export(document)
        elif doc_type == DocumentType.IMAGE:
            document = self._transform_image(document)

        return document

    def _transform_report(self, document: Document) -> Document:
        """Transform REPORT document schema.

        Extracts sections, headings, and narrative flow.

        Args:
            document: Document to transform

        Returns:
            Document with REPORT schema
        """
        structure = document.structure

        # Standardize section structure
        if "sections" in structure:
            standardized_sections = []
            for section in structure["sections"]:
                standardized_sections.append(
                    {
                        "title": section.get("title", ""),
                        "content": section.get("content", ""),
                        "level": section.get("level", 1),
                    }
                )
            structure["standardized_sections"] = standardized_sections

        return document

    def _transform_matrix(self, document: Document) -> Document:
        """Transform MATRIX document schema.

        Preserves table structure (rows, columns, headers).

        Args:
            document: Document to transform

        Returns:
            Document with MATRIX schema
        """
        document = self.preserve_excel_structure(document)
        return document

    def _transform_export(self, document: Document) -> Document:
        """Transform EXPORT document schema.

        Parses Archer-specific field schemas and hyperlinks, applies field name standardization.

        Args:
            document: Document to transform

        Returns:
            Document with EXPORT schema
        """
        archer_data = self.parse_archer_export(document)
        if archer_data:
            # Standardize field names
            if archer_data.get("fields"):
                archer_data["standardized_fields"] = self.standardize_field_names(
                    archer_data["fields"],
                    DocumentType.EXPORT,
                    document.metadata.document_subtype,
                )

            document.structure["archer_fields"] = archer_data

        return document

    def _transform_image(self, document: Document) -> Document:
        """Transform IMAGE document schema.

        Validates OCR metadata presence.

        Args:
            document: Document to transform

        Returns:
            Document with IMAGE schema
        """
        # Ensure OCR metadata is present
        if "ocr_confidence" not in document.metadata.quality_scores:
            updated_quality_flags = document.metadata.quality_flags.copy()
            updated_quality_flags.append("missing_ocr_confidence")
            document.metadata = document.metadata.model_copy(
                update={"quality_flags": updated_quality_flags}
            )

        return document

    def parse_archer_export(self, document: Document) -> Dict[str, Any]:
        """Parse Archer GRC HTML/XML export.

        Extracts Archer-specific field schemas and hyperlinks representing
        entity relationships.

        Args:
            document: Document with Archer export content

        Returns:
            Dictionary with parsed Archer fields and relationships
        """
        text = document.text
        archer_data: Dict[str, Any] = {
            "fields": {},
            "hyperlinks": [],
            "module": None,
        }

        try:
            # Parse HTML/XML content
            soup = BeautifulSoup(text, "lxml")

            # Extract Archer module type
            module_patterns = {
                "Risk Management": ["risk_id", "risk description", "inherent risk"],
                "Compliance": ["compliance", "regulation", "requirement"],
                "Issues": ["issue_id", "issue description", "remediation"],
            }

            text_lower = text.lower()
            for module_name, patterns in module_patterns.items():
                if any(pattern in text_lower for pattern in patterns):
                    archer_data["module"] = module_name
                    document.metadata = document.metadata.model_copy(
                        update={"document_subtype": module_name}
                    )
                    break

            # Extract hyperlinks (entity relationships)
            for link in soup.find_all("a"):
                href = link.get("href", "")
                # Ensure href is a string (BeautifulSoup may return AttributeValueList)
                href_str = str(href) if href else ""
                link_text = link.get_text(strip=True)
                if href_str and "recordId=" in href_str:
                    archer_data["hyperlinks"].append(
                        {
                            "text": link_text,
                            "url": href_str,
                            "record_id": href_str.split("recordId=")[-1].split("&")[0],
                        }
                    )

            # Extract field values (check for <field> tags and divs with archer classes)
            for field in soup.find_all("field"):
                field_name = field.get("name", "")
                field_value = field.get_text(strip=True)
                if field_name:
                    archer_data["fields"][field_name] = field_value

            # Also check for div elements with archer-field class
            for field in soup.find_all("div", class_=["field", "archer-field"]):
                field_name = field.get("name") or field.get("data-field-name", "")
                field_value = field.get_text(strip=True)
                if field_name:
                    archer_data["fields"][field_name] = field_value

        except Exception as e:
            self.logger.warning(
                "archer_parsing_failed",
                document_id=document.id,
                error=str(e),
            )

        return archer_data

    def preserve_excel_structure(self, document: Document) -> Document:
        """Preserve Excel table structure.

        Extracts rows, columns, and headers from tables and ensures they're
        preserved in a structured format for control matrices and risk registers.

        Args:
            document: Document with Excel table content

        Returns:
            Document with preserved table structure
        """
        structure = document.structure
        tables = structure.get("tables", [])

        standardized_tables = []
        for table in tables:
            standardized_table = {
                "headers": table.get("headers", []),
                "rows": table.get("rows", []),
                "columns": table.get("columns", []),
                "sheet_name": table.get("sheet_name", ""),
            }
            standardized_tables.append(standardized_table)

        structure["standardized_tables"] = standardized_tables

        return document
