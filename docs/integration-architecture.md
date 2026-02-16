# Integration Architecture

## Overview

This repository is a two-part system:

- `backend` (`src/data_extract/`) provides API, queue orchestration, persistence, and pipeline execution.
- `ui` (`ui/`) provides desktop browser workflows for config, run launch, monitoring, and evidence handoff.

Primary integration protocol: HTTP/JSON over `/api/v1/*`.

## Integration Points

1. Auth session lifecycle
- From: `ui/src/pages/ConfigPage.tsx`, `ui/src/api/client.ts`
- To: `src/data_extract/api/routers/auth.py`
- Type: REST + signed session cookie
- Details: API key login establishes session, status polling validates readiness, logout clears cookie.

2. Guided run launch
- From: `ui/src/pages/NewRunPage.tsx`
- To: `src/data_extract/api/routers/jobs.py`
- Type: REST JSON/multipart
- Details: UI enforces verify-before-run gate before posting to `/jobs/process`.

3. Job monitoring and integrity handling
- From: `ui/src/pages/JobsPage.tsx`, `ui/src/pages/JobDetailPage.tsx`, `ui/src/components/integrity/*`
- To: `src/data_extract/api/routers/jobs.py`
- Type: REST polling + command endpoints
- Details: list/detail polling, retry-failures, artifacts list/download/cleanup, and lifecycle event rendering.

4. Config/preset evidence workflow
- From: `ui/src/pages/ConfigPage.tsx`, `ui/src/components/evidence/*`
- To: `src/data_extract/api/routers/config.py`
- Type: REST query/mutation
- Details: effective config, preset listing/preview/apply, and readiness drift detection.

5. Session control-tower summaries
- From: `ui/src/pages/SessionsPage.tsx`, `ui/src/components/control-tower/*`
- To: `src/data_extract/api/routers/sessions.py`
- Type: REST query
- Details: session throughput/failure/staleness signals drive summary chips and filtering.

## Data Flow

1. Operator configures run context in UI.
2. UI validates readiness and submits run intent.
3. Backend enqueues and processes workload through pipeline stages.
4. Backend persists jobs/files/events/sessions and artifacts.
5. UI polls status endpoints and renders integrity/evidence/control-tower views.
6. Optional retry/cleanup actions loop back into backend orchestration.

## Shared Contracts and Dependencies

- UI contracts live in `ui/src/types.ts`; backend payloads are emitted by routers/services.
- `ui/src/api/client.ts` centralizes retry/timeout/auth behavior.
- Backend runtime queue and DB projection logic are exposed through job/session routers.
