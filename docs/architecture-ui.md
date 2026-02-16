# Architecture - UI

## Executive Summary

The UI is a React + TypeScript desktop web console focused on four operator tasks: configuring runs, preparing inputs, launching runs with verification gates, and interpreting results with explicit integrity/evidence signals.

## Technology Stack

- React 18 + TypeScript
- React Router DOM
- MUI 7 + Emotion styling system
- Vite build/dev tooling
- Vitest + RTL unit tests, Playwright e2e flows

## Architecture Pattern

- **Route-driven SPA shell** (`App.tsx`) with focused pages (`NewRun`, `Jobs`, `JobDetail`, `Sessions`, `Config`)
- **Tokenized theme foundation** (`ui/src/theme/*`)
- **Component domain layering** (`foundation`, `patterns`, `run-builder`, `integrity`, `control-tower`, `evidence`)
- **Centralized API boundary** (`ui/src/api/client.ts`)

## Data and Contract Architecture

- API-facing contracts and view models in `ui/src/types.ts`
- Includes run-readiness and integrity models:
  - `RunReadinessState`, `IntegritySeverity`, `IntegrityTimelineEventViewModel`, `EvidenceReadinessState`, `GuidanceTipModel`
- Contract mapping details: `docs/api-contracts-ui.md`

## UX and State Semantics

- Verify-before-run gate blocks invalid/unsafe submissions until acknowledged.
- Integrity timeline makes failures/remediation explicit.
- Control-tower summaries provide high-signal routing into corrective flows.
- Config evidence cards surface readiness, drift, and handoff actions.

## Source Tree and Dev Flow

- Structure reference: `docs/source-tree-analysis.md`
- Component catalog: `docs/component-inventory-ui.md`
- Developer setup: `docs/development-guide-ui.md`

## Deployment and Test Strategy

- Build output: `ui/dist` (served by backend in integrated mode)
- Unit test focus: component and gating behavior under `ui/src/**/*.test.tsx`
- E2E critical flow: `ui/e2e/job-lifecycle.spec.ts`
