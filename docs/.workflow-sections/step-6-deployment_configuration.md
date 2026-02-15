# Deployment Configuration

## CI/CD Workflows

- `.github/workflows/test.yml`
  - unit/integration tests, coverage threshold, lint, type-check, format, pre-commit, refactor gates.
- `.github/workflows/performance.yml`
  - performance regression checks and threshold assertions.
- `.github/workflows/security.yml`
  - dependency and secrets/security scanning.
- `.github/workflows/uat.yaml`
  - UAT/test harness jobs and artifacts.

## Packaging and Runtime

- Backend API serves built UI assets from `ui/dist` via `src/data_extract/api/main.py`.
- Windows packaging scripts and docs in `build_scripts/`.
