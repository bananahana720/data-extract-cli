# Test Strategy Summary

## Test Levels

**Performance Tests** (tests/performance/) - NEW in Epic 2.5
- **Scope:** Validate NFR-P1 (throughput) and NFR-P2 (memory usage) under load
- **Coverage Target:** 100-file batch, large individual files (50+ pages, 10K+ rows)
- **Approach:** Real processing with psutil monitoring, cProfile profiling, before/after benchmarks
- **Execution:** Weekly in CI (too slow for every commit), manual runs by developers
- **Success Criteria:** <10 min for 100 files, <2GB peak memory, baseline documented

**Integration Tests** (tests/integration/) - EXPANDED in Epic 2.5
- **Scope:** spaCy integration, large file processing, end-to-end pipeline validation
- **Coverage Target:** All new integration points (spaCy model loading, sentence segmentation, large file streaming)
- **Approach:** Real fixtures, real spaCy model, memory monitoring during execution
- **Execution:** Every commit in CI (alongside existing integration tests)
- **Success Criteria:** All integration tests pass, no memory spikes, 95%+ spaCy accuracy

**Unit Tests** (tests/unit/) - NEW for Epic 2.5.2
- **Scope:** get_sentence_boundaries() utility function edge cases
- **Coverage Target:** 100% coverage of nlp.py utility functions
- **Approach:** Mock spaCy model where appropriate, test edge cases (empty text, single sentence, etc.)
- **Execution:** Every commit in CI (fast tests)
- **Success Criteria:** All unit tests pass, edge cases handled correctly

**Manual Testing** (Story 2.5.1 Profiling)
- **Scope:** cProfile analysis, bottleneck identification, optimization validation
- **Coverage Target:** Entire pipeline execution flow
- **Approach:** Run cProfile, analyze output with pstats/snakeviz, document top 10 bottlenecks
- **Execution:** Once during Story 2.5.1, repeat after optimizations
- **Success Criteria:** Bottlenecks identified with line-level precision, documented

## Test Frameworks and Tools

- **pytest:** Primary test framework (existing)
- **pytest-cov:** Coverage measurement (existing)
- **pytest.mark.performance:** New marker for performance tests
- **psutil:** Memory and CPU monitoring (new)
- **cProfile:** Performance profiling (built-in, no install)
- **memory_profiler:** Line-by-line memory profiling (new, optional)
- **spaCy test utilities:** Model validation and accuracy testing (new)

## Coverage Strategy

**Epic 2.5 Coverage Targets:**
- Performance tests: 100% of NFR-P1, NFR-P2 validation scenarios
- spaCy integration: 100% of model loading, segmentation, error handling paths
- Large file processing: 100% of large fixture types (PDF, Excel, scanned)
- Utility functions: 100% of get_sentence_boundaries() code paths
- Code review fixes: 100% of validation.py bug fixes validated by type checker

**Overall Project Coverage:**
- Baseline established in Epic 1: ~60%
- After Epic 2: ~75% (target from PRD)
- After Epic 2.5: ~78% (incremental improvement with test infrastructure)
- Target for Epic 3+: >80%

## Edge Cases and Error Conditions

**Performance Edge Cases:**
- Very large files (100+ pages, 50K+ rows) - ensure no OOM
- Mixed batch with some corrupted files - ensure batch continues
- Rapid successive batches - ensure no memory leaks between runs
- Cold start vs. warm start - document model loading overhead

**spaCy Edge Cases:**
- Empty text input - expect ValueError with clear message
- Single sentence - return single boundary position
- Text with complex punctuation (abbreviations, acronyms) - measure accuracy
- Model not installed - graceful error with setup instructions
- Model load failure - clear error message, not silent failure

**Large File Edge Cases:**
- Streaming processing maintains constant memory (not batch load)
- Progress reporting accurate for large files
- Timeout handling for extremely slow OCR processing
- Corrupted large files don't crash entire batch

## Acceptance Criteria Validation

**Story 2.5.1 Validation:**
1. Automated: pytest performance tests assert <10 min, <2GB
2. Manual: cProfile output reviewed, bottlenecks documented
3. Automated: Baseline metrics written to file/docstrings, CI job configured

**Story 2.5.2 Validation:**
1. Automated: `python -m spacy validate` in CI
2. Automated: pytest integration tests for model loading, segmentation accuracy
3. Automated: pytest unit tests for get_sentence_boundaries()
4. Manual: Documentation review (CLAUDE.md, README.md updates)

**Story 2.5.3 Validation:**
1. Manual: Fixture file review (sanitization, structure)
2. Automated: pytest integration tests process fixtures without errors
3. Automated: psutil monitoring asserts <2GB for large files
4. Manual: Documentation review (tests/fixtures/README.md, CLAUDE.md lessons)
5. Automated: Black, Ruff, Mypy run with 0 violations (CI enforcement)

## Definition of Done for Epic 2.5

- [ ] All story acceptance criteria validated (18 ACs across 3 stories)
- [ ] Performance baseline documented (<10 min for 100 files confirmed)
- [ ] spaCy 3.7.2 installed, en_core_web_md model validated, 95%+ accuracy achieved
- [ ] Large test fixtures added (50+ page PDF, 10K+ row Excel, scanned PDF)
- [ ] Integration tests passing for spaCy and large files
- [ ] Code review blockers resolved (validation.py Mypy/Ruff clean)
- [ ] Documentation updated (CLAUDE.md, README.md, fixtures README)
- [ ] CI pipeline green (all tests pass, no quality gate violations)
- [ ] Epic 2.5 marked as "contexted" in sprint-status.yaml
- [ ] Ready for Epic 3 Story 3.1 (semantic chunking with spaCy)
