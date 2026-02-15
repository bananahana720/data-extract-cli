# Architecture - UI

## Executive Summary

The UI is a React + TypeScript single-page application (Vite) that provides operator workflows for runs, jobs, sessions, and configuration by consuming backend `/api/v1` endpoints.

## Technology Stack

- React 18
- TypeScript 5
- React Router DOM
- Vite build/dev tooling
- Playwright E2E tests

## Architecture Pattern

- Route-driven SPA with centralized API client:
  - Route shell: `ui/src/App.tsx`
  - API gateway module: `ui/src/api/client.ts`
  - Typed contracts: `ui/src/types.ts`

## Data and Contract Architecture

- No client DB schema detected.
- Typed interfaces mirror backend JSON contracts.
- Request retry/timeout logic in shared client wrapper.

## API Design (Client Perspective)

- Consumes:
  - auth/session APIs
  - jobs and artifact APIs
  - sessions APIs
  - config/preset APIs
- Details in `docs/api-contracts-ui.md`.

## Component Overview

- Pages:
  - `NewRunPage`
  - `JobsPage`
  - `JobDetailPage`
  - `SessionsPage`
  - `ConfigPage`
- Inventory in `docs/component-inventory-ui.md`.

## Source Tree

See `docs/source-tree-analysis.md` for UI folder annotation.

## Development Workflow

See `docs/development-guide-ui.md`.

## Deployment Architecture

- Built with `npm run build` to `ui/dist`.
- Served by backend FastAPI in integrated deployment mode.

## Testing Strategy

- Playwright suites in `ui/e2e/`.
- Backend/API contract behavior validated by Python test suites and CI.
