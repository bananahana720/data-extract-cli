# Comprehensive Analysis - UI

## Configuration and Entry Patterns

- Entry: `ui/src/main.tsx` -> `ui/src/App.tsx`.
- Build/proxy config: `ui/vite.config.ts` (dev proxy to backend API).
- Scripts and test tooling: `ui/package.json`, `ui/playwright.config.ts`.

## Auth and Security

- Auth session API integration in `ui/src/api/client.ts` and `ui/src/pages/ConfigPage.tsx`.
- Same-origin credential usage and retry/timeout handling in API wrapper.

## Shared Code and Contracts

- Central API client: `ui/src/api/client.ts`.
- Shared typed contracts: `ui/src/types.ts`.

## State and Async Patterns

- Page-local state with hooks.
- Polling and resilience logic in jobs/detail pages.

## UI Composition

- Route-first composition with feature pages under `ui/src/pages/`.
- Styles and reusable classes centralized in `ui/src/styles.css`.
