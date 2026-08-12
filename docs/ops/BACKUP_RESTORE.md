# Backup & Restore

**Findings:** `F-OPS-01`, repo portion of `F-EXT-03`  
**Live restore drill evidence in buyer cloud remains EXTERNAL.**

## Postgres

```bash
# Backup
python scripts/backup_postgres.py --out backups/blackdark-$(date -u +%Y%m%dT%H%M%SZ).sql

# Restore (destructive — confirm target DSN)
python scripts/restore_postgres.py --in backups/<file>.sql
```

### RPO / RTO targets (declared, not live-proven here)

| Mode | RPO | RTO | Evidence required |
|------|-----|-----|-------------------|
| Soft Launch SQLite | best-effort | best-effort | local file copy |
| Production Postgres | ≤ 24h (default ops) | ≤ 4h | buyer restore drill artifact |

## Redis

Redis is a **cache / coordination** plane for viral/HA — not the system of record for financial history. Rebuild from Postgres + re-ingest; do not treat Redis dumps as financial truth.

## Secrets

- Restore secret files to `keys/` with mode `0600`
- Re-seal Fernet master key from buyer secret store
- Rotate session pepper after suspected compromise (`SECRET_ROTATION.md`)

## Drill template (buyer executes)

1. Snapshot production-like DB
2. Restore into isolated instance
3. Boot app against restored DSN
4. Verify `/api/production/guard`, admin login, sample oracle
5. Attach checksum + timestamp artifact to data room as `EXTERNAL` evidence
