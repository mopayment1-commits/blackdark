# Taker Pressure Module — #296 (Sprint 2 Intelligence Ledger)

Sub-feature of **Orderflow analytics**. Measures aggressive buy/sell pressure from taker-side trade classification.

## Scope Lock

| Market | Included |
|--------|----------|
| CEX spot | Yes |
| CEX perp | Yes |
| DEX | No — separate (no taker concept) |

## Classification

| Criterion | Implementation |
|-----------|----------------|
| Taker definition | Aggressor side |
| Validation | Tested against exchange official CVD |
| Min accuracy | > 95% |
| Venue coverage | Documented (not all venues provide trade side) |

## Output

- Taker buy/sell volume and ratio
- Rolling imbalance (60-min default)
- Pressure state: `buy_pressure` | `sell_pressure` | `neutral`

## APIs (Intelligence Ledger)

| Endpoint | Description |
|----------|-------------|
| `GET /api/platform/intelligence-ledger/taker-pressure/status` | Module status |
| `GET /api/platform/intelligence-ledger/taker-pressure` | Pressure panel per asset |
| `GET /api/platform/intelligence-ledger/taker-pressure/classification-tests` | CVD accuracy tests |

## Disclaimer

Not investment advice. Not trade signals. DEX excluded.
