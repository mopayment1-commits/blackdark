# BLACKDARK Launch Guide (English)

## A) Railway Deploy — step by step

1. **Push to GitHub**
   - Create repo `blackdark` on GitHub
   - Push this folder to `main`

2. **Create Railway project**
   - Go to [railway.app](https://railway.app) → **New Project** → **Deploy from GitHub**
   - Select your `blackdark` repo

3. **Generate domain**
   - Railway → your service → **Settings** → **Networking** → **Generate Domain**
   - Copy URL (e.g. `blackdark-production.up.railway.app`)

4. **Set variables**
   - Run locally: **`setup_railway.bat`**
   - Paste output into Railway → **Variables** → **Raw Editor**
   - Replace `YOUR-DOMAIN` with your Railway domain

5. **Deploy**
   - Railway auto-deploys on push
   - Check **Deployments** → logs should show `Uvicorn running`
   - Open `https://YOUR-DOMAIN/` and `/dashboard`

6. **Verify**
   ```bash
   python scripts/launch_verify.py https://YOUR-DOMAIN
   ```

---

## B) Stripe Setup

1. [Stripe Dashboard](https://dashboard.stripe.com) → **Developers** → **API keys**
2. Copy **Secret key** (`sk_live_...` or `sk_test_...` for testing)
3. Run **`setup_stripe.bat`** and paste keys
4. **Webhooks** → Add endpoint:
   - URL: `https://YOUR-DOMAIN/webhook`
   - Event: `checkout.session.completed`
   - Copy **Signing secret** → `STRIPE_WEBHOOK_SECRET`
5. (Optional) Create Products → copy Price IDs → `STRIPE_PRICE_PRO`, `STRIPE_PRICE_WHALE`
6. Test: Register at `/login` → click **Pro $29/mo** on dashboard

---

## C) Telegram Bot

1. Telegram → **@BotFather** → `/newbot` → copy token
2. Run **`setup_telegram.bat`** → paste token
3. Open your bot link → send **`/start`**
4. Restart server → Dashboard → **Test Telegram**
5. For production webhook (optional):
   - Set `TELEGRAM_WEBHOOK_URL=https://YOUR-DOMAIN/api/telegram/webhook`
   - Set `TELEGRAM_POLLING_ENABLED=false`

---

## D) Dashboard (user product)

Public URLs only:
- `/` — Landing
- `/dashboard` — Oracle, chart, market, arb, whales
- `/platform` — Advanced tools
- `/login` — Register / billing

No developer pages on the web.

---

## Quick local scripts

| Script | Purpose |
|--------|---------|
| `start_blackdark.bat` | Start server locally |
| `setup_railway.bat` | Generate Railway env block |
| `setup_stripe.bat` | Stripe keys in `.env` |
| `setup_telegram.bat` | Telegram bot in `.env` |
| `launch_verify.bat` | Pre-launch HTTP checks |
