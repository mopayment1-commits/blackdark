# Decision Intelligence Engine (#48) — Core Product

BLACKDARK's core AI engine for market analysis and actionable trading signals.

## Pipeline (gradual improvement)

```
prototype → backtest → paper_trading → live_candidate → live
```

Institutional acceptance targets (aspirational — tracked, not blocking prototype):

| Metric | Target |
|--------|--------|
| Sharpe | ≥ 1.5 |
| Max Drawdown | ≤ 15% |
| Win Rate | ≥ 55% |
| Backtest history | ≥ 2 years |
| Latency | ≤ 5 minutes |

## Architecture

| Layer | Module | Role |
|-------|--------|------|
| Features | `ml/decision_features.py` | 100+ leak-guarded features |
| ML | `ml/inference.py` | Direction prediction + OOD gate |
| Oracle | `oracle_unified.py` | Multi-modal score fusion |
| Alpha | `bd_platform/alpha_engine.py` | Multi-source alpha composite |
| Backtest | `ml/walk_forward.py` | Walk-forward OOS validation |
| Orchestrator | `bd_platform/decision_intelligence_engine.py` | Unified signal + reasoning |

## APIs

| Endpoint | Description |
|----------|-------------|
| `GET /api/platform/decision-intelligence/signal` | Full decision signal |
| `GET /api/platform/decision-intelligence/ranking` | Universe ranking |
| `GET /api/platform/decision-intelligence/features` | Feature extraction |
| `GET /api/platform/decision-intelligence/backtest` | Walk-forward backtest |

## UI

`/decision-intelligence` — Core product dashboard

## Output

- **Signal:** ACT / WAIT / AVOID with confidence %
- **Reasoning:** Explainable factor breakdown
- **Risk-adjusted:** Sharpe, max DD, win rate from walk-forward
- **Pipeline stage:** Current maturity level
