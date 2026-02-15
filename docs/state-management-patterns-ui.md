# State Management Patterns - UI

## Primary Pattern

- Local state per page with React hooks (`useState`, `useEffect`, `useMemo`, `useRef`).
- No Redux/MobX/Zustand store detected.

## Notable Implementations

- `ui/src/pages/JobsPage.tsx`
  - Polling loop, filter state, derived counts, backoff handling.
- `ui/src/pages/JobDetailPage.tsx`
  - Detail state, lifecycle traces, artifact refresh, retry controls.
- `ui/src/pages/NewRunPage.tsx`
  - Upload/path source state, validation errors, async submit state.
- `ui/src/pages/ConfigPage.tsx`
  - Auth session state, preset state, preview/apply actions.

## Async Resilience

- Retry and timeout wrappers in `ui/src/api/client.ts`.
- Poll interval and lock handling logic in jobs/detail pages.
