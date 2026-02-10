# Epic Technical Specification: Robust Normalization & Quality Validation

Date: 2025-11-10
Author: andrew
Epic ID: 2
Status: Draft

---

## Overview

Epic 2 addresses the **critical normalization gap** identified in the PRD by building a comprehensive normalization layer that transforms raw extracted text into clean, validated, RAG-ready content. This epic is foundational to the entire data-extraction-tool mission: preventing AI hallucinations by ensuring only high-quality, standardized content reaches LLM systems.

Without robust normalization, the tool cannot deliver on its core promise—acting as a "knowledge quality gateway" for enterprise Gen AI. This epic eliminates OCR artifacts, standardizes audit domain entities (risks, controls, policies), applies schema consistency across document types (Word, Excel, PDF, Archer exports), and implements comprehensive quality validation with zero silent failures.

Epic 2 builds directly on Epic 1's pipeline architecture, implementing the `normalize/` module with six distinct processing components: text cleaning, entity normalization, schema standardization, OCR confidence scoring, completeness validation, and metadata enrichment. Each component is deterministic (audit trail requirement), configurable (YAML-based rules), and thoroughly tested (>80% coverage target).

## Objectives and Scope

### Primary Objectives

1. **Eliminate LLM Input Pollution**: Remove OCR artifacts, formatting noise, and gibberish that cause AI hallucinations
2. **Standardize Audit Domain Entities**: Normalize six entity types (processes, risks, controls, regulations, policies, issues) with consistent formatting and cross-reference resolution
3. **Ensure Schema Consistency**: Apply uniform structure across Word reports, Excel matrices, PDF documents, and Archer GRC exports
4. **Validate Quality Gates**: Flag low-confidence OCR (<95%), detect content gaps, quarantine problematic files before LLM upload
5. **Enable Audit Traceability**: Enrich all content with comprehensive metadata (source, timestamps, entity tags, quality scores) for full audit trail compliance

### In Scope

**Story 2.1: Text Cleaning and Artifact Removal**
- OCR artifact detection and removal (garbled characters, repeated symbols)
- Header/footer repetition detection and cleaning across pages
- Whitespace normalization preserving semantic structure (paragraphs, lists, tables)
- Configurable cleaning rules per document type (YAML-based)
- Deterministic processing with audit logging

**Story 2.2: Entity Normalization for Audit Domain**
- Recognition and standardization of 6 entity types (processes, risks, controls, regulations, policies, issues)
- Abbreviation expansion using configurable dictionaries (GRC, SOX, NIST CSF, etc.)
- Cross-reference resolution with canonical entity IDs
- Entity tagging in metadata for downstream retrieval
- Support for Archer entity ID formats

**Story 2.3: Schema Standardization Across Document Types**
- Auto-detection of 4+ document types (report, matrix, export, image)
- Type-specific schema transformations (Pydantic models per type)
- Archer-specific field pattern handling (hyperlinks, custom fields, module variations)
- Excel table structure preservation (control matrices, risk registers)
- Source → output field mapping traceability

**Story 2.4: OCR Confidence Scoring and Validation**
- Per-page/image confidence scoring using pytesseract
- Image preprocessing pipeline (deskew, denoise, contrast enhancement via Pillow/OpenCV)
- 95% confidence threshold with configurable override
- Quarantine mechanism for low-confidence extractions
- Scanned vs. native PDF auto-detection

**Story 2.5: Completeness Validation and Gap Detection**
- Detection of images without alt text
- Flagging of complex objects that can't be extracted (OLE objects, charts, diagrams)
- Extraction completeness ratio calculation (extracted / total elements)
- Zero silent failures—all gaps logged with actionable suggestions
- Content gap reporting with specific locations (page, section)

**Story 2.6: Metadata Enrichment Framework**
- Comprehensive metadata structure (source path/hash, document type, timestamps, tool version)
- Entity tags with types and locations
- Quality scores aggregation (OCR confidence, readability, completeness)
- Processing configuration snapshot for reproducibility
- JSON-serializable metadata for persistence

### Out of Scope

- **Chunking logic** (covered in Epic 3)
- **Semantic analysis** (TF-IDF, LSA covered in Epic 4)
- **CLI interface improvements** (covered in Epic 5)
- **Output format generation** (JSON, TXT, CSV covered in Epic 3)
- **Advanced NLP** (Word2Vec, LDA, topic modeling deferred to post-MVP)
- **GUI or web interface**
- **Direct Archer API integration** (file-based processing only)
- **Multi-language support** (English only for MVP)

## System Architecture Alignment

Epic 2 implements the **normalize/** module defined in the Architecture (pages 100-105), adhering to the Pipeline Stage Pattern established in Epic 1.

### Architectural Components Referenced

**Core Architecture (Epic 1 Foundation)**:
- `src/data_extract/core/pipeline.py` - PipelineStage[Input, Output] protocol implemented by all normalizers
- `src/data_extract/core/models.py` - Pydantic models (Document, ContentBlock, Metadata, Entity) used as data contracts
- `src/data_extract/core/exceptions.py` - Exception hierarchy (ProcessingError for recoverable errors, CriticalError for fatal)

**New Components (Epic 2)**:
- `src/data_extract/normalize/normalizer.py` - Main normalization orchestrator implementing PipelineStage[Document, Document]
- `src/data_extract/normalize/cleaning.py` - Text cleaning and artifact removal
- `src/data_extract/normalize/entities.py` - Entity normalization with 6 audit domain types
- `src/data_extract/normalize/schema.py` - Schema standardization across document types
- `src/data_extract/normalize/validation.py` - Completeness validation and quality checking
- `src/data_extract/normalize/metadata.py` - Metadata enrichment framework

### Design Pattern Compliance

**Pipeline Stage Pattern** (Architecture pages 349-398):
- All normalizers implement `PipelineStage[Document, Document]` protocol
- Input: `Document` with raw extracted text from Epic 1 extractors
- Output: `Document` with cleaned text, normalized entities, enriched metadata
- Processing context passed through for logging and configuration

**Error Handling Pattern** (Architecture pages 412-433):
- Continue-on-error: ProcessingError for file-level failures (log, quarantine, continue batch)
- Halt-on-critical: CriticalError for unrecoverable errors (invalid configuration, missing dependencies)
- No silent failures: all quality issues flagged in metadata

**Configuration Cascade Pattern** (Architecture pages 486-508):
- Cleaning rules: YAML config > defaults (e.g., OCR artifact patterns, header/footer thresholds)
- Entity dictionaries: User config > built-in defaults (GRC acronyms, entity patterns)
- Quality thresholds: CLI flags > env vars > config file > hardcoded (e.g., 95% OCR confidence)

### Constraints from Architecture

**ADR-002 (Pydantic v2)**: All data models use Pydantic with runtime validation
- `Entity`, `Metadata`, `Document` models enforce schema compliance
- Schema standardization leverages Pydantic validation for document type detection

**ADR-004 (Classical NLP Only)**: Entity recognition uses spaCy statistical models (no transformers)
- spaCy `en_core_web_md` model for sentence boundaries and NER patterns
- Custom entity patterns via spaCy's rule-based matcher (no BERT/GPT)

**ADR-005 (Streaming Pipeline)**: Normalization processes documents one at a time
- Constant memory footprint (not batch-loading entire corpus)
- Enables batch processing with graceful error handling

**NFR-R1 (Deterministic Processing)**: Same input + config → identical output
- No randomness in normalization (fixed cleaning rules, consistent entity matching)
- Audit trail requirement: processing decisions logged with before/after snapshots

## Detailed Design

### Services and Modules

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

### Data Models and Contracts

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

### APIs and Interfaces

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

### Workflows and Sequencing

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

## Non-Functional Requirements

### Performance

**NFR-P1: Normalization Throughput** (from Architecture NFR-P1, PRD FR-6.1)
- **Target**: Normalize 100 mixed-format documents in <10 minutes (sustained ~10 files/min)
- **Per-Document**: Text cleaning <2 seconds, entity normalization <3 seconds, total normalization <5 seconds per document
- **Measurement**: Benchmark with representative audit corpus (PDFs, Word, Excel, Archer exports)
- **Story Impact**: Story 2.1 (cleaning performance), Story 2.2 (entity recognition speed)

**NFR-P2: Memory Efficiency** (from Architecture NFR-P2)
- **Target**: <2GB RAM during batch normalization
- **Implementation**: Streaming architecture (process one document at a time, release memory after)
- **Story Impact**: All stories follow streaming pattern established in Epic 1
- **Constraint**: No batch-loading of entire corpus into memory

**NFR-P3: Configuration Loading Performance**
- **Target**: Configuration loading <100ms (YAML parsing + dictionary initialization)
- **Implementation**: Cache loaded configurations in ProcessingContext (don't reload per document)
- **Story Impact**: Story 2.1 (config loading), Story 2.2 (entity dictionary loading)

**NFR-P4: Parallel Processing Support** (from Epic 2 Transition Brief)
- **Target**: Support parallel document normalization (ThreadPoolExecutor for I/O-bound)
- **Implementation**: Stateless normalization per document (no shared mutable state)
- **Story Impact**: Architecture design in Story 2.1, enables Epic 5 batch processing optimization

**Performance Acceptance Criteria**:
- [ ] Text cleaning processes 100 documents in <200 seconds (Story 2.1)
- [ ] Entity normalization adds <3 seconds per document (Story 2.2)
- [ ] Schema standardization adds <2 seconds per document (Story 2.3)
- [ ] OCR confidence validation adds <1 second per document (Story 2.4)
- [ ] Memory footprint remains <2GB for batches of 100+ documents
- [ ] Configuration loading cached (not repeated per document)

### Security

**NFR-S1: Data Confidentiality**
- All normalization occurs locally with no external API calls
- No cloud services, no external LLM APIs, no telemetry
- File hashes enable integrity verification without transmitting content

**NFR-S2: Configuration Security**
- Entity dictionaries stored as user-editable YAML for transparency
- Clear-text YAML in config/normalize/ directory for audit review

**NFR-S3: Input Validation**
- Pydantic validation for all configuration inputs
- Prevent malicious configuration injection

**NFR-S4: Quarantine Isolation**
- Quarantined files isolated in separate directory
- Quarantine log includes reason, timestamp, file hash

### Reliability/Availability

**NFR-R1: Deterministic Processing** (from Architecture NFR-R1, PRD NFR-R1)
- **Requirement**: Same input document + same configuration → identical normalized output (every time)
- **Implementation**:
  - No randomness in normalization (fixed cleaning rules, consistent entity matching)
  - Consistent ordering of entities in output (sorted by position)
  - Timestamps and hashes in metadata only (not affecting processing logic)
- **Story Impact**: All stories (2.1-2.6) must be deterministic
- **Testing**: Determinism validation tests (run same document 10 times, assert identical output)

**NFR-R2: Graceful Degradation** (from Architecture NFR-R2)
- **Requirement**: No silent failures—flag problems rather than silently drop content
- **Implementation**:
  - Low OCR confidence → flag QualityFlag.LOW_OCR_CONFIDENCE, log, quarantine (don't drop)
  - Missing images → flag QualityFlag.MISSING_IMAGES, log gaps (don't ignore)
  - Entity recognition failures → log unrecognized patterns, include raw text (don't remove)
- **Story Impact**: Story 2.4 (OCR validation), Story 2.5 (completeness validation)

**NFR-R3: Error Handling** (from Architecture NFR-R3, Error Handling Pattern)
- **Requirement**: Continue batch processing when individual files fail (continue-on-error)
- **Implementation**:
  - ProcessingError: Recoverable errors (corrupted file, missing metadata) → log, quarantine, continue
  - CriticalError: Fatal errors (invalid configuration, missing dependencies) → halt processing
- **Story Impact**: All stories implement error handling pattern
- **Exit Codes**: 0=success, 1=partial failure (some files failed), 2=complete failure

**NFR-R4: Data Integrity** (from Architecture NFR-R4)
- **Requirement**: Verify processing integrity using checksums and validation
- **Implementation**:
  - File hash (SHA-256) calculated before normalization
  - Validation reports include completeness ratio, OCR confidence
  - Configuration snapshot stored in metadata (reproducibility)
- **Story Impact**: Story 2.6 (metadata enrichment with hash calculation)

**Reliability Acceptance Criteria**:
- [ ] Determinism tests pass: same input → same output (10 runs)
- [ ] Zero silent failures: all quality issues flagged in metadata
- [ ] Continue-on-error works: 1 corrupted file in batch of 10 doesn't halt other 9
- [ ] Exit codes accurate: 0 (all success), 1 (partial), 2 (failure)
- [ ] File hashes match before/after (content not corrupted during normalization)

### Observability

**NFR-O1: Structured Logging**
- Use structlog for JSON-formatted logs with timestamps and context
- Log all normalization decisions for audit trail compliance
- Log levels: DEBUG, INFO, WARNING, ERROR

**NFR-O2: Processing Metrics**
- Track cleaning transformations, entity recognition, OCR confidence
- Accumulate metrics in ProcessingContext

**NFR-O3: Transformation Audit Trail**
- CleaningResult logs transformations with before/after snapshots
- Entity normalization logs original mention to normalized ID mappings

**NFR-O4: Quality Dashboard Data**
- Export metrics in JSON format for visualization
- Track OCR confidence distribution, entity success rates, completeness ratios

## Dependencies and Integrations

### Python Dependencies

**New Dependencies for Epic 2** (add to `pyproject.toml`):

```toml
[project.dependencies]
# Existing from Epic 1
pydantic = ">=2.0.0,<3.0"
pyyaml = ">=6.0.0,<7.0"
structlog = ">=24.0.0,<25.0"

# New for Epic 2
spacy = ">=3.7.0,<3.8"           # NLP: sentence boundaries, entity recognition (Story 2.2)
textstat = ">=0.7.0,<0.8"        # Readability metrics (Story 2.6)
pillow = ">=10.0.0,<11.0"        # Image preprocessing for OCR (Story 2.4)
pytesseract = ">=0.3.0,<0.4"     # OCR confidence scoring (Story 2.4)
beautifulsoup4 = ">=4.12.0,<5.0" # Archer HTML/XML parsing (Story 2.3)
lxml = ">=5.0.0,<6.0"            # XML parser for BeautifulSoup (Story 2.3)
```

**spaCy Language Model** (system-level dependency):
```bash
# Install after pip install
python -m spacy download en_core_web_md
```

**Tesseract OCR Engine** (system-level dependency):
- **Linux**: `sudo apt-get install tesseract-ocr`
- **macOS**: `brew install tesseract`
- **Windows**: Download installer from https://github.com/UB-Mannheim/tesseract/wiki

### Dependency Details by Story

| Dependency | Version | Story | Purpose | License |
|------------|---------|-------|---------|---------|
| **spacy** | 3.7.x | 2.2 | Sentence tokenization, NER patterns, entity recognition | MIT |
| **en_core_web_md** | 3.7.x | 2.2 | spaCy language model (50MB, includes word vectors) | MIT |
| **textstat** | 0.7.x | 2.6 | Readability metrics (Flesch-Kincaid, Gunning Fog, SMOG) | MIT |
| **pytesseract** | 0.3.x | 2.4 | Tesseract OCR wrapper, confidence scoring | Apache 2.0 |
| **Pillow** | 10.x | 2.4 | Image preprocessing (deskew, denoise, contrast enhancement) | PIL License |
| **beautifulsoup4** | 4.12.x | 2.3 | HTML/XML parsing for Archer exports | MIT |
| **lxml** | 5.x | 2.3 | Fast XML parser backend for BeautifulSoup | BSD |
| **pydantic** | 2.x | All | Data validation, configuration management (already in Epic 1) | MIT |
| **pyyaml** | 6.x | 2.1 | Configuration file parsing (already in Epic 1) | MIT |
| **structlog** | 24.x | All | Structured logging for audit trail (already in Epic 1) | MIT/Apache 2.0 |

### Integration Points

**Epic 1 → Epic 2 Integration**:
- **Input**: `ExtractionResult` from `src/data_extract/extract/` stage
  - Contains `List[ContentBlock]` with raw extracted text
  - Metadata includes source file, extraction confidence, document structure
- **Output**: `ProcessingResult` to `src/data_extract/chunk/` stage (Epic 3)
  - Contains normalized `List[ContentBlock]` with cleaned text
  - Enriched metadata with quality scores, entity tags, validation reports
- **Shared**: Pipeline protocols from `src/data_extract/core/pipeline.py`
- **Shared**: Data models from `src/data_extract/core/models.py`

**Configuration Integration**:
- **Input**: Configuration cascade (CLI flags > env vars > YAML > defaults)
  - `NormalizationConfig` loaded by `src/data_extract/normalize/config.py`
  - User-editable YAML files in `config/normalize/` directory
- **Configuration Files**:
  - `config/normalize/cleaning_rules.yaml` - OCR artifact patterns, thresholds
  - `config/normalize/entity_patterns.yaml` - 6 entity type regex patterns
  - `config/normalize/entity_dictionary.yaml` - Abbreviation expansions
  - `config/normalize/schema_templates.yaml` - Document type schemas

**Brownfield Integration** (from Story 1.2 Assessment):
- **Existing Extractors**: `src/extractors/` (PDF, DOCX, XLSX, PPTX, CSV)
  - Epic 2 normalizers work with outputs from existing extractors
  - No refactoring of extractors required (maintain "ADAPT AND EXTEND" strategy)
- **Existing Data Models**: Some models may need extension for Epic 2
  - Add `EntityType`, `DocumentType`, `QualityFlag` enums
  - Extend `Metadata` with quality scores and entity tags
  - Add `CleaningResult`, `ValidationReport` models

**External System Integration**:
- **None**: Epic 2 operates on extracted content only (no external APIs)
- **File System Only**: Read input documents, write quarantine files
- **No Database**: All state in-memory per document (streaming architecture)

### Dependency Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| **spaCy model download** (en_core_web_md, 50MB) | HIGH - Required for Story 2.2 | Document in setup instructions, include in CI/CD pipeline |
| **Tesseract not installed** | HIGH - Blocks Story 2.4 OCR validation | Check for Tesseract in setup script, provide clear install instructions |
| **Version conflicts** (spaCy requires specific Python/numpy versions) | MEDIUM - May conflict with other deps | Pin compatible versions in pyproject.toml, test in CI |
| **Performance overhead** (spaCy model loading ~2 seconds) | LOW - One-time cost per batch | Lazy load model, cache in ProcessingContext |
| **Windows path issues** (Tesseract executable path) | LOW - Windows-specific | Detect Tesseract path automatically, allow override in config |

### Installation Verification

After Epic 2 dependencies installed, verify:
```bash
# Verify Python packages
pip list | grep -E "(spacy|textstat|pytesseract|pillow|beautifulsoup4|lxml)"

# Verify spaCy model
python -m spacy validate

# Verify Tesseract
tesseract --version

# Run verification script
python scripts/verify_epic2_deps.py
```

## Acceptance Criteria (Authoritative)

This section consolidates all acceptance criteria from Epic 2's six stories. These are **authoritative requirements** that must be met for epic completion.

### Story 2.1: Text Cleaning and Artifact Removal

**AC-2.1.1**: OCR artifacts are removed (garbled characters, repeated symbols, noise patterns)
**AC-2.1.2**: Excessive whitespace is normalized (single spaces, max 2 consecutive newlines)
**AC-2.1.3**: Page numbers, headers, footers are removed when not content-relevant
**AC-2.1.4**: Header/footer repetition is detected and cleaned across pages
**AC-2.1.5**: Intentional formatting is preserved (lists, emphasis, code blocks, paragraph breaks)
**AC-2.1.6**: Cleaning is deterministic (same input + config → same output, every time)
**AC-2.1.7**: Cleaning decisions are logged for audit trail (transformations, before/after)

### Story 2.2: Entity Normalization for Audit Domain

**AC-2.2.1**: Six entity types are recognized: processes, risks, controls, regulations, policies, issues
**AC-2.2.2**: Entity references are standardized (e.g., "Risk #123" → "Risk-123")
**AC-2.2.3**: Acronyms and abbreviations are expanded using configurable dictionary (GRC, SOX, NIST CSF)
**AC-2.2.4**: Consistent capitalization is applied to entity types
**AC-2.2.5**: Cross-references are resolved and linked to canonical entity IDs
**AC-2.2.6**: Entity mentions are tagged in metadata for downstream retrieval
**AC-2.2.7**: Normalization rules are configurable per organization (YAML-based)

### Story 2.3: Schema Standardization Across Document Types

**AC-2.3.1**: Document type is auto-detected (report, matrix, export, image) with >95% accuracy
**AC-2.3.2**: Type-specific schema transformations are applied (Pydantic models per type)
**AC-2.3.3**: Field names are standardized across source systems (Word, Excel, PDF, Archer)
**AC-2.3.4**: Semantic relationships are preserved (risk → control mappings, entity links)
**AC-2.3.5**: Metadata structure is consistent across all document types
**AC-2.3.6**: Archer-specific field schemas and hyperlinks are handled correctly
**AC-2.3.7**: Tables are converted to structured format with preserved rows/columns/headers

### Story 2.4: OCR Confidence Scoring and Validation

**AC-2.4.1**: OCR confidence score is calculated for each page/image using pytesseract
**AC-2.4.2**: Scores below 95% threshold are flagged for manual review (configurable threshold)
**AC-2.4.3**: OCR preprocessing is applied (deskew, denoise, contrast enhancement via Pillow)
**AC-2.4.4**: Scanned vs. native PDF is auto-detected
**AC-2.4.5**: Low-confidence results are quarantined separately with clear audit log
**AC-2.4.6**: Confidence scores are included in output metadata (per-page and document average)
**AC-2.4.7**: OCR operations are logged with before/after confidence metrics

### Story 2.5: Completeness Validation and Gap Detection

**AC-2.5.1**: Images without alt text are detected and flagged (QualityFlag.MISSING_IMAGES)
**AC-2.5.2**: Complex objects that can't be extracted are reported (OLE objects, charts, diagrams)
**AC-2.5.3**: Extraction completeness ratio is calculated (extracted_elements / total_elements)
**AC-2.5.4**: Content gaps are logged with specific locations (page number, section name)
**AC-2.5.5**: No silent failures occur - all issues are surfaced in validation report
**AC-2.5.6**: Validation report identifies what was skipped and why (actionable explanations)
**AC-2.5.7**: Flagged documents are marked in output metadata (QualityFlag enum values)

### Story 2.6: Metadata Enrichment Framework

**AC-2.6.1**: Source file path and SHA-256 hash are included in metadata
**AC-2.6.2**: Document type classification is added (DocumentType enum)
**AC-2.6.3**: Processing timestamp (ISO 8601) and tool version are recorded
**AC-2.6.4**: Entity tags list all identified entities in content (by type and ID)
**AC-2.6.5**: Quality scores aggregated (OCR confidence, readability, completeness ratio)
**AC-2.6.6**: Configuration snapshot used for processing is embedded (reproducibility)
**AC-2.6.7**: Metadata is serializable to JSON for persistence
**AC-2.6.8**: Metadata supports full audit trail (chunk → source document traceability)

### Epic-Level Acceptance Criteria

**AC-EPIC-2.1**: Overall test coverage >80% for all normalization modules
**AC-EPIC-2.2**: Entity normalization accuracy >90% on representative audit corpus
**AC-EPIC-2.3**: Document type detection accuracy >95% on test corpus
**AC-EPIC-2.4**: Zero brownfield regressions (existing tests still pass)
**AC-EPIC-2.5**: End-to-end normalization pipeline functional (extract → normalize → chunk integration)
**AC-EPIC-2.6**: All 6 stories delivered with 100% story-level acceptance criteria met

## Traceability Mapping

This table maps acceptance criteria to technical components, APIs, and test strategies, ensuring full traceability from requirements → implementation → testing.

| Acceptance Criteria | Spec Section | Component/API | Test Strategy |
|---------------------|-------------|---------------|---------------|
| **Story 2.1: Text Cleaning** | | | |
| AC-2.1.1 (OCR artifact removal) | Data Models: CleaningResult | `normalize/cleaning.py::TextCleaner.remove_ocr_artifacts()` | Unit: Test regex patterns on known OCR artifacts (^^^^^, ■■■■) |
| AC-2.1.2 (Whitespace normalization) | Workflows: Step 3 | `normalize/cleaning.py::TextCleaner.clean_text()` | Unit: Test various whitespace scenarios, verify max 2 newlines |
| AC-2.1.3 (Header/footer removal) | Workflows: Step 3 | `normalize/cleaning.py::TextCleaner.detect_headers_footers()` | Unit: Multi-page documents with repeated headers, edge cases |
| AC-2.1.4 (Header repetition detection) | Services: cleaning.py | `normalize/cleaning.py::TextCleaner.detect_headers_footers()` | Integration: Real PDF with headers, verify removal |
| AC-2.1.5 (Preserve formatting) | Workflows: Step 3 | `normalize/cleaning.py::TextCleaner.clean_text()` | Unit: Markdown lists, emphasis, verify preservation |
| AC-2.1.6 (Determinism) | NFR-R1 | All cleaning methods | Integration: Run same doc 10 times, assert identical output |
| AC-2.1.7 (Audit logging) | Data Models: CleaningResult | `normalize/cleaning.py` + structlog | Unit: Verify CleaningResult populated, logs written |
| **Story 2.2: Entity Normalization** | | | |
| AC-2.2.1 (6 entity types) | Data Models: EntityType enum | `normalize/entities.py::EntityNormalizer.recognize_entity_type()` | Unit: Test all 6 types with sample mentions |
| AC-2.2.2 (Entity standardization) | APIs: EntityNormalizer | `normalize/entities.py::EntityNormalizer.normalize_entities()` | Unit: "Risk #123" → "Risk-123", various formats |
| AC-2.2.3 (Abbreviation expansion) | Configuration: entity_dictionary.yaml | `normalize/entities.py` + config loading | Unit: GRC→Governance Risk Compliance, SOX→Sarbanes-Oxley |
| AC-2.2.4 (Consistent capitalization) | APIs: EntityNormalizer | `normalize/entities.py::EntityNormalizer.normalize_entities()` | Unit: "risk" → "Risk", verify consistency |
| AC-2.2.5 (Cross-reference resolution) | APIs: EntityNormalizer | `normalize/entities.py::EntityNormalizer.resolve_cross_references()` | Integration: Multi-entity doc, verify links |
| AC-2.2.6 (Entity metadata tagging) | Data Models: Metadata.entity_tags | `normalize/metadata.py::MetadataEnricher` | Unit: Verify entity_tags populated in metadata |
| AC-2.2.7 (Configurable rules) | Configuration: entity_patterns.yaml | `normalize/config.py::NormalizationConfig` | Integration: Custom YAML, verify override works |
| **Story 2.3: Schema Standardization** | | | |
| AC-2.3.1 (Document type detection) | Data Models: DocumentType enum | `normalize/schema.py::SchemaStandardizer.detect_document_type()` | Unit: Test all 4 types (report, matrix, export, image) |
| AC-2.3.2 (Type-specific transformations) | APIs: SchemaStandardizer | `normalize/schema.py::SchemaStandardizer.standardize_schema()` | Unit: Each doc type has specific test case |
| AC-2.3.3 (Field name standardization) | Services: schema.py | `normalize/schema.py` | Integration: Word + Excel + Archer, verify consistent fields |
| AC-2.3.4 (Relationship preservation) | Workflows: Step 5 | `normalize/schema.py` | Integration: Risk→control matrix, verify mapping intact |
| AC-2.3.5 (Consistent metadata structure) | Data Models: Metadata | `normalize/metadata.py` | Unit: All doc types produce same Metadata schema |
| AC-2.3.6 (Archer field handling) | APIs: SchemaStandardizer.parse_archer_export() | `normalize/schema.py::SchemaStandardizer.parse_archer_export()` | Unit: Archer HTML/XML samples, verify hyperlink parsing |
| AC-2.3.7 (Table structure preservation) | APIs: SchemaStandardizer.preserve_excel_structure() | `normalize/schema.py::SchemaStandardizer.preserve_excel_structure()` | Unit: Excel matrix, verify rows/cols/headers preserved |
| **Story 2.4: OCR Confidence** | | | |
| AC-2.4.1 (Confidence scoring) | Data Models: ValidationReport | `normalize/validation.py::QualityValidator.validate_ocr_confidence()` | Unit: Mock pytesseract, verify score calculation |
| AC-2.4.2 (Threshold flagging) | NFR: OCR 95% threshold | `normalize/validation.py` | Unit: 93% confidence → quarantine, 96% → pass |
| AC-2.4.3 (Preprocessing) | APIs: QualityValidator.preprocess_image_for_ocr() | `normalize/validation.py::QualityValidator.preprocess_image_for_ocr()` | Unit: Test deskew, denoise, contrast on sample images |
| AC-2.4.4 (Scanned vs. native detection) | Workflows: Step 6 | `normalize/validation.py` | Unit: Scanned PDF vs. native PDF, verify correct detection |
| AC-2.4.5 (Quarantine) | NFR-S4 | Quarantine directory creation | Integration: Low confidence doc → quarantine directory |
| AC-2.4.6 (Confidence in metadata) | Data Models: Metadata.ocr_confidence | `normalize/metadata.py` | Unit: Verify ocr_confidence field populated |
| AC-2.4.7 (OCR logging) | NFR-O1 | structlog | Unit: Verify OCR events logged with before/after confidence |
| **Story 2.5: Completeness Validation** | | | |
| AC-2.5.1 (Missing images detection) | Data Models: QualityFlag enum | `normalize/validation.py::QualityValidator.check_completeness()` | Unit: Document with images, verify flagging |
| AC-2.5.2 (Complex objects reporting) | Data Models: ValidationReport | `normalize/validation.py` | Unit: OLE object, chart → reported in validation |
| AC-2.5.3 (Completeness ratio) | Data Models: Metadata.completeness_ratio | `normalize/validation.py` | Unit: 8/10 elements extracted → 0.8 ratio |
| AC-2.5.4 (Gap locations) | Data Models: ValidationReport.extraction_gaps | `normalize/validation.py` | Unit: Gap on page 3, section "Controls" → logged |
| AC-2.5.5 (No silent failures) | NFR-R2 | Error handling pattern | Integration: Verify all gaps flagged, none silently dropped |
| AC-2.5.6 (Actionable validation report) | Data Models: ValidationReport | `normalize/validation.py` | Manual: Review validation report readability |
| AC-2.5.7 (Quality flags in metadata) | Data Models: Metadata.quality_flags | `normalize/metadata.py` | Unit: Verify quality_flags list populated |
| **Story 2.6: Metadata Enrichment** | | | |
| AC-2.6.1 (File hash) | APIs: MetadataEnricher.calculate_file_hash() | `normalize/metadata.py::MetadataEnricher.calculate_file_hash()` | Unit: SHA-256 calculation, verify correctness |
| AC-2.6.2 (Document type) | Data Models: Metadata.document_type | `normalize/metadata.py` | Unit: Verify document_type from Step 2 detection |
| AC-2.6.3 (Timestamp + version) | Data Models: Metadata | `normalize/metadata.py` | Unit: Verify ISO 8601 timestamp, tool version string |
| AC-2.6.4 (Entity tags) | Data Models: Metadata.entity_tags | `normalize/metadata.py` | Integration: Entity normalization → metadata tags |
| AC-2.6.5 (Quality scores aggregation) | APIs: MetadataEnricher.enrich_metadata() | `normalize/metadata.py::MetadataEnricher.enrich_metadata()` | Unit: Aggregate OCR, readability, completeness scores |
| AC-2.6.6 (Config snapshot) | Data Models: Metadata.config_snapshot | `normalize/metadata.py` | Unit: Verify NormalizationConfig serialized to dict |
| AC-2.6.7 (JSON serialization) | Data Models: Metadata | Pydantic `.model_dump_json()` | Unit: Serialize to JSON, deserialize, verify roundtrip |
| AC-2.6.8 (Audit trail) | NFR-A1 | Full metadata structure | Integration: Trace chunk → ContentBlock → source file |
| **Epic-Level** | | | |
| AC-EPIC-2.1 (Test coverage >80%) | Test Strategy | pytest --cov | CI: Coverage report, fail if <80% |
| AC-EPIC-2.2 (Entity accuracy >90%) | Test Strategy | Manual validation on audit corpus | Performance: 100 docs, manual entity validation |
| AC-EPIC-2.3 (Doc type accuracy >95%) | Test Strategy | Automated classification test | Integration: 100 docs, assert detection accuracy |
| AC-EPIC-2.4 (Zero brownfield regressions) | Test Strategy | Existing test suite | CI: Run all Epic 1 tests, assert still pass |
| AC-EPIC-2.5 (End-to-end pipeline) | Test Strategy | Integration test | Integration: Extract → normalize → verify output |
| AC-EPIC-2.6 (All stories 100% complete) | Epic completion | Story review | Manual: SM review, verify all ACs met |

**Traceability Notes**:
- Every AC maps to at least one test strategy (unit, integration, performance, or manual)
- All components referenced in this table exist in the "Services and Modules" section
- All data models are defined in the "Data Models and Contracts" section
- All APIs are documented in the "APIs and Interfaces" section

## Risks, Assumptions, Open Questions

### Risks

**RISK-1: OCR Quality Variability** (HIGH)
- **Description**: OCR quality varies widely by document (scan quality, font, language, noise)
- **Impact**: May result in high quarantine rate (>30%), slowing adoption
- **Mitigation**:
  - Implement aggressive preprocessing (Story 2.4: deskew, denoise, contrast enhancement)
  - Make 95% threshold configurable (allow user to adjust for their corpus)
  - Provide clear actionable guidance in quarantine reports
- **Owner**: Story 2.4

**RISK-2: Archer Pattern Diversity** (MEDIUM)
- **Description**: Archer HTML/XML patterns vary by organization, module, and version
- **Impact**: Schema standardization may not work for all Archer configurations
- **Mitigation**:
  - Make Archer patterns configurable in YAML (Story 2.3)
  - Provide default patterns for common modules (Risk, Compliance, Issues)
  - Document how to customize patterns for organization-specific needs
- **Owner**: Story 2.3

**RISK-3: Entity Recognition Ambiguity** (MEDIUM)
- **Description**: Some acronyms/mentions are ambiguous (e.g., "Control" could be entity or verb)
- **Impact**: False positives in entity recognition, requiring manual cleanup
- **Mitigation**:
  - Use context-aware patterns (spaCy NER with surrounding words)
  - Configurable entity patterns with priority ordering
  - Confidence scoring for entity matches (flag low-confidence for review)
- **Owner**: Story 2.2

**RISK-4: Brownfield Test Coverage Gap** (HIGH - from Epic 1 Retrospective)
- **Description**: Brownfield extractors have low coverage (PDF 19%, CSV 24%, Excel 26%, PPTX 24%)
- **Impact**: Prevents safe refactoring, risk of breaking existing functionality
- **Mitigation**:
  - Action #1 (HIGH priority): Triage 229 failing tests before Story 2.1
  - Action #3 (MEDIUM priority): Improve coverage incrementally during Epic 2
  - Maintain "ADAPT AND EXTEND" strategy (don't refactor brownfield in Epic 2)
- **Owner**: All stories (incremental improvement)

**RISK-5: spaCy Model Download Failure** (MEDIUM)
- **Description**: en_core_web_md (50MB) download may fail in restricted networks
- **Impact**: Blocks Story 2.2 entity normalization development
- **Mitigation**:
  - Document offline installation method (download model, install from file)
  - Include model check in setup verification script
  - Provide clear error message if model missing
- **Owner**: Story 2.2

**RISK-6: Performance Regression** (LOW)
- **Description**: Normalization adds processing time (target: <5 seconds per document)
- **Impact**: May not meet NFR-P1 throughput target (100 docs in 10 minutes)
- **Mitigation**:
  - Benchmark each story (measure overhead)
  - Optimize hot paths (regex compilation, spaCy model caching)
  - Lazy load expensive resources (spaCy model, config dictionaries)
- **Owner**: All stories

### Assumptions

**ASSUMPTION-1: Epic 1 Complete** (VALIDATED)
- **Description**: All Epic 1 stories complete with pipeline architecture functional
- **Status**: ✅ VALIDATED (Epic 1 retrospective confirms 100% completion)
- **Impact**: Epic 2 can start immediately after prerequisites

**ASSUMPTION-2: Python 3.12 Available** (VALIDATED)
- **Description**: Development and target environments have Python 3.12 installed
- **Status**: ✅ VALIDATED (Enterprise requirement, documented in architecture)
- **Impact**: No compatibility issues with dependencies

**ASSUMPTION-3: Tesseract OCR Installed**
- **Description**: System has Tesseract OCR engine installed for Story 2.4
- **Status**: ⚠️ TO VALIDATE (check in setup verification)
- **Impact**: Story 2.4 blocks without Tesseract
- **Action**: Document installation in setup instructions, verify in CI

**ASSUMPTION-4: Representative Test Corpus Available**
- **Description**: Audit documents available for testing (sanitized if needed)
- **Status**: ⚠️ TO VALIDATE (confirm with user)
- **Impact**: Cannot test entity recognition, doc type detection without real docs
- **Action**: Request sample documents or create synthetic test corpus

**ASSUMPTION-5: Brownfield "ADAPT AND EXTEND" Strategy**
- **Description**: Existing extractors work correctly; no refactoring required
- **Status**: ✅ VALIDATED (Story 1.2 assessment confirms high code quality)
- **Impact**: Epic 2 focuses on normalization, not extraction improvements

**ASSUMPTION-6: Classical NLP Sufficient for Entity Recognition**
- **Description**: spaCy statistical models + regex patterns sufficient (no transformers needed)
- **Status**: ⚠️ TO VALIDATE (test accuracy in Story 2.2)
- **Impact**: If accuracy <90%, may need more sophisticated patterns or custom training
- **Action**: Measure entity recognition accuracy, iterate patterns if needed

### Open Questions

**QUESTION-1: Entity Dictionary Scope**
- **Question**: What level of audit domain coverage is required in default entity dictionary?
- **Options**:
  - Minimal: Core GRC acronyms only (GRC, SOX, NIST, ISO)
  - Moderate: Add common frameworks (CIS, COBIT, PCI-DSS) (~50 terms)
  - Comprehensive: Industry-wide audit terminology (~200+ terms)
- **Decision Needed By**: Story 2.2 kickoff
- **Recommendation**: Start with Moderate, expand based on user feedback
- **Owner**: andrew (domain expert)

**QUESTION-2: Archer Module Coverage**
- **Question**: Which Archer modules require schema templates?
- **Options**:
  - Core modules: Risk Management, Compliance, Issues (3 templates)
  - Extended: Add Policy, Incident, Audit, Vendor (7 templates)
  - Configurable: Provide template framework, user defines modules
- **Decision Needed By**: Story 2.3 development
- **Recommendation**: Core modules + configurable framework
- **Owner**: andrew (Archer domain expert)

**QUESTION-3: Quarantine UX**
- **Question**: How should quarantined files be presented to users?
- **Options**:
  - Separate directory only (current plan)
  - Separate directory + summary report (JSON/CSV)
  - Interactive review mode (future CLI command)
- **Decision Needed By**: Story 2.4 development
- **Recommendation**: Separate directory + JSON summary report
- **Owner**: Story 2.4 developer

**QUESTION-4: Readability Metrics Baseline**
- **Question**: What readability thresholds are appropriate for audit documents?
- **Context**: Audit docs are inherently technical (may have high Flesch-Kincaid scores)
- **Decision Needed By**: Story 2.6 (metadata enrichment)
- **Recommendation**: Calculate baseline from sample corpus, set thresholds at 90th percentile
- **Owner**: Story 2.6 developer + andrew (domain context)

**QUESTION-5: Determinism Testing Scope**
- **Question**: How many runs required to validate determinism (NFR-R1)?
- **Options**:
  - 10 runs (current plan in NFR-R1)
  - 100 runs (more rigorous)
  - Statistical test (chi-square for hash distribution)
- **Decision Needed By**: Integration test development
- **Recommendation**: 10 runs for unit tests, 100 runs for CI nightly build
- **Owner**: Test strategy (Story 1.3 framework)

## Test Strategy Summary

### Testing Philosophy

Epic 2 follows the testing framework established in Epic 1 (Story 1.3), with >80% coverage target and comprehensive test organization mirroring the src/ structure.

### Test Organization

```
tests/
├── unit/
│   └── test_normalize/
│       ├── test_cleaning.py           # Story 2.1: 20+ tests
│       ├── test_entities.py           # Story 2.2: 25+ tests
│       ├── test_schema.py             # Story 2.3: 30+ tests
│       ├── test_validation.py         # Story 2.4, 2.5: 25+ tests
│       ├── test_metadata.py           # Story 2.6: 15+ tests
│       └── test_config.py             # Configuration: 10+ tests
├── integration/
│   ├── test_normalization_pipeline.py # End-to-end: Extract → Normalize
│   ├── test_determinism.py           # NFR-R1: Run same doc 10 times
│   ├── test_brownfield_integration.py # Brownfield extractors → normalizers
│   └── test_batch_processing.py      # Batch of 10 mixed documents
├── performance/
│   ├── test_normalization_throughput.py # 100 docs in <10 minutes
│   └── test_entity_recognition_accuracy.py # >90% accuracy validation
└── fixtures/
    └── normalization/
        ├── dirty_text_samples/        # OCR artifacts, formatting issues
        ├── entity_test_docs/          # 6 entity types with known entities
        ├── schema_test_docs/          # Report, matrix, export, image samples
        └── ocr_test_images/           # Scanned PDFs, low/high quality
```

### Coverage Targets by Story

| Story | Module | Target Coverage | Critical Paths |
|-------|--------|----------------|----------------|
| 2.1 | normalize/cleaning.py | >90% | Text cleaning, header/footer detection, audit logging |
| 2.2 | normalize/entities.py | >85% | Entity recognition, normalization, cross-reference resolution |
| 2.3 | normalize/schema.py | >80% | Document type detection, schema transformations, Archer parsing |
| 2.4 | normalize/validation.py (OCR) | >85% | Confidence scoring, preprocessing, quarantine |
| 2.5 | normalize/validation.py (Completeness) | >85% | Gap detection, completeness ratio, validation report |
| 2.6 | normalize/metadata.py | >85% | Metadata enrichment, file hashing, JSON serialization |
| Epic | Overall normalize/ module | >80% | All modules combined |

### Test Types and Strategy

**Unit Tests (125+ tests estimated)**:
- **Story 2.1** (20 tests): Regex patterns, whitespace normalization, header detection, determinism
- **Story 2.2** (25 tests): 6 entity types, abbreviation expansion, cross-refs, config loading
- **Story 2.3** (30 tests): 4 doc types, schema transformations, Archer parsing, Excel tables
- **Story 2.4** (15 tests): OCR confidence, preprocessing, threshold flagging, quarantine
- **Story 2.5** (10 tests): Missing images, complex objects, completeness ratio, gap locations
- **Story 2.6** (15 tests): File hash, entity tags, quality scores, config snapshot, JSON serialization
- **Config** (10 tests): YAML loading, Pydantic validation, cascade precedence

**Integration Tests (10+ tests estimated)**:
- End-to-end pipeline: Extract (brownfield) → Normalize → verify output structure
- Determinism validation: Same document 10 runs, assert byte-identical output
- Brownfield integration: Existing extractors → new normalizers, verify compatibility
- Batch processing: 10 mixed documents (PDF, Word, Excel, Archer), verify all normalized
- Configuration cascade: CLI flags > env vars > YAML, verify precedence
- Quarantine workflow: Low OCR confidence → quarantine directory with log
- Multi-story integration: Text cleaning → entity normalization → schema → metadata
- Epic 1 regression: Run all Epic 1 tests, assert still passing (zero brownfield regressions)

**Performance Tests (2+ benchmarks)**:
- **Throughput**: 100 mixed documents in <10 minutes (NFR-P1), measure per-story overhead
- **Entity accuracy**: 100 documents with known entities, calculate precision/recall (>90% target)

**Test Fixtures Required**:
- **Dirty text samples** (Story 2.1): OCR artifacts (^^^^^, ■■■■), repeated headers, excessive whitespace
- **Entity test docs** (Story 2.2): Documents with known entities (annotated ground truth)
- **Schema test docs** (Story 2.3): Word report, Excel matrix, Archer HTML/XML export, scanned image
- **OCR test images** (Story 2.4): High-quality scan (>95%), low-quality scan (<90%), native PDF
- **Completeness test docs** (Story 2.5): Documents with images, charts, OLE objects (known gaps)

### Test Execution Strategy

**Per Story (Development)**:
1. Write unit tests first (TDD approach)
2. Implement functionality to pass tests
3. Run tests frequently during development (`pytest -v tests/unit/test_normalize/test_<story>.py`)
4. Achieve >85% coverage before marking story complete

**Per Epic (Integration)**:
1. Run all unit tests (`pytest tests/unit/test_normalize/`)
2. Run integration tests (`pytest tests/integration/`)
3. Run performance benchmarks (`pytest tests/performance/`)
4. Generate coverage report (`pytest --cov=src/data_extract/normalize --cov-report=html`)
5. Validate >80% overall coverage
6. Run Epic 1 regression suite (ensure zero brownfield breaks)

**CI/CD Pipeline**:
```yaml
# .github/workflows/test.yml (add Epic 2 jobs)
jobs:
  test-epic2-unit:
    runs-on: ubuntu-latest
    steps:
      - Install dependencies (including spaCy model, Tesseract)
      - Run: pytest tests/unit/test_normalize/ --cov --cov-report=xml
      - Upload coverage to codecov

  test-epic2-integration:
    runs-on: ubuntu-latest
    steps:
      - Install dependencies
      - Run: pytest tests/integration/ -v

  test-epic2-determinism:
    runs-on: ubuntu-latest
    steps:
      - Run: pytest tests/integration/test_determinism.py --runs=10

  test-brownfield-regression:
    runs-on: ubuntu-latest
    steps:
      - Run: pytest tests/ -k "not epic2" --cov
      - Assert: Epic 1 tests still pass
```

### Definition of Done (Testing Perspective)

**Story-Level**:
- [ ] All unit tests written and passing (>85% coverage)
- [ ] Story-specific integration tests passing
- [ ] Pre-commit hooks passing (black, ruff, mypy)
- [ ] No brownfield test regressions

**Epic-Level**:
- [ ] Overall coverage >80% for normalize/ module
- [ ] All integration tests passing
- [ ] Performance benchmarks meet targets (throughput, entity accuracy)
- [ ] Determinism validation passing (10 runs, identical output)
- [ ] All Epic 1 tests still passing (zero regressions)
- [ ] CI/CD pipeline green for all Epic 2 jobs

### Test Automation

**Automated in CI**:
- All unit tests (fast, <1 minute)
- Integration tests (moderate, <5 minutes)
- Coverage reporting (automatic upload)
- Brownfield regression suite (Epic 1 tests)

**Manual/On-Demand**:
- Performance benchmarks (slow, ~10 minutes for 100 docs)
- Entity accuracy validation (requires manual ground truth annotation)
- UX testing (quarantine reports, validation summaries)

**Test Data Management**:
- Fixtures committed to git (sanitized audit documents)
- Large fixtures (<10MB) stored in git LFS
- Synthetic test data generated where real docs unavailable
- Ground truth annotations stored alongside test fixtures (JSON format)
