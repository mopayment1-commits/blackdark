# USD Payments & Financial Data Security (Binding)

**Currency:** USD only for Trust OS self-serve SKUs.  
**Principle:** BLACKDARK never stores card PAN, CVV, or retail full bank account numbers.

## Architecture

```
Browser → Hosted Checkout (Lemon Squeezy MoR or Stripe)
       → 3-D Secure / SCA when required by PSP
       → PSP token vault (outside our PCI scope)
       → Signed webhook → our API
       → DB: email, tier, status, provider ids only
       → PSP payout → operator bank account (USD)
```

**PCI target:** SAQ A (hosted payment page / redirect).  
**Not in scope for us:** PCI Level 1 merchant processing on our hosts.

## Self-serve SKUs (USD)

| SKU | Tier | Price | Trial |
|-----|------|-------|-------|
| Decision Pro | `pro` | $29/mo | 7 days |
| Whale Desk | `whale` | $199/mo | — |

Institutional (from $3,000/mo USD): invoice + wire — `POST /api/billing/institutional-inquiry` / Data Room. Not a Checkout SKU.

## Providers

1. **Lemon Squeezy** (launch default / Merchant of Record)  
   - `LEMON_SQUEEZY_CHECKOUT_PRO`  
   - `LEMON_SQUEEZY_CHECKOUT_WHALE`  
   - `LEMON_SQUEEZY_WEBHOOK_SECRET` → `POST /webhook/lemon`  
   - Optional: `LEMON_SQUEEZY_CUSTOMER_PORTAL_URL`

2. **Stripe Billing** (control path when entity ready)  
   - `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET` → `POST /webhook`  
   - `STRIPE_PRICE_PRO`, `STRIPE_PRICE_WHALE` (USD recurring)  
   - Customer Portal via `POST /api/billing/portal`

## Payment methods (launch)

- Card (Visa / Mastercard, etc.) — USD  
- Apple Pay / Google Pay — via PSP Checkout wallets when domain verified  

Deferred: SEPA/ACH volume rails, local schemes, crypto.

## Bank payout (operator)

Customer pays the PSP → PSP fees/tax → **Payout to your linked USD bank account** after KYC in the PSP dashboard. This is unrelated to storing customer card data.

## Security controls (implemented)

| Control | Implementation |
|---------|----------------|
| No PAN/CVV in app | Hosted Checkout only |
| Webhook auth | Stripe signature / Lemon HMAC |
| Idempotency | `billing_webhook_events` unique (provider, event_id) |
| Dunning | `invoice.payment_failed` / Lemon payment_failed → `past_due` + grace |
| Portal | Stripe Billing Portal or Lemon portal URL |
| Refunds | Policy at `/refund` + `/api/billing/refund-policy` |
| Secrets | Env only — never commit live keys |
| Logs | Do not log raw card payloads or full webhook secrets |

## Public APIs

- `GET /api/billing/payments` — architecture + readiness (no secrets)  
- `GET /api/billing/refund-policy`  
- `POST /api/billing/checkout` `{ "tier": "pro"|"whale" }`  
- `POST /api/billing/portal`  
- `POST /api/billing/institutional-inquiry`  
- `GET /api/billing/status`

## Ops checklist

```bash
python scripts/setup_payments_usd.py
```

Before campaign: Pro + Whale USD checkouts live, webhook secrets set, test purchase, confirm payout bank linked, Whale Lemon URL present.

## Honesty

We sell reviewable decision access — not guaranteed returns. Subscription fees are USD software access fees.
