# Payment Security Policy (#61)

Stripe covers PCI-DSS Level 1 — NOT a new payment gateway.

## Policy

- No card data on BLACKDARK servers (PAN/CVV/expiry forbidden)
- Stripe-hosted Elements / Checkout only
- Webhook signature verification required
- Idempotency keys on every payment intent
- Test Mode before Live Mode

PCI: SAQ A via Stripe Checkout — Stripe is card data handler.

## API

```
GET /api/platform/legal/commercial/status
```

Fee DB logs Stripe fees (2.9% + $0.30) per transaction.
