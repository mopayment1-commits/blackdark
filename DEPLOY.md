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

| URL | Expected |
|-----|----------|
| `/health` | JSON `{"status":"ok"}` |
| `/` | Landing page |
| `/login` | Auth |
| `/dashboard` | Full dashboard |
| `/b2b` | B2B one-pager |
| `/oracle/BTC` | Live Oracle |

## Notes

- Docker build excludes local SQLite DB — fresh DB on first boot.
- Add a **Railway Volume** mounted at `/app/data` if you want persistent users/subscriptions.
- Aggregator runs in the same process as the web server (background task).

## Tiers

| Tier | Price | Features |
|------|-------|----------|
| Free | $0 | Oracle 10/day, Market Radar, Journal |
| Pro | $29/mo | Unlimited Oracle, Arbitrage, Chat, Alerts, Research |
| Whale | $199/mo | + Voice, B2B API |

New signups get **7-day Pro trial** automatically. Promo codes: `LAUNCHPRO`, `DARKSIDE`, `BLACKDARK`.
