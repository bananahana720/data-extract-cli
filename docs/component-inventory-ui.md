# Component Inventory - UI

## App Shell and Routing

- `ui/src/main.tsx` (ThemeProvider, CssBaseline, BrowserRouter)
- `ui/src/App.tsx` (navigation shell + route map)

## Foundation Layer (`ui/src/components/foundation/*`)

- `SectionCard`, `PageSectionHeader`, `StatusPill`, `GuidanceTip`, `EmptyStatePanel`
- Shared style composition helper: `sx.ts`

## Pattern Layer (`ui/src/components/patterns/*`)

- `FeedbackBanner`, `FilterChipsBar`, `LoadingState`, `EmptyState`

## Feature Domains

- `run-builder/*`
  - `GuidedRunBuilderShell`, `VerifyBeforeRunSummaryCard`
- `integrity/*`
  - `IntegrityTimelineRail`, adapters, remediation helpers
- `control-tower/*`
  - `ControlTowerStatusConsole`
- `evidence/*`
  - `EvidenceHandoffCard`

## Route Pages

- `NewRunPage` (guided config/input flow + verify-before-run gate)
- `JobsPage` (control-tower summary + searchable/polling job table)
- `JobDetailPage` (integrity timeline + retry/cleanup + artifact workflow)
- `SessionsPage` (session signal console + stale/failure surfacing)
- `ConfigPage` (auth + presets + evidence readiness handoff)

## Test Coverage for New UI Layer

- Unit/component tests under:
  - `ui/src/components/run-builder/*.test.tsx`
  - `ui/src/components/integrity/*.test.tsx`
  - `ui/src/components/control-tower/*.test.tsx`
  - `ui/src/components/evidence/*.test.tsx`
