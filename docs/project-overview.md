# Project Overview

## Project

- Name: `data-extraction-tool-main`
- Repository type: `multi-part`
- Parts: `backend` and `ui`

## Purpose

A document/data extraction platform with a Python processing backend and a React operator UI for submitting jobs, monitoring status, managing sessions, and configuring presets.

## Architecture Classification

- Backend: modular pipeline + API/CLI adapter architecture
- UI: route-driven SPA with centralized API client
- System: client-server API orchestration

## Tech Stack Summary

| Part | Primary Stack |
|---|---|
| backend | Python, FastAPI, SQLAlchemy/Alembic, Typer |
| ui | React, TypeScript, Vite, React Router, Playwright |

## Documentation Links

- `docs/architecture-backend.md`
- `docs/architecture-ui.md`
- `docs/source-tree-analysis.md`
- `docs/api-contracts-backend.md`
- `docs/api-contracts-ui.md`
- `docs/data-models-backend.md`
- `docs/data-models-ui.md`
- `docs/component-inventory-ui.md`
- `docs/integration-architecture.md`
- `docs/development-guide-backend.md`
- `docs/development-guide-ui.md`
- `docs/deployment-guide.md`
- `docs/contribution-guide.md`
