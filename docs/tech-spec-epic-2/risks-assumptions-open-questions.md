# Risks, Assumptions, Open Questions

## Risks

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

## Assumptions

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

## Open Questions

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
