# ETF Intelligence Module — #210 + #240 (Sprint 2, Pro)

Merged Spot ETF market data (#210) and ETF Flow Intelligence (#240) into one macro
context layer over Market Radar. Analysis only — NOT buy/sell recommendations.

## Architecture

```
Market Radar
     │
     ▼
┌─────────────────────────────┐
│   ETF Intelligence Module   │
│   (#210 + #240 merged)      │
├─────────────────────────────┤
│  Inputs:                    │
│  • Spot ETF flows (Farside) │
│  • AUM, Creation/Redemption │
│  • Crypto price + volume    │
├─────────────────────────────┤
│  Output: Flow Dashboard +   │
│  Market Context (no rec)    │
└─────────────────────────────┘
```

## Core Logic

| Component | Logic |
|-----------|-------|
| Normalize flows | Daily net = Creation − Redemption |
| Rolling totals | 7D / 30D / YTD sum of daily net flows |
| Missing days | Holidays/weekends marked — no interpolation |
| Timezone | ETF 16:00 EST close + 1H lag vs crypto UTC |
| Regime | Inflow-Driven / Price-Driven / Divergent |
| Triangle | AUM + Daily Flow + Price Change + interpretation |

## APIs

| Endpoint | Description |
|----------|-------------|
| `GET /api/platform/market-radar/etf-intelligence/status` | Module status |
| `GET /api/platform/market-radar/etf-intelligence/dashboard` | Unified dashboard |
| `GET /api/platform/market-radar/etf-intelligence/flows` | Daily flow series |
| `GET /api/platform/market-radar/etf-intelligence/market-context` | Correlation + regime |

## Acceptance Criteria

| Criterion | Implementation |
|-----------|----------------|
| Official source mapping | Farside + verified URL + last verified date |
| Timezone alignment | EST close + 1H lag documented |
| Missing-day handling | Holiday display, no interpolation |
| Rolling totals methodology | Sum of daily net flows documented |
| Market context | 30D correlation + regime classification |
| AUM + Flow + Price triangle | Never show flow alone |
| Disclaimer non-hideable | Top + bottom, no collapse |
| Not recommendation | Context language only |
| Merged #210 + #240 | Single module, not standalone |

## Integration

- `bd_platform/etf_intelligence.py` — core engine
- `bd_platform/market_radar_dashboard.py` — `etf_intelligence` block
- `data/etf_intelligence_seed.json` — versioned flows + prices
