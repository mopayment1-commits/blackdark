# Futures Volume Intelligence — #246 (Sprint 1 Core Data)

Futures volume with validated contract/unit mapping, disclosed venue coverage,
notional USD mapping, OI context, and perpetual vs delivery separation.

Replaces **#245** (incomplete data dump). Integrated into **#705 Asset Metadata**
with dashboard + trend surface.

## Institutional Rules

| Rule | Implementation |
|------|----------------|
| Contract/unit mapping | Validated per contract — size, unit, notional, venue |
| Venue coverage | Binance, Bybit, OKX, CME, BitMEX + excluded venues disclosed |
| Notional mapping | Contract size × Price × Volume — not contracts only |
| Spot vs Futures | Separate volumes + Futures/Spot ratio |
| OI context | Volume + OI + OI Change + Funding |
| Perpetual vs Delivery | Perpetual, Quarterly, Monthly as separate rows |
| Disclaimer | Non-hideable — exchange-reported estimates |
| No opportunity language | `Futures Volume (24H): $X \| Trend: ↑ \| OI: $Y` — neutral only |
| Fee DB (#130) | Mandatory for funding arbitrage / basis trade context |
| Methodology versioned | Futures Volume v1.2, 15 venues |
| Dashboard + trend | 7D / 30D / trend % / venue leader |
| Update frequency | Every 5 minutes, Exchange APIs |

## APIs

| Endpoint | Description |
|----------|-------------|
| `GET /api/platform/futures-volume/status` | Module status |
| `GET /api/platform/futures-volume/dashboard` | Aggregated dashboard + trend |
| `GET /api/platform/connectors/assets/{symbol}/futures-volume` | Per-asset futures volume block |

## Integration (#705)

`canonical_asset_registry._enrich_asset()` adds `futures_volume` to asset profiles.

## Related

- `bd_platform/dex_volume_feed.py` — #235 DEX volume (spot on-chain)
- `bd_platform/derivatives_hub.py` — derivatives data hub
- `bd_platform/free_market_data.py` — Binance futures snapshot fallback
