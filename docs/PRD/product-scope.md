# Product Scope

**Context:** This is a **brownfield project** with foundational data extraction capabilities already implemented. The MVP focuses on completing the pipeline from raw extraction → RAG-optimized output.

## MVP - Minimum Viable Product

**Goal:** Complete the extraction-to-RAG pipeline with robust normalization, improved CLI usability, and foundational semantic processing.

**What's Already Built (Brownfield Foundation):**
- ✅ Core document extraction from multiple file types
- ✅ Basic text processing and structure preservation
- ✅ Initial output generation

**What Must Be Added for MVP:**

**1. Robust Normalization Layer** (Critical Gap)
- Text cleaning and standardization (remove OCR artifacts, formatting noise)
- Schema standardization across different source document types
- Entity normalization (consistent formatting of risks, controls, policies, etc.)
- Quality validation and flagging (identify incomplete or problematic extractions)
- Metadata enrichment (document type, source file, extraction confidence)

**2. CLI UI/UX Improvements** (Usability Blocker)
- Streamlined command structure (reduce current cumbersome workflow)
- Interactive configuration prompts for common options
- Clear progress indicators for batch processing
- Helpful error messages and recovery suggestions
- Configuration file support (avoid re-entering parameters)

**3. Structured Output Formats** (Quality of Life)
- Chunking with multiple output formats:
  - **JSON:** Structured chunks with metadata (section, entities, quality scores)
  - **TXT:** Clean plain text chunks for direct LLM upload
  - **CSV:** Tabular chunk index for analysis and tracking
- Configurable chunk size and overlap settings
- Output organization (by document, by entity type, or flat structure)

**4. Foundational Semantic Processing** (New Capability - User Journey B)
- **TF-IDF vectorization:** Identify important terms in audit documents
- **Document similarity:** Find related documents/chunks using cosine similarity
- **Basic LSA:** Dimensionality reduction for semantic grouping
- **Quality metrics:** Readability scores and content assessment (textstat integration)
- **Semantic chunking baseline:** Sentence-aware chunking that respects semantic boundaries

**MVP Acceptance Criteria:**
- Can process a batch of mixed file types (PDF, Word, Excel, Archer HTML) end-to-end
- Outputs are clean, normalized, and chunked in all three formats (JSON, TXT, CSV)
- CLI workflow is streamlined vs. current implementation
- Can calculate document similarity and identify related content
- Quality scores flag problematic content before upload to LLM

## Growth Features (Post-MVP)

**Goal:** Make the tool compelling enough to share with coworkers and expand semantic capabilities.

**Advanced Semantic Analysis:**
- **Word2Vec/FastText:** Domain-specific word embeddings trained on audit corpus
- **LDA Topic Modeling:** Automatic discovery of themes in document collections
- **Custom NER:** Trained entity recognition for audit-specific entities (risks, controls, policies)
- **Knowledge Graph Generation:** Visual representation of entity relationships

**Enhanced Output & Integration:**
- Knowledge graph export formats (GraphML, Neo4j, RDF)
- Direct integration with vector databases (Pinecone, Weaviate, Chroma)
- Chunk embedding generation for RAG systems
- Deduplication across document sets (identify redundant content)

**Team-Friendly Features:**
- Preset configurations for common audit document types
- Batch reporting (summary stats, processing logs, quality dashboard)
- Comparison mode (before/after RAG quality metrics)
- Documentation and examples for coworker onboarding

**Advanced CLI Capabilities:**
- Pipeline composition (chain multiple processing steps)
- Watch mode (auto-process new files in a folder)
- Incremental processing (skip already-processed files)

## Vision (Future)

**Goal:** The dream version - team standard tool with full capabilities.

**GUI Wrapper:**
- Desktop application for non-technical users
- Visual configuration builder
- Drag-and-drop file processing
- Interactive knowledge graph visualization

**Advanced Intelligence:**
- Automated entity relationship extraction
- Cross-document inference (identify gaps in compliance coverage)
- Anomaly detection (flag unusual patterns in audit documents)
- Smart chunking (adaptive chunk sizes based on content complexity)

**Enterprise Integration:**
- Direct Archer GRC API integration (optional, replacing file export workflow)
- SharePoint/OneDrive connector
- Scheduled batch processing for recurring audit cycles
- Multi-user configuration management

**Expanded Domain Support:**
- Configurable entity types for different audit domains
- Industry-specific templates (SOX, HIPAA, GDPR, etc.)
- Multi-language support for international operations

**Advanced Analytics:**
- Trend analysis across audit periods
- Gap analysis (identify missing controls or policies)
- Risk coverage mapping
- Compliance dashboard generation

---

## V1.0 Implementation Status (December 2025)

**MVP Status: COMPLETE**

All MVP requirements delivered with enhancements:

### Robust Normalization Layer
- **Status:** COMPLETE (Epic 2)
- **Stories:** 6 delivered
- **Enhancement:** Schema validation beyond original requirements

### CLI UI/UX Improvements
- **Status:** COMPLETE (Epic 5)
- **Stories:** 8 delivered
- **Enhancement:** Rich terminal UI, learning mode, session persistence with resume capability

### Structured Output Formats
- **Status:** COMPLETE (Epic 3)
- **Stories:** 7 delivered
- **Enhancement:** Full schema validation, all three formats (JSON/TXT/CSV) with configurable organization

### Foundational Semantic Processing
- **Status:** COMPLETE (Epic 4)
- **Stories:** 6 delivered
- **Enhancement:** Performance 10-83x better than targets; full TF-IDF, LSA, similarity analysis suite

### Growth Features Delivered in V1.0
Several growth features were pulled forward into V1.0:
- Preset configurations (quality, speed, balanced)
- Batch reporting with comprehensive summary statistics
- Incremental processing with hash-based change detection
- Semantic deduplication detection via similarity analysis

---
