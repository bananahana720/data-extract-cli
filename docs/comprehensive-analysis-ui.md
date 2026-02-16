# Comprehensive Analysis - UI

## Configuration and Entry Patterns

- Entry flow: `main.tsx` -> `App.tsx` -> route pages.
- Theme/tokens centralized in `ui/src/theme/*` and shared via MUI ThemeProvider.

## Interaction Model by Critical Task

- Choosing configs: `ConfigPage` with preview/apply and evidence readiness cards.
- Preparing inputs: `NewRunPage` guided builder with domain context prompts and checklist progress.
- Launching runs: verify-before-run summary card enforces blocking + acknowledgement gates.
- Interpreting results: `JobDetailPage` integrity timeline and remediation hints.

## State, Error, and Integrity Semantics

- Polling/backoff patterns in Jobs/Sessions/JobDetail avoid tight loops and surface failures.
- Integrity severity model (`info|success|warning|error`) powers timeline/status components.
- Readiness states (`pending|ready|warning|blocked|stale`) keep run gating explicit.

## Shared Pattern and Accessibility Notes

- Componentized UX primitives reduce repeated logic across pages.
- Key live status regions are annotated (`aria-live`) for update announcements.
- `data-testid` hooks are retained/expanded for unit and e2e coverage.

## Testability and Reliability

- Vitest/RTL coverage added for core UX modules.
- Playwright lifecycle flow remains aligned with core job lifecycle path.
