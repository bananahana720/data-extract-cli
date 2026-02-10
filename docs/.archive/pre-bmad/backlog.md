# Engineering Backlog

This backlog collects cross-cutting or future action items that emerge from reviews and planning.

Routing guidance:

- Use this file for non-urgent optimizations, refactors, or follow-ups that span multiple stories/epics.
- Must-fix items to ship a story belong in that story's `Tasks / Subtasks`.
- Same-epic improvements may also be captured under the epic Tech Spec `Post-Review Follow-ups` section.

| Date | Story | Epic | Type | Severity | Owner | Status | Notes |
| ---- | ----- | ---- | ---- | -------- | ----- | ------ | ----- |
| 2025-11-10 | 1.1 | Epic 1 | TechDebt | Medium | TBD | Open | Fix mypy pre-commit hook - remove `--ignore-missing-imports` flag; add type stubs for typed dependencies [file: .pre-commit-config.yaml:29] |
| 2025-11-10 | 1.1 | Epic 1 | TechDebt | Low | TBD | Open | Add mypy exclusions for brownfield code - add exclude pattern in [tool.mypy] section [file: pyproject.toml:125] |
| 2025-11-10 | 1.1 | Epic 1 | Documentation | Low | TBD | Open | Document expected verification output in README after each verification command [file: README.md:81-98] |
| 2025-11-10 | 1.3 | Epic 1 | Bug | High | TBD | Open | Fix hardcoded relative paths in integration tests causing test fragility [file: tests/integration/test_pipeline_basic.py:28,101,144,171-172] |
| 2025-11-10 | 1.3 | Epic 1 | TechDebt | High | TBD | Open | Add edge case tests for empty files and extraction failures (empty PDF/DOCX/Excel, malformed documents, failure paths) [file: tests/integration/test_pipeline_basic.py] |
| 2025-11-10 | 1.3 | Epic 1 | TechDebt | High | TBD | Open | Replace str(Path) anti-pattern with native Path support in test fixtures [file: tests/integration/conftest.py:98,125,209,273] |
| 2025-11-10 | 1.3 | Epic 1 | TechDebt | Medium | TBD | Open | Add try-except error handling and timeout handling in integration tests [file: tests/integration/test_pipeline_basic.py:110-126] |
| 2025-11-10 | 1.3 | Epic 1 | Configuration | Medium | TBD | Open | Remove coverage threshold duplication from CI workflow; use pytest.ini as single source of truth [file: .github/workflows/test.yml:67] |
| 2025-11-10 | 1.3 | Epic 1 | TechDebt | Medium | TBD | Open | Improve ImportError handling in test fixtures (replace pytest.skip with graceful fallbacks and clear messages) [file: tests/integration/conftest.py:42-45,116-120] |
| 2025-11-10 | 1.3 | Epic 1 | TechDebt | Medium | TBD | Open | Add type hints to test fixture callbacks for better IDE support [file: tests/integration/conftest.py:506] |
| 2025-11-10 | 1.3 | Epic 1 | TechDebt | Medium | TBD | Open | Add actual cleanup logic to cleanup_temp_files fixture (track files outside tmp_path) [file: tests/integration/conftest.py:554-561] |
| 2025-11-10 | 1.3 | Epic 1 | TechDebt | Low | TBD | Open | Convert manual test loops to parametrized tests for better test output and debugging [file: tests/integration/test_pipeline_basic.py:170-189] |
| 2025-11-10 | 1.3 | Epic 1 | TechDebt | Low | TBD | Open | Install missing test dependencies: psutil (performance tests), reportlab (PDF fixtures) [file: pyproject.toml] |
| 2025-11-10 | 1.3 | Epic 1 | TechDebt | Low | TBD | Open | Improve extractor test coverage to 60%+ baseline (PDF 19%→60%, CSV/Excel/PPTX 24-26%→60%) - Epic 2 prerequisite [files: src/extractors/*.py] |

## Story 2.5 Code Review Follow-ups (2025-11-11)

| Date | Story | Epic | Type | Severity | Owner | Status | Notes |
|------|-------|------|------|----------|-------|--------|-------|
| 2025-11-11 | 2.5 | 2 | Bug | High | TBD | Open | Fix Mypy violations in ValidationReport instantiations - add document_average_confidence=None, scanned_pdf_detected=None to lines 694, 719, 736 in validation.py |
| 2025-11-11 | 2.5 | 2 | Bug | Medium | TBD | Open | Remove unused variable ocr_validation_performed at validation.py:697 (Ruff F841) |
| 2025-11-11 | 2.5 | 2 | TechDebt | High | TBD | Open | Re-run quality gates (Black/Ruff/Mypy) and verify 0 violations, update Task 8 completion notes with proof |
