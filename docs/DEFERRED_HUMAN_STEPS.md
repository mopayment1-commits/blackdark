# Deferred — requires human decision (do not block product)

> Owner: product/founder  
> Agent rule: **do not ask again until explicitly unblocked**  
> Related: [`CANONICAL_BINDING.md`](./CANONICAL_BINDING.md) · [`REPORT_INVENTORY_STATUS.md`](./REPORT_INVENTORY_STATUS.md)

| ID | Item | Why deferred | Unblock condition |
|----|------|--------------|-------------------|
| H1 | Browser Extension (OQS overlay) | Built in PR #4 (`browser_extension/`) | Merge PR #4 + Load unpacked |
| H2 | Glass Box Challenge launch timing + channel | LAUNCH_ONLY narrative | Choose event clock + post drafts from `GET /api/glass-box/announce-drafts` (competitor challenge is product-ready) |
| Prod | Strict production Postgres | Soft Launch may use SQLite | Before institutional pitch: `DATABASE_URL=postgresql://…` and unset `SOFT_LAUNCH` — guard enforces `sqlite_forbidden_in_strict_production` |
| H3 | 60-second value confirm (human) | Needs founder cold walkthrough | Founder opens live URL cold; machine probe is `GET /api/acceptance/60s` |
| HA | Signed HA capacity claim | Needs Postgres+Redis multi-worker staging | Fill a real row in [`LOAD_TEST_RUN_LOG.md`](./LOAD_TEST_RUN_LOG.md) |
| Ops | Railway trial ended · Stripe/Telegram optional | Railway cannot redeploy free | **Free path:** merge Render Blueprint — [`RENDER_FREE_AR.md`](./RENDER_FREE_AR.md) |

## Announce copy (ready — human posts)

```bash
curl -s "$BASE/api/glass-box/announce-drafts" | jq .
```

## 60s machine probe (does not replace H3)

```bash
python scripts/acceptance_60s.py --base http://127.0.0.1:8080
# or: curl -s "$BASE/api/acceptance/60s?base_url=$BASE"
```

Old Railway URL may be stale: `https://blackdark-production.up.railway.app/`  
Free Render steps: [`RENDER_FREE_AR.md`](./RENDER_FREE_AR.md)

Everything else is treated as **product-complete in code** under the canonical hierarchy. See [`PRODUCT_COMPLETE_STATUS.md`](./PRODUCT_COMPLETE_STATUS.md) · [`CANONICAL_BINDING.md`](./CANONICAL_BINDING.md).
