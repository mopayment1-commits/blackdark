# AML Compliance Layer (#59)

Merged into Stripe integration — NOT standalone. Triggered on direct financial transactions only.

## Rule-Based triggers

- Transaction > $500 USD
- Suspicious pattern score ≥ 0.75
- Sanctions list hit (OFAC/UN/EU screening)

## Policy

- No KYC on free tier
- AML starts at first payment
- SAR workflow internal only — user not notified
- Records retained 5 years

## API

```
POST /api/platform/legal/aml/evaluate  (admin)
GET  /api/platform/legal/commercial/status
```

Scope: Stripe subscription only — no on-chain, no custody.
