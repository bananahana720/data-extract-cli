# Acceptance Criteria (Authoritative)

## Story 2.5.1: Performance Validation & Optimization

**AC-2.5.1.1:** 100-file batch processes within NFR-P1 target
- 100 mixed-format files (PDFs, DOCX, XLSX) process in <10 minutes
- Measured with real timer, not estimates
- Test batch includes variety of file sizes and formats

**AC-2.5.1.2:** Memory usage stays within NFR-P2 limits
- Peak memory <2GB during 100-file batch processing
- Measured with psutil process monitoring
- No memory leaks detected (memory returns to baseline after batch)

**AC-2.5.1.3:** Performance bottlenecks identified and documented
- cProfile run generates profile.stats file
- Top 10 slowest functions identified with line numbers
- Bottlenecks documented in Story 2.5.1 completion notes

**AC-2.5.1.4:** Critical bottlenecks optimized
- Slowest operation(s) improved by measurable amount
- Performance improvement validated with before/after benchmarks
- No regressions introduced in optimization (tests still pass)

**AC-2.5.1.5:** Automated performance test suite created
- tests/performance/test_throughput.py exists and runs successfully
- Tests validate NFR-P1 (throughput) and NFR-P2 (memory)
- Performance CI job configured (weekly schedule)

**AC-2.5.1.6:** Baseline metrics documented
- Throughput (files/min), memory (peak/avg), CPU utilization recorded
- Baseline documented in test docstrings or separate metrics file
- Future epics can compare against baseline to detect regressions

## Story 2.5.2: spaCy Integration & Validation

**AC-2.5.2.1:** spaCy 3.7.2 installed and validated
- `python -m spacy validate` succeeds
- spaCy version check returns 3.7.2
- Installation documented in pyproject.toml

**AC-2.5.2.2:** en_core_web_md model downloaded and loadable
- `python -m spacy download en_core_web_md` completes successfully
- Model loads in Python: `nlp = spacy.load("en_core_web_md")` works
- Model version and size logged on load

**AC-2.5.2.3:** Sentence segmentation accuracy validated
- Accuracy ≥95% on gold standard test corpus
- Test corpus includes edge cases (abbreviations, acronyms, complex punctuation)
- Accuracy metric documented in test results

**AC-2.5.2.4:** get_sentence_boundaries() utility function implemented
- Function exists in src/data_extract/utils/nlp.py
- Signature: `get_sentence_boundaries(text: str, nlp: Language = None) -> List[int]`
- Returns character positions of sentence ends
- Handles edge cases: empty text (raises ValueError), single sentence, multi-paragraph

**AC-2.5.2.5:** Unit tests cover utility function edge cases
- Test empty/whitespace-only text (expect ValueError)
- Test single sentence (returns one boundary)
- Test multi-sentence text (returns multiple boundaries)
- Test with/without provided nlp model parameter

**AC-2.5.2.6:** Integration tests validate spaCy pipeline
- tests/integration/test_spacy_integration.py exists and passes
- Tests model loading, sentence segmentation, error handling
- Tests run in CI pipeline

**AC-2.5.2.7:** Documentation updated with spaCy setup
- CLAUDE.md includes spaCy installation steps
- README.md mentions model download requirement
- Troubleshooting guide created for common spaCy issues

## Story 2.5.3: Large Document Fixtures & UAT Framework

**AC-2.5.3.1:** Large PDF fixture created (50+ pages)
- PDF with ≥50 pages added to tests/fixtures/pdfs/large/
- Content sanitized (no PII or sensitive audit data)
- Structure preserved (headings, tables, images representative of audit docs)

**AC-2.5.3.2:** Large Excel fixture created (10K+ rows)
- Excel file with ≥10,000 rows added to tests/fixtures/xlsx/large/
- Simulates audit data structure (risks, controls, policies, etc.)
- Content synthetic, no real organization data

**AC-2.5.3.3:** Scanned PDF fixture created (OCR required)
- Scanned/image-based PDF added to tests/fixtures/pdfs/scanned/
- Tests OCR pipeline end-to-end
- Representative of real-world scanned audit documents

**AC-2.5.3.4:** Fixture creation process documented
- tests/fixtures/README.md describes how fixtures were created
- Includes sanitization steps and tools used
- Enables future contributors to add more fixtures

**AC-2.5.3.5:** Integration tests for large files passing
- tests/integration/test_large_files.py exists and passes
- Tests process large PDF without memory spike
- Tests process large Excel without timeout
- Tests scanned PDF OCR completes successfully

**AC-2.5.3.6:** Memory monitoring validates NFR-P2 for large files
- psutil tracks memory during large file processing
- Peak memory <2GB for individual large files
- No OOM crashes on large documents

**AC-2.5.3.7:** UAT workflow structure designed
- Design documented for bmad:bmm:workflows:create-test-cases
- Input: Story markdown files with acceptance criteria
- Output: Test scenarios and execution framework
- Integration with tmux-cli for CLI testing considered

**AC-2.5.3.8:** CLAUDE.md updated with Epic 2 lessons
- "Lessons from Epic 2" section added to CLAUDE.md
- Documents quality gate patterns (Black/Ruff/Mypy first)
- Documents PipelineStage protocol scaling lessons
- Documents anti-patterns to avoid

**AC-2.5.3.9:** Code review blockers resolved
- validation.py:694, 719, 736 fixed (add document_average_confidence, scanned_pdf_detected)
- validation.py:697 unused variable removed (ocr_validation_performed)
- Quality gates re-run: `black && ruff && mypy` all pass with 0 violations
- Proof of 0 violations documented in completion notes
