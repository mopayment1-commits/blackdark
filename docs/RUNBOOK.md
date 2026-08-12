# BLACKDARK — Operations Runbook (RC2)

> Constitution: `docs/PRODUCT_CONSTITUTION_AR.md`  
> Handover: `docs/ops/BUYER_HANDOVER_PACK.md`  
> Findings closed here: `F-OPS-01`, portions of `F-XFER-01`

## Finalize (code → Railway)
```bash
python scripts/finalize_launch.py
python scripts/verify_constitution_live.py
# → writes .env.launch.local (gitignored) + data/finalize_launch.json
# Paste secrets into Railway Variables, then set DATABASE_URL
# After announce: python scripts/mark_golive.py --url https://YOUR-DOMAIN
# Full pack: docs/GO_LIVE_AR.md
```

## Pre-flight
1. `GET /api/production/guard` → `required_pass: true`
2. `GET /api/launch/readiness` → `code_launch_ready` + constitution modules
3. `GET /api/admin/launch-checklist` (admin) → review blocked items
4. `GET /api/oracle/accuracy/public` → proof_chain.verify ok
5. `GET /oracle/BTC?ux_mode=beginner&lang=en` → must include `decision_sentence`, `persona_clarity`
6. `GET /oracle/BTC?ux_mode=pro&lang=en` → must include `net_edge_truth`, `opportunity_half_life`, `signal_registry`
7. Confirm `CSP_NONCE_MODE` is ON (`docs/ops/CSP_PRODUCTION_ATTESTATION.md`)
8. Confirm `CORS_ALLOWED_ORIGINS` reviewed (`docs/ops/CORS_ALLOWLIST_REVIEW.md`)

## Required production env
See `docs/ops/ENV_VAR_REGISTRY.md` and `docs/ENV_CONFIG_MATRIX.md`.

Minimum:
- `SECRETS_MASTER_KEY` or `SECRETS_VAULT_KEY`
- `SESSION_TOKEN_PEPPER`
- `ADMIN_API_KEY` / `ADMIN_API_KEY_FILE` + `ADMIN_EMAILS`
- `APP_BASE_URL=https://...`
- Billing: Lemon **or** Stripe (+ webhook)
- Optional Telegram via `TELEGRAM_SECRETS_FILE` (0600), not cleartext `.env` token

## Deploy
| Mode | Command / path |
|------|----------------|
| Local Soft Launch | `bootstrap_free_human_ops.py` + uvicorn |
| Docker web | `docker compose up --build` |
| Optional Vault -dev | `docker compose --profile vault-dev up` (**not** prod secrets) |
| HA rehearsal | Postgres+Redis; `WEB_CONCURRENCY`/`WEB_REPLICAS` ≥2; Soft Launch unset |
| k8s | `deploy/k8s/` |

## Critical routes
| Route | Access | Purpose |
|-------|--------|---------|
| `/oracle/{symbol}` | quota | Primary Oracle (`oracle_unified`) + enrichment |
| `/oracle-accuracy` | public | Proof-native accuracy page |
| `/api/oracle/accuracy/public` | public | Hit-rate JSON + proof_chain |
| `/api/due-diligence/evidence-pack` | whale/admin | Full M&A pack |
| `/api/due-diligence/evidence-pack/public-summary` | public | Redacted teaser |
| `/api/production/guard` | ops | Fail-closed readiness |
| `/health/live` · `/health/ready` | public | Probes |
| `/metrics` | ops | Process metrics |

## Fail-closed behavior
- Contradiction veto / Net-Edge reject / Half-life expired → no execution
- Unknown trading/withdrawal fee → no executable opportunity (`fee_matrix` → `None`)
- Unknown/stale gas or native/USD mid → no executable DeFi P&L (`gas_oracle` → `None`)
- Unknown bridge protocol fee → `executable=false` (no invented flat bridge fee)
- Directional oracle soft-pass → labeled `ADVISORY_NOT_EXECUTABLE`
- Drift / OOD → rules fallback or withhold ML
- Missing production secrets → guard fails
- `CSP_NONCE_MODE=false` is break-glass only

## Incident response
Follow `docs/ops/INCIDENT_RESPONSE.md`.

## Backup / restore
Follow `docs/ops/BACKUP_RESTORE.md`. Live buyer drill evidence remains EXTERNAL (`F-EXT-03`).

## Secret rotation
Follow `docs/ops/SECRET_ROTATION.md`.

## Rollback
1. Redeploy previous Railway/Docker/k8s image (known-good SHA)
2. Keep DB intact (labeled corpus is the moat)
3. Freeze trading via panic if needed (`execution_engine.trigger_panic`)
4. Verify `/api/production/guard` and sample `/oracle/BTC`

## Post-launch 24h
- Watch `/health/ready`, billing webhooks, Telegram alerts
- Confirm live samples accumulating (flywheel)
- Do **not** claim HFT, guaranteed profit, or unproven 1k/10k user capacity
- Capacity claims must cite MEASURED rows in `docs/LOAD_TEST_RUN_LOG.md`
