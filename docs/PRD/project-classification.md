# Project Classification

**Technical Type:** CLI Tool
**Domain:** Cybersecurity Internal Audit (GRC/Compliance)
**Complexity:** High

This is a **command-line interface tool** designed for batch processing and scriptable automation. It operates in the **cybersecurity internal audit domain** within a F100 enterprise environment, specifically working with GRC (Governance, Risk, Compliance) platform data from Archer.

**Why CLI:**
- Power user target audience (AI-savvy but learning semantic analysis)
- Batch processing workflows (hundreds/thousands of documents)
- Automation and scripting potential
- Enterprise environment compatibility (no GUI deployment overhead)
- Future consideration: GUI wrapper for broader adoption

**Domain Characteristics:**
- **Highly structured entities:** processes, risks, controls, regulations, policies, issues, audit findings
- **Accuracy-critical:** Compliance and audit require high precision
- **Sensitive data:** Enterprise security policies, restricted access
- **Complex relationships:** Interconnected compliance frameworks, regulatory requirements

## Domain Context

**Cybersecurity Internal Audit Environment:**

The tool operates in a F100 company's internal audit function focused on cybersecurity compliance. **Source data consists of user-provided files** in various formats:

- **Office Documents:** Word (.doc/.docx), Excel (.xlsx/.csv), PowerPoint (.pptx)
- **PDF Files:** Standard PDFs and scanned/printed PDFs requiring OCR
- **Images:** Screenshots and image files
- **Archer GRC Exports:** HTML and XML files (with or without hyperlinks)
- **Context Files:** User-provided context documents in supported formats

All inputs are user-supplied files, not direct system integrations. This provides flexibility to process any audit-related document regardless of origin system.

**Domain Complexity Drivers:**
1. **Entity Structure:** Documents contain tightly defined entity types (processes, risks, controls, regulations, policies, issues) with specific relationships and metadata requirements
2. **Accuracy Requirements:** Audit and compliance contexts demand high precision—incomplete or inaccurate AI retrievals can lead to compliance gaps or incorrect risk assessments
3. **Enterprise Constraints:** Python 3.11+ required (minimum version), no transformer-based LLMs allowed (enterprise restriction), on-premise processing only
4. **Knowledge Graph Needs:** Entities and relationships need preservation for downstream AI consumption

**Technical Constraints from Domain:**
- No external LLM APIs (security policy)
- No transformer models (enterprise IT restriction)
- Classical NLP methods only (TF-IDF, LSA, Word2Vec, LDA)
- On-premise, local processing required

---
