# GDPR Compliance Layer (#58)

Infrastructure compliance — NOT standalone. Privacy by Design on data layer + auth + logging.

## Requirements

- Minimal PII: email, tier, usage, preferences only
- Right to erasure: 30-day workflow via `/user/delete` or `/api/privacy/dsr/erase`
- Data portability: JSON export via `/user/export` or `/api/privacy/dsr/export`
- Explicit consent logging: `/api/privacy/consent`
- EU auto-enable: Rule-Based country detection
- DPO: privacy@blackdark.io

## API

```
GET  /api/privacy/gdpr/status
POST /api/privacy/consent
POST /api/privacy/dsr/export
POST /api/privacy/dsr/erase
```

No wallet storage. No mandatory KYC on free tier.
