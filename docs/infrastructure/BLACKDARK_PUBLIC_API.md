# BLACKDARK API — Features #162 + #183

Unified API Platform product: **BLACKDARK API**

## Endpoints (read-only)

| Endpoint | Description |
|----------|-------------|
| `GET /api/v1/blackdark/status` | API platform status |
| `GET /api/v1/blackdark/price/{asset}` | Aggregated price + freshness |
| `GET /api/v1/blackdark/market-health/{asset}` | Market health pillars |
| `GET /api/v1/blackdark/risk-score/{asset}` | Risk/confidence score |

## Auth & rate limits

- Header: `X-API-Key`
- Tiers: free (30/min), pro (300/min), institutional (3000/min)
- Env keys: `BLACKDARK_PUBLIC_API_KEY`, `BLACKDARK_PRO_API_KEY`, `BLACKDARK_INSTITUTION_API_KEY`

## Null semantics

Missing values returned as `null` — no synthetic defaults for failed fetches.

## Contract tests

See `tests/test_blackdark_public_api.py` — schema contracts validated per endpoint.
