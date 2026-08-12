# BLACKDARK Buyer Handover Pack (RC2)

**Finding:** `F-XFER-01`  
**Goal:** A competent buyer engineering team can clone → install → configure → run → test → deploy → operate → monitor → backup → restore → rotate secrets → diagnose → rollback → upgrade without undocumented founder knowledge.

## 0. Freeze references

| Item | Value |
|------|-------|
| RC1 baseline (immutable) | `de6537fb29d6bc6203d58b572924db55b9c74d53` |
| RC2 candidate branch | `cursor/rc2-zero-defect-120d` |
| Product constitution | `docs/PRODUCT_CONSTITUTION_AR.md` |
| Architecture | `ARCHITECTURE.md` |
| Data room index | `docs/DATA_ROOM.md` + `docs/data-room/` |

## 1. Clone & install

```bash
git clone <repo-url> blackdark && cd blackdark
python -m venv .venv && source .venv/bin/activate
pip install --upgrade "pip==25.2"
pip install --require-hashes --only-binary=:all: -r requirements.hashes.txt
# Soft Launch local:
python scripts/bootstrap_free_human_ops.py --admin-email YOU@example.com --rotate
set -a; source .env.softlaunch.local; set +a
python -m uvicorn dashboard:app --host 127.0.0.1 --port 8080
```

See also: `README.md`, `DEPLOY.md`, `LAUNCH_GUIDE.md`, `docs/ENV_CONFIG_MATRIX.md`.

## 2. Configure (secrets map)

| Secret / pointer | Where | Rotation |
|------------------|-------|----------|
| `SECRETS_MASTER_KEY` / `SECRETS_VAULT_KEY` | env / private file | `docs/ops/SECRET_ROTATION.md` |
| `SESSION_TOKEN_PEPPER` | env | rotate + invalidate sessions |
| `ADMIN_API_KEY` or `ADMIN_API_KEY_FILE` | env / `keys/` 0600 | `scripts/setup_admin.py` |
| `TELEGRAM_SECRETS_FILE` | `keys/telegram.secrets.env` 0600 | `setup_telegram.py` |
| Stripe | `keys/stripe.secrets.env` 0600 | `scripts/setup_stripe.py` |
| `DATABASE_URL` | Postgres DSN | platform secret store |
| `REDIS_URL` | Redis DSN (viral/HA) | platform secret store |
| PSP webhooks | Stripe/Lemon dashboard | owner account |

**Production secrets authority:** Fernet + private 0600 files.  
**Not production:** `docker compose --profile vault-dev` HashiCorp Vault `-dev`.

## 3. Deploy

| Path | Doc |
|------|-----|
| Docker / compose HA rehearsal | `docker-compose.yml`, `DEPLOY.md` |
| Railway Soft Launch | `docs/GO_LIVE_AR.md`, `docs/RUNBOOK.md` |
| Kubernetes | `deploy/k8s/` |
| Production guard | `GET /api/production/guard` must pass |

## 4. Operate & monitor

- Day-2 ops: `docs/ops/INCIDENT_RESPONSE.md`, `docs/RUNBOOK.md`
- Glass Box announce: `docs/GLASS_BOX_OPERATOR_RUNBOOK.md` (human channel still EXTERNAL)
- Health: `/health/live`, `/health/ready`, `/health/viral`
- Metrics: `/metrics` (`observability.py`) — Prometheus/OTel full stack still post-close enhancement
- Alerts: Telegram when configured; pager wiring template in `docs/ops/PAGER_ONCALL.md`

## 5. Backup / restore / rollback

- `docs/ops/BACKUP_RESTORE.md`
- Scripts: `scripts/backup_postgres.py`, `scripts/restore_postgres.py`
- Rollback: redeploy previous image; keep DB; panic freeze via execution engine if needed

## 6. Account ownership (EXTERNAL fill-in)

Buyer must complete `docs/ops/ACCOUNT_OWNERSHIP_SCHEDULE.md` (cloud, DNS, Sonar, GitHub, PSP, Telegram). Until filled, transferability residual risk remains EXTERNAL.

## 7. Tabletop (no founder)

Run `docs/ops/HANDOVER_TABLETOP.md` checklist with two buyer engineers only. Pass = can recover from secret loss + DB restore + rollback without calling the founder.

## 8. Still EXTERNAL (cannot be repo-completed)

See RC2 final certification EXTERNAL list: live PSP purchase, CodeQL UI open=0, counsel IP/regulatory, Sonar New Code admin, branch protection export, WAF/pentest, founder 60s walkthrough.
