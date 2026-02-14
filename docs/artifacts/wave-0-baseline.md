# Wave 0 Baseline and Failure Harness

Date: 2026-02-13

## Scope
Baseline coverage for queue saturation behavior, SQLite lock retry observability, and terminal artifact consistency signals.

## Baseline Tests Added/Updated
- `tests/unit/data_extract/api/test_health_router.py`
- `tests/unit/data_extract/api/test_jobs_router.py`
- `tests/unit/data_extract/api/test_state_recovery.py`
- `tests/unit/data_extract/runtime/test_queue.py`

## Baseline Assertions
- Detailed health payload exposes queue overload snapshot and operation-scoped lock retry stats.
- Queue saturation and high-watermark throttling return `503` with `Retry-After` hint.
- Retry queue transitions remain durable and rollback correctly when enqueue fails.
- Startup reconciliation repairs missing `result.json` from DB payload and repairs DB payload from artifact.
- Reconciliation emits explicit `repair`/`error` events when repair succeeds/fails.

## Verification Commands
```bash
./.venv/bin/pytest \
  tests/unit/data_extract/api/test_health_router.py \
  tests/unit/data_extract/api/test_jobs_router.py \
  tests/unit/data_extract/api/test_state_recovery.py \
  tests/unit/data_extract/runtime/test_queue.py
```

## Exit Status
Baseline harness is in place and passing for the touched runtime/API units.
