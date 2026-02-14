# Phase 2 Runtime Hardening Report (2026-02-14)

## Scope
- Runtime under test: local FastAPI + `ApiRuntime` + `LocalJobQueue` + SQLite + filesystem artifacts.
- Load path: `POST /api/v1/jobs/process` with JSON payload.
- Workload: 240 requests, concurrency 16, fixed sample input.
- Health telemetry sampled during and after load: `queue_backlog`, `queue_utilization`, `pending_dispatch_jobs`, `artifact_sync_backlog`, `session_projection_drift`, `db_lock_retry_stats`, `worker_restarts`.
- Raw dataset: `docs/artifacts/phase2-runtime-hardening-matrix-2026-02-14.json`.

## Matrix Results
| Profile | Status | RPS | P95 (ms) | Error % | Max pending dispatch | Max artifact backlog | DB lock retries/failures | Drained |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| baseline | pass | 100.20 | 263.27 | 0.00 | 0 | 2 | 0 / 0 | true |
| dispatch_fast | pass | 93.41 | 309.03 | 0.00 | 0 | 1 | 0 / 0 | true |
| dispatch_conservative | pass | 97.99 | 294.96 | 0.00 | 0 | 1 | 0 / 0 | true |
| high_workers | pass | 62.30 | 454.66 | 0.00 | 1 | 2 | 0 / 0 | true |

## Findings
1. All profiles completed with zero request failures and no unresolved backlog after drain checks.
2. SQLite lock contention was not observed in this workload (`db_lock_retry_stats.retries == 0`, `failures == 0` in all profiles).
3. `high_workers` increased latency and reduced throughput versus baseline on this host; adding workers above 2 was counterproductive here.
4. Artifact sync backlog remained bounded (max 1-2) and converged to zero in all profiles.

## Recommended Runtime Profile (Phase 2)
Use **baseline** settings for this environment:
- `DATA_EXTRACT_API_WORKERS=2`
- `DATA_EXTRACT_API_QUEUE_MAX_BACKLOG=1000`
- `DATA_EXTRACT_API_QUEUE_HIGH_WATERMARK=0.90`
- `DATA_EXTRACT_API_DISPATCH_POLL_MS=250`
- `DATA_EXTRACT_API_DISPATCH_BATCH_SIZE=50`
- `DATA_EXTRACT_API_DB_LOCK_RETRIES=5`
- `DATA_EXTRACT_API_DB_LOCK_BACKOFF_MS=100`
- `DATA_EXTRACT_API_ARTIFACT_SYNC_INTERVAL_SECONDS=30`

Rationale: best measured P95 and highest throughput while maintaining zero lock retries/failures and bounded backlogs.

## Phase 2 Exit Criteria Check
- Stable enqueue/dispatch under burst load: **met**
- No escalating lock failures under tested load: **met**
- Bounded dispatch/artifact backlogs with drain-to-zero: **met**
- Health telemetry available for operational guardrails: **met**

## Notes
- Results are host/workload specific; re-run matrix after material runtime, hardware, or dependency changes.
- ADR thresholds should continue to gate migration decisions: `docs/architecture/adr-013-runtime-scaling-thresholds.md`.
