# Retention & Deletion Policy — #949 + #1023

**Not a standalone product.** Unified compliance framework merged into Data Retention Governance (#949) and GDPR Compliance (#1023).

## Retention Tiers

| Tier | Retention | Scope |
|------|-----------|-------|
| Raw data | 90 days | Market ticks, ingestion snapshots, hot spool |
| Aggregated | 2 years | Analytics aggregates, canonical records |
| Archive | 5 years | Long-term archive tier |
| Audit logs | 2 years | Activity/audit JSONL files |
| Immutable records | 5 years | Recommendation audit (#1029) — anonymized on erasure, not deleted |
| Session data | 90 days | User sessions |
| Temporary cache | 7 days | Intermediate caches |
| Billing metadata | 7 years | Stripe-aligned billing records |

## Deletion Workflow

1. **User request** → `POST /api/privacy/dsr/erase` with `confirm=true`
2. **Soft delete** — immediate session purge + behavior anonymization
3. **30-day grace** — scheduled hard delete timestamp recorded
4. **Hard delete** — daily cron executes `erase_user_personal_data()`
5. **Immutable audit** — PII anonymized, records retained per 5-year policy

## Legal Hold

- Admin-only: `POST /api/platform/retention-deletion/legal-hold`
- Blocks automated hard delete for subject
- All hold actions logged append-only

## APIs

| Endpoint | Purpose |
|----------|---------|
| `GET /api/privacy/status` | GDPR + retention policy status |
| `POST /api/privacy/dsr/erase` | Schedule Art. 17 erasure |
| `GET /api/privacy/dsr/status` | Check pending erasure |
| `GET /api/platform/retention-deletion/status` | Full policy status |
| `GET /api/platform/retention-deletion/gate` | Production gate |
| `POST /api/platform/retention-deletion/run` | Admin — run daily job |

## Cron

```bash
python scripts/run_retention_deletion_job.py
```

## Integrations

| Ref | Integration |
|-----|-------------|
| #949 | Retention schedules = unified governance policy |
| #1023 | Deletion = GDPR Article 17 implementation |
| #1038 | Deletion events logged in retention audit trail |
| #1029 | Immutable records anonymized, not deleted |
| #908 | Billing retention aligned with Stripe/PCI-DSS |
| #1016 | Deleted data purged from backups after retention + legal hold |

## Non-Custodial

- Deletion applies to **platform data only**
- No wallet private keys held
- On-chain data is public/immutable — not deletable

## Production Gate

`check_retention_deletion_production_gate()` blocks production without:
- Documented retention tiers
- 30-day soft-delete grace
- Automated daily job capability
- Legal hold support
- GDPR erasure workflow
