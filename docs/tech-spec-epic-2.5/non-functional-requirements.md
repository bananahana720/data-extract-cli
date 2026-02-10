# Non-Functional Requirements

## Performance

**NFR-P1: Batch Processing Throughput** (VALIDATE)
- **Target:** 100 mixed-format files processed in <10 minutes
- **Current State:** Unknown - Story 2.5.1 establishes baseline
- **Validation:** Automated performance tests in CI (weekly runs)
- **Measurement:** `tests/performance/test_throughput.py` with psutil monitoring

**NFR-P2: Memory Footprint** (VALIDATE)
- **Target:** Peak memory usage <2GB during batch processing
- **Current State:** Unknown - Story 2.5.1 validates streaming architecture
- **Validation:** Memory profiling during large document processing
- **Measurement:** psutil memory monitoring in integration tests

**NFR-P3: Individual File Processing** (INHERITED from PRD)
- **Target:** <5 seconds per document (excluding OCR), <10 seconds per scanned page
- **Current State:** Assumed compliant from Epic 2 - Story 2.5.1 confirms
- **Validation:** Per-file timing in performance tests

**spaCy Performance** (NEW for Epic 2.5.2):
- **Model Load Time:** <5 seconds for en_core_web_md initial load
- **Sentence Segmentation:** <100ms for 1000-word document
- **Validation:** Unit tests measure execution time

**Performance Regression Detection:**
- Baseline metrics documented in Story 2.5.1
- Future epics must not degrade throughput >10% without justification
- CI pipeline tracks performance trends (weekly reports)

## Security

**NFR-S1: Dependency Security** (STRENGTHEN)
- **spaCy 3.7.2:** Verify no known CVEs before installation
- **Profiling Tools:** psutil, cProfile, memory_profiler from official PyPI only
- **Pinned Versions:** All new dependencies locked in pyproject.toml
- **Validation:** Dependabot alerts monitored, no HIGH/CRITICAL vulnerabilities

**NFR-S2: Test Fixture Security** (Story 2.5.3)
- **Sanitization:** All large document fixtures must have sensitive data removed
- **No PII:** Test PDFs/Excel files contain synthetic audit data only
- **Repository Safety:** Fixtures committed to version control must be publicly safe
- **Validation:** Manual review of each fixture before commit

**NFR-S3: Code Quality Security** (Code Review Blockers)
- **Type Safety:** Fix all Mypy violations (strict mode compliance)
- **Linting:** Ruff checks must pass with 0 errors
- **Pre-commit Hooks:** Enforce quality gates before commit
- **Validation:** CI pipeline blocks merges on quality gate failures

## Reliability/Availability

**NFR-R1: Deterministic Performance** (VALIDATE)
- **Consistency:** Same 100-file batch produces identical throughput metrics across runs
- **Reproducibility:** Performance tests run on same hardware/config produce <5% variance
- **Validation:** Run performance suite 3x, verify standard deviation <5%

**NFR-R2: Graceful Degradation** (VALIDATE)
- **Large Files:** Pipeline continues processing batch even if one large file fails
- **Memory Spikes:** No OOM crashes on 50+ page PDFs or 10K+ row Excel files
- **Error Recovery:** Failed files logged with actionable error messages
- **Validation:** Integration tests with intentionally problematic fixtures

**NFR-R3: spaCy Model Availability** (Story 2.5.2)
- **Offline Support:** en_core_web_md model bundled or downloadable during setup
- **Fallback:** Clear error message if model missing (not silent failure)
- **Validation:** Tests check model existence before attempting to load
- **Documentation:** Setup instructions include model download step

**NFR-R4: Test Infrastructure Reliability**
- **CI Stability:** Performance tests must not flake (false positives/negatives)
- **Fixture Integrity:** Large test fixtures validated with checksums
- **Isolation:** Performance tests don't interfere with unit/integration tests
- **Validation:** CI runs performance suite separately, weekly schedule

## Observability

**NFR-O1: Performance Metrics Tracking** (Story 2.5.1)
- **Metrics Collected:** Throughput (files/min), memory (peak/avg), CPU utilization, bottleneck locations
- **Storage:** Performance test results logged to CI artifacts, trends tracked over time
- **Visibility:** CI dashboard shows performance trends (green if <10% degradation from baseline)
- **Validation:** Weekly performance CI job publishes metrics report

**NFR-O2: Profiling Data Analysis** (Story 2.5.1)
- **Tool:** cProfile generates detailed call graphs and timing data
- **Output:** Profile stats saved to `profile.stats`, analyzed with pstats or snakeviz
- **Actionable:** Top 10 bottlenecks identified with line-level precision
- **Documentation:** Profiling results documented in Story 2.5.1 completion notes

**NFR-O3: Test Execution Reporting**
- **Coverage:** pytest-cov reports coverage for new test modules
- **Test Times:** pytest reports execution time per test (identify slow tests)
- **CI Integration:** Test results published to CI dashboard with pass/fail status
- **Markers:** Performance tests tagged with `@pytest.mark.performance` for selective execution

**NFR-O4: spaCy Integration Visibility** (Story 2.5.2)
- **Model Info:** Log spaCy model version, language, and size on load
- **Segmentation Stats:** Log sentence count, avg sentence length for processed documents
- **Error Logging:** spaCy failures logged with context (input text snippet, stack trace)
- **Validation:** Integration tests verify logging output contains expected fields
