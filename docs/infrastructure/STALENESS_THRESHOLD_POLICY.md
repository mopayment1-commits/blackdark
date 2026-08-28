# Staleness Threshold Policy Engine (#1031)

Cross-cutting monitoring policy — NOT standalone. Merged into **#945 Provenance**, **#1017 Incident Response**, and **#1025 Automatic Failover**.

Defines per-source staleness thresholds, evaluates latency on a fixed schedule, dispatches internal ops alerts, and escalates to incident response and failover.

## Thresholds (versioned 1.0.0)

| Category | Base threshold |
|----------|----------------|
| Price | 5 minutes (300s) |
| Volume | 1 hour (3600s) |
| On-chain | 1 block (~12s) |
| Governance | 24 hours (86400s) |
| News | 30 minutes (1800s) |

## Tier multipliers (backend-enforced)

| Tier | Multiplier | Effect |
|------|------------|--------|
| Free | 1.5× | Looser (acceptable for free tier) |
| Pro | 0.85× | Stricter |
| Institution / Whale | 0.75× | Stricter |

## Detection

- Health check every **30 seconds**
- Deterministic latency vs threshold comparison — **no ML**
- Breach without internal alert = **pipeline failure** (no silent degradation)

## Internal alert

- Threshold breached → immediate internal alert to ops (Slack / PagerDuty)
- **Not user-facing** — UI badge updates are handled by #1030

## Escalation sequence

| Breach | Action |
|--------|--------|
| ≥ 1× threshold | Internal ops alert |
| ≥ 2× threshold | #1017 Incident Response auto-trigger |
| ≥ 3× threshold | #1025 Automatic Failover activation |

## Integrations

| Ref | Integration |
|-----|-------------|
| #945 | `freshness_score` = Degraded (breach) / Failed (>2×) — audit trail |
| #1025 | Failover trigger — source marked unreliable |
| #1026 | Stale + outlier → combined "Data Compromised" — suppress display |
| #1028 | Gap + staleness → prioritized backfill attempt |
| #1030 | Breach → badge auto-update to "Delayed" with exact delay |

## Fee DB

Every threshold evaluation, alert dispatch, and escalation action logs compute + notification cost with `source_id`.

## Sprint rollout

| Sprint | Scope |
|--------|-------|
| **0** | Threshold definitions with #945 |
| **1** | Alert automation + health check cycle |

## API

```
GET /api/platform/staleness-policy/status
GET /api/platform/staleness-policy/production-gate
GET /api/platform/staleness-policy/health-check
GET /api/platform/staleness-policy/audit-trail
GET /api/platform/staleness-policy/e2e
```

## Module

- `bd_platform/staleness_threshold_policy_engine.py`
- `data/staleness_threshold_seed.json`
