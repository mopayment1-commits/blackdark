# DEX Volume Feed — #235 (Sprint 1 Core Data)

On-chain DEX swap event volume with mandatory wash/noise policy and USD normalization.

Integrated into **#705 Asset Metadata** as a profile field. **Not** a standalone dashboard.

## Institutional Rules

| Rule | Implementation |
|------|----------------|
| Wash/noise policy | `$500 minimum trade size`, bot-filtered, heuristic + address clustering v1.2 |
| USD normalization | Hourly VWAP FX, stablecoin peg adjustment |
| Protocol breakdown | Uniswap v3, Curve, PancakeSwap, Balancer — no total without breakdown |
| Historical trend | 7D / 30D / 90D / YoY — not snapshot only |
| Chain separation | Ethereum, BSC, Arbitrum, Polygon as separate rows |
| Disclaimer | Non-hideable — methodology differences acknowledged |
| Methodology versioned | DEX Volume v2.1, Wash Policy v1.3 |
| No opportunity language | `DEX Volume (24H): $X \| Trend: ↑/↓` — neutral only |
| Fee DB (#130) | Mandatory when yield/farming context shown |
| #705 integration | Field in asset profile via `canonical_asset_registry._enrich_asset()` |
| Update frequency | Every 15 minutes, on-chain events, last block — no "instant" claims |

## APIs

| Endpoint | Description |
|----------|-------------|
| `GET /api/platform/dex-volume/status` | Module status |
| `GET /api/platform/connectors/assets/{symbol}/dex-volume` | Per-asset DEX volume block |

## Integration (#705)

`canonical_asset_registry._enrich_asset()` adds `dex_volume` to asset profiles:

```json
{
  "symbol": "ETH",
  "dex_volume": {
    "volume_display": "DEX Volume (24H): $2.84B | Trend: ↑",
    "wash_noise_policy": { "display": "Wash trades excluded: Yes | ..." },
    "protocol_breakdown": { "display": "Uniswap v3: 50% | ..." },
    "chain_breakdown": { "display": "Ethereum: $1.99B | ..." },
    "historical_trend": { "display": "7D: $18.2B | 30D: $78B | ..." }
  }
}
```

## Related

- `bd_platform/canonical_asset_registry.py` — #705 integration
- `bd_platform/defi_slippage_mapper.py` — related DeFi liquidity context (#228)
- `wash_trade_guard.py` — wash trade detection infrastructure
