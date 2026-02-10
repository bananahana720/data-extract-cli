# data-extraction-tool - Epic Breakdown

**Author:** andrew
**Date:** 2025-11-09
**Project Level:** High Complexity
**Target Scale:** MVP → Growth → Vision

---

## Overview

This document provides the complete epic and story breakdown for data-extraction-tool, decomposing the requirements from the [PRD](./PRD.md) into implementable stories.

## Epic Summary

This project transforms the data-extraction-tool from a functional brownfield foundation into a production-ready **knowledge quality gateway for enterprise Gen AI**. The epic breakdown addresses critical gaps (normalization, chunking, semantic analysis) while improving CLI usability to deliver RAG-optimized outputs that prevent AI hallucinations in high-accuracy audit environments.

**5 Epics Delivering Complete MVP:**

1. **Foundation & Project Setup** - Establish development infrastructure and brownfield baseline
2. **Robust Normalization & Quality Validation** - Critical gap: Clean, validated, RAG-ready content
3. **Intelligent Chunking & Output Formats** - Complete extraction-to-RAG pipeline with multi-format outputs
4. **Foundational Semantic Analysis** - Classical NLP capabilities (TF-IDF, LSA, similarity)
5. **Enhanced CLI UX & Batch Processing** - Usability blocker: Professional CLI experience

**Sequencing:** Foundation → Normalize → Chunk → Semantic → Polish
Each epic delivers independent value while building toward the complete MVP vision.

---

## Epic 1: Foundation & Project Setup

**Goal:** Establish robust development infrastructure and assess brownfield codebase to create a solid foundation for all subsequent work.

**Value:** Enables reliable development, testing, and deployment while understanding what's already built and what needs enhancement.

### Story 1.1: Project Infrastructure Initialization

As a developer,
I want a properly configured Python 3.12 development environment with dependency management,
So that I have a reliable foundation for building the data-extraction-tool.

**Acceptance Criteria:**

**Given** a fresh development environment
**When** I set up the project infrastructure
**Then** Python 3.12 is configured with virtual environment
**And** pyproject.toml defines all dependencies with pinned versions
**And** Development dependencies include pytest, black, mypy, ruff
**And** .gitignore properly excludes venv, __pycache__, output files
**And** Basic project structure is organized (src/, tests/, docs/, config/)
**And** README.md documents setup instructions and quick start

**Prerequisites:** None (first story)

**Technical Notes:**
- Use pyproject.toml for modern Python packaging (PEP 621)
- Pin all dependency versions for reproducibility (audit trail requirement)
- Include pre-commit hooks for code quality (black, ruff, mypy)
- Document Python 3.12 requirement clearly

### Story 1.2: Brownfield Codebase Assessment

As a developer,
I want to assess and document the existing brownfield extraction capabilities,
So that I understand what's already built and what gaps need to be filled.

**Acceptance Criteria:**

**Given** the existing data-extraction-tool codebase
**When** I perform a comprehensive assessment
**Then** I document all existing extraction capabilities by file type
**And** I identify which FR requirements are already met vs. missing
**And** I map existing code to the new project structure
**And** I document any technical debt or refactoring needs
**And** I create a brownfield assessment document in docs/
**And** I identify dependencies that need upgrading or replacing

**Prerequisites:** Story 1.1 (project infrastructure)

**Technical Notes:**
- Review existing PyMuPDF, python-docx, pytesseract usage
- Identify which normalization/chunking code exists
- Document current CLI command structure for comparison
- Note any hardcoded paths or configuration that needs fixing

### Story 1.3: Testing Framework and CI Pipeline

As a developer,
I want a comprehensive testing framework with CI automation,
So that I can develop confidently with automated quality checks.

**Acceptance Criteria:**

**Given** the project infrastructure is set up
**When** I implement the testing framework
**Then** pytest is configured with test discovery and coverage reporting
**And** Test fixtures exist for each document format (PDF, Word, Excel, etc.)
**And** Unit test structure mirrors src/ directory organization
**And** Integration test framework can process sample audit documents
**And** CI pipeline runs tests on every commit (GitHub Actions or similar)
**And** Code coverage reports are generated and tracked
**And** Pre-commit hooks enforce code quality before commits

**Prerequisites:** Story 1.1 (project infrastructure)

**Technical Notes:**
- Create test fixtures directory with sample files (sanitized audit docs)
- Configure pytest.ini with coverage thresholds (aim for >80%)
- Set up determinism validation tests (same input → same output)
- Include performance benchmarking in test suite

### Story 1.4: Core Pipeline Architecture Pattern

As a developer,
I want a well-defined pipeline architecture pattern for modular processing,
So that I can build composable components (extract → normalize → chunk → analyze).

**Acceptance Criteria:**

**Given** requirements for pipeline-style command composition
**When** I design the core architecture
**Then** Pipeline interface is defined with clear contracts
**And** Each stage (extract, normalize, chunk, semantic, output) is a standalone module
**And** Data flows between stages using standardized structures (Document, Chunk classes)
**And** Pipeline configuration is centralized and type-safe
**And** Architecture supports both pipeline and single-command execution
**And** Error handling strategy is consistent across all stages
**And** Architecture documentation exists in docs/architecture.md

**Prerequisites:** Story 1.2 (brownfield assessment to understand existing patterns)

**Technical Notes:**
- Define data models: Document, Chunk, Metadata classes with type hints
- Use Protocol/ABC for pipeline stage interfaces
- Consider using dataclasses or pydantic for configuration
- Design for determinism (no hidden state between stages)
- Ensure streaming/memory-efficient processing

---

## Epic 2: Robust Normalization & Quality Validation

**Goal:** Build the critical normalization layer that transforms raw extracted text into clean, validated, RAG-ready content with quality assurance.

**Value:** Addresses the critical gap identified in PRD - without this, the tool cannot deliver hallucination-free AI outputs. This is the foundation for all downstream processing.

### Story 2.1: Text Cleaning and Artifact Removal

As a data quality engineer,
I want to remove OCR artifacts and formatting noise from extracted text,
So that LLMs receive clean input without gibberish or formatting distractions.

**Acceptance Criteria:**

**Given** raw extracted text with OCR artifacts and formatting issues
**When** I apply text cleaning normalization
**Then** OCR artifacts are removed (garbled characters, repeated symbols)
**And** Excessive whitespace is normalized (single spaces, max 2 consecutive newlines)
**And** Page numbers, headers, footers are removed when not content-relevant
**And** Header/footer repetition is detected and cleaned
**And** Intentional formatting is preserved (lists, emphasis, code blocks)
**And** Cleaning is deterministic (same input → same output)
**And** Cleaning decisions are logged for audit trail

**Prerequisites:** Epic 1 complete (pipeline architecture exists)

**Technical Notes:**
- Use regex patterns for common OCR artifacts (^^^^^^^, ■■■■, etc.)
- Detect header/footer by repetition across pages
- Preserve semantic whitespace (paragraph breaks, list structure)
- Create configurable cleaning rules for different document types
- Log all transformations with before/after examples

### Story 2.2: Entity Normalization for Audit Domain

As an audit professional,
I want consistent formatting of audit entities (risks, controls, policies, etc.) across all documents,
So that AI can accurately understand and retrieve entity information.

**Acceptance Criteria:**

**Given** documents containing audit entities with inconsistent formatting
**When** I apply entity normalization
**Then** Six entity types are recognized: processes, risks, controls, regulations, policies, issues
**And** Entity references are standardized (e.g., "Risk #123" → "Risk-123")
**And** Acronyms and abbreviations are expanded using configurable dictionary
**And** Consistent capitalization is applied to entity types
**And** Cross-references are resolved and linked
**And** Entity mentions are tagged in metadata for retrieval
**And** Normalization rules are configurable per domain

**Prerequisites:** Story 2.1 (clean text to work with)

**Technical Notes:**
- Create entity recognition patterns (regex + context rules)
- Build audit domain dictionary (GRC, SOX, NIST CSF, etc.)
- Design entity linking system (mentions → canonical IDs)
- Support Archer entity ID formats
- Tag entities in chunk metadata for downstream use

### Story 2.3: Schema Standardization Across Document Types

As a developer,
I want to apply consistent schemas across different document source types,
So that Word reports, Excel matrices, and Archer exports have uniform structure.

**Acceptance Criteria:**

**Given** documents from multiple source types (Word, Excel, PDF, Archer HTML/XML)
**When** I apply schema standardization
**Then** Document type is auto-detected (report, matrix, export, image)
**And** Type-specific schema transformations are applied
**And** Field names are standardized across source systems
**And** Semantic relationships are preserved (risk → control mappings)
**And** Metadata structure is consistent across all document types
**And** Archer-specific field schemas and hyperlinks are handled
**And** Tables are converted to structured format (preserve rows/columns)

**Prerequisites:** Story 2.1 (clean text), Story 2.2 (entity normalization)

**Technical Notes:**
- Create schema definitions for each document type
- Handle Archer HTML/XML field patterns and module variations
- Parse Excel tables preserving structure (control matrices, risk registers)
- Extract Word document structure (headings, sections, embedded tables)
- Maintain traceability (output → source field mapping)

### Story 2.4: OCR Confidence Scoring and Validation

As a quality assurance engineer,
I want OCR operations to include confidence scoring and validation,
So that low-quality extractions are flagged before reaching AI systems.

**Acceptance Criteria:**

**Given** scanned PDFs and images requiring OCR
**When** I process them with quality validation
**Then** OCR confidence score is calculated for each page/image
**And** Scores below 95% threshold are flagged for manual review
**And** OCR preprocessing is applied (deskew, denoise, contrast enhancement)
**And** Scanned vs. native PDF is auto-detected
**And** Low-confidence results are quarantined separately
**And** Confidence scores are included in output metadata
**And** OCR operations are logged with before/after confidence metrics

**Prerequisites:** Story 2.1 (cleaning framework exists)

**Technical Notes:**
- Use pytesseract confidence scoring features
- Implement image preprocessing pipeline (OpenCV or Pillow)
- Create configurable confidence thresholds
- Design quarantine directory structure for flagged content
- Log OCR metrics for audit trail compliance

### Story 2.5: Completeness Validation and Gap Detection

As an audit professional,
I want to detect and flag incomplete extractions or missing content,
So that I can trust all critical information is captured (no silent data loss).

**Acceptance Criteria:**

**Given** documents with potentially unextracted content
**When** I run completeness validation
**Then** Images without alt text are detected and flagged
**And** Complex objects that can't be extracted are reported
**And** Extraction confidence score is generated per document
**And** Content gaps are logged with specific locations (page, section)
**And** No silent failures occur - all issues are surfaced
**And** Validation report identifies what was skipped and why
**And** Flagged documents are marked in output metadata

**Prerequisites:** Story 2.1-2.4 (normalization pipeline complete)

**Technical Notes:**
- Detect embedded images, charts, diagrams in source files
- Flag complex tables that may lose structure in extraction
- Calculate extraction completeness ratio (extracted / total content)
- Create actionable validation reports with suggestions
- Support manual review workflow for flagged content

### Story 2.6: Metadata Enrichment Framework

As a developer,
I want to enrich all processed content with comprehensive metadata,
So that outputs include traceability, quality scores, and entity information.

**Acceptance Criteria:**

**Given** normalized and validated content
**When** I apply metadata enrichment
**Then** Source file path and hash are included
**And** Document type classification is added
**And** Processing timestamp and tool version are recorded
**And** Entity tags list all identified entities in content
**And** Quality scores include OCR confidence, readability, completeness
**And** Configuration used for processing is embedded
**And** Metadata is serializable to JSON for persistence
**And** Metadata supports full audit trail (chunk → source traceability)

**Prerequisites:** Story 2.1-2.5 (all normalization components exist)

**Technical Notes:**
- Define Metadata dataclass with comprehensive fields
- Include processing configuration for reproducibility
- Add section/heading context from source document
- Store entity mentions with types and locations
- Design metadata schema versioning for future evolution

---

## Epic 3: Intelligent Chunking & Output Formats

**Goal:** Implement semantic chunking that respects boundaries and context, then deliver outputs in multiple RAG-optimized formats (JSON, TXT, CSV).

**Value:** Completes the extraction-to-RAG pipeline, delivering the core "product magic" - clean, structured, ready-to-upload chunks that prevent AI hallucinations.

### Story 3.1: Semantic Boundary-Aware Chunking Engine

As a RAG engineer,
I want chunks that respect semantic boundaries (sentences, paragraphs, sections),
So that each chunk contains complete, coherent thoughts without mid-sentence splits.

**Acceptance Criteria:**

**Given** normalized text with preserved structure
**When** I apply semantic chunking
**Then** Chunks never split mid-sentence
**And** Section boundaries are respected when possible (complete sections)
**And** Chunk size is configurable (default: 256-512 tokens)
**And** Chunk overlap is configurable (default: 10-20%)
**And** Sentence tokenization uses spaCy for accuracy
**And** Edge cases are handled (very long sentences, short sections)
**And** Chunking is deterministic (same input → same chunks)

**Prerequisites:** Epic 2 complete (normalized, validated text available)

**Technical Notes:**
- Use spaCy sentence segmentation for accuracy
- Implement sliding window with overlap for context preservation
- Handle edge cases: sentences > chunk size, micro-sections
- Support both token-based and character-based sizing
- Log chunking decisions for audit trail

### Story 3.2: Entity-Aware Chunking

As an audit professional,
I want chunks that keep entity mentions and their context together,
So that entity relationships are preserved and retrievals are complete.

**Acceptance Criteria:**

**Given** text with identified entity mentions (from Epic 2)
**When** I apply entity-aware chunking
**Then** Entity mentions are kept within single chunks when possible
**And** Entities split across chunks are noted in metadata (continued/partial flags)
**And** Relationship context is preserved (e.g., "Risk X mitigated by Control Y")
**And** Chunk boundaries avoid splitting entity definitions
**And** Cross-references are maintained with entity IDs
**And** Entity tags in chunk metadata indicate which entities appear

**Prerequisites:** Story 3.1 (semantic chunking engine), Story 2.2 (entity normalization)

**Technical Notes:**
- Analyze entity mentions before chunking to plan boundaries
- Prefer chunk splits between entities rather than within
- Add "entity_context" metadata field for partial entities
- Maintain entity relationship graph across chunks
- Support configurable entity priority (some entities more important to keep intact)

### Story 3.3: Chunk Metadata and Quality Scoring

As a quality engineer,
I want each chunk enriched with quality scores and contextual metadata,
So that RAG systems can filter and prioritize high-quality retrievals.

**Acceptance Criteria:**

**Given** semantically chunked content
**When** I calculate chunk metadata and scores
**Then** Each chunk includes source document and file path
**And** Section/heading context shows document structure location
**And** Entity tags list all entities appearing in chunk
**And** Readability score is calculated (Flesch-Kincaid, Gunning Fog)
**And** Quality score combines OCR confidence, completeness, coherence
**And** Chunk position in document is tracked (sequential index)
**And** Word count and token count are included
**And** Low-quality chunks are flagged with specific issues

**Prerequisites:** Story 3.1-3.2 (chunking complete), Story 2.6 (metadata framework)

**Technical Notes:**
- Use textstat library for readability metrics
- Calculate coherence using semantic similarity within chunk
- Combine multiple quality signals into composite score
- Flag chunks: low_ocr, incomplete_extraction, high_complexity, gibberish
- Include chunk_id with source file prefix for traceability

### Story 3.4: JSON Output Format with Full Metadata

As a developer,
I want structured JSON output with complete chunk metadata,
So that I can use chunks in vector databases and RAG systems.

**Acceptance Criteria:**

**Given** enriched chunks with metadata
**When** I export to JSON format
**Then** JSON structure includes chunk text and full metadata object
**And** Output is valid, parsable JSON (not JSON Lines)
**And** Metadata includes all fields: source, entities, quality, position, timestamps
**And** JSON is pretty-printed for human readability
**And** Array of chunks can be filtered/queried easily
**And** Configuration and processing version are in JSON header
**And** JSON validates against a defined schema (optional: JSON Schema file)

**Prerequisites:** Story 3.3 (chunk metadata complete)

**Technical Notes:**
- Design JSON schema: { "metadata": {...}, "chunks": [{...}] }
- Include processing configuration in header for reproducibility
- Use Python json module with indent=2 for readability
- Consider JSON Lines (.jsonl) as alternative for very large outputs
- Provide schema validation capability

### Story 3.5: Plain Text Output Format for LLM Upload

As a user,
I want clean plain text output optimized for direct LLM upload (ChatGPT, Claude),
So that I can quickly process and upload audit documents to AI tools.

**Acceptance Criteria:**

**Given** enriched chunks with metadata
**When** I export to TXT format
**Then** Each chunk is clean plain text without markup or noise
**And** Chunks are separated by configurable delimiter (default: ━━━ CHUNK N ━━━)
**And** Optional metadata header per chunk (source file, entities, quality score)
**And** Output organization: single concatenated file OR one file per chunk
**And** Character encoding is UTF-8 with proper handling
**And** No formatting artifacts that would confuse LLMs
**And** TXT files are ready for direct copy-paste or upload

**Prerequisites:** Story 3.3 (chunk metadata complete)

**Technical Notes:**
- Configurable options: concatenated vs. separate files
- Chunk delimiter should be visually distinct but LLM-friendly
- Metadata header optional (--include-metadata flag)
- File naming: source_file_chunk_001.txt for traceability
- Ensure proper line ending handling (CRLF on Windows)

### Story 3.6: CSV Output Format for Analysis and Tracking

As a data analyst,
I want tabular CSV output with chunks and metadata in columns,
So that I can analyze, filter, and track processed content in spreadsheets.

**Acceptance Criteria:**

**Given** enriched chunks with metadata
**When** I export to CSV format
**Then** CSV has columns: chunk_id, source_file, chunk_text, entities, quality_score, readability, section, word_count
**And** CSV is properly escaped (handles commas, quotes, newlines in text)
**And** Header row clearly labels all columns
**And** CSV is importable to Excel, Google Sheets, pandas
**And** Very long chunk text is optionally truncated with indicator
**And** Entity lists are formatted as semicolon-separated values
**And** CSV validates with standard parsers (Python csv module, pandas)

**Prerequisites:** Story 3.3 (chunk metadata complete)

**Technical Notes:**
- Use Python csv module with QUOTE_ALL for safety
- Consider separate CSV for chunk index vs. full text (handle length limits)
- Include all quality and metadata fields as columns
- Support filtering options (e.g., export only high-quality chunks)
- Document CSV schema in README or docs/

### Story 3.7: Configurable Output Organization Strategies

As a user,
I want flexible output organization (by document, by entity, or flat),
So that outputs match my downstream workflow needs.

**Acceptance Criteria:**

**Given** processed chunks in multiple formats
**When** I configure output organization
**Then** Three strategies are supported: by_document, by_entity, flat
**And** **by_document** creates folder per source file with its chunks
**And** **by_entity** groups chunks by entity type (all risks together, all controls together)
**And** **flat** puts all chunks in single directory with prefixed naming
**And** Organization is configurable via CLI flag or config file
**And** Source file traceability is maintained regardless of organization
**And** All three formats (JSON, TXT, CSV) respect organization strategy
**And** Output directory structure is documented

**Prerequisites:** Story 3.4-3.6 (all output formats exist)

**Technical Notes:**
- Design directory structure for each organization strategy
- File naming conventions preserve traceability: {source}_{chunk_id}.{ext}
- Entity organization requires entity tags from Story 2.2
- Create manifest file listing all outputs with metadata
- Support custom organization strategies in future (extensibility)

---

## Epic 4: Foundational Semantic Analysis

**Goal:** Implement classical NLP techniques (TF-IDF, LSA, similarity) to enable document understanding, similarity analysis, and semantic grouping.

**Value:** Unlocks User Journey B (semantic analysis learning), enables advanced use cases (find related docs, detect redundancy), builds foundation for future knowledge graph features.

### Story 4.1: TF-IDF Vectorization Engine

As a data scientist,
I want to generate TF-IDF vectors for documents and chunks,
So that I can identify important terms and concepts in my audit corpus.

**Acceptance Criteria:**

**Given** a corpus of processed documents and chunks
**When** I generate TF-IDF vectors
**Then** scikit-learn TfidfVectorizer is used with configurable parameters
**And** Vocabulary size is configurable (default: 10,000 features)
**And** N-gram range is configurable (default: unigrams and bigrams)
**And** Custom stopwords can be provided (domain-specific exclusions)
**And** IDF weights are calculated and exportable
**And** Term importance rankings are generated per document
**And** Vectors are sparse matrices for memory efficiency
**And** Vectorizer can be saved/loaded for reproducibility

**Prerequisites:** Epic 3 complete (chunks available)

**Technical Notes:**
- Use scikit-learn TfidfVectorizer with max_features, ngram_range parameters
- Save fitted vectorizer using joblib for consistency
- Generate vocabulary with IDF scores for inspection
- Support both document-level and chunk-level vectorization
- Log vectorization parameters for audit trail

### Story 4.2: Document and Chunk Similarity Analysis

As a user,
I want to find semantically similar documents and chunks using cosine similarity,
So that I can identify related content and detect redundancy.

**Acceptance Criteria:**

**Given** TF-IDF vectors for corpus
**When** I compute similarity analysis
**Then** Pairwise cosine similarity is calculated between all items
**And** Top-N most similar items can be queried for any document/chunk
**And** Similarity threshold is configurable (default: 0.8 for "similar")
**And** Similarity matrix is generated for entire corpus
**And** Results show similarity scores with source references
**And** Both document-level and chunk-level similarity are supported
**And** Computation is optimized for large corpora (sparse matrix operations)

**Prerequisites:** Story 4.1 (TF-IDF vectors available)

**Technical Notes:**
- Use scikit-learn cosine_similarity on sparse TF-IDF matrices
- Implement efficient top-K retrieval (avoid full sort for large N)
- Store similarity matrix in sparse format to save memory
- Provide similarity report: query → top matches with scores
- Support filtering by document type or entity type

### Story 4.3: Latent Semantic Analysis (LSA) Implementation

As a data scientist,
I want to apply LSA dimensionality reduction to discover latent semantic topics,
So that I can understand themes and patterns in audit documents.

**Acceptance Criteria:**

**Given** TF-IDF vectors for corpus
**When** I apply LSA transformation
**Then** TruncatedSVD (LSA) is applied to reduce dimensionality
**And** Number of components is configurable (default: 100-300)
**And** Lower-dimensional semantic embeddings are generated
**And** Explained variance ratio is reported for component selection
**And** Documents can be clustered in semantic space
**And** LSA model can be saved/loaded for reproducibility
**And** Semantic similarity in reduced space can be computed

**Prerequisites:** Story 4.1 (TF-IDF vectors), Story 4.2 (similarity framework)

**Technical Notes:**
- Use scikit-learn TruncatedSVD for LSA
- Report explained variance to guide component count selection
- Generate semantic embeddings for all documents/chunks
- Support clustering in LSA space (KMeans or hierarchical)
- Provide topic inspection (top terms per component)

### Story 4.4: Quality Metrics Integration with Textstat

As a quality engineer,
I want comprehensive readability and quality metrics for all chunks,
So that I can objectively assess content quality before LLM upload.

**Acceptance Criteria:**

**Given** chunked content
**When** I calculate quality metrics
**Then** Flesch-Kincaid Grade Level is calculated per chunk
**And** Gunning Fog Index is calculated
**And** SMOG Index is calculated
**And** Lexical diversity is assessed
**And** Sentence count, word count, syllable count are provided
**And** Quality scores are included in chunk metadata
**And** Chunks exceeding complexity thresholds are flagged
**And** Average metrics are reported across entire corpus

**Prerequisites:** Story 3.3 (chunk metadata framework exists)

**Technical Notes:**
- Use textstat library for all readability metrics
- Set domain-appropriate thresholds (audit docs are inherently technical)
- Add quality scores to chunk metadata dictionary
- Generate quality distribution report (histogram of scores)
- Flag overly complex chunks with specific metric values

### Story 4.5: Similarity Analysis CLI Command and Reporting

As a user,
I want a CLI command to find similar documents and generate similarity reports,
So that I can explore relationships in my document corpus.

**Acceptance Criteria:**

**Given** processed documents with TF-IDF/LSA vectors
**When** I run the similarity analysis command
**Then** `data-extract similarity <file>` finds top-N similar documents
**And** `data-extract similarity --matrix` generates full similarity matrix
**And** Similarity report shows: query doc, top matches, scores, shared entities
**And** Results are exportable (JSON, CSV)
**And** Similarity visualization is generated (optional: heatmap, network graph)
**And** Progress indicator shows computation status for large corpora
**And** Results are cached for faster subsequent queries

**Prerequisites:** Story 4.1-4.3 (semantic analysis components), Epic 5 (CLI framework)

**Technical Notes:**
- Design CLI interface: `data-extract similarity [options] <query>`
- Support query by file path or document ID
- Generate human-readable report with highlights
- Export formats: JSON (structured), CSV (tabular), TXT (readable)
- Consider optional visualization using matplotlib or plotly

---

## Epic 5: Enhanced CLI UX & Batch Processing

**Goal:** Build professional CLI interface with streamlined commands, configuration management, progress feedback, and robust error handling.

**Value:** Removes usability blocker, makes tool production-ready for daily use. Delivers on PRD requirement for "improved CLI UX" and batch processing efficiency.

**UX Design Specification:** `docs/ux-design-specification.md` - 7 user journeys defined with UAT assertions.

**UAT Strategy:** tmux-cli based automated testing validates CLI user journeys on every PR.

### Story 5.0: UAT Testing Framework (P0 Foundation)

As a QA engineer,
I want an automated UAT testing framework using tmux-cli that validates CLI user journeys against the UX Design Specification,
So that every PR ensures the interactive CLI experience matches our design intent.

**Acceptance Criteria:**

**Given** the UAT test framework
**When** a PR is submitted
**Then** tmux-cli launches CLI in automated pane
**And** User journeys (1-7) are validated programmatically
**And** Rich components (panels, progress bars, tables) are detected
**And** Test results report UX compliance status

**Priority:** P0 - Blocks all other Epic 5 stories
**Estimate:** 8 hours
**Status:** drafted
**Story File:** `docs/stories/5-0-uat-testing-framework.md`

**Key Dependencies:**
- tmux-cli tool (`uv tool install tmux-cli`)
- UX Design Specification (complete)
- Sample corpus for testing

**Implementation Notes:**
- Tests run on every PR via GitHub Actions
- Ubuntu runner with tmux installed
- Validates all 7 user journeys from UX spec
- Uses screen capture and ANSI parsing for Rich component detection

### Story 5.1: Refactored Command Structure with Pipeline Support

As a user,
I want intuitive pipeline-style commands that are modular and composable,
So that I can customize workflows or use simple defaults.

**Acceptance Criteria:**

**Given** the new CLI architecture
**When** I use pipeline commands
**Then** Basic processing works: `data-extract process <input>`
**And** Pipeline composition is supported: `data-extract <input> | normalize | chunk | output`
**And** Each component (normalize, chunk, semantic, output) is modular
**And** Components can be reordered or omitted as needed
**And** Single-step commands also work (non-pipeline mode)
**And** Default pipeline executes when no components specified
**And** Help text clearly explains pipeline vs. single-step usage

**Prerequisites:** Epic 1 (pipeline architecture), Epics 2-4 (processing components exist)

**Technical Notes:**
- Use Click or Typer for modern CLI framework
- Implement pipeline pattern with standardized data passing
- Each component returns processed data for next stage
- Support both: `process --normalize --chunk` and pipeline syntax
- Clear error messages if pipeline is misconfigured

### Story 5.2: Configuration Management System

As a user,
I want persistent configuration with multiple sources (file, env vars, CLI flags),
So that I don't have to re-enter parameters for every execution.

**Acceptance Criteria:**

**Given** the need for reproducible workflows
**When** I configure the tool
**Then** YAML config file is supported (~/.data-extract/config.yaml or project-local)
**And** Environment variables override config file values
**And** CLI flags override environment variables
**And** Precedence is clear: CLI > env vars > config file > defaults
**And** `data-extract config init` creates default config file
**And** `data-extract config show` displays merged configuration
**And** `data-extract config validate` checks config for errors
**And** Interactive prompts for missing required values save to config when requested

**Prerequisites:** Story 5.1 (CLI framework)

**Technical Notes:**
- Use PyYAML or similar for config file parsing
- Define configuration schema with validation
- Support both global (~/.data-extract/) and project-local config
- Environment variables: DATA_EXTRACT_* prefix
- Include processing version in config for reproducibility

### Story 5.3: Real-Time Progress Indicators and Feedback

As a user,
I want real-time progress bars and status updates during batch processing,
So that I know what's happening and can estimate completion time.

**Acceptance Criteria:**

**Given** a batch of files being processed
**When** I monitor progress
**Then** Progress bar shows: percentage, file count (13/20), current file
**And** Elapsed time and estimated time remaining are displayed
**And** Progress updates at least every 2 seconds
**And** Verbose mode levels control detail: -v, -vv, -vvv
**And** Quiet mode (-q) suppresses all but errors
**And** Progress indicator uses entire terminal width effectively
**And** Errors during processing are shown but don't halt progress bar

**Prerequisites:** Story 5.1 (CLI framework), Story 5.7 (batch processing)

**Technical Notes:**
- Use tqdm or rich library for progress bars
- Stream verbose output in real-time (not buffered)
- Handle terminal width detection and resizing
- Clean progress bar cleanup on completion or error
- Support non-TTY environments (log output without fancy formatting)

### Story 5.4: Comprehensive Summary Statistics and Reporting

As a user,
I want detailed summary statistics after processing completes,
So that I understand what was processed, quality metrics, and next steps.

**Acceptance Criteria:**

**Given** batch processing has completed
**When** I view the summary
**Then** Files processed count is shown (with error count)
**And** Total chunks created across all files
**And** Output formats generated (JSON, TXT, CSV)
**And** Quality metrics summary: avg OCR confidence, flagged chunks, entities identified
**And** Time elapsed for entire batch
**And** Output location is clearly indicated
**And** Error summary lists each failed file with actionable suggestions
**And** Next step recommendations are provided (validate, similarity, review flagged)

**Prerequisites:** Story 5.1-5.3 (CLI framework and progress)

**Technical Notes:**
- Design summary report template with sections
- Include processing configuration in summary for reproducibility
- Provide actionable suggestions based on results (e.g., "Review 12 flagged chunks")
- Format summary with clear visual separators (━━━ sections)
- Export summary to log file for later reference

### Story 5.5: Preset Configurations for Common Workflows

As a user,
I want named presets for common use cases (ChatGPT upload, knowledge graphs, high accuracy),
So that I can execute workflows with a single command.

**Acceptance Criteria:**

**Given** common workflow scenarios
**When** I use preset configurations
**Then** `--preset chatgpt` optimizes for ChatGPT upload (256 tokens, TXT format)
**And** `--preset knowledge-graph` optimizes for entity extraction and relationships
**And** `--preset high-accuracy` maximizes quality validation, lowers throughput
**And** Presets override defaults but can be further customized with flags
**And** Custom presets are definable in config file
**And** `data-extract presets list` shows all available presets with descriptions
**And** Presets are versioned and documented

**Prerequisites:** Story 5.2 (configuration system)

**Technical Notes:**
- Define presets as YAML configurations
- Built-in presets shipped with tool, custom in user config
- Preset inheritance: custom can extend built-in
- Document each preset: purpose, parameters, use case
- Allow CLI flag overrides: `--preset chatgpt --chunk-size 512`

### Story 5.6: Graceful Error Handling and Recovery

As a user,
I want robust error handling that continues batch processing and provides recovery options,
So that one bad file doesn't block my entire workflow.

**Acceptance Criteria:**

**Given** batch processing with potential file errors
**When** errors occur
**Then** Processing continues for remaining files (no halt)
**And** All errors are collected and shown in summary
**And** Detailed errors are written to log file with stack traces
**And** Exit code reflects status: 0=success, 1=partial failure, 2=complete failure
**And** Error messages categorize: CRITICAL, ERROR, WARNING, INFO
**And** Error messages include actionable suggestions
**And** `data-extract retry <log-file>` can retry only failed files
**And** Problematic files are quarantined for manual review

**Prerequisites:** Story 5.1 (CLI framework), Story 5.4 (summary reporting)

**Technical Notes:**
- Implement error categorization system
- Catch expected errors gracefully (file not found, corrupted, etc.)
- Log unexpected errors with full stack traces
- Create retry mechanism using processing log
- Design quarantine directory structure
- Provide specific suggestions: "Try --ocr-threshold 0.85" for low OCR confidence

### Story 5.7: Batch Processing Optimization and Incremental Updates

As a user,
I want efficient batch processing with incremental updates (skip already-processed files),
So that I can re-process document sets quickly when adding new files.

**Acceptance Criteria:**

**Given** a directory with some previously processed files
**When** I run batch processing
**Then** Previously processed files are detected by hash or timestamp
**And** Unchanged files are skipped automatically
**And** Only new or modified files are processed
**And** `--force` flag overrides skip logic (force re-processing)
**And** Processing manifest tracks all processed files with metadata
**And** Parallel processing is supported for improved throughput (configurable workers)
**And** Memory usage remains constant regardless of batch size (streaming)

**Prerequisites:** Story 5.1 (CLI framework), Epics 2-4 (processing components)

**Technical Notes:**
- Use file hashing (SHA-256) for change detection
- Maintain manifest: {file_hash: {processed_date, output_path, metadata}}
- Implement parallel processing with multiprocessing or concurrent.futures
- Configurable worker count (default: CPU count - 1)
- Ensure determinism even with parallel processing (consistent ordering)

---

## Epic Breakdown Summary

**Total Stories:** 34 bite-sized, implementable stories across 5 epics

**Epic Completion Sequence:**
1. **Epic 1** (4 stories) - Foundation established, brownfield assessed, ready to build
2. **Epic 2** (6 stories) - Critical gap closed: normalization and quality validation complete
3. **Epic 3** (7 stories) - MVP pipeline complete: chunking and multi-format output delivered
4. **Epic 4** (5 stories) - Semantic analysis unlocked: TF-IDF, LSA, similarity working
5. **Epic 5** (8 stories) - Production-ready: Professional CLI UX and batch processing with UAT

**MVP Completion:** All 5 epics = Complete MVP with:
- ✅ Robust normalization layer (Epic 2)
- ✅ CLI UI/UX improvements (Epic 5)
- ✅ Structured output formats (Epic 3)
- ✅ Foundational semantic processing (Epic 4)
- ✅ Solid development foundation (Epic 1)

**Key Dependencies:**
- Epic 1 must complete first (foundation for all work)
- Epic 2 enables Epic 3 (normalized data needed for chunking)
- Epic 3 enables Epic 4 (chunks needed for semantic analysis)
- Epic 5 can develop in parallel with Epic 2-4 (CLI framework is independent)

**Acceptance Criteria Coverage:**
- All stories use BDD format (Given/When/Then)
- All stories are vertically sliced (complete functionality)
- No forward dependencies (only reference previous stories)
- All stories sized for single dev agent session
- All stories connect to user value and PRD requirements

**Domain Compliance:**
- Entity preservation (6 types: processes, risks, controls, regulations, policies, issues)
- Deterministic processing (audit trail requirement)
- Quality validation (no silent failures)
- Classical NLP only (no transformers)
- Python 3.12 requirement
- On-premise processing

---

_For implementation: Use the `create-story` workflow to generate individual story implementation plans from this epic breakdown._
