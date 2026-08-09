# Deploy BLACKDARK to Railway

## Quick deploy (5 minutes)

1. Push this repo to GitHub (`main` branch)
2. [Railway](https://railway.app) → **New Project** → **Deploy from GitHub** → select `blackdark`
3. **Settings → Networking → Generate Domain** (e.g. `blackdark-production.up.railway.app`)
4. **Variables** — paste the block below (replace `YOUR-DOMAIN`)
5. **Settings → Deploy** → Redeploy if needed
6. Open `https://YOUR-DOMAIN/` — Landing, `/login`, `/dashboard`, `/b2b` should work

## Required environment variables

```env
PORT=8080
RUN_AGGREGATOR=true
MANIFEST_AUTO_APPROVE=true
MANIFEST_REQUIRE_REVIEW=false
PRO_TRIAL_DAYS=7
AUTH_SESSION_DAYS=30
MARKET_RADAR_LIMIT=25

STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_SUCCESS_URL=https://YOUR-DOMAIN/success?session_id={CHECKOUT_SESSION_ID}
STRIPE_CANCEL_URL=https://YOUR-DOMAIN/cancel

BLACKDARK_B2B_DEMO_KEY=bd_demo_launch_2026
BLACKDARK_B2B_API_KEY=your_production_b2b_key
```

## Optional

| Variable | Purpose |
|----------|---------|
| `TELEGRAM_BOT_TOKEN` | Telegram arbitrage alerts |
| `TELEGRAM_CHAT_ID` | Alert destination |
| `TELEGRAM_ALERTS_ENABLED` | `true` |
| `SMTP_*` | Email alerts |
| `OPENAI_API_KEY` | AI Chat (falls back to rules if empty) |
| `COINMARKETCAP_API_KEY` | Liquidity discovery |

## Stripe webhook

In Stripe Dashboard → Webhooks → Add endpoint:

- URL: `https://YOUR-DOMAIN/webhook`
- Events: `checkout.session.completed`

Copy signing secret → `STRIPE_WEBHOOK_SECRET`

## Health checks

| URL | Expected | Use |
|-----|----------|-----|
| `:8180/health/live` | JSON `{"status":"ok","sidecar":true}` | **Docker/K8s liveness** (<10ms) |
| `/health/ready` | DB + Redis stats | Load balancer readiness |
| `/health` | Basic JSON | Legacy |
| `/api/services/status` | Microservices + bus | Buyer due diligence |

Sidecar port = app port + 100 (8080 → 8180). Started automatically by `run_service.py`.

Quick verify (local):
```bash
python scripts/verify_buyer.py http://127.0.0.1:8080
```

## Docker Compose (microservices + PostgreSQL)

Requires [Docker Desktop](https://www.docker.com/products/docker-desktop/) on Windows.

```bash
docker compose up -d --scale web=2 --scale arbitrage=2
```

- **PostgreSQL** activates when `DATABASE_URL=postgresql://...` is set (default in compose).
- **Redis** required for cross-service pub/sub (local fallback if absent).
- Without Docker locally: `.\scripts\start_microservices.ps1`

## Railway scale-out (1M users path)

1. Add **Redis** + **PostgreSQL** plugins in Railway
2. Create 4 services from same repo with `SERVICE_MODE=web|aggregator|arbitrage|ingestion`
3. Set `DATABASE_URL`, `REDIS_URL`, `HEALTH_PORT` per service
4. Health probe: `/health/live` on sidecar port (see `railway.toml`)
5. Scale replicas: web=2+, arbitrage=3+ (see `deploy/k8s/` for K8s HPA example)

## Tiers

| Tier | Price | Features |
|------|-------|----------|
| Free | $0 | Oracle 10/day, Market Radar, Journal |
| Pro | $29/mo | Unlimited Oracle, Arbitrage, Chat, Alerts, Research |
| Decision Desk | $49/mo | + Voice, B2B API |

New signups get **7-day Pro trial** automatically. Promo codes: `LAUNCHPRO`, `DARKSIDE`, `BLACKDARK`.
