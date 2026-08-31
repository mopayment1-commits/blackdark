# Token Incentives & Emissions — #298 (Wave 2 / Sprint 2)

Niche Intelligence Ledger module measuring DeFi protocol incentive and emission USD values.

## Scope Lock

| Phase | Scope |
|-------|-------|
| 1 (Wave 2) | DeFi protocols only |
| 2 | CEX incentives |
| 3 | Airdrops |

Emissions source: on-chain query or protocol docs.

## Price Alignment

| Rule | Implementation |
|------|----------------|
| USD at emission timestamp | `emission_amount × price_at_emission_timestamp_usd` |
| No current price | `no_current_price: true` on every record |
| Price/time alignment | Emission timestamp + price paired |

## APIs

| Endpoint | Description |
|----------|-------------|
| `GET /api/platform/intelligence-ledger/token-incentives/status` | Module status |
| `GET /api/platform/intelligence-ledger/token-incentives` | Protocol incentives panel |
| `GET /api/platform/intelligence-ledger/token-incentives/emissions` | Emission records |
