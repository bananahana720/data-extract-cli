"""Core data models for the data extraction pipeline.

This module defines Pydantic v2 models for pipeline data flow:
- Entity: Domain entities (risk, control, policy, process, regulation, issue)
- Metadata: Provenance and quality tracking for documents and chunks
- ValidationReport: OCR and extraction quality validation report
- Document: Processed document after extraction with entities and metadata
- Chunk: Semantic chunk for RAG with quality scoring and readability metrics
- ProcessingContext: Shared pipeline state (config, logger, metrics)

Enums:
- EntityType: Audit domain entity types
- DocumentType: Document classification types
- QualityFlag: Quality validation flags for OCR and extraction issues

All models use Pydantic v2 for runtime validation and type safety.
"""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator

if TYPE_CHECKING:
    pass


# Content structure models for document parsing
class ContentType(str, Enum):
    """Content block types for document structure.

    Intentional subset of brownfield ContentType for greenfield architecture.
    Includes essential types for Epic 3 chunking and future expansion.

    Note: UNKNOWN added for graceful degradation when content type cannot
    be determined. Prevents extraction failures on unrecognized content.

    Future expansion candidates (from brownfield): QUOTE, CHART, LIST_ITEM,
    TABLE_CELL, METADATA, FOOTNOTE, COMMENT, HYPERLINK.
    """

    HEADING = "heading"
    PARAGRAPH = "paragraph"
    TABLE = "table"
    LIST = "list"
    IMAGE = "image"
    CODE = "code"
    UNKNOWN = "unknown"  # Fallback for unrecognized content types


class Position(BaseModel):
    """Position information for content blocks."""

    model_config = ConfigDict(frozen=True)

    page: int = Field(..., description="Page number (1-indexed)")
    sequence_index: int = Field(..., description="Sequence index within page")


class ContentBlock(BaseModel):
    """Content block representing a structural element in a document."""

    model_config = ConfigDict(frozen=False)

    block_type: ContentType = Field(..., description="Type of content block")
    content: str = Field(..., description="Content text")
    position: Position = Field(..., description="Position in document")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class EntityType(str, Enum):
    """Audit domain entity types.

    Six entity types recognized in audit documents for consistent
    naming and cross-reference resolution.

    Values:
        PROCESS: Business or operational processes
        RISK: Identified risks or risk factors
        CONTROL: Control measures or procedures
        REGULATION: Regulatory requirements or standards
        POLICY: Organizational policies or guidelines
        ISSUE: Identified issues, findings, or audit observations
    """

    PROCESS = "process"
    RISK = "risk"
    CONTROL = "control"
    REGULATION = "regulation"
    POLICY = "policy"
    ISSUE = "issue"


class DocumentType(str, Enum):
    """Document classification types for schema standardization.

    Four document types for applying type-specific transformations and
    schema standardization across different source formats.

    Values:
        REPORT: Narrative documents (Word, PDF) with sections and headings
        MATRIX: Tabular documents (Excel) like control matrices or risk registers
        EXPORT: System exports (Archer GRC HTML/XML) with structured fields
        IMAGE: Scanned documents or images requiring OCR processing
    """

    REPORT = "report"
    MATRIX = "matrix"
    EXPORT = "export"
    IMAGE = "image"


class QualityFlag(str, Enum):
    """Quality validation flags for OCR and extraction issues.

    Quality flags used by validation pipeline to mark documents
    requiring manual review or quarantine.

    Values:
        LOW_OCR_CONFIDENCE: OCR confidence score below threshold (default 95%)
        MISSING_IMAGES: Referenced images not found or failed to extract
        INCOMPLETE_EXTRACTION: Extraction incomplete or partially failed
        COMPLEX_OBJECTS: Complex objects (OLE, charts, diagrams) that can't be extracted
    """

    LOW_OCR_CONFIDENCE = "low_ocr_confidence"
    MISSING_IMAGES = "missing_images"
    INCOMPLETE_EXTRACTION = "incomplete_extraction"
    COMPLEX_OBJECTS = "complex_objects"


class Entity(BaseModel):
    """Domain entity extracted from documents.

    Represents entities from the audit domain: risk, control, policy,
    process, regulation, issue. Used by Document and Chunk models.

    Attributes:
        type: Entity type from EntityType enum
        id: Canonical entity identifier (e.g., 'Risk-123')
        text: Entity text content as it appears in document
        confidence: Confidence score (0.0-1.0) for entity extraction
        location: Character position in document (start and end indices)
    """

    model_config = ConfigDict(frozen=True)

    type: EntityType = Field(..., description="Entity type from EntityType enum")
    id: str = Field(..., description="Canonical entity identifier (e.g., Risk-123)")
    text: str = Field(..., description="Entity text content as it appears in document")
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score for entity extraction (0.0-1.0)",
    )
    location: Dict[str, int] = Field(
        ...,
        description="Character position in document (start and end indices)",
    )


class Metadata(BaseModel):
    """Provenance and quality tracking metadata.

    Embedded in Document and Chunk models to track processing history,
    quality metrics, and audit trail information.

    Note: frozen=True ensures metadata immutability. Metadata should be
    created once during processing and never modified. This prevents
    pipeline state corruption and ensures audit trail integrity.

    Attributes:
        source_file: Path to original source file
        file_hash: SHA-256 hash of source file for integrity verification
        processing_timestamp: When the document/chunk was processed
        tool_version: Version of the data extraction tool
        config_version: Version of the configuration used
        document_type: Document classification (report, matrix, export, image)
        document_subtype: Document subtype (e.g., Archer module variations)
        quality_scores: Quality metrics dict (e.g., {'ocr_confidence': 0.95})
        quality_flags: List of quality warnings/flags (string values from QualityFlag enum)
        ocr_confidence: Per-page OCR confidence scores (page_num -> confidence 0.0-1.0)
        completeness_ratio: Extraction completeness ratio (0.0-1.0, extracted/total elements)
        entity_tags: List of canonical entity IDs for RAG retrieval filtering
        entity_counts: Count of entities by type (e.g., {'risk': 5, 'control': 3})
        config_snapshot: Full configuration snapshot for reproducibility (all processing settings)
        validation_report: Serialized ValidationReport with quality validation results
    """

    model_config = ConfigDict(frozen=True)

    source_file: Path = Field(..., description="Path to original source file")
    file_hash: str = Field(
        ..., description="SHA-256 hash of source file for integrity verification"
    )
    processing_timestamp: datetime = Field(..., description="When the document/chunk was processed")
    tool_version: str = Field(..., description="Version of the data extraction tool")
    config_version: str = Field(..., description="Version of the configuration used")
    document_type: Optional[Union[DocumentType, str]] = Field(
        None,
        description="Document classification type (report, matrix, export, image) or legacy string",
    )
    document_subtype: Optional[str] = Field(
        None, description="Document subtype (e.g., Archer module: Risk Management, Compliance)"
    )
    quality_scores: Dict[str, float] = Field(
        default_factory=dict, description="Quality metrics (e.g., ocr_confidence)"
    )
    ocr_confidence: Dict[int, float] = Field(
        default_factory=dict,
        description="Per-page OCR confidence scores (page_num -> confidence 0.0-1.0)",
    )
    completeness_ratio: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Extraction completeness ratio (extracted_elements / total_elements)",
    )

    @field_validator("document_type", mode="before")
    @classmethod
    def validate_document_type(cls, v: Any) -> Optional[Union[DocumentType, str]]:
        """Validate and optionally convert document_type.

        Accepts DocumentType enum, string, or None for backwards compatibility.

        Args:
            v: Value to validate

        Returns:
            DocumentType enum, string (for legacy support), or None
        """
        if v is None:
            return None
        if isinstance(v, DocumentType):
            return v
        if isinstance(v, str):
            # Allow legacy string values for backwards compatibility
            return v
        return None

    quality_flags: List[str] = Field(
        default_factory=list, description="List of quality warnings/flags"
    )
    entity_tags: List[str] = Field(
        default_factory=list,
        description="List of canonical entity IDs for RAG retrieval filtering",
    )
    entity_counts: Dict[str, int] = Field(
        default_factory=dict,
        description="Count of entities by type (e.g., {'risk': 5, 'control': 3})",
    )
    entity_relationships: List[Tuple[str, str, str]] = Field(
        default_factory=list,
        description="Entity relationships in chunk (entity1_id, relation_type, entity2_id). "
        "Lightweight tuple design chosen for simplicity and JSON serializability. "
        "Each tuple is (str, str, str) representing entity pair and relationship type. "
        "Example: ('RISK-001', 'mitigated_by', 'CTRL-042'). "
        "TODO(Epic 4): Consider structured EntityRelationship model for type safety if "
        "relationship analysis becomes more complex.",
    )
    section_context: Optional[str] = Field(
        None,
        description="Section breadcrumb for chunk (e.g., 'Risk Assessment > Controls')",
    )
    config_snapshot: Dict[str, Any] = Field(
        default_factory=dict,
        description="Configuration snapshot used for processing (for reproducibility)",
    )
    validation_report: Dict[str, Any] = Field(
        default_factory=dict,
        description="Serialized ValidationReport with quality validation results",
    )


class ValidationReport(BaseModel):
    """OCR and extraction quality validation report.

    Generated by QualityValidator to assess OCR confidence and extraction
    completeness. Used to determine quarantine recommendations.

    Attributes:
        quarantine_recommended: Whether document should be quarantined for manual review
        confidence_scores: Per-page OCR confidence scores (page_num -> confidence 0.0-1.0)
        quality_flags: List of quality issues detected (from QualityFlag enum)
        extraction_gaps: Descriptions of detected extraction gaps or issues
        document_average_confidence: Document-level average OCR confidence (0.0-1.0)
        scanned_pdf_detected: Whether document was detected as scanned (vs native PDF)
        completeness_passed: Whether completeness ratio meets threshold (>=0.90 default)
        missing_images_count: Count of images without alt text detected
        complex_objects_count: Count of complex objects (OLE, charts, diagrams) detected
    """

    model_config = ConfigDict(frozen=False)

    quarantine_recommended: bool = Field(
        ..., description="Whether document should be quarantined for manual review"
    )
    confidence_scores: Dict[int, float] = Field(
        default_factory=dict,
        description="Per-page OCR confidence scores (page_num -> confidence 0.0-1.0)",
    )
    quality_flags: List[QualityFlag] = Field(
        default_factory=list, description="List of quality issues detected (from QualityFlag enum)"
    )
    extraction_gaps: List[str] = Field(
        default_factory=list, description="Descriptions of detected extraction gaps or issues"
    )
    document_average_confidence: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Document-level average OCR confidence (0.0-1.0)",
    )
    scanned_pdf_detected: Optional[bool] = Field(
        None, description="Whether document was detected as scanned (vs native PDF)"
    )
    completeness_passed: bool = Field(
        default=True, description="Whether completeness ratio meets threshold (>=0.90 default)"
    )
    missing_images_count: int = Field(
        default=0, ge=0, description="Count of images without alt text detected"
    )
    complex_objects_count: int = Field(
        default=0, ge=0, description="Count of complex objects (OLE, charts, diagrams) detected"
    )


class Document(BaseModel):
    """Processed document model.

    Type contract: Extract → Normalize stage.
    Represents a document after extraction with raw/cleaned text,
    extracted entities, and processing metadata.

    Attributes:
        id: Unique document identifier
        text: Document text content (raw or normalized)
        entities: List of extracted entities
        metadata: Processing metadata and quality tracking
        structure: Document structure metadata (e.g., sections, pages)
    """

    model_config = ConfigDict(frozen=False)

    id: str = Field(..., description="Unique document identifier")
    text: str = Field(..., description="Document text content")
    entities: List[Entity] = Field(default_factory=list, description="List of extracted entities")
    metadata: Metadata = Field(..., description="Processing metadata and quality tracking")
    structure: Dict[str, Any] = Field(
        default_factory=dict,
        description="Document structure metadata (e.g., sections, pages)",
    )


class Chunk(BaseModel):
    """Semantic chunk for RAG (Retrieval-Augmented Generation).

    Type contract: Chunk → Semantic stage.
    Represents a semantically coherent chunk with quality scoring,
    readability metrics, and full provenance tracking.

    Attributes:
        id: Unique chunk identifier (format: {source}_{index:03d})
        text: Chunk text content
        document_id: Reference to parent document
        position_index: Position in original document (0-based)
        token_count: Number of tokens in chunk
        word_count: Number of words in chunk
        entities: List of entities in this chunk
        section_context: Section/heading context for this chunk
        quality_score: Overall quality score (0.0-1.0)
        readability_scores: Readability metrics dict (e.g., flesch_reading_ease)
        metadata: Processing metadata and quality tracking (Metadata or ChunkMetadata for entity-aware chunks)
    """

    model_config = ConfigDict(frozen=False, arbitrary_types_allowed=True)

    id: str = Field(..., description="Unique chunk identifier (format: {source}_{index:03d})")
    text: str = Field(..., description="Chunk text content")
    document_id: str = Field(..., description="Reference to parent document")
    position_index: int = Field(..., ge=0, description="Position in original document (0-based)")
    token_count: int = Field(..., ge=0, description="Number of tokens in chunk")
    word_count: int = Field(..., ge=0, description="Number of words in chunk")
    entities: List[Entity] = Field(
        default_factory=list, description="List of entities in this chunk"
    )
    section_context: str = Field(default="", description="Section/heading context for this chunk")
    quality_score: float = Field(..., ge=0.0, le=1.0, description="Overall quality score (0.0-1.0)")
    readability_scores: Dict[str, float] = Field(
        default_factory=dict, description="Readability metrics (e.g., flesch_reading_ease)"
    )
    metadata: Union[Metadata, Any] = Field(
        ...,
        description="Processing metadata and quality tracking (Metadata or ChunkMetadata for entity-aware chunks)",
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert chunk to dictionary (Pydantic v2 compatibility wrapper).

        Returns:
            Dict representation of chunk with all fields JSON-serializable
        """
        from datetime import datetime
        from pathlib import Path

        def make_json_serializable(obj: Any) -> Any:
            """Recursively convert objects to JSON-serializable types."""
            if isinstance(obj, dict):
                return {k: make_json_serializable(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [make_json_serializable(item) for item in obj]
            elif isinstance(obj, (Path,)):
                return str(obj)
            elif isinstance(obj, datetime):
                return obj.isoformat()
            elif hasattr(obj, "value"):  # Enum types
                return obj.value
            elif hasattr(obj, "to_dict"):  # ChunkMetadata or other objects with to_dict()
                return obj.to_dict()
            else:
                return obj

        # Use mode="python" for full serialization
        data: Dict[str, Any] = self.model_dump(mode="python")
        # Make all nested objects JSON-serializable
        result: Dict[str, Any] = make_json_serializable(data)
        return result


class ProcessingResult(BaseModel):
    """Output from Epic 2 normalization stage (Story 3.3 integration).

    Represents normalized document content ready for chunking. Contains
    extracted content blocks, entities, and quality metadata from Epic 2.

    Attributes:
        file_path: Path to source document
        document_type: Classification from Epic 2 (report, matrix, export, image)
        content_blocks: Normalized content blocks (text, tables, images)
        entities: Extracted entities from document
        metadata: Document-level metadata (OCR confidence, completeness, etc.)

    Example:
        >>> result = ProcessingResult(
        ...     file_path=Path("/docs/report.pdf"),
        ...     document_type=DocumentType.REPORT,
        ...     content_blocks=[ContentBlock(...)],
        ...     entities=[],
        ...     metadata=Metadata(ocr_confidence=0.99, completeness=0.98)
        ... )
    """

    model_config = ConfigDict(frozen=False, arbitrary_types_allowed=True)

    file_path: Path = Field(description="Path to source document")
    document_type: DocumentType = Field(description="Document classification")
    content_blocks: List[ContentBlock] = Field(
        default_factory=list, description="Normalized content blocks"
    )
    entities: List[Entity] = Field(default_factory=list, description="Extracted entities")
    metadata: Metadata = Field(description="Document-level metadata")


class ProcessingContext(BaseModel):
    """Shared pipeline state passed through all stages.

    Carries configuration, logger, and metrics through the entire
    pipeline to ensure deterministic processing and audit trail.

    Attributes:
        config: Configuration dictionary (three-tier precedence: CLI > env > YAML > defaults)
        logger: Structured logger instance for audit trail
        metrics: Metrics accumulation dictionary
    """

    model_config = ConfigDict(frozen=False, arbitrary_types_allowed=True)

    config: Dict[str, Any] = Field(
        default_factory=dict,
        description="Configuration dictionary (CLI > env > YAML > defaults)",
    )
    logger: Optional[Any] = Field(
        default=None, description="Structured logger instance for audit trail"
    )
    metrics: Dict[str, Any] = Field(
        default_factory=dict, description="Metrics accumulation dictionary"
    )
