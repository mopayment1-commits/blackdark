# Monetization Tiers Core — Feature #126

## Role

**Non-negotiable commercial foundation** — not a marketing page, the business model SSOT.

## 3 Tiers

| Tier | Price | Oracle | Market Radar | Alerts | Extras |
|------|-------|--------|--------------|--------|--------|
| **Free** | $0 | 3/day | 15-min delay | 3 basic | Journal |
| **Pro** | $29/mo | Unlimited | Real-time | 10 | Portfolio AI, 7-day trial |
| **Institution** | $199/mo | Unlimited | Real-time | Unlimited | API, On-Chain, White Label, support |

## Golden rule

Free tier is **useful but limited** — never disabled, never useless.

## A/B testing

| Variant | Pro | Institution |
|---------|-----|-------------|
| A (default) | $29 | $199 |
| B | $24.99 | $179 |

Assignment: deterministic hash of `user_id` / `email`.  
Override: `MONETIZATION_AB_VARIANT=A|B`

## Stripe integration

- Pro → `STRIPE_PRICE_PRO` / `/create-checkout-session?tier=pro`
- Institution → maps to Elite canonical plan / `STRIPE_PRICE_ELITE`

## API

| Endpoint | Description |
|----------|-------------|
| `GET /api/platform/billing/monetization-tiers` | Full catalog |
| `GET /api/platform/billing/monetization-status` | Engine status |
| `GET /api/platform/billing/entitlements?tier=pro` | Tier entitlements |

## Canonical mapping

```
free        → free
pro         → pro
institution → elite (entitlements bundle)
```
