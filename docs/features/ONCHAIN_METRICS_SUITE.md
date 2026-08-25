# On-Chain Metrics Suite — #750 Realized Cap Model (merged)

**NOT standalone** — merged into On-Chain Metrics Suite (Sprint 2 — On-Chain Intelligence).

Competitor reference: Glassnode Realized Cap.

## Institutional Rules

| Rule | Implementation |
|------|----------------|
| Not standalone | `standalone: false`, merged into suite |
| True network value | Realized Cap + Realized Price + Market Cap |
| Methodology documented | SMA200 cost-basis proxy when UTXO data unavailable |
| Source metadata | Binance klines, CoinGecko supply |
| Alerts | MVRV Z-Score overheated/undervalued zones |
| SLA | Response ≤2s, accuracy ≥95%, uptime 99% targets |

## Display

`Realized Cap: $990.0B | Realized Price: $50,000 | Market Cap: $1.98T`

## APIs

| Endpoint | Description |
|----------|-------------|
| `GET /api/platform/onchain/metrics-suite/status` | Suite status |
| `GET /api/platform/onchain/metrics-suite` | Full suite (realized cap + MVRV + NUPL + alerts) |
| `GET /api/platform/onchain/metrics-suite/realized-cap` | Realized Cap Model (#750) |
| `GET /api/platform/onchain/metrics-suite/methodology` | Methodology + Glassnode reference |

## Related

- `bd_platform/onchain_advanced.py` — MVRV, NUPL, SOPR proxies
- `bd_platform/mvrv_realignment.py` — regime detection + alerts
- `bd_platform/free_tier_capabilities.py` — legacy `realized_cap_metrics`
