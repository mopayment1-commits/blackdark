# BLACKDARK — Launch / On-Call Runbook

> Constitution: `docs/PRODUCT_CONSTITUTION_AR.md`

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

## Required production env
- `DATABASE_URL=postgresql://...` (mandatory — Soft Launch only for demos)
- `REDIS_URL` + `SERVICE_BUS_LOCAL=false`
- `SECRETS_MASTER_KEY` or `SECRETS_VAULT_KEY`
- `SESSION_TOKEN_PEPPER`
- `ADMIN_API_KEY` + `ADMIN_EMAILS` + `ADMIN_TOTP_SECRET`
- `VAULT_KEY_ROTATION_DAYS` + `VAULT_KEY_LAST_ROTATED_AT`
- `APP_BASE_URL=https://...`
- Billing: Lemon (`LEMON_SQUEEZY_*`) **or** Stripe (`STRIPE_*` + webhook)
- Optional: OAuth (`OAUTH_GOOGLE_*` / `OAUTH_GITHUB_*`), `TELEGRAM_BOT_TOKEN`

## Vault key rotation
```bash
export OLD_SECRETS_MASTER_KEY=$SECRETS_MASTER_KEY
python scripts/rotate_vault_key.py --dry-run
python scripts/rotate_vault_key.py --apply
# set printed SECRETS_MASTER_KEY + VAULT_KEY_LAST_ROTATED_AT, restart pods
```

## Kubernetes
See `k8s/README.md` — `kubectl apply -f k8s/` after editing secrets.

## Critical routes
| Route | Access | Purpose |
|-------|--------|---------|
| `/oracle/{symbol}` | quota | Primary Oracle + constitution enrich |
| `/oracle-accuracy` | public | Proof-native accuracy page |
| `/api/oracle/accuracy/public` | public | Hit-rate JSON + proof_chain |
| `/api/due-diligence/evidence-pack` | whale/admin | Full M&A pack |
| `/api/due-diligence/evidence-pack/public-summary` | public | Redacted teaser |
| `/api/production/guard` | ops | Fail-closed readiness |
| `/health/live` · `/health/ready` | public | Probes |

## Fail-closed behavior
- Contradiction veto / Net-Edge reject / Half-life expired → no execution
- Drift / OOD → rules fallback or withhold ML
- Missing production secrets → guard fails

## Rollback
1. Redeploy previous Railway/Docker image
2. Keep DB intact (labeled corpus is the moat)
3. Freeze trading via panic if needed (`execution_engine.trigger_panic`)

## Post-launch 24h
- Watch `/health/ready`, billing webhooks, Telegram alerts
- Confirm live samples accumulating (flywheel)
- Do **not** claim HFT or guaranteed profit
