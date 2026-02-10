# Non-Functional Requirements

## Performance

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

## Security

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

## Reliability/Availability

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

## Observability

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
