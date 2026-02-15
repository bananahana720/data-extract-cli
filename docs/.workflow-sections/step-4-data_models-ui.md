# Data Models - UI

Primary typed contracts: `ui/src/types.ts`

## Core Types

- `JobStatus`
- `JobSummary`
- `JobDetail`
- `ProcessResultPayload`
- `JobArtifactEntry`
- `JobArtifactsResponse`
- `SessionSummary`
- `ConfigPresetSummary`
- `AuthSessionStatus`
- `SemanticOutcome`
- `SemanticArtifact`

## Usage

- Jobs list and filters: `ui/src/pages/JobsPage.tsx`
- Job detail and lifecycle timeline: `ui/src/pages/JobDetailPage.tsx`
- Session dashboards: `ui/src/pages/SessionsPage.tsx`
- Configuration/preset/auth flows: `ui/src/pages/ConfigPage.tsx`

## Contract Source

- Types mirror backend JSON payloads from `api/v1` endpoints.
- No client-side persistence schema (local DB) detected.
