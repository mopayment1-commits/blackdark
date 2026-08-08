# BLACKDARK — Architecture (Canonical Entry)

> **Status:** Living document · entry point for M&A / engineering onboarding  
> **Detailed audits:** [`docs/FULL_ARCHITECTURE_AUDIT.md`](docs/FULL_ARCHITECTURE_AUDIT.md) · [`docs/MICROSERVICES_ARCHITECTURE.md`](docs/MICROSERVICES_ARCHITECTURE.md)  
> **Product law:** [`docs/PRODUCT_CONSTITUTION_AR.md`](docs/PRODUCT_CONSTITUTION_AR.md) · [`docs/الملف_المرجعي_الملزم.md`](docs/الملف_المرجعي_الملزم.md)

---

## 1) What the system is

BLACKDARK is a **decision intelligence engine** (ACT/WAIT), not a charting terminal.

Core user loop:

```
Market/Ingestion feeds → Feature context → Oracle / Arb engines
        → Dimension Conflict Guard → Net-Edge / Half-Life gates
        → Decision Certificate + Audit Chain → UI / Alerts / B2B
```

---

## 2) Runtime topology

| Mode (`SERVICE_MODE`) | Process | Role |
|-----------------------|---------|------|
| `web` | `dashboard:app` :8080 | UI + Oracle API (preferred production) |
| `aggregator` | worker :8091 | Market polling / WS |
| `arbitrage` | worker :8092 | Scan + alerts + optional auto-exec |
| `ingestion` | worker :8093 | News/macro/data lake |
| `all` | monolith | Local/dev only |

Launcher: `python run_service.py web|aggregator|arbitrage|ingestion|all`

---

## 3) Data flow (happy path)

```
Exchanges / Hub sources
        │
        ▼
Ingestion + Hot storage (+ optional Redis/Kafka)
        │
        ▼
Oracle unified score + Persona Clarity (ACT/WAIT)
        │
        ├─ Contradiction Veto (D2)
        ├─ Net-Edge Truth (D3)
        ├─ Opportunity Half-Life (D4)
        └─ Regime models (D5)
        │
        ▼
prediction_id + hash chain (D1) + Decision Certificate (Hero #6)
        │
        ▼
Landing / Dashboard / Telegram / B2B Evidence Pack (D6)
```

Public proof surface: **`/oracle-accuracy`** (no login).

---

## 4) Persistence

| Env | Store | Gate |
|-----|-------|------|
| Local / `SOFT_LAUNCH=true` | SQLite | Allowed for demo |
| Production (`ENV=production`) | **PostgreSQL required** via `DATABASE_URL` | `production_guard.py` fail-closed |

Secrets: Fernet vault (`SECRETS_MASTER_KEY`) — fail-closed in production.

---

## 5) Security surfaces (as implemented)

- Password hashing: PBKDF2-SHA256 (high iterations)
- Session tokens hashed + pepper + HttpOnly `bd_token` cookie
- OAuth2: Google / GitHub (`oauth_service.py`, authlib)
- Admin: `ADMIN_API_KEY` / `ADMIN_EMAILS` + **TOTP MFA** (`ADMIN_TOTP_SECRET` / per-user enroll)
- Rate limits + durable auth audit JSONL
- Postgres `pgcrypto` enabled on init; Fernet app vault for exchange keys
- Production guard requires Postgres + Redis + admin TOTP (unless Soft Launch)
- Compliance footer on primary AI surfaces (Anti-Hype)
- Investor reports: `/api/billing/reports/mrr` + `/churn`

**Human/ops remaining (not code gaps):** provider OAuth client secrets, run `scripts/load_test_10k.py` on prod-like stack, external SEC/MiCA counsel letter. Multi-tenant org isolation remains intentionally out of scope.

**Docs:** [`docs/ACQUISITION_READINESS_CORRECTION_AR.md`](docs/ACQUISITION_READINESS_CORRECTION_AR.md) · [`docs/SEC_MICA_COMPLIANCE_PACK.md`](docs/SEC_MICA_COMPLIANCE_PACK.md)

---

## 6) Key modules (map)

| Concern | Primary files |
|---------|----------------|
| HTTP / UI | `dashboard.py`, `templates/` |
| Oracle | `ai_oracle.py`, `oracle_unified.py`, `decision_enrichment.py` |
| Conflict veto | `dimension_conflict_guard.py` |
| Whale S/N | `whale_signal_classifier.py` |
| Audience | `audience_routing.py`, `ux_mode.py` |
| Arb | `arbitrage_engine.py` |
| Auth | `auth_service.py`, `security_auth.py` |
| Vault | `secrets_vault.py` |
| Postgres | `postgres_backend.py`, `database.py` |
| Prod gate | `production_guard.py` |
| Accuracy | `ml/public_accuracy.py`, `oracle_track_record.py`, `templates/oracle_accuracy.html` |

---

## 7) Deploy notes

- Local setup: [`README.md`](README.md)
- Compose (local/scale-out): `docker-compose.yml`
- Production compose template: `docker-compose.prod.yml`
- Kubernetes templates: [`k8s/`](k8s/) (`deployment`, `service`, `hpa`, `ingress`, `pdb`)
- Vault rotation: `python scripts/rotate_vault_key.py --apply`
- Coverage: `python scripts/run_coverage.py`
- Free soft launch: `SOFT_LAUNCH=true` + `SERVICE_MODE=web` (SQLite demo — not an acquisition-grade HA claim)
