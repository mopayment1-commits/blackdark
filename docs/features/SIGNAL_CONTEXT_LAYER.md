# Signal Context Layer — #330-REV (Sprint 2, Pro)

Rule-based context panel transforming raw data into understandable stories.
Layer over Market Radar + Portfolio AI — NOT standalone, NOT recommendations.

## Architecture

```
Market Radar / Portfolio AI
        │
        ▼
┌─────────────────────────────┐
│   Signal Context Layer      │
│   (Rule-Based Engine v1.0)  │
├─────────────────────────────┤
│  Inputs: CVD #232, Funding, │
│  Liquidity, Exchange #132,  │
│  Bot Activity #721, On-Chain│
│  Fee DB #130                │
├─────────────────────────────┤
│  Output: Context Panel      │
│  (data only — no rec)       │
└─────────────────────────────┘
```

## Rule-Based Weights (v1.0)

| Component | Weight |
|-----------|--------|
| Data Alignment | 30% |
| CVD Context | 20% |
| Funding Context | 15% |
| Liquidity Context | 15% |
| Exchange Risk | 10% |
| Fee Impact | 10% |

Weights versioned — changes require version bump + announcement.

## APIs

| Endpoint | Description |
|----------|-------------|
| `GET /api/platform/market-radar/signal-context/status` | Module status |
| `GET /api/platform/market-radar/signal-context` | Context panel (Market Radar) |
| `GET /api/platform/portfolio/signal-context` | Context panel (Portfolio AI) |

## Acceptance Criteria

| Criterion | Implementation |
|-----------|----------------|
| Rule-based documented | Methodology + weights version |
| Risk Flags X/10 | Numeric score + sources |
| Data Alignment X% | Sources agree N/M |
| Panel ≤500ms | SLA tracked |
| 3 reasons minimum | Insufficient context if <3 |
| Fee DB #130 | Net after fees shown |
| Disclaimer non-hideable | Top + bottom, no collapse |
| No look-ahead | Data ≤ moment T |
| Not recommendation | No Buy/Sell language |

## Integration

- `bd_platform/market_radar_dashboard.py` — `signal_context` block
- `bd_platform/signal_context_layer.py` — core engine

## Related

- `data/signal_context_seed.json` — versioned weights + asset inputs
