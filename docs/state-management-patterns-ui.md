# State Management Patterns - UI

## Primary Pattern

- Feature-local state with React hooks (`useState`, `useEffect`, `useMemo`, `useRef`, `useCallback`).
- URL query parameters (search/filter) used as durable page state for Jobs and Sessions.
- No global Redux/Zustand/MobX store.

## High-Signal Implementations

- `ui/src/pages/NewRunPage.tsx`
  - Guided builder state, validation snapshots, checklist progress, verify-before-run acknowledgement, stale acknowledgement invalidation.
- `ui/src/pages/JobsPage.tsx`
  - Polling cadence with jitter/backoff, status/query URL synchronization, summary signal derivation.
- `ui/src/pages/JobDetailPage.tsx`
  - Job/event polling, artifact refresh cadence, lifecycle mapping to integrity timeline entries.
- `ui/src/pages/SessionsPage.tsx`
  - Session signal aggregation, stale session detection, filter URL synchronization.
- `ui/src/pages/ConfigPage.tsx`
  - Auth/preset/effective config state, preview/apply sequencing, evidence-readiness derivation.

## Async and Error Behavior

- API client handles read retries, timeout aborts, and retry-after semantics.
- UI surfaces errors in alerts and keeps remediation hints near action surfaces.
- Integrity state is intentionally explicit (no silent failure patterns in run/detail flows).
