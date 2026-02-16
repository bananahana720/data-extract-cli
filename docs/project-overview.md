# Project Overview

## Project

- Name: `data-extraction-tool-main`
- Repository type: `multi-part`
- Parts: `backend` and `ui`

## Purpose

Data extraction platform that converts mixed-source files into structured outputs. The backend orchestrates processing and persistence while the UI provides guided operator workflows for configuration, input preparation, run launch, and result interpretation.

## Architecture Classification

- Backend: modular processing pipeline with API and CLI adapters
- UI: route-driven SPA with tokenized design system and workflow-specific component domains
- System: API-driven client-server integration with shared lifecycle contracts

## Tech Stack Summary

| Part | Primary Stack |
|---|---|
| backend | Python, FastAPI, SQLAlchemy/Alembic, Typer, spaCy/scikit-learn |
| ui | React, TypeScript, MUI, Vite, React Router, Vitest, Playwright |

## Documentation Links

- [Root README](../README.md)
- `docs/architecture-backend.md`
- `docs/architecture-ui.md`
- `docs/source-tree-analysis.md`
- `docs/api-contracts-backend.md`
- `docs/api-contracts-ui.md`
- `docs/data-models-backend.md`
- `docs/data-models-ui.md`
- `docs/state-management-patterns-ui.md`
- `docs/component-inventory-backend.md`
- `docs/component-inventory-ui.md`
- `docs/integration-architecture.md`
- `docs/development-guide-backend.md`
- `docs/development-guide-ui.md`
- `docs/deployment-guide.md`
- `docs/contribution-guide.md`
