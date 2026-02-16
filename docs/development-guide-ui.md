# Development Guide - UI

## Prerequisites

- Node.js 20+
- npm

## Setup

1. `cd ui`
2. `npm install`

## Core Commands

- Local dev server: `npm run dev`
- Production build: `npm run build`
- Build preview: `npm run preview`
- Unit tests: `npm run test:unit`
- Watch-mode unit tests: `npm run test:unit:watch`
- Critical e2e lifecycle: `npm run e2e:gui`

## UI Architecture Anchors

- App bootstrap/theme: `ui/src/main.tsx`, `ui/src/theme/*`
- Route shell: `ui/src/App.tsx`
- API boundary: `ui/src/api/client.ts`
- Feature workflows: `ui/src/pages/*`
- Reusable UI system: `ui/src/components/*`
