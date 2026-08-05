# BLACKDARK — Launch / On-Call Runbook

> Constitution: `docs/PRODUCT_CONSTITUTION_AR.md`

## Finalize (code → Railway)
```bash
python scripts/finalize_launch.py
# → writes .env.launch.local (gitignored) + data/finalize_launch.json
# Paste secrets into Railway Variables, then set DATABASE_URL + Lemon/Stripe
```

## Pre-flight
1. `GET /api/production/guard` → `required_pass: true`
2. `GET /api/launch/readiness` → `code_launch_ready` + constitution modules
3. `GET /api/admin/launch-checklist` (admin) → review blocked items
4. `GET /api/oracle/accuracy/public` → proof_chain.verify ok
5. `GET /oracle/BTC?ux_mode=beginner&lang=ar` → must include `decision_sentence`, `persona_clarity`
6. `GET /oracle/BTC?ux_mode=pro&lang=en` → must include `net_edge_truth`, `opportunity_half_life`, `signal_registry`

## Required production env
- `SECRETS_MASTER_KEY` or `SECRETS_VAULT_KEY`
- `SESSION_TOKEN_PEPPER`
- `ADMIN_API_KEY` + `ADMIN_EMAILS`
- `APP_BASE_URL=https://...`
- Billing: Lemon (`LEMON_SQUEEZY_*`) **or** Stripe (`STRIPE_*` + webhook)
- Optional: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`

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
