# BLACKDARK Service Level Agreement (Draft)

**Status:** DRAFT — requires legal review and publication  
**Version:** 1.0-draft

## Availability Target

| Tier | Monthly Uptime Target | Measurement |
|---|---|---|
| Pro | 99.5% | `/health` + observability probes |
| Whale | 99.7% | Dedicated probe set |
| Institutional | 99.9% | Contractual — requires signed HA load evidence (REL-002) |

## Support Response

| Severity | Pro | Whale | Institutional |
|---|---|---|---|
| P1 — Platform down | 4h | 2h | 1h |
| P2 — Degraded | 8h | 4h | 2h |
| P3 — General | 48h | 24h | 8h |

## Evidence

Uptime measured via `data/uptime_probes.jsonl` and observability stack.

## Remaining external step

Legal review, institutional tier negotiation, and signed publication.
