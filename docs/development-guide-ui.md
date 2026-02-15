# Development Guide - UI

## Prerequisites

- Node.js 20+
- npm

## Setup

1. `cd ui`
2. `npm install`

## Common Commands

- Dev server: `npm run dev`
- Production build: `npm run build`
- Preview build: `npm run preview`
- E2E tests: `npm run e2e:gui`

## Architecture Notes

- App bootstrap: `ui/src/main.tsx`
- Route shell: `ui/src/App.tsx`
- API integration: `ui/src/api/client.ts`
