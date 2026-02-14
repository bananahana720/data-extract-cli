# Wave 5 Operational Readiness

Date: 2026-02-13

## Objective
Define operational thresholds and runbook-level actions for the hardened single-node runtime.

## Key Signals
- Queue overload: `queue_overload` in `/api/v1/health?detailed=true`
- DB lock behavior: `db_lock_retry_stats` (including per-operation counters)
- Startup consistency: `startup_terminal_reconciliation`

## Runbook Actions
1. Queue overload response:
- Inspect backlog/capacity/utilization and `Retry-After` trends.
- Tune worker count/backlog safely.
- If sustained overload persists, open external queue migration ticket.

2. DB lock contention response:
- Inspect per-operation lock retry hotspots.
- Reduce write amplification and validate serialized write behavior.
- If retries/failures persist above ADR-013 thresholds, open external DB migration ticket.

3. Consistency reconciliation response:
- Investigate repair/failure events for terminal jobs.
- Validate disk health and artifact directory permissions.
- If repeated reconciliation failures occur, prioritize durability redesign.

## Readiness Outcome
Operational decision criteria are now explicit and tied to runtime metrics, enabling repeatable go/no-go scaling decisions without changing architecture in this cycle.
