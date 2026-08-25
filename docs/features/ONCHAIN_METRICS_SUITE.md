# On-Chain Metrics Suite — #745 MDIA + #750 Realized Cap (merged)

**NOT standalone** — merged into On-Chain Metrics Suite (Sprint 2 — On-Chain Intelligence).

## #750 — Realized Cap Model

Competitor reference: Glassnode Realized Cap.

| Rule | Implementation |
|------|----------------|
| True network value | Realized Cap + Realized Price + Market Cap |
| Methodology documented | SMA200 cost-basis proxy when UTXO data unavailable |
| Alerts | MVRV Z-Score overheated/undervalued zones |

## #745 — Mean Dollar Invested Age (MDIA)

Competitor reference: Glassnode Mean Dollar Invested Age.

| Rule | Implementation |
|------|----------------|
| Valuation methodology | `MDIA = Σ(coin_age_days × usd_at_last_move) / Σ(usd_at_last_move)` |
| Time alignment | Daily snapshot at 00:00 UTC, aligned with realized_cap/mvrv/hodl_waves |
| Chain coverage explicit | Per-asset: `utxo_native` / `account_proxy` / `supported: false` |
| Output | MDIA trend + regime (mature/neutral/young) |

## APIs

| Endpoint | Description |
|----------|-------------|
| `GET /api/platform/onchain/metrics-suite/status` | Suite status |
| `GET /api/platform/onchain/metrics-suite` | Full suite (realized cap + MDIA + MVRV + alerts) |
| `GET /api/platform/onchain/metrics-suite/realized-cap` | Realized Cap Model (#750) |
| `GET /api/platform/onchain/metrics-suite/mdia` | Mean Dollar Invested Age (#745) |
| `GET /api/platform/onchain/metrics-suite/methodology` | Methodology + competitor references |

## Related

- `bd_platform/onchain_advanced.py` — MVRV, NUPL, SOPR proxies
- `bd_platform/mvrv_realignment.py` — regime detection + alerts
- `bd_platform/free_tier_capabilities.py` — legacy `realized_cap_metrics`
