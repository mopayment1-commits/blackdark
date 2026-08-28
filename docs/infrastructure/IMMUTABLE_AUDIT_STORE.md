# Immutable Recommendation Audit Store (#1029)

Cross-cutting WORM policy — NOT standalone. Physically locks data used in recommendations for non-repudiation and audit.

## WORM policy

| Rule | Enforcement |
|------|-------------|
| **Write-once** | SHA-256 hash + timestamp + lock — no edit/delete/soft delete/override |
| **Selective scope** | Only datums referenced in recommendation computation |
| **Verification** | Merkle tree per batch + per-recommendation hash — deterministic replay |
| **Storage** | Append-only JSONL — physically isolated — AES-256 at-rest |
| **Retention** | 5 years minimum — legal hold check before cleanup |

## Sprint rollout

| Sprint | Scope |
|--------|-------|
| **0/1** | WORM infrastructure — blocks production if incomplete |
| **2** | Enforcement when Intelligence Ledger produces recommendations |

## Integrations

- **#955** Decision Traceability — `trace_id` flows ingest→recommendation→immutable store
- **#952** Decision Certificate — `certificate_hash` of evidence set
- **#945** Provenance — full lineage on every immutable record
- **#987** Public Accuracy Ledger — historical scores use immutable data only
- **#980** Point-in-Time Metrics — PIT snapshots auto-locked when feeding recommendations
- **#1022** RBAC — read-only audit API for Admin/Super Admin/Compliance Officer

## API (read-only audit)

```
GET  /api/platform/immutable-audit/status
GET  /api/platform/immutable-audit/verify/{verification_id}     (admin)
GET  /api/platform/immutable-audit/record/{verification_id}       (admin)
GET  /api/platform/immutable-audit/trail                         (admin)
GET  /api/platform/immutable-audit/infrastructure-gate
GET  /api/platform/immutable-audit/integrity-check               (admin)
GET  /api/platform/immutable-audit/e2e                           (admin)
```

## Integrity

Daily hash recomputation vs stored — mismatch triggers #1017 Incident Response.

## Fee DB

Storage + verification compute + cross-region replication — per recommendation.
