# Macro Intelligence Hub — #263 (Sprint 2, Pro/Institution)

Integration dashboard aggregating macro modules into one institutional macro view.
NOT standalone — layers over existing macro intelligence modules.

## Integrated Modules

| Feature | Module |
|---------|--------|
| #248 | Global Liquidity Intelligence |
| #211 | Economic Calendar |
| #244 | Fed M2 Macro Flow (via #248) |
| #210/#240 | ETF Intelligence |
| #233/#255 | Premium Intelligence |
| #239 | Treasury Companies (planned) |

## Architecture

```
Macro Intelligence Hub (#263)
        │
        ├── Global Liquidity (#248)
        ├── Economic Calendar (#211)
        ├── Fed M2 Macro Flow (#244)
        ├── ETF Intelligence (#210/#240)
        ├── Premium Intelligence (#233/#255)
        └── Treasury Companies (#239, planned)
```

## APIs

| Endpoint | Description |
|----------|-------------|
| `GET /api/platform/market-radar/macro-hub/status` | Hub status |
| `GET /api/platform/market-radar/macro-hub/dashboard` | Integration dashboard |
| `GET /api/platform/market-radar/macro-hub/coupling` | Crypto coupling context |

## Tier Features

| Tier | Features |
|------|----------|
| Free | Summary headline only |
| Pro | Correlation tables + source calendar |
| Enterprise | Regime analysis + anomaly detection + custom factors |

## Acceptance Criteria

| Criterion | Implementation |
|-----------|----------------|
| Not standalone | Integration layer over 7 modules |
| Release-time alignment | Minute-level DXY/crypto alignment |
| No look-ahead | Data ≤ calculation date T only |
| Source calendar | Upcoming releases with impact |
| Rolling correlation | 30D/90D/1Y windows |
| Regime documented | Past performance ≠ future |
| No causation language | Coupling descriptive only |
| Disclaimer non-hideable | Top + bottom |

## Integration

- `bd_platform/macro_intelligence_hub.py` — hub engine
- `bd_platform/market_radar_dashboard.py` — `macro_intelligence_hub` block
