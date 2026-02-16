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
  2. start backend API runtime with UI serving enabled

## Deployment Modes

### 1) Integrated deployment (default)

1. Build frontend:
   - `cd ui && npm ci && npm run build`
2. Package artifacts with backend process.
3. Run API worker from project root and expose port.
4. Confirm `/api/v1/health` and root UI route.

### 2) Split deployment

1. Run backend API independently for job/session/config endpoints.
2. Host frontend separately with `VITE_API_BASE_URL` or equivalent API proxy settings.
3. Keep auth/session secret settings aligned across both systems.
4. Validate CORS and cookie/session-domain assumptions in staging before production.

## Packaging / Distribution Notes

- Packaging-related scripts and assets are under `build_scripts/`.
- Ensure environment-based secrets are injected at runtime; do not embed credentials in source.

## Practical pre-production checklist

- Confirm required dependencies:
  - OCR runtime for image/PDF OCR scenarios
  - spaCy model availability
  - Database permissions and writable work dirs
- Run security checks before release candidate:
  - `python scripts/scan_security.py --secrets-only`
  - `python scripts/scan_security.py --deps-only`
- Validate runtime and startup:
  - `data-extract ui --check`
  - `data-extract status`
- Smoke critical paths:
  - validation, extract/process, session resume, retry, semantic analyze
- Confirm logs include request/response and queue/job status signals.
