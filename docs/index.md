# Project Documentation Index

## Project Overview

- **Type:** multi-part with 2 parts
- **Primary Language:** Python (backend) and TypeScript (UI)
- **Architecture:** API-driven client-server system with modular processing pipeline and guided desktop operator UX

## Quick Reference

## User Documentation

### Start Here

- [Root README](../README.md) - quick project entry point, overview, and quick start
- [Product Documentation](./product-documentation.md) - product purpose, capabilities, and operational model
- [User Guide](./user-guide.md) - installation, CLI onboarding, workflows, and troubleshooting

### Common Operator Paths

- [Deployment Guide](./deployment-guide.md) - local and production deployment patterns
- [Contribution Guide](./contribution-guide.md) - how to work effectively in this repo

### Backend (`backend`)

- **Type:** backend
- **Tech Stack:** Python, FastAPI, SQLAlchemy/Alembic, Typer
- **Root:** `.`

### UI (`ui`)

- **Type:** web
- **Tech Stack:** React, TypeScript, MUI, Vite, React Router, Vitest, Playwright
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
- [State Management Patterns - UI](./state-management-patterns-ui.md)
- [Comprehensive Analysis - Backend](./comprehensive-analysis-backend.md)
- [Comprehensive Analysis - UI](./comprehensive-analysis-ui.md)
- [Integration Architecture](./integration-architecture.md)
- [Project Parts Metadata](./project-parts.json)

## Existing Documentation

- [Repository Rules and Standards](../AGENTS.md) - security gatekeeper and repository workflow constraints
- [Project Source README](../src/README.md) - backend source package orientation
- [Tests README](../tests/README.md) - test strategy and execution guidance
- [Examples README](../examples/README.md) - usage patterns and examples
- [Build Scripts README](../build_scripts/README.md) - packaging/build helper scripts
- [Project Context Artifact](../_bmad-output/project-context.md) - generated project context summary
- [UX Design Specification](../_bmad-output/planning-artifacts/ux-design-specification.md) - UX specification artifact
- [CI Test Workflow](../.github/workflows/test.yml)
- [CI Security Workflow](../.github/workflows/security.yml)
- [CI Performance Workflow](../.github/workflows/performance.yml)
- [CI UAT Workflow](../.github/workflows/uat.yaml)

## Getting Started

1. Start with [Product Documentation](./product-documentation.md) for scope and capabilities.
2. Continue with [User Guide](./user-guide.md) for first-run setup and commands.
3. For technical implementation details, use `project-overview.md`, `architecture-backend.md`, and `architecture-ui.md`.
4. For integration work, include `integration-architecture.md`, `api-contracts-backend.md`, and `api-contracts-ui.md`.
5. For release or deployment readiness, follow `deployment-guide.md` and `development-guide-*` docs.

## Documentation Quality Notes

- User-facing flow: `user-guide.md`
- Technical flow: `project-overview.md` and the backend/ui architecture docs
- Data/API flow: `api-contracts-backend.md` and `api-contracts-ui.md`
- Process model flow: `component-inventory-*`, `data-models-*`

## Maintenance

- When adding new documentation, keep the index synchronized and preserve this structure:
  - Product summary
  - User flow
  - Engineering flow
  - Operations flow
