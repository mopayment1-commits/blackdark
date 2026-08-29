# Subscription Tier Policy (#60)

Extension of existing Stripe tiered keys — NOT a new billing system.

## Tiers

| Tier | API calls/day | Features |
|------|---------------|----------|
| Free | 10 | Market Radar basic, Portfolio AI limited |
| Pro | 500 | Intelligence Ledger, Signal Engine, Alerts |
| Institutional | 10,000 | On-Chain, Custom Reports |

## Policy

- Recurring subscriptions only (monthly/annual) — no lifetime access
- 7-day Pro trial logged as CAC in Fee DB
- Transparent limits on `/pricing` page
- Rate limits = verification tool, not technical restriction

## API

```
GET /api/platform/legal/tiers/limits?tier=free
```
