# Documentation Status Registry

Last sweep: 2026-02-15
Scope: Keep only context-critical docs for repository understanding, structure, dependencies, ADRs, and human/AI workflows.

## Status Legend

- `current`: Valid and aligned with active repository structure
- `needs-update`: Kept for context, but likely includes stale references, outdated metrics, or pre-sweep assumptions

## Current

- `README.md`
- `docs/index.md`
- `docs/QUICKSTART.md`
- `docs/USER_GUIDE.md`
- `docs/CONFIG_GUIDE.md`
- `docs/ERROR_HANDLING_GUIDE.md`
- `docs/LOGGING_GUIDE.md`
- `docs/INFRASTRUCTURE_INTEGRATION_GUIDE.md`
- `docs/ci-cd-pipeline.md`
- `docs/architecture/`
- `docs/json-schema-reference.md`
- `docs/txt-format-reference.md`
- `docs/csv-format-reference.md`
- `docs/organizer-reference.md`
- `docs/UI_RUNTIME_GUIDE.md`
- `AGENTS.md`
- `GEMINI.md`

## Needs Update

- `docs/development-operations-guide.md` (overlaps with sharded guide)
- `docs/development-operations-guide-2025-11-13/` (contains stale references to removed story/UAT docs)
- `docs/PRD/` (content is useful but historical and should be revalidated)
- `docs/epics.md`
- `docs/tech-spec-epic-1.md`
- `docs/tech-spec-epic-2/`
- `docs/tech-spec-epic-2.5/`
- `docs/tech-spec-epic-3/`
- `docs/tech-spec-epic-3.5.md`
- `docs/tech-spec-epic-4.md`
- `docs/tech-spec-epic-5.md`
- `docs/brownfield-assessment/`
- `docs/bmm-index.md`
- `docs/bmm-project-overview.md`
- `docs/bmm-data-models.md`
- `docs/bmm-source-tree-analysis.md`
- `docs/bmm-pipeline-integration-guide/`
- `docs/bmm-processor-chain-analysis/`
- `docs/uv-migration-guide.md`
- `docs/automation-guide.md` (references removed story/UAT paths)
- `docs/tmux-cli-instructions.md` (references removed UAT setup doc)
- `CLAUDE.md`

## Removed in This Sweep

- Artifact/report-heavy and historical directories removed from active docs scope:
  - `docs/archive/` (superseded; historical files retained under `docs/.archive/`)
  - `docs/artifacts/`
  - `docs/reviews/`
  - `docs/testing/`
  - `docs/uat/`
  - `docs/test-plans/`
  - `docs/stories/`
  - `docs/retrospectives/`
  - `docs/research/`
  - `docs/implementation/`
  - `docs/implementation-readiness-report-2025-11-10/`
  - `docs/processes/`
  - `docs/tech-debt/`

- Transient reports/artifacts removed:
  - `quality-reports/*` (superseded by ignored runtime output dir `.quality-reports/`)
  - `scripts/PRUNING-SUMMARY.md`
  - `scripts/TRASH-FILES.md`
  - `TRASH-FILES.md`
