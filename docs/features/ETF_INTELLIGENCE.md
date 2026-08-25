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
| `GET /api/platform/market-radar/etf-intelligence/etp-data` | ETF/ETP market data (#210) |

## Acceptance Criteria

| Criterion | Implementation |
|-----------|----------------|
| Official source mapping | Issuer Filing \| SEC \| Bloomberg — mandatory attribution |
| Crypto linkage visible | BTC exposure % \| ETH % \| Other % per product |
| AUM + flows + premium/discount | Normalized per ETP product + aggregate |
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

## Disclaimer

> ETP data based on issuer disclosures. NAV may differ from market price. ETF flow correlation with crypto prices is historical, not predictive. Not investment advice.
