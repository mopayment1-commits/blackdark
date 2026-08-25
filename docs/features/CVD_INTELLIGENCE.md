# CVD Intelligence — #232 (Sprint 2, Pro)

Cumulative Volume Delta from aggressive (taker) buy vs sell volume.
Includes **#264 Maker/Taker Volume Net Delta** merged as alternative classification.
Technical context layer over Market Radar — NOT buy/sell signals.

## #264 Merge Decision

**#264 is NOT standalone** — merged into #232 CVD Module.

| Aspect | #232 CVD | #264 (merged) |
|--------|----------|---------------|
| Classification | Aggressive/Passive (default) | Maker/Taker (alternative) |
| Calculation | Taker buy - Taker sell | Same net delta, different labels |
| Alerts | Divergence context only | Same alert framework — no separate alerts |
| Scope | Multi-venue + divergence + coverage | Subset of #232 |

## Classification Modes

```
CVD Components: Aggressive/Passive (default) | Maker/Taker (alternative classification) | Venue: X | Method: v1.2
```

| Mode | Mapping |
|------|---------|
| Aggressive Buy | Taker Buy (market buy) |
| Aggressive Sell | Taker Sell (market sell) |
| Passive Buy | Maker Buy (limit order filled) |
| Passive Sell | Maker Sell (limit order filled) |

Net Delta = Buy Volume - Sell Volume classified by execution type.

## Architecture

```
Market Radar / Signal Context Layer
        │
        ▼
┌─────────────────────────────┐
│     CVD Intelligence        │
│   (Methodology v1.2)        │
├─────────────────────────────┤
│  Inputs:                    │
│  • Aggressive buy volume    │
│  • Aggressive sell volume   │
│  • Multi-venue taker trades │
├─────────────────────────────┤
│  Output: CVD chart +        │
│  divergence context         │
└─────────────────────────────┘
```

## Classification

| Side | Definition |
|------|------------|
| Aggressive Buy | market buy (taker buy) |
| Aggressive Sell | market sell (taker sell) |

Tested on 10,000+ trades against exchange API ground truth.

## APIs

| Endpoint | Description |
|----------|-------------|
| `GET /api/platform/market-radar/cvd/status` | Module status |
| `GET /api/platform/market-radar/cvd/analysis` | CVD analysis panel (`classification_mode=aggressive_passive\|maker_taker`) |
| `GET /api/platform/market-radar/cvd/chart` | CVD chart with gap markers |

## Output Format

- CVD Value: +X million USD
- Trend: Rising / Flat / Falling
- Divergence: None / Bullish / Bearish
- Confidence: X%
- Coverage: Y/5 exchanges
- Disclaimer (non-hideable)

## Acceptance Criteria

| Criterion | Implementation |
|-----------|----------------|
| Trade-side classification tested | 12,500 trades, accuracy displayed |
| Gap handling | Dashed interpolation, coverage shown |
| Divergence alerts | Context only, not sell signal |
| Multi-venue aggregation | Volume-weighted across 5 exchanges |
| Disclaimer non-hideable | Top + bottom |
| Version documented | CVD Methodology v1.2 |
| Historical validation | 6-month precision transparency |
| #264 merged | Maker/Taker alternative classification, no standalone |
| No separate #264 alerts | Uses CVD divergence alert framework |

## Integration

- `bd_platform/cvd_intelligence.py` — core engine
- `bd_platform/market_radar_dashboard.py` — `cvd_intelligence` block
- `data/cvd_intelligence_seed.json` — venues, series, audit data
