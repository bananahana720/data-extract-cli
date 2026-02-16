# Critical Folders Summary

- `src/data_extract/api/`: API routers, middleware/auth, DB and runtime integration.
- `src/data_extract/services/`: orchestration services for jobs/sessions/retries/status.
- `src/data_extract/{extract,normalize,chunk,semantic,output}/`: processing pipeline stages.
- `src/data_extract/cli/`: CLI command surface and preset operations.
- `ui/src/pages/`: task-focused UI workflow pages.
- `ui/src/components/{foundation,run-builder,integrity,control-tower,evidence,patterns}/`: UX system layers.
- `ui/src/theme/`: tokenized visual + semantic status system.
- `tests/` and `ui/e2e/`: backend and frontend verification suites.
- `scripts/`: quality/performance/security automation.
