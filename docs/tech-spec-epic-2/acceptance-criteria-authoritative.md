# Acceptance Criteria (Authoritative)

This section consolidates all acceptance criteria from Epic 2's six stories. These are **authoritative requirements** that must be met for epic completion.

## Story 2.1: Text Cleaning and Artifact Removal

**AC-2.1.1**: OCR artifacts are removed (garbled characters, repeated symbols, noise patterns)
**AC-2.1.2**: Excessive whitespace is normalized (single spaces, max 2 consecutive newlines)
**AC-2.1.3**: Page numbers, headers, footers are removed when not content-relevant
**AC-2.1.4**: Header/footer repetition is detected and cleaned across pages
**AC-2.1.5**: Intentional formatting is preserved (lists, emphasis, code blocks, paragraph breaks)
**AC-2.1.6**: Cleaning is deterministic (same input + config → same output, every time)
**AC-2.1.7**: Cleaning decisions are logged for audit trail (transformations, before/after)

## Story 2.2: Entity Normalization for Audit Domain

**AC-2.2.1**: Six entity types are recognized: processes, risks, controls, regulations, policies, issues
**AC-2.2.2**: Entity references are standardized (e.g., "Risk #123" → "Risk-123")
**AC-2.2.3**: Acronyms and abbreviations are expanded using configurable dictionary (GRC, SOX, NIST CSF)
**AC-2.2.4**: Consistent capitalization is applied to entity types
**AC-2.2.5**: Cross-references are resolved and linked to canonical entity IDs
**AC-2.2.6**: Entity mentions are tagged in metadata for downstream retrieval
**AC-2.2.7**: Normalization rules are configurable per organization (YAML-based)

## Story 2.3: Schema Standardization Across Document Types

**AC-2.3.1**: Document type is auto-detected (report, matrix, export, image) with >95% accuracy
**AC-2.3.2**: Type-specific schema transformations are applied (Pydantic models per type)
**AC-2.3.3**: Field names are standardized across source systems (Word, Excel, PDF, Archer)
**AC-2.3.4**: Semantic relationships are preserved (risk → control mappings, entity links)
**AC-2.3.5**: Metadata structure is consistent across all document types
**AC-2.3.6**: Archer-specific field schemas and hyperlinks are handled correctly
**AC-2.3.7**: Tables are converted to structured format with preserved rows/columns/headers

## Story 2.4: OCR Confidence Scoring and Validation

**AC-2.4.1**: OCR confidence score is calculated for each page/image using pytesseract
**AC-2.4.2**: Scores below 95% threshold are flagged for manual review (configurable threshold)
**AC-2.4.3**: OCR preprocessing is applied (deskew, denoise, contrast enhancement via Pillow)
**AC-2.4.4**: Scanned vs. native PDF is auto-detected
**AC-2.4.5**: Low-confidence results are quarantined separately with clear audit log
**AC-2.4.6**: Confidence scores are included in output metadata (per-page and document average)
**AC-2.4.7**: OCR operations are logged with before/after confidence metrics

## Story 2.5: Completeness Validation and Gap Detection

**AC-2.5.1**: Images without alt text are detected and flagged (QualityFlag.MISSING_IMAGES)
**AC-2.5.2**: Complex objects that can't be extracted are reported (OLE objects, charts, diagrams)
**AC-2.5.3**: Extraction completeness ratio is calculated (extracted_elements / total_elements)
**AC-2.5.4**: Content gaps are logged with specific locations (page number, section name)
**AC-2.5.5**: No silent failures occur - all issues are surfaced in validation report
**AC-2.5.6**: Validation report identifies what was skipped and why (actionable explanations)
**AC-2.5.7**: Flagged documents are marked in output metadata (QualityFlag enum values)

## Story 2.6: Metadata Enrichment Framework

**AC-2.6.1**: Source file path and SHA-256 hash are included in metadata
**AC-2.6.2**: Document type classification is added (DocumentType enum)
**AC-2.6.3**: Processing timestamp (ISO 8601) and tool version are recorded
**AC-2.6.4**: Entity tags list all identified entities in content (by type and ID)
**AC-2.6.5**: Quality scores aggregated (OCR confidence, readability, completeness ratio)
**AC-2.6.6**: Configuration snapshot used for processing is embedded (reproducibility)
**AC-2.6.7**: Metadata is serializable to JSON for persistence
**AC-2.6.8**: Metadata supports full audit trail (chunk → source document traceability)

## Epic-Level Acceptance Criteria

**AC-EPIC-2.1**: Overall test coverage >80% for all normalization modules
**AC-EPIC-2.2**: Entity normalization accuracy >90% on representative audit corpus
**AC-EPIC-2.3**: Document type detection accuracy >95% on test corpus
**AC-EPIC-2.4**: Zero brownfield regressions (existing tests still pass)
**AC-EPIC-2.5**: End-to-end normalization pipeline functional (extract → normalize → chunk integration)
**AC-EPIC-2.6**: All 6 stories delivered with 100% story-level acceptance criteria met
