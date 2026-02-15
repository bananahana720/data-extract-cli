# Project Documentation Index

## Project Overview

- **Type:** multi-part with 2 parts
- **Primary Language:** Python (backend) and TypeScript (UI)
- **Architecture:** API-driven client-server with modular processing pipeline

## Quick Reference

### Backend (`backend`)

- **Type:** backend
- **Tech Stack:** Python, FastAPI, SQLAlchemy/Alembic, Typer
- **Root:** `.`

### UI (`ui`)

- **Type:** web
- **Tech Stack:** React, TypeScript, Vite, React Router, Playwright
- **Root:** `ui/`

## Generated Documentation

- [Project Overview](./project-overview.md)
- [Architecture - Backend](./architecture-backend.md)
- [Architecture - UI](./architecture-ui.md)
- [Source Tree Analysis](./source-tree-analysis.md)
- [Component Inventory - Backend](./component-inventory-backend.md)
- [Component Inventory - UI](./component-inventory-ui.md)
- [Development Guide - Backend](./development-guide-backend.md)
- [Development Guide - UI](./development-guide-ui.md)
- [Deployment Guide](./deployment-guide.md)
- [Contribution Guide](./contribution-guide.md)
- [API Contracts - Backend](./api-contracts-backend.md)
- [API Contracts - UI](./api-contracts-ui.md)
- [Data Models - Backend](./data-models-backend.md)
- [Data Models - UI](./data-models-ui.md)
- [Integration Architecture](./integration-architecture.md)
- [Project Parts Metadata](./project-parts.json)

## Existing Documentation

- [AGENTS](../AGENTS.md) - Repository rules, security constraints, and contribution expectations
- [Source README](../src/README.md) - Pipeline and source architecture notes
- [Tests README](../tests/README.md) - Testing strategy and commands
- [Examples README](../examples/README.md) - Example usage patterns
- [Build Scripts README](../build_scripts/README.md) - Build/package guidance
- [CI Test Workflow](../.github/workflows/test.yml) - Main CI validation pipeline
- [CI Security Workflow](../.github/workflows/security.yml) - Security/dependency scanning pipeline
- [CI Performance Workflow](../.github/workflows/performance.yml) - Performance regression checks
- [CI UAT Workflow](../.github/workflows/uat.yaml) - UAT automation pipeline

## Getting Started

1. Start at `project-overview.md` and `architecture-backend.md` for system context.
2. For UI work, pair `architecture-ui.md` with `api-contracts-ui.md`.
3. For backend work, use `architecture-backend.md`, `api-contracts-backend.md`, and `data-models-backend.md`.
4. For end-to-end changes, include `integration-architecture.md`.
5. Use this `index.md` as the primary input for brownfield PRD workflows.
