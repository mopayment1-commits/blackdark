# Backup & Restore

**Control:** REL-003 · **Feature:** #828 Backup & DR Policy  
**Findings:** `F-OPS-01`, repo portion of `F-EXT-03`  
**Module:** `bd_platform/infrastructure_backup_disaster_recovery.py`

## Policy (Sprint-0 — mandatory)

| Requirement | Target |
|-------------|--------|
| Full backup | Daily |
| Incremental backup | Every 6 hours |
| Off-site storage | S3 cross-region (not same datacenter) |
| Encryption at-rest | AES-256 |
| Encryption in-transit | TLS 1.3 |
| DR restore test | Real restore every 30 days (not simulation-only) |
| RPO | ≤ 6 hours |
| RTO | ≤ 2 hours |
| Retention — daily | 30 days |
| Retention — weekly | 12 weeks |
| Retention — monthly | 12 months |

**Scope:** database · historical archive (#967) · configuration files · secrets backup (encrypted separately)

**Tenant isolation:** per-tenant encryption key — no cross-tenant recovery leak.

**Alerting:** backup failure → immediate ops alert (no silent failure).

**Audit:** every operation logged (timestamp, size, checksum, location, test result) — 2 year retention.

**Post-restore:** lineage integrity check via #945 Provenance.

**BCP governance:** see `docs/ops/BUSINESS_CONTINUITY_PLAN.md` (#1057 merged into #1016).

**Off-site geographic separation:** primary region ≠ backup region · minimum 100km apart · different availability zone · no shared network/power/staff infrastructure.

## Postgres

```bash
# Backup
python scripts/backup_postgres.py --out data/backups

# Restore (destructive — confirm target DSN)
python scripts/restore_postgres.py data/backups/<file>.sql.gz --yes
```

## API (admin only)

```
GET  /api/platform/internal/infrastructure/backup-dr/status
GET  /api/platform/internal/infrastructure/backup-dr/panel
POST /api/platform/internal/infrastructure/backup-dr/record
POST /api/platform/internal/infrastructure/backup-dr/drill
GET  /api/platform/internal/infrastructure/backup-dr/audit-trail
GET  /api/platform/internal/infrastructure/backup-dr/bcp
GET  /api/platform/internal/infrastructure/backup-dr/production-gate
GET  /api/platform/internal/infrastructure/backup-dr/e2e
```

## Redis

Redis is a **cache / coordination** plane — not the system of record. Rebuild from Postgres + re-ingest.

## Secrets

- Restore secret files to `keys/` with mode `0600`
- Re-seal Fernet master key from buyer secret store
- Rotate session pepper after suspected compromise (`SECRET_ROTATION.md`)

## Drill template (ops executes monthly)

1. Select latest off-site full backup (cross-region replica)
2. Restore into isolated instance
3. Run integrity validation (checksum + size)
4. Run post-restore lineage check (#945)
5. Boot app against restored DSN
6. Verify `/api/production/guard`, admin login, sample oracle
7. Record drill via `POST /api/platform/internal/infrastructure/backup-dr/drill`
8. Attach artifact to data room
