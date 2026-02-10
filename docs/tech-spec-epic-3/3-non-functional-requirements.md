# 3. Non-Functional Requirements

## 3.1 Performance Requirements

### NFR-P1-E3: End-to-End Pipeline Throughput
**Requirement:** Process 100 PDFs through full pipeline (Extract → Normalize → Chunk → Output) in <10 minutes

**Baseline Context (from Party-Mode Discussion):**
- Epic 2 achieved 6.86 minutes for Extract + Normalize (148% improvement over conservative estimate)
- Epic 3 target: <10 minutes total includes chunking + output overhead
- This represents ~33% improvement over conservative 15-minute baseline

**Measurement Strategy (Murat's Hybrid Approach):**
- **Story 3-1 Baseline:** Measure chunking engine critical path (sentence segmentation, chunk generation, entity analysis)
- **Stories 3-2, 3-3:** Skip micro-benchmarks (metadata enrichment overhead negligible <0.1s per doc)
- **Stories 3-4, 3-5, 3-6:** Measure output format overhead (JSON, TXT, CSV generation time)
- **Story 3-7:** Measure organization strategy overhead (by_document vs by_entity vs flat)
- **Epic-End Integration Test:** Full pipeline benchmark vs <10 min target on standard 100-PDF corpus

**Tracking:** `docs/performance-baselines-epic-3.md` (created in Story 3-1)

**Target Breakdown:**
- Extract + Normalize: 6.86 min (Epic 2 actual)
- Chunking (Story 3-1): <1.5 min target (15 sec per 10-doc batch)
- Metadata Enrichment (Stories 3-2, 3-3): <0.5 min target (negligible per-doc overhead)
- Output Generation (Stories 3-4, 3-5, 3-6): <1.0 min target (parallel writes, I/O bound)
- Organization (Story 3-7): <0.2 min target (file moves, manifest generation)
- **Total:** 6.86 + 1.5 + 0.5 + 1.0 + 0.2 = ~10 min

**Acceptance Criteria:**
- Full pipeline completes 100 PDFs in ≤10 minutes (600 seconds) on reference hardware
- Individual chunking operations complete in <2 seconds per 10,000-word document
- Output format generation completes in <1 second per document (all 3 formats parallel)
- Performance baselines documented in `docs/performance-baselines-epic-3.md`
- Regression tests fail if performance degrades >10% from baseline

### NFR-P2-E3: Memory Efficiency
**Requirement:** Batch processing of 100 PDFs uses <5.5GB total memory (peak RSS)

**Baseline Context:**
- Epic 2 individual file processing: 167MB ✅
- Epic 2 batch processing: 4.15GB (documented trade-off for throughput)
- Epic 3 target: <5.5GB allows 1.35GB headroom for chunking + output overhead

**Memory Budget:**
- Epic 2 baseline: 4.15GB
- Chunking overhead: <500MB (streaming generators, no buffering)
- Metadata enrichment: <300MB (frozen dataclass pooling, flyweight pattern)
- Output generation: <550MB (parallel writes with chunked I/O, no full buffering)
- **Total:** 4.15 + 0.5 + 0.3 + 0.55 = 5.5GB

**Winston's Optimizations (Memory Reduction Strategies):**
1. **Streaming Generators:** Chunks yielded one at a time (no full document buffering)
2. **Lazy spaCy Loading:** Model loaded once globally, shared across processes (saves ~300MB per worker)
3. **Metadata Pooling:** Flyweight pattern for common fields (source_file, document_type) - ~40% reduction
4. **Parallel Writer Memory Sharing:** `itertools.tee()` enables concurrent format writes without 3x memory duplication

**Acceptance Criteria:**
- Peak memory usage ≤5.5GB for 100-PDF batch (measured via `get_total_memory()` from Story 2.5.1)
- Individual document processing uses ≤500MB peak memory
- Memory usage remains constant across batch size (streaming architecture, no accumulation)
- Memory profiling included in performance baselines document

### NFR-P3: Chunking Latency
**Requirement:** Chunk a 10,000-word document in <2 seconds

**Rationale:**
- 100 PDFs average 8,000 words each = 800,000 words total
- At 2 sec per 10k words: 800k / 10k * 2 sec = 160 seconds = 2.67 minutes
- Leaves buffer for smaller/larger docs and parallel processing benefits

**Optimization Strategies:**
- spaCy model loaded once (lazy loading pattern)
- Sentence segmentation vectorized (batch processing via spaCy)
- Entity analysis performed once upfront, cached for chunk decisions
- Generator pattern avoids materialization overhead

**Acceptance Criteria:**
- 10,000-word document chunks in ≤2 seconds (wall-clock time)
- Sentence boundary detection completes in <0.5 seconds
- Entity analysis completes in <0.3 seconds
- Chunk generation (sliding window) completes in <1.2 seconds

### NFR-P4: Deterministic Chunking
**Requirement:** 100% reproducibility - same input always produces same chunks

**Rationale:**
- Audit trail requirement: chunks must be reproducible from source documents
- Enables diff-based change detection in document versions
- Supports regression testing (chunk output should not change without code changes)

**Implementation:**
- No random number generators in chunking pipeline
- Deterministic sentence segmentation (spaCy is deterministic with fixed model)
- Frozen configuration embedded in output metadata
- Timestamps excluded from chunk content (only in metadata for audit trail)

**Acceptance Criteria:**
- Process same document 10 times → identical chunks (byte-for-byte comparison)
- Chunk IDs are deterministic (derived from source file + position, not timestamps)
- Configuration changes produce different chunks (sensitivity test)
- Determinism validated via automated test suite (100 documents, 3 runs each)

## 3.2 Security Requirements

### NFR-S1: Data Sanitization in Outputs
**Requirement:** Prevent sensitive data leakage in metadata and output files

**Scope:**
- Redact file paths containing usernames or sensitive directory names
- Sanitize error messages (no stack traces with internal paths in production logs)
- Strip EXIF metadata from images before OCR
- Remove internal tool configuration details from output metadata

**Acceptance Criteria:**
- File paths in output metadata use relative paths or sanitized absolute paths
- Error logs exclude internal directory structures
- Output metadata includes only processing-relevant configuration (not secrets)

### NFR-S2: No PII Leakage in Metadata
**Requirement:** Chunk metadata must not expose personally identifiable information

**Implementation:**
- Entity normalization (Epic 2) already handles PII redaction for known patterns
- Metadata fields limited to: source file, document type, quality scores, entity tags
- No user information, machine names, or network paths in metadata
- Processor identity: tool version only (not username or hostname)

**Acceptance Criteria:**
- Metadata schema review confirms no PII fields
- Automated PII detection tests (scan for email, SSN, phone patterns in metadata)
- Output JSON files pass PII scanner (e.g., Microsoft Presidio or regex-based checks)

## 3.3 Reliability Requirements

### NFR-R1: Continue-on-Error Pattern
**Requirement:** Graceful degradation - single file failure does not halt batch processing

**Implementation:**
- Each document processed in isolated try-except block
- Errors logged with context (file path, stage, error message, stack trace)
- Failed files quarantined separately with error report
- Batch processing continues with remaining files
- Summary report lists all failures with actionable suggestions

**Acceptance Criteria:**
- 1 corrupted file in 100-file batch: 99 files process successfully
- Error summary includes file path, stage (chunking/metadata/output), error message
- Failed files written to `output/failed/` with error log
- Exit code reflects status: 0=all success, 1=partial failure, 2=total failure

### NFR-R2: Graceful Degradation
**Requirement:** Reduce quality gracefully when optimal processing fails

**Degradation Strategy:**
1. **Entity-aware chunking fails:** Fall back to semantic boundary chunking (no entity optimization)
2. **Readability calculation fails:** Assign default quality score, flag chunk as "quality_unknown"
3. **Output format generation fails:** Continue with remaining formats (e.g., JSON fails, TXT/CSV succeed)
4. **Organization strategy fails:** Fall back to flat organization

**Acceptance Criteria:**
- Degradation triggers are logged with warning level
- Chunks always generated (even if metadata incomplete)
- At least one output format always succeeds (TXT as minimum viable output)
- Degraded outputs flagged in manifest.json

### NFR-R3: 100% Traceability
**Requirement:** Every chunk traceable to source document with full audit trail

**Implementation:**
- Chunk ID format: `{source_file_stem}_chunk_{position:03d}`
- Metadata includes: source file path, source file hash (SHA-256), section context
- Manifest.json maps all chunks to source documents
- Processing configuration embedded in output metadata

**Acceptance Criteria:**
- Every chunk links to source document in metadata
- Source file hash enables integrity verification
- Manifest.json provides complete mapping: source → chunks, chunks → source
- Traceability validated via automated tests (random chunk → source document lookup)

## 3.4 Observability Requirements

### NFR-O1: Chunking Metrics
**Requirement:** Collect and report comprehensive chunking metrics for monitoring

**Metrics to Track:**
- Total chunks generated per document
- Average chunk size (words, tokens, characters)
- Chunk size distribution (histogram: min, max, median, p95, p99)
- Entity preservation rate (% entities kept intact within chunks)
- Sentence boundary violations (should be 0 - flag if any detected)
- Processing time per stage (chunking, metadata, output)

**Output:**
- Metrics logged to structured logs (JSON format via structlog)
- Summary statistics in processing report
- Optional metrics export to CSV for analysis

**Acceptance Criteria:**
- Metrics logged for every document processed
- Summary report includes aggregate metrics across batch
- Metrics exportable to CSV for trend analysis
- Metrics schema documented in `docs/observability.md`

### NFR-O2: Output Format Metrics
**Requirement:** Track output generation performance and file sizes

**Metrics to Track:**
- Time to generate each format (JSON, TXT, CSV)
- Output file sizes (bytes) per format
- Parallel write speedup (sequential vs parallel comparison)
- Error rate per format (% files with format generation failures)

**Acceptance Criteria:**
- Format generation time logged per document
- File sizes tracked in manifest.json
- Performance comparison: parallel vs sequential writes documented
- Error rates reported in summary

### NFR-O3: Quality Score Distributions
**Requirement:** Monitor chunk quality distributions to detect corpus quality issues

**Metrics to Track:**
- Readability score distributions (Flesch-Kincaid, Gunning Fog)
- OCR confidence distributions (from source documents)
- Quality flag frequency (low_ocr, high_complexity, incomplete_extraction)
- Entity completeness rate (% entities preserved intact)

**Output:**
- Quality histograms in processing report
- Outlier detection: flag documents with >20% low-quality chunks
- Quality trends over time (if processing multiple batches)

**Acceptance Criteria:**
- Quality distributions calculated and reported
- Outlier documents flagged in summary report
- Quality metrics exportable for visualization
- Quality baselines documented for regression detection

## 3.5 NFR Summary Table

| NFR ID | Category | Requirement | Target | Measurement | Priority |
|--------|----------|-------------|--------|-------------|----------|
| NFR-P1-E3 | Performance | End-to-end pipeline throughput | <10 min for 100 PDFs | Integration test | P0 |
| NFR-P2-E3 | Performance | Batch memory efficiency | <5.5GB peak RSS | `get_total_memory()` | P0 |
| NFR-P3 | Performance | Chunking latency | <2 sec per 10k words | Per-doc timing | P1 |
| NFR-P4 | Performance | Deterministic chunking | 100% reproducibility | Repeated runs diff | P0 |
| NFR-S1 | Security | Data sanitization | No internal paths in output | Output scan | P1 |
| NFR-S2 | Security | No PII leakage | No PII in metadata | PII scanner | P0 |
| NFR-R1 | Reliability | Continue-on-error | 99/100 succeed if 1 fails | Batch error injection | P0 |
| NFR-R2 | Reliability | Graceful degradation | Fallback modes work | Failure simulation | P1 |
| NFR-R3 | Reliability | 100% traceability | All chunks → source mapping | Manifest validation | P0 |
| NFR-O1 | Observability | Chunking metrics | All metrics logged | Log inspection | P1 |
| NFR-O2 | Observability | Output format metrics | Time + size tracked | Performance report | P2 |
| NFR-O3 | Observability | Quality distributions | Histograms generated | Summary report | P1 |

**Priority Levels:**
- **P0:** Must-have for MVP (blocker if not met)
- **P1:** Should-have for production readiness (degraded experience if not met)
- **P2:** Nice-to-have for operational excellence (can defer to post-MVP)

---
