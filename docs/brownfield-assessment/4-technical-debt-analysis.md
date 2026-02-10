# 4. Technical Debt Analysis

## 4.1 Technical Debt Heat Map

| Category | Priority | Severity | Complexity | Effort | Risk | Epic |
|----------|----------|----------|------------|--------|------|------|
| **Feature Incompleteness** |
| DOCX image extraction | 🔴 HIGH | Medium | Medium | Medium | Low | Epic 2 |
| TXT encoding/markdown parsing | 🔴 HIGH | Medium | Medium | Medium | Medium | Epic 2 |
| Chunk overlap implementation | 🔴 HIGH | Low | Low | Low | Low | Epic 3 |
| Markdown table rendering | 🟡 MEDIUM | Low | Low | Medium | Low | Epic 3 |
| CSV output formatter | 🟡 MEDIUM | Medium | Medium | Medium | Low | Epic 3 |
| **Architecture & Design** |
| Config loading duplication | 🟡 MEDIUM | Low | Low | Low | Low | Epic 1 |
| Error code registry | 🟡 MEDIUM | Low | Low | Low | Low | Epic 1 |
| Pipeline adapter complexity | 🟡 MEDIUM | Medium | Medium | High | Medium | Epic 1 |
| Infrastructure coupling | 🟢 LOW | Low | Medium | Medium | Low | Epic 1 |
| **Testing & Quality** |
| Test coverage audit needed | 🔴 HIGH | High | Low | High | High | Epic 1 |
| PDF performance validation | 🟡 MEDIUM | Low | Low | Medium | Low | Epic 2 |
| **Functionality Gaps** |
| Text normalization/cleaning | 🔴 HIGH | High | High | High | Low | Epic 2 |
| Entity extraction (spaCy) | 🔴 HIGH | High | High | High | Low | Epic 2 |
| Semantic chunking | 🔴 HIGH | High | High | High | Low | Epic 3 |
| TF-IDF/LSA analysis | 🔴 HIGH | High | High | High | Low | Epic 4 |
| **User Experience** |
| Shell completion | 🟢 LOW | Low | Low | Low | Low | Epic 5 |
| Config wizard | 🟢 LOW | Low | Medium | Medium | Low | Epic 5 |
| Preset configurations | 🟡 MEDIUM | Low | Medium | Medium | Low | Epic 5 |

## 4.2 Critical Technical Debt (MUST FIX)

### 4.2.1 Test Coverage Gaps 🔴 CRITICAL

**Issue:** Test coverage unknown for most modules

**Impact:** Cannot verify correctness, prevent regressions, or safely refactor

**Evidence:**
- Story 1.1 found 1007 tests with 778 passing (77% pass rate)
- 229 failing tests (23%) indicates test brittleness or broken functionality
- Coverage report never run (`pytest --cov=src --cov-report=html`)
- TXT extractor has no test framework integration

**Recommendation:**
1. **Story 1.3:** Run coverage analysis
   - `pytest --cov=src/extractors --cov-report=html`
   - `pytest --cov=src/processors --cov-report=html`
   - `pytest --cov=src/formatters --cov-report=html`
2. **Story 1.3:** Fix failing tests before refactoring
3. **Story 1.3:** Target: 80% coverage for brownfield code before Epic 2

**Epic:** Epic 1 (Story 1.3)

### 4.2.2 Text Normalization Missing 🔴 CRITICAL

**Issue:** No text cleaning logic (FR-N1 gap)

**Impact:** Cannot deliver "product magic" - RAG quality depends on artifact removal

**Evidence:**
- No artifact removal (OCR garbled text, formatting noise)
- No whitespace normalization
- No header/footer removal
- QualityValidator detects issues but doesn't fix them

**Recommendation:**
1. **Story 2.1:** Create `normalize/cleaning.py` module
2. Implement deterministic cleaning pipeline:
   - OCR artifact removal (repeated symbols, garbled characters)
   - Whitespace normalization (excessive blank lines, spacing)
   - Header/footer detection and removal
   - Preserve intentional formatting (lists, code blocks)
3. Integrate with QualityValidator for feedback loop

**Epic:** Epic 2 (Story 2.1)

### 4.2.3 Semantic Chunking Missing 🔴 CRITICAL

**Issue:** ChunkedTextFormatter is token-based, not semantic (FR-C1 gap)

**Impact:** Chunks may split mid-sentence or mid-entity, reducing RAG quality

**Evidence:**
- Simple token-based splitting (words * 1.3)
- No sentence boundary detection
- No entity-aware chunking
- `chunk_overlap` config exists but not implemented

**Recommendation:**
1. **Story 3.1:** Refactor ChunkedTextFormatter → `chunk/chunker.py`
2. Implement semantic chunking:
   - Sentence boundary detection (nltk, spaCy, or regex)
   - Section boundary respect (heading-aware)
   - Entity-aware chunking (keep entity mentions within chunks)
   - Configurable overlap (implement the missing feature)
3. Use deterministic algorithm (same input → same chunks)

**Epic:** Epic 3 (Story 3.1)

### 4.2.4 Entity Extraction Placeholder 🔴 CRITICAL

**Issue:** MetadataAggregator has entity extraction placeholder only (FR-N2 gap)

**Impact:** Cannot normalize entities or implement entity-aware chunking

**Evidence:**
```python
# In metadata_aggregator.py
enable_entities: false  # Requires spaCy
# Entity extraction not implemented
```

**Recommendation:**
1. **Story 2.2:** Implement entity extraction with spaCy
2. Support 6 audit entity types:
   - Processes
   - Risks
   - Controls
   - Regulations
   - Policies
   - Issues
3. Create `normalize/entities.py` for entity normalization (FR-N2)

**Epic:** Epic 2 (Story 2.2)

## 4.3 High-Priority Technical Debt (SHOULD FIX)

### 4.3.1 DOCX Image Extraction Missing 🔴 HIGH

**Issue:** DOCX extractor spike implementation is missing image extraction

**Impact:** API inconsistency (PDF and PPTX have images, DOCX doesn't)

**Evidence:**
```python
# From docx_extractor.py comments:
# Not Yet Implemented:
# - Images (DOCX-IMAGE-001)
```

**Recommendation:**
1. **Story 2.1:** Implement DOCX image extraction
2. Follow PPTX pattern: extract ImageMetadata
3. Extract images to files (optional)

**Epic:** Epic 2 (Story 2.1)

### 4.3.2 Error Code Registry Missing 🟡 MEDIUM

**Issue:** Error codes scattered across extractors, no central registry

**Impact:** Harder to debug, potential code collisions, no documentation

**Evidence:**
- Error codes: E001, E100, E110, E130, E150, E170, E171, E500
- Magic strings in each extractor
- No `error_codes.yaml` file (ErrorHandler expects it but defaults if missing)

**Recommendation:**
1. **Story 1.4:** Create `src/core/error_codes.py` with constants
2. Create `error_codes.yaml` with registry:
   ```yaml
   E001:
     category: ValidationError
     message: "File validation failed"
     technical_message: "File does not exist or is not readable"
     recoverable: false
     suggested_action: "Check file path and permissions"
   ```
3. Update all extractors to use constants

**Epic:** Epic 1 (Story 1.4)

### 4.3.3 Config Loading Duplication 🟡 MEDIUM

**Issue:** Every extractor has 30-40 lines of repetitive config loading

**Impact:** Violates DRY principle, harder to maintain

**Evidence:**
```python
# Repeated in every extractor:
if self._config_manager:
    cfg = self._config_manager.get_section("extractors.pdf", default={})
    self.use_ocr = self._get_config_value(cfg, "use_ocr", True)
elif isinstance(config, dict):
    self.use_ocr = config.get("use_ocr", True)
else:
    self.use_ocr = True
```

**Recommendation:**
1. **Story 1.4:** Extract to `BaseExtractor._load_config()` helper
2. Create unified config loading:
   ```python
   def _load_config(self, key: str, default: Any, config_section: str) -> Any:
       # Unified logic
   ```
3. Update all extractors to use helper

**Epic:** Epic 1 (Story 1.4)

## 4.4 Medium-Priority Technical Debt (NICE TO FIX)

### 4.4.1 Chunk Overlap Not Implemented 🟡 MEDIUM

**Issue:** `chunk_overlap` config loaded but feature not implemented

**Impact:** Cannot create overlapping chunks for better context continuity

**Evidence:**
```python
# In chunked_text_formatter.py
chunk_overlap: 0  # Config loaded but NOT IMPLEMENTED
```

**Recommendation:**
1. **Story 3.1:** Implement chunk overlap in semantic chunker
2. Use sliding window approach with configurable overlap tokens

**Epic:** Epic 3 (Story 3.1)

### 4.4.2 Markdown Table Rendering Incomplete 🟡 MEDIUM

**Issue:** Markdown formatter has table reference only (not fully implemented)

**Impact:** Tables not rendered in markdown output

**Evidence:**
```python
# In markdown_formatter.py
def _convert_table(self, block: ContentBlock) -> str:
    # TODO: Implement full table rendering
    return f"<!-- Table: {block.metadata.get('table_id')} -->\n\n"
```

**Recommendation:**
1. **Story 3.5:** Implement full markdown table rendering
2. Use GitHub-flavored markdown table syntax

**Epic:** Epic 3 (Story 3.5)

### 4.4.3 TXT Extractor Claims vs Reality 🔴 HIGH

**Issue:** Claims .md and .log support but doesn't parse them

**Impact:** Misleading API, broken for markdown files

**Evidence:**
```python
# Supports .txt, .md, .log but only parses plain text
# No markdown parsing, no log structure parsing
```

**Recommendation:**
1. **Story 2.1:** Either remove .md/.log from supported extensions OR implement parsing
2. Add markdown parser (markdown-it-py or mistune)
3. Add log structure parser (regex patterns for common log formats)

**Epic:** Epic 2 (Story 2.1)

## 4.5 Low-Priority Technical Debt (DEFER)

- File hash duplication (move to BaseExtractor)
- Infrastructure coupling (Null Object pattern)
- Table header detection heuristics
- Performance monitoring/metrics
- No streaming for large documents
- No async support

## 4.6 Code Quality Observations

**Strengths:**
- ✅ Type hints: 95% coverage (except TXT extractor)
- ✅ Documentation: Excellent docstrings with examples
- ✅ Error handling: Comprehensive with error codes
- ✅ Immutability: Frozen dataclasses prevent bugs
- ✅ Logging: Structured logging with context

**Weaknesses:**
- ⚠️ Some code duplication (config loading, file hashing)
- ⚠️ Infrastructure coupling (INFRASTRUCTURE_AVAILABLE checks throughout)
- ⚠️ Adapter pattern complexity (ProcessingResult → ExtractionResult)

---
