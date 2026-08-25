# Global Liquidity Intelligence — #248 (Sprint 2, Pro/Institution)

Estimates global liquidity environment and historical relationship with crypto assets.
Macro context only — NOT predictions, opportunities, or buy signals.

## Architecture

```
Market Radar
     │
     ▼
┌─────────────────────────────┐
│ Global Liquidity Intelligence│
│   (Module v2.1)             │
├─────────────────────────────┤
│  Inputs:                    │
│  • Fed/ECB/BoJ M2           │
│  • Global policy rates        │
│  • DXY                      │
├─────────────────────────────┤
│  Output: Regime + Index +   │
│  Historical relationship    │
└─────────────────────────────┘
```

## Composite Index (v1.2)

| Component | Weight |
|-----------|--------|
| Fed M2 | 30% |
| ECB M2 | 25% |
| BoJ M2 | 20% |
| Global Policy Rate Average | 15% |
| DXY | 10% |

## Lag Methodology

| Series | Lag |
|--------|-----|
| M2 (Fed) | 14-day lag |
| M2 (ECB) | 30-day lag |
| M2 (BoJ) | 45-day lag |
| Policy Rate | same-day |
| FX (DXY) | hourly |

## APIs

| Endpoint | Description |
|----------|-------------|
| `GET /api/platform/market-radar/global-liquidity/status` | Module status |
| `GET /api/platform/market-radar/global-liquidity/dashboard` | Full dashboard |
| `GET /api/platform/market-radar/global-liquidity/regime` | Liquidity regime |
| `GET /api/platform/market-radar/global-liquidity/index` | Composite index |

## Acceptance Criteria

| Criterion | Implementation |
|-----------|----------------|
| Source/lag documented | Per-series lag display |
| Revisions tracked | Initial + revision trail |
| No fabricated real-time | Latest available + as-of dates |
| Composite documented | Weighted components v1.2 |
| Historical ≠ prediction | Correlation with regime note |
| Regime descriptive | Tightening/Neutral/Easing |
| Disclaimer non-hideable | Top + bottom |
| Batch updates only | Daily/Monthly/Quarterly |
| Version per data point | Index version + calculation date |

## Integration

- `bd_platform/global_liquidity_intelligence.py` — core engine
- `bd_platform/market_radar_dashboard.py` — `global_liquidity` block
- `data/global_liquidity_seed.json` — series, revisions, weights
