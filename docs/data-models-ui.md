# Data Models - UI

Primary typed contracts: `ui/src/types.ts`

## Lifecycle and Job Contracts

- `JobStatus`, `JobSummary`, `JobDetail`
- `ProcessResultPayload`
- `JobArtifactEntry`, `JobArtifactsResponse`
- `SessionSummary`
- `ConfigPresetSummary`
- `AuthSessionStatus`

## UX Integrity and Guidance Contracts

- `RunReadinessState`
- `IntegritySeverity`
- `IntegrityTimelineEventViewModel`
- `EvidenceReadinessState`
- `GuidanceTipModel`

## Semantic Contracts

- `SemanticOutcome`
- `SemanticArtifact`

## Usage Anchors

- Run-builder and verify-before-run gating: `ui/src/pages/NewRunPage.tsx`, `ui/src/components/run-builder/*`
- Integrity timeline rendering: `ui/src/components/integrity/*`
- Evidence/readiness handoff cards: `ui/src/components/evidence/*`
- Control-tower summary flows: `ui/src/components/control-tower/*`
