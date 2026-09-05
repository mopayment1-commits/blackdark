# Alpha Engine (#13) — MVP Signal Hub

**Not a standalone AI product.** Aggregates ingestion-layer inputs into actionable signals with explanations.

## Architecture

| Component | Path | Role |
|-----------|------|------|
| Feature extraction | `bd_platform/alpha_features.py` | 8 MVP features (scale to 100+ later) |
| Signal engine | `bd_platform/alpha_engine.py` | Weighted ensemble + explanations |
| Backtest | `bd_platform/alpha_backtest.py` | Walk-forward MVP metrics |

## MVP Features (8)

1. `momentum_24h` — 24h price change
2. `momentum_7d_proxy` — slower momentum proxy
3. `fear_greed` — Alternative.me contrarian score
4. `entity_flow` — Arkham / whale flow proxy
5. `liquidity` — price source confidence
6. `volume_ratio` — activity proxy
7. `volatility_24h` — short-term vol
8. `trend_strength` — directional strength

## Model strategy

- **Now:** `weighted_ensemble_v1` (interpretable, fast)
- **Next:** Random Forest / XGBoost when feature stability proven
- **Later:** Deep learning only after walk-forward validation

## Realistic MVP thresholds

| Metric | Institutional spec | MVP target |
|--------|-------------------|------------|
| Sharpe | ≥1.5 | ≥0.8 |
| Max Drawdown | ≤15% | ≤25% |
| Win Rate | ≥55% | ≥50% |
| Latency | ≤5 min | ≤5 min |
| Backtest | ≥2 years | ≥2 years (730d CoinGecko) |

## APIs

| Endpoint | Purpose |
|----------|---------|
| `GET /api/platform/alpha/signal?asset=` | Signal + explanations |
| `GET /api/platform/alpha/ranking` | Ranked universe |
| `GET /api/platform/alpha/backtest?asset=` | Walk-forward metrics |

## Output fields

- `alpha_score` — 0-100 composite
- `confidence_pct` — distance from neutral
- `explanations[]` — human-readable reasons
- `features` — 8 normalized feature values
- `mvp_metrics` — realistic acceptance targets
