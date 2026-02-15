# Integration Architecture

## Overview

This repository is a two-part system:

- `ui` (React SPA) as client and operator interface
- `backend` (FastAPI + pipeline services) as orchestration and processing API

Primary protocol: HTTP/JSON REST over `/api/v1/*`.

## Integration Points

1. Auth session flow
- From: `ui/src/api/client.ts`, `ui/src/pages/ConfigPage.tsx`
- To: `src/data_extract/api/routers/auth.py`, `src/data_extract/api/main.py`
- Type: REST + session cookie auth
- Details: UI creates/reads/deletes auth session; backend validates API key or signed session cookie.

2. Job intake and execution
- From: `ui/src/pages/NewRunPage.tsx`
- To: `src/data_extract/api/routers/jobs.py`
- Type: REST JSON/multipart
- Details: UI submits path/upload jobs to `/api/v1/jobs/process`; backend enqueues and tracks execution.

3. Job monitoring and artifacts
- From: `ui/src/pages/JobsPage.tsx`, `ui/src/pages/JobDetailPage.tsx`
- To: `src/data_extract/api/routers/jobs.py`
- Type: REST polling and command operations
- Details: UI polls list/detail, triggers retry-failures, manages artifact listing/cleanup/downloads.

4. Config and presets
- From: `ui/src/pages/ConfigPage.tsx`
- To: `src/data_extract/api/routers/config.py`, `src/data_extract/cli/config.py`
- Type: REST config contract
- Details: UI previews/applies presets; backend persists preset/app settings and returns effective config.

5. Session summaries
- From: `ui/src/pages/SessionsPage.tsx`
- To: `src/data_extract/api/routers/sessions.py`, `src/data_extract/services/session_service.py`
- Type: REST query
- Details: backend serves session summaries from DB with filesystem fallback.

## Data Flow

1. User initiates run in UI.
2. UI posts job request to backend.
3. Backend dispatches to runtime queue and pipeline services.
4. Backend persists job/session/event records.
5. UI polls API for status and artifacts.
6. Backend serves UI bundle and API from same service boundary.

## Shared Dependencies and Contracts

- Typed UI contracts in `ui/src/types.ts` map to backend JSON payloads.
- API wrappers in `ui/src/api/client.ts` encode retry/timeout/auth semantics.
- Backend service/runtime layers provide queueing, retries, persistence, and health metrics.
