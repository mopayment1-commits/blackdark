# Cryptographic Timestamping Layer (#1066)

**Cross-cutting cryptographic foundation** — NOT standalone UI. Serves #931 · #952 · #1065 · #1029.

## Guarantee

Every prediction is hashed (SHA-256) + timestamped (UTC) + platform-signed **before** publication. Pre-event guarantee: timestamp < outcome time.

## Components

1. Per-prediction hash + signature
2. Hourly Merkle batching — root published publicly
3. Third-party anchoring — external timestamp authority / blockchain anchor tx
4. Public verification API — no authentication required

## API

```
GET /api/platform/trust/timestamping/status
GET /api/platform/trust/timestamping/verify?prediction_hash=...&timestamped_at=...&platform_signature=...
GET /api/platform/trust/timestamping/e2e
```

## Storage

- `data/crypto_timestamping/predictions.jsonl`
- `data/crypto_timestamping/merkle_roots.jsonl`

## Legal defense

Verifiable proof against hindsight-bias allegations — "we published this before the event."
