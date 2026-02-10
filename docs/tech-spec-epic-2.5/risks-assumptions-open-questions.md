# Risks, Assumptions, Open Questions

## Risks

**Risk-1: Performance targets may not be achievable without major refactoring**
- **Description:** Current pipeline may have fundamental bottlenecks preventing NFR-P1 (<10 min for 100 files)
- **Impact:** HIGH - Would require Epic 1/2 code rework
- **Likelihood:** LOW - Epic 2 designed with performance in mind
- **Mitigation:** Story 2.5.1 identifies bottlenecks early. If major refactoring needed, escalate to product owner for timeline adjustment vs. relaxed NFR.

**Risk-2: spaCy model download fails in enterprise environment**
- **Description:** Corporate firewall may block model downloads, or no internet access
- **Impact:** MEDIUM - Blocks Story 2.5.2 and Epic 3
- **Likelihood:** MEDIUM (enterprise environment restrictions)
- **Mitigation:** Document offline model installation process. Bundle model with repository if allowed. Request IT exception for spaCy model downloads.

**Risk-3: Large test fixtures difficult to sanitize**
- **Description:** Real audit documents contain sensitive data, synthetic data may not represent complexity
- **Impact:** MEDIUM - Test fixtures may not catch real-world edge cases
- **Likelihood:** MEDIUM
- **Mitigation:** Use publicly available audit reports (government disclosures, public companies). Generate synthetic data with realistic structure. Accept some trade-off between sanitization and realism.

**Risk-4: Code review blockers indicate deeper technical debt**
- **Description:** Mypy/Ruff violations may be symptoms of broader code quality issues
- **Impact:** MEDIUM - May require more extensive refactoring than Story 2.5.3 scope
- **Likelihood:** LOW - Violations are minor (missing optional fields, unused variable)
- **Mitigation:** Fix immediate blockers in Story 2.5.3. Document any deeper issues found for future tech debt epic.

## Assumptions

**Assumption-1:** Current pipeline architecture supports performance targets
- **Validation:** Story 2.5.1 performance tests will confirm
- **If False:** May need ADR revision or NFR adjustment

**Assumption-2:** spaCy en_core_web_md is sufficient for sentence segmentation
- **Validation:** Story 2.5.2 accuracy tests (95%+ target)
- **If False:** May need larger model (en_core_web_lg) or custom training

**Assumption-3:** 100-file test batch is representative of production workloads
- **Validation:** Compare test batch diversity to actual audit document corpus
- **If False:** Adjust test batch composition to better match production

**Assumption-4:** Developer has access to create/source large test fixtures
- **Validation:** Check availability of public audit documents or synthetic data generators
- **If False:** Request samples from stakeholders (sanitized) or use generic large documents

## Open Questions

**Question-1:** Should performance tests run on every commit or weekly?
- **Context:** Performance tests are slow (10+ minutes), may slow CI pipeline
- **Decision Needed By:** Story 2.5.1
- **Recommendation:** Weekly schedule in CI, developers can run manually as needed. Track trends, alert on >10% degradation.

**Question-2:** What sentence segmentation accuracy is acceptable?
- **Context:** 95% is target, but 100% may be impossible (NLP inherent ambiguity)
- **Decision Needed By:** Story 2.5.2
- **Recommendation:** Accept 95%+ as success. Document known failure modes (e.g., abbreviations). Perfect accuracy not required for RAG chunking.

**Question-3:** Should UAT workflow be implemented now or deferred?
- **Context:** Story 2.5.3 includes UAT workflow design, but implementation may be extensive
- **Decision Needed By:** Story 2.5.3
- **Recommendation:** Design only in Epic 2.5. Implement in future epic if UAT automation proves valuable after Epic 2/3.

**Question-4:** How should performance baselines be stored long-term?
- **Context:** Baselines needed for trend analysis, but test docstrings may not be sufficient
- **Decision Needed By:** Story 2.5.1
- **Recommendation:** Store in separate `docs/performance-baselines.md` or CI artifact storage. Include timestamp, hardware specs, Epic/Story context.
