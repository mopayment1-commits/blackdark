# On-Chain Intelligence API — Feature #164

Module within Unified API (#162). **Read-only** — no separate API surface.

## Endpoints

| Endpoint | Auth | Description |
|----------|------|-------------|
| `GET /api/v1/entities/{address}` | Pro+ | Entity intelligence (schema parity with UI #10) |
| `GET /api/v1/transactions/{hash}` | Pro+ | Transaction decoder (schema parity with UI) |

## Schema parity

API responses mirror `address_intelligence` UI fields:
- `entity_label`, `total_usd`, `balance`, `labels`, `clusters`, `arkham_entity`
- `chain`, `chain_id`, `data_state`, `sla_met`

## Rate limits

- 120 requests / 60 seconds per authenticated user

## Acceptance criteria

| Criterion | Target |
|-----------|--------|
| Auth | Pro tier or above |
| Rate limits | Enforced per user |
| Schema parity | Matches UI address intelligence |
| Write ops | None (read-only) |
