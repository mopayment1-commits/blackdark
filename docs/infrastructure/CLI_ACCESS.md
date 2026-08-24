# CLI Access — Feature #167

Institution tier only. Thin wrapper around Unified REST API (#162).

## Install

```bash
pip install -e .
blackdark --version
```

## Commands (13)

| CLI | API |
|-----|-----|
| `blackdark price BTC` | `GET /api/platform/infra/prices/aggregate` |
| `blackdark alert list` | `GET /api/alerts/inbox` |
| `blackdark portfolio check ETH` | `GET /api/platform/cli/portfolio-check` |
| `blackdark market-health BTC` | `GET /api/platform/market-health/dashboard` |
| `blackdark confidence BTC` | `GET /api/platform/confidence/score` |
| `blackdark execution-quality ETH 5000` | `GET /api/platform/infra/execution-quality/score` |
| `blackdark macro BTC` | `GET /api/platform/macro/context` |
| `blackdark spread BTC` | `GET /api/platform/infra/spread/calculate` |
| `blackdark transfer USDT binance kraken 1000` | `GET /api/platform/transfer/optimizer` |
| `blackdark entity 0x... ethereum` | `GET /api/v1/entities/{address}` |
| `blackdark tx 0x... ethereum` | `GET /api/v1/transactions/{hash}` |
| `blackdark dd BTC one_page` | `GET /api/platform/research/dd-report` |
| `blackdark status` | `GET /api/platform/cli/status` |

## Auth

Set `BLACKDARK_TOKEN` (Bearer) or `BLACKDARK_API_KEY` (X-API-Key). Institution tier required for CLI status commands.

## Exit codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Auth / permission (401, 403) |
| 3 | Not found (404) |
| 4 | Usage / client error |
| 5 | Rate limit (429) |

## Acceptance

- CLI/API parity — every command maps 1:1 to REST
- Exit codes tested for HTTP errors
