# Legal Framework (#1018 + merged #1068)

**Cross-cutting compliance** — Terms of Service · Privacy Policy · production gate.

## Merged feature

#1068 (lawyer-reviewed ToS/Privacy) is fully merged into this framework — no separate module.

## Requirements

- Lawyer review (fintech/crypto) before production deployment
- ToS: analytical tool · not financial advice · no buy/sell recommendation · no return guarantee
- Privacy: limited collection · no private keys · GDPR/CCPA deletion on request
- User consent checkbox logged immutably at registration
- Forbidden language scan on all user-facing text

## Forbidden terms (automated scan)

`guaranteed` · `مضمون` · `ربح مضمون` · `استغلال` · `مؤكد` — and similar certainty claims.

## API

```
GET  /api/platform/trust/legal/status
POST /api/platform/trust/legal/scan
GET  /api/platform/trust/legal/e2e
```

## Sprint 0 priority

Blocks production without signed legal docs. Localization: Arabic + English (both legally binding).

## Integrations

#921 AI Provenance footer · #11 Signal Engine disclaimers · #908 Billing tiers · #907 Read-only sync · #1017 Incident Response · #949 Retention
