# BLACKDARK

Decision intelligence engine (ACT / WAIT) — not a charting terminal.

> Canonical architecture: [`ARCHITECTURE.md`](ARCHITECTURE.md)  
> Product law: [`docs/PRODUCT_CONSTITUTION_AR.md`](docs/PRODUCT_CONSTITUTION_AR.md)  
> Ops runbook: [`docs/RUNBOOK.md`](docs/RUNBOOK.md)

---

## Quick start (local)

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

export LOCAL_DEV=true
export SERVICE_MODE=web
export SECRETS_MASTER_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')"
export SESSION_TOKEN_PEPPER="$(python -c 'import secrets; print(secrets.token_hex(32))')"

python run_service.py web --port 8080
# → http://127.0.0.1:8080
```

SQLite is allowed for **local / Soft Launch demos only**.

---

## Production (mandatory Postgres + Redis)

```bash
export ENV=production
export SERVICE_MODE=web
export SOFT_LAUNCH=false
export DATABASE_URL=postgresql://user:pass@host:5432/blackdark
export REDIS_URL=redis://:password@host:6379/0
export SERVICE_BUS_LOCAL=false
export REDIS_REQUIRED=true
export SECRETS_MASTER_KEY=...          # openssl rand -hex 32
export SESSION_TOKEN_PEPPER=...
export ADMIN_API_KEY=...
export ADMIN_TOTP_SECRET=...           # base32
export VAULT_KEY_ROTATION_DAYS=90
export VAULT_KEY_LAST_ROTATED_AT=$(date -u +%F)

# Compose (hardened)
docker compose -f docker-compose.prod.yml up -d --build

# Or Kubernetes
kubectl apply -f k8s/
```

`production_guard.py` **fail-closes** if Postgres / Redis / secrets / admin MFA are missing.

---

## Key features (engineering)

| Surface | Path / module |
|---------|----------------|
| Oracle | `/oracle/{symbol}` |
| Public accuracy | `/oracle-accuracy` |
| Legal shield | `legal_shield.py` · `/api/status` · `/system/info` |
| Terms gate | `/api/legal/accept-terms` |
| OAuth2 | `/api/auth/oauth/{google\|github}/login` |
| Admin MFA | `X-Admin-TOTP` |
| MRR / Churn | `/api/billing/reports/mrr` · `/churn` |
| GDPR deletion | `/request-deletion` |

---

## Tests & coverage

```bash
pip install -r requirements.txt
pytest tests/ -q
python scripts/run_coverage.py
```

Coverage config: `.coveragerc` (fail-under for core modules). Expand toward project quality targets with `pytest --cov`.

---

## Vault key rotation

```bash
# Dry-run
python scripts/rotate_vault_key.py --dry-run

# Apply (rewrites encrypted user exchange keys)
export OLD_SECRETS_MASTER_KEY=...
python scripts/rotate_vault_key.py --apply
# → prints new SECRETS_MASTER_KEY + VAULT_KEY_LAST_ROTATED_AT
```

---

## Load evidence (10k harness)

```bash
# Against a Postgres+Redis stack (not Soft Launch SQLite)
python scripts/load_test_10k.py --base http://127.0.0.1:8080 --users 10000
# → data/load_test_10k_report.json
```

---

## Docs map

- [`ARCHITECTURE.md`](ARCHITECTURE.md) — data flow + topology
- [`docs/ACQUISITION_READINESS_CORRECTION_AR.md`](docs/ACQUISITION_READINESS_CORRECTION_AR.md) — M&A claim correction
- [`docs/SEC_MICA_COMPLIANCE_PACK.md`](docs/SEC_MICA_COMPLIANCE_PACK.md) — engineering compliance pack
- [`k8s/`](k8s/) — Kubernetes deployment templates

---

## License / posture

BLACKDARK is an **analytical tool** (`SYSTEM_CLASSIFICATION=analytical_tool`).  
Not financial advice. Not a registered adviser / MiCA CASP claim in product UI.
