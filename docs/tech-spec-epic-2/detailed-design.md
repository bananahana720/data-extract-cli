# Detailed Design

## Services and Modules

| Module | Responsibility | Inputs | Outputs | Story | Test Coverage Target |
|--------|---------------|--------|---------|-------|---------------------|
| **normalize/normalizer.py** | Main normalization orchestrator; coordinates all normalization stages in sequence | `ExtractionResult` from extract stage | `ProcessingResult` with normalized content | 2.1 | >85% |
| **normalize/cleaning.py** | Text cleaning and artifact removal; OCR noise, header/footer detection, whitespace normalization | Raw text from ContentBlocks | Cleaned text, transformation audit log | 2.1 | >90% |
| **normalize/entities.py** | Entity recognition and normalization for 6 audit domain types; abbreviation expansion, cross-reference resolution | Cleaned text, entity dictionaries (YAML) | List[Entity] with normalized IDs, entity tags in metadata | 2.2 | >85% |
| **normalize/schema.py** | Schema standardization across document types; auto-detection, type-specific transformations | Document with ContentBlocks | Document with standardized schema, type classification | 2.3 | >80% |
| **normalize/validation.py** | Quality validation; OCR confidence scoring, completeness checking, gap detection | Document with extraction metadata | Validation report, quality flags, quarantine decisions | 2.4, 2.5 | >85% |
| **normalize/metadata.py** | Metadata enrichment; aggregates quality scores, entity tags, configuration snapshots | All normalization outputs | Enriched Metadata object (Pydantic) | 2.6 | >85% |
| **normalize/config.py** | Configuration management for normalization; loads cleaning rules, entity dictionaries, thresholds | YAML config files, env vars, CLI flags | NormalizationConfig (Pydantic) | 2.1-2.6 | >85% |

**Module Dependencies (Call Graph)**:
```
normalizer.py (orchestrator)
  ├─→ config.py (load configuration)
  ├─→ cleaning.py (text cleaning)
  │   └─→ validation.py (quality checks)
  ├─→ entities.py (entity normalization)
  │   └─→ config.py (entity dictionaries)
  ├─→ schema.py (schema standardization)
  │   └─→ validation.py (completeness checks)
  └─→ metadata.py (metadata enrichment)
      └─→ entities.py, validation.py (aggregate results)
```

**Configuration Files (User-Modifiable)**:
- `config/normalize/cleaning_rules.yaml` - OCR artifact patterns, header/footer thresholds
- `config/normalize/entity_patterns.yaml` - 6 entity type patterns, Archer ID formats
- `config/normalize/entity_dictionary.yaml` - Abbreviation expansions (GRC, SOX, NIST CSF, etc.)
- `config/normalize/schema_templates.yaml` - Document type schemas (report, matrix, export, image)

**Ownership**:
- Stories 2.1-2.6 each own specific modules
- Story 2.1 establishes normalizer.py orchestrator and config.py foundation
- Story 2.6 integrates all modules and ensures end-to-end pipeline works

## Data Models and Contracts

**Core Data Models** (defined in `src/data_extract/core/models.py`, extended in Epic 2):

```python
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path
from enum import Enum

# Entity Types (Audit Domain)
class EntityType(str, Enum):
    PROCESS = "process"
    RISK = "risk"
    CONTROL = "control"
    REGULATION = "regulation"
    POLICY = "policy"
    ISSUE = "issue"

class Entity(BaseModel):
    """Domain entity with normalized formatting (Story 2.2)"""
    type: EntityType
    id: str  # Canonical ID after normalization (e.g., "Risk-123")
    text: str  # Entity mention text
    confidence: float = Field(ge=0.0, le=1.0)
    location: Optional[Dict[str, Any]] = None  # {page, section, char_offset}

    model_config = ConfigDict(frozen=False)

# Document Type Classification (Story 2.3)
class DocumentType(str, Enum):
    REPORT = "report"  # Word/PDF narrative reports
    MATRIX = "matrix"  # Excel control matrices, risk registers
    EXPORT = "export"  # Archer GRC HTML/XML exports
    IMAGE = "image"    # Scanned documents, screenshots

class QualityFlag(str, Enum):
    LOW_OCR_CONFIDENCE = "low_ocr_confidence"
    INCOMPLETE_EXTRACTION = "incomplete_extraction"
    MISSING_IMAGES = "missing_images"
    COMPLEX_OBJECTS = "complex_objects"
    FORMATTING_ARTIFACTS = "formatting_artifacts"

# Extended Metadata (Story 2.6)
class Metadata(BaseModel):
    """Enriched metadata for audit trail compliance"""
    # Source Information
    source_file: Path
    file_hash: str  # SHA-256
    processing_timestamp: datetime
    tool_version: str
    config_snapshot: Dict[str, Any]  # Configuration used for processing

    # Document Classification (Story 2.3)
    document_type: DocumentType
    document_subtype: Optional[str] = None  # e.g., "Archer Risk Module"

    # Quality Metrics (Stories 2.4, 2.5)
    ocr_confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    completeness_ratio: Optional[float] = Field(None, ge=0.0, le=1.0)
    quality_flags: List[QualityFlag] = Field(default_factory=list)

    # Entity Information (Story 2.2)
    entity_tags: List[str] = Field(default_factory=list)  # ["Risk-123", "Control-456"]
    entity_counts: Dict[EntityType, int] = Field(default_factory=dict)

    # Validation Results (Story 2.5)
    validation_report: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(frozen=False, arbitrary_types_allowed=True)

# Cleaning Result (Story 2.1)
class CleaningResult(BaseModel):
    """Audit log of text cleaning transformations"""
    original_length: int
    cleaned_length: int
    artifacts_removed: int
    headers_footers_removed: int
    whitespace_normalized: bool
    transformations: List[Dict[str, Any]] = Field(default_factory=list)

    model_config = ConfigDict(frozen=False)

# Validation Report (Stories 2.4, 2.5)
class ValidationReport(BaseModel):
    """Comprehensive quality validation results"""
    ocr_confidence_passed: bool
    completeness_passed: bool
    missing_images_count: int = 0
    complex_objects_count: int = 0
    extraction_gaps: List[Dict[str, Any]] = Field(default_factory=list)
    quarantine_recommended: bool = False

    model_config = ConfigDict(frozen=False)

# Normalization Configuration (All Stories)
class NormalizationConfig(BaseModel):
    """Configuration for normalization pipeline"""
    # Text Cleaning (Story 2.1)
    remove_ocr_artifacts: bool = True
    remove_headers_footers: bool = True
    header_repetition_threshold: int = 3  # pages
    whitespace_max_consecutive_newlines: int = 2

    # Entity Normalization (Story 2.2)
    entity_types: List[EntityType] = Field(default_factory=lambda: list(EntityType))
    entity_dictionary_path: Path = Path("config/normalize/entity_dictionary.yaml")
    entity_pattern_path: Path = Path("config/normalize/entity_patterns.yaml")

    # Schema Standardization (Story 2.3)
    document_type_detection: bool = True
    archer_hyperlink_parsing: bool = True
    excel_table_preservation: bool = True

    # OCR Validation (Story 2.4)
    ocr_confidence_threshold: float = 0.95
    ocr_preprocessing_enabled: bool = True
    quarantine_low_confidence: bool = True

    # Completeness Validation (Story 2.5)
    detect_missing_images: bool = True
    detect_complex_objects: bool = True
    completeness_threshold: float = 0.90  # 90% completeness required

    model_config = ConfigDict(frozen=False)
```

**Data Contracts Between Pipeline Stages**:

**Input Contract** (from Extract stage → Normalize):
- `ExtractionResult` with `List[ContentBlock]` containing raw text
- Each `ContentBlock` has `block_type`, `content`, `position`, `metadata`
- Metadata includes source file, extraction confidence, document structure

**Output Contract** (from Normalize → Chunk stage):
- `ProcessingResult` with normalized `List[ContentBlock]`
- Each `ContentBlock` has:
  - Cleaned text (artifacts removed, whitespace normalized)
  - Normalized entities with canonical IDs
  - Enriched metadata (document type, quality scores, entity tags)
  - Validation report (OCR confidence, completeness, quality flags)

**State Management**:
- Normalization is **stateless** per document (no shared state between files)
- Processing context carries configuration and logger (not mutable state)
- All transformations logged in metadata for audit trail

## APIs and Interfaces

**Main Normalization Interface** (implements PipelineStage protocol):

```python
from typing import Protocol
from data_extract.core.models import ExtractionResult, ProcessingResult, ProcessingContext

class Normalizer(Protocol):
    """Main normalization orchestrator (Story 2.1)"""

    def process(
        self,
        extraction_result: ExtractionResult,
        context: ProcessingContext
    ) -> ProcessingResult:
        """
        Normalize extracted content through all stages.

        Args:
            extraction_result: Raw extraction from document
            context: Processing context (config, logger, metrics)

        Returns:
            ProcessingResult with normalized content

        Raises:
            ProcessingError: Recoverable errors (continue batch)
            CriticalError: Fatal errors (halt processing)
        """
        ...
```

**Component Interfaces**:

**Text Cleaning (Story 2.1)**:
```python
class TextCleaner:
    def clean_text(self, text: str, doc_type: DocumentType) -> tuple[str, CleaningResult]:
        """
        Remove OCR artifacts, headers/footers, normalize whitespace.

        Args:
            text: Raw extracted text
            doc_type: Document type for type-specific rules

        Returns:
            (cleaned_text, cleaning_result_audit_log)
        """
        ...

    def detect_headers_footers(self, pages: List[str]) -> tuple[str, str]:
        """Detect repeated headers/footers across pages."""
        ...

    def remove_ocr_artifacts(self, text: str) -> str:
        """Remove OCR-specific noise patterns."""
        ...
```

**Entity Normalization (Story 2.2)**:
```python
class EntityNormalizer:
    def normalize_entities(
        self,
        text: str,
        entity_dict: Dict[str, Any]
    ) -> tuple[str, List[Entity]]:
        """
        Recognize and normalize audit domain entities.

        Args:
            text: Cleaned text from TextCleaner
            entity_dict: Abbreviation dictionary and patterns

        Returns:
            (text_with_normalized_refs, entity_list)
        """
        ...

    def recognize_entity_type(self, mention: str) -> Optional[EntityType]:
        """Classify entity mention by type."""
        ...

    def resolve_cross_references(self, entities: List[Entity]) -> List[Entity]:
        """Link entity mentions to canonical IDs."""
        ...
```

**Schema Standardization (Story 2.3)**:
```python
class SchemaStandardizer:
    def detect_document_type(self, extraction_result: ExtractionResult) -> DocumentType:
        """
        Auto-detect document type.

        Returns:
            DocumentType enum value
        """
        ...

    def standardize_schema(
        self,
        blocks: List[ContentBlock],
        doc_type: DocumentType
    ) -> List[ContentBlock]:
        """
        Apply type-specific schema transformations.

        Args:
            blocks: Content blocks from extraction
            doc_type: Detected document type

        Returns:
            Blocks with standardized schema
        """
        ...

    def parse_archer_export(self, html_content: str) -> Dict[str, Any]:
        """Parse Archer-specific HTML/XML patterns."""
        ...

    def preserve_excel_structure(self, worksheet_data: Any) -> List[ContentBlock]:
        """Preserve Excel table structure (matrices, registers)."""
        ...
```

**Quality Validation (Stories 2.4, 2.5)**:
```python
class QualityValidator:
    def validate_ocr_confidence(
        self,
        blocks: List[ContentBlock],
        threshold: float = 0.95
    ) -> ValidationReport:
        """
        Validate OCR confidence scores.

        Args:
            blocks: Content blocks with OCR metadata
            threshold: Minimum confidence threshold

        Returns:
            ValidationReport with pass/fail and quarantine recommendation
        """
        ...

    def check_completeness(
        self,
        extraction_result: ExtractionResult
    ) -> ValidationReport:
        """
        Detect extraction gaps (missing images, complex objects).

        Returns:
            ValidationReport with completeness ratio and gap details
        """
        ...

    def preprocess_image_for_ocr(self, image_path: Path) -> Path:
        """Apply deskew, denoise, contrast enhancement."""
        ...
```

**Metadata Enrichment (Story 2.6)**:
```python
class MetadataEnricher:
    def enrich_metadata(
        self,
        metadata: Metadata,
        entities: List[Entity],
        validation: ValidationReport,
        config: NormalizationConfig
    ) -> Metadata:
        """
        Aggregate all normalization results into enriched metadata.

        Args:
            metadata: Base metadata from extraction
            entities: Normalized entity list
            validation: Quality validation results
            config: Configuration snapshot

        Returns:
            Enriched Metadata with all quality scores and entity tags
        """
        ...

    def calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash for audit trail."""
        ...
```

**Error Response Format**:

All interfaces use structured exceptions:
```python
try:
    result = normalizer.process(extraction_result, context)
except ProcessingError as e:
    # Recoverable error - log, quarantine, continue batch
    logger.warning("normalization_failed", file=file_path, error=str(e))
    quarantine_file(file_path, error=e)
except CriticalError as e:
    # Fatal error - halt processing
    logger.error("critical_normalization_failure", error=str(e))
    raise
```

## Workflows and Sequencing

**End-to-End Normalization Workflow**:

```
┌─────────────────────────────────────────────────────────────────┐
│ INPUT: ExtractionResult from Extract Stage (Epic 1)            │
│   - List[ContentBlock] with raw text                           │
│   - Source file metadata                                        │
│   - Extraction confidence scores                               │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 1: Configuration Loading (Story 2.1)                      │
│   - Load NormalizationConfig from YAML/env/CLI                 │
│   - Load entity dictionaries and patterns                      │
│   - Initialize logging context                                 │
│   Output: NormalizationConfig, ProcessingContext               │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 2: Document Type Detection (Story 2.3)                    │
│   - Analyze ContentBlock structure and metadata                │
│   - Classify as: REPORT, MATRIX, EXPORT, or IMAGE              │
│   - Store in metadata for type-specific processing             │
│   Output: DocumentType classification                          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 3: Text Cleaning (Story 2.1)                              │
│   FOR EACH ContentBlock:                                        │
│     a. Remove OCR artifacts (regex patterns)                   │
│     b. Detect and remove headers/footers (repetition analysis) │
│     c. Normalize whitespace (preserve structure)               │
│     d. Log transformations in CleaningResult                   │
│   Output: Cleaned ContentBlocks + CleaningResult audit log     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 4: Entity Normalization (Story 2.2)                       │
│   FOR EACH ContentBlock:                                        │
│     a. Recognize 6 entity types using spaCy + patterns         │
│     b. Expand abbreviations (entity_dictionary)                │
│     c. Normalize entity IDs (e.g., "Risk #123" → "Risk-123")  │
│     d. Resolve cross-references (link mentions to canonical)   │
│   Output: List[Entity] + entity tags in metadata               │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 5: Schema Standardization (Story 2.3)                     │
│   SWITCH on DocumentType:                                       │
│     CASE REPORT: Extract sections, headings, narrative flow    │
│     CASE MATRIX: Preserve table structure (rows/cols/headers)  │
│     CASE EXPORT: Parse Archer fields, hyperlinks, metadata     │
│     CASE IMAGE: Validate OCR metadata                          │
│   Output: Standardized schema with field mapping traceability  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 6: OCR Confidence Validation (Story 2.4)                  │
│   IF document contains OCR content:                             │
│     a. Extract confidence scores from metadata                 │
│     b. Calculate per-page average confidence                   │
│     c. IF confidence < threshold (95%):                        │
│        - Flag in metadata (QualityFlag.LOW_OCR_CONFIDENCE)     │
│        - Recommend quarantine                                  │
│     d. Apply preprocessing if enabled (deskew, denoise)        │
│   Output: OCR validation results in ValidationReport           │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 7: Completeness Validation (Story 2.5)                    │
│   a. Count total elements (text blocks, images, objects)       │
│   b. Count successfully extracted elements                     │
│   c. Calculate completeness_ratio = extracted / total          │
│   d. Detect gaps:                                              │
│      - Images without alt text                                 │
│      - Complex objects (OLE, charts) not extracted             │
│   e. IF completeness_ratio < threshold (90%):                  │
│      - Flag QualityFlag.INCOMPLETE_EXTRACTION                  │
│      - Log specific gaps with locations                        │
│   Output: Completeness ValidationReport                        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 8: Metadata Enrichment (Story 2.6)                        │
│   a. Calculate file hash (SHA-256)                             │
│   b. Aggregate entity counts by type                           │
│   c. Collect all quality flags from Steps 3-7                  │
│   d. Snapshot configuration for reproducibility                │
│   e. Add timestamps, tool version                              │
│   f. Compile ValidationReport from Steps 6-7                   │
│   Output: Enriched Metadata object (Pydantic)                  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 9: Quality Gate Decision                                  │
│   IF any ValidationReport.quarantine_recommended:              │
│     - Move file to quarantine directory                        │
│     - Log quarantine reason with actionable suggestions        │
│     - Continue batch processing (don't halt)                   │
│   ELSE:                                                         │
│     - Mark as validated                                        │
│     - Ready for next stage (Chunk - Epic 3)                    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ OUTPUT: ProcessingResult for Chunk Stage (Epic 3)              │
│   - Normalized ContentBlocks (cleaned, entities tagged)        │
│   - Enriched Metadata (quality scores, entity tags, audit log) │
│   - ValidationReport (OCR confidence, completeness)             │
│   - Configuration snapshot (reproducibility)                   │
└─────────────────────────────────────────────────────────────────┘
```

**Parallel Processing Opportunities**:

While normalization is sequential per document, these steps can run in parallel:
- **Story 2.4 (OCR Confidence)** can run independently if OCR metadata exists
- **Story 2.5 (Completeness)** can run in parallel with Story 2.2 (Entity Normalization)
- **Batch-level**: Multiple documents processed in parallel (ThreadPoolExecutor for I/O-bound)

**Error Handling Sequencing**:

```python
for document in batch:
    try:
        # Steps 1-9 execute in sequence
        result = normalizer.process(document, context)
        successful_results.append(result)
    except ProcessingError as e:
        # Recoverable error - log, quarantine, continue
        logger.warning("normalization_failed", doc=document.id, error=str(e))
        quarantine_document(document, error=e)
        failed_documents.append((document, e))
        continue  # CRITICAL: Don't halt batch
    except CriticalError as e:
        # Fatal error - halt immediately
        logger.error("critical_failure", error=str(e))
        raise

# After batch completion
report_summary(successful_results, failed_documents)
```

**Story Execution Sequence** (Development Order):

1. **Story 2.1** (8-12 hours) - Text cleaning foundation, establishes orchestrator
2. **Parallel**:
   - **Story 2.2** (12-16 hours) - Entity normalization (requires 2.1 complete)
   - **Story 2.4** (8-12 hours) - OCR confidence (can start after 2.1)
3. **Story 2.3** (16-20 hours) - Schema standardization (requires 2.1, 2.2)
4. **Story 2.5** (8-10 hours) - Completeness validation (requires 2.1-2.4)
5. **Story 2.6** (6-8 hours) - Metadata enrichment (integration layer, requires all others)

**Total Timeline**: 60-82 hours (7.5-10 working days)
