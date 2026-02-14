# ADR-013: Runtime Scaling Thresholds for Local API/Queue/SQLite Architecture

Date: 2026-02-13
Status: Accepted

## Context
The runtime uses a single-process FastAPI server, in-process worker queue, local SQLite persistence, and filesystem job artifacts. This keeps local deployment simple, but saturation and lock contention must be monitored with explicit migration triggers.

## Decision
Adopt measurable thresholds to decide when to keep hardening the current architecture vs. migrate to external queue and/or external database.

## Thresholds
1. Queue saturation trigger:
- Condition: `queue_overload.throttle_rejections > 0` for 3 consecutive 5-minute windows OR `queue_overload.queue_full_rejections >= 10` in any 15-minute window.
- Action: Increase worker/backlog within local limits and investigate workload profile.
- Escalation: If condition persists after one tuning cycle, create migration ticket for durable external queue.

2. SQLite lock contention trigger:
- Condition: `db_lock_retry_stats.retries / db_lock_retry_stats.attempts >= 0.05` over 24 hours OR any non-zero lock failure count.
- Action: Review write serialization and transaction scope.
- Escalation: If contention remains above threshold after optimization, create migration ticket for external database.

3. Consistency repair trigger:
- Condition: `startup_terminal_reconciliation.failed > 0` on startup OR recurring repairs (`repaired > 0`) in 3 consecutive startups.
- Action: run artifact/DB integrity investigation and storage checks.
- Escalation: If recurring, schedule durability redesign and crash-recovery hardening sprint.

4. Latency and availability trigger:
- Condition: user-visible retries/timeouts increase in UI and jobs API returns frequent `503` due queue overload.
- Action: tune queue and throughput settings.
- Escalation: If still above threshold after one iteration, begin external queue/database migration design.

## Migration Trigger Rule
Open migration ADR for external queue and external DB when any two threshold categories are breached in the same release cycle after one remediation iteration.

## Consequences
- Keeps current architecture by default while reducing subjective scaling decisions.
- Creates explicit handoff criteria for moving to distributed components.
- Requires health payload monitoring discipline in operations and CI/perf review.
