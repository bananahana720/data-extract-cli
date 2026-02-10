# Engineering Backlog

This backlog collects cross-cutting or future action items that emerge from reviews and planning.

Routing guidance:

- Use this file for non-urgent optimizations, refactors, or follow-ups that span multiple stories/epics.
- Must-fix items to ship a story belong in that story’s `Tasks / Subtasks`.
- Same-epic improvements may also be captured under the epic Tech Spec `Post-Review Follow-ups` section.

| Date | Story | Epic | Type | Severity | Owner | Status | Notes |
| ---- | ----- | ---- | ---- | -------- | ----- | ------ | ----- |
| 2025-11-15 | 3.4 | 3 | Bug | High | TBD | Open | Propagate chunk config + source file metadata so JSON headers report real chunk_size/overlap (`src/data_extract/chunk/metadata_enricher.py`, `src/data_extract/output/formatters/json_formatter.py`). |
| 2025-11-15 | 3.4 | 3 | Bug | High | TBD | Open | Normalize `ChunkMetadata.to_dict()` so all required fields serialize without nulls and include source_file provenance (`src/data_extract/chunk/models.py`). |
| 2025-11-15 | 3.4 | 3 | Bug | Medium | TBD | Open | Reinstate UTF-8 BOM support when writing JSON as required by AC-3.4-2 (`src/data_extract/output/formatters/json_formatter.py`). |
| 2025-11-15 | 3.4 | 3 | Bug | Medium | TBD | Open | Surface schema validation failures as hard errors instead of silent `FormatResult` entries (`src/data_extract/output/formatters/json_formatter.py`). |
| 2025-11-15 | 3.4 | 3 | Documentation | Low | TBD | Open | Update Dev Agent File List / docs to enumerate formatter base + unit test changes for traceability (`docs/stories/3-4-json-output-format-with-full-metadata.md`). |
| 2025-11-16 | 3.6 | 3 | Bug | High | TBD | Open | Implement OutputWriter/organization and expose `--format csv` so CsvFormatter can be invoked via CLI/pipeline; re-enable the CSV integration tests that currently skip (`src/data_extract/cli.py`, `tests/integration/test_output/test_csv_pipeline.py`). |
| 2025-11-16 | 3.6 | 3 | Quality | High | TBD | Open | Add pandas/csvkit dependencies, fail `_validate_pandas/_validate_cli` when tools are missing, and capture Excel/Sheets validation evidence for AC-3.6-4/7 (`pyproject.toml`, `src/data_extract/output/validation/csv_parser.py`, `docs/atdd-checklist-3.6.md`). |
| 2025-11-17 | 3.8 | 3 | Documentation | Medium | TBD | Open | Update traceability matrix to reflect Gap 1 resolution: Change AC-3.2-5 from PARTIAL → FULL, update Gap 1 section to show "RESOLVED via Story 3.8 (2025-11-17)", add test reference `test_entity_aware_chunking.py::TestCrossChunkEntityLookup`, update P1 Coverage from "90% (9/10)" to "100% (10/10)" (`docs/traceability-matrix-epic-3.md:266-308, lines 1086-1108`). Effort: ~15 minutes. |
| 2025-11-18 | 3.5-5 | 3.5 | Bug | High | Winston | Resolved | Add `.data-extract-cache/` to .gitignore file to prevent cache commits (AC #2) - ADR claims gitignored but pattern missing (`.gitignore:45-49`). **RESOLVED 2025-11-18**: Entry added to `.gitignore:52`. |
| 2025-11-18 | 3.5-5 | 3.5 | Documentation | Medium | Winston | Resolved | Document cache warming strategy with concrete examples in ADR (AC #5) - Task mentions warming strategy but ADR only briefly mentions without details (`docs/architecture/adr-012-semantic-model-cache.md:61`). **RESOLVED 2025-11-18**: Added comprehensive "Cache Warming Strategy" section with 5 concrete examples (automatic, manual, team collaboration, CI/CD, selective warming). |
| 2025-11-18 | 3.5-4 | 3.5 | Enhancement | Low | TBD | Resolved | Add executable permission to scripts/smoke-test-semantic.py - has shebang but not executable (`scripts/smoke-test-semantic.py`). **RESOLVED 2025-11-18**: Executable permission added via chmod +x. |
| 2025-11-18 | 3.5-4 | 3.5 | Quality | Low | TBD | Resolved | Add type: ignore comments for scientific library imports to suppress Mypy warnings (`scripts/smoke-test-semantic.py:19-24`). **RESOLVED 2025-11-18**: Added `# type: ignore[import-untyped]` comments to all 6 scientific library imports. |
| 2025-11-18 | 3.5-8 | 3.5 | Quality | Medium | DevOps Team | Open | Add missing return type annotations to functions in audit_dependencies.py - AC14 requires 0 Mypy violations (`scripts/audit_dependencies.py:52,103,134,172,195,464`). |
| 2025-11-18 | 3.5-8 | 3.5 | Quality | Medium | DevOps Team | Open | Add missing return type annotations to functions in generate_tests.py - AC14 requires 0 Mypy violations (`scripts/generate_tests.py:52,103,134,172,195,698`). |
| 2025-11-18 | 3.5-8 | 3.5 | Quality | Low | DevOps Team | Open | Add types-toml to dev dependencies in pyproject.toml or use type: ignore comments for toml imports (`pyproject.toml`, `scripts/audit_dependencies.py:208`). |
