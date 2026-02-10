# Traceability Mapping

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
