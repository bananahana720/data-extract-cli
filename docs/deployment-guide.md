# Deployment Guide

## CI/CD Pipelines

- `.github/workflows/test.yml`: tests, coverage, lint, mypy, formatting, pre-commit, refactor gates.
- `.github/workflows/performance.yml`: performance benchmark checks.
- `.github/workflows/security.yml`: security and dependency scanning.
- `.github/workflows/uat.yaml`: UAT flow and artifacts.

## Runtime Deployment Shape

- Backend FastAPI service (`src/data_extract/api/main.py`) serves REST APIs and static UI bundle from `ui/dist`.
- Build UI with `cd ui && npm run build` before serving bundled assets via backend.

## Packaging

- Windows packaging tooling and scripts are in `build_scripts/`.
