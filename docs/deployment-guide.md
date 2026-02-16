# Deployment Guide

## CI/CD Workflows

- `.github/workflows/test.yml`: lint, type-check, tests, coverage and quality gates
- `.github/workflows/security.yml`: security/dependency scan checks
- `.github/workflows/performance.yml`: performance regressions
- `.github/workflows/uat.yaml`: UAT/flow validation

## Runtime Deployment Shape

- Backend FastAPI service (`src/data_extract/api/main.py`) exposes `/api/v1/*` and can serve built UI assets from `ui/dist`.
- Typical integrated build path:
  1. `cd ui && npm run build`
  2. start backend API runtime

## Packaging / Distribution Notes

- Packaging-related scripts and assets are under `build_scripts/`.
- Ensure environment-based secrets are injected at runtime; do not embed credentials in source.
