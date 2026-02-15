"""Story 5-6: Graceful Error Handling and Recovery - TDD Red Phase Tests.

This module contains failing tests (RED phase) for Story 5-6 acceptance criteria:

- AC-5.6-1: Session state persisted to .data-extract-session/
- AC-5.6-2: --resume flag detects and resumes interrupted batches
- AC-5.6-3: Failed file tracking with retry --last command
- AC-5.6-4: Interactive error prompts (InquirerPy)
- AC-5.6-5: Continue-on-error pattern
- AC-5.6-6: Journey 6 (Error Recovery) UAT passes
- AC-5.6-7: Session cleanup on successful completion

Test Philosophy:
- Given-When-Then format with clear comments
- One assertion per test (atomic)
- Tests MUST FAIL initially - this is RED phase
- Implementation follows in GREEN phase

Reference: docs/tech-spec-epic-5.md
"""
