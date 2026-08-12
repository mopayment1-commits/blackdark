# Secret Rotation Guide

**Finding:** `F-XFER-01` / ops transferability

| Secret | Generator | Steps | Notes |
|--------|-----------|-------|-------|
| Fernet master | `scripts/generate_launch_secrets.py` | Generate → store in platform secret manager → rolling restart | Re-encrypt user keys if format requires |
| Session pepper | same | Set new pepper → restart → users re-login | Invalidates cookies |
| Admin API key | `scripts/setup_admin.py` | Write 0600 file → update `ADMIN_API_KEY_FILE` | Revoke old key |
| Telegram bot token | `setup_telegram.py` | New BotFather token → private file | Update webhooks |
| Stripe | `scripts/setup_stripe.py` | Dashboard rotate → private file → webhook secret | Replay risk window |
| DB password | cloud console | Rotate role → update `DATABASE_URL` → recycle pools | |
| Redis | cloud console | Rotate → update `REDIS_URL` → restart workers | |

## Rules

1. Never commit secrets; never paste into chat logs.
2. Prefer pointer env vars (`*_FILE`) + mode 0600 files.
3. After rotation, confirm `/api/security/status` and `/api/production/guard`.
4. Record rotation in buyer change log (EXTERNAL process).
