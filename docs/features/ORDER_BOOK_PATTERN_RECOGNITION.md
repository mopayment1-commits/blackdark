# Order Book Pattern Recognition Engine — #281 (Wave 3, renamed)

**Renamed from** "Order Book Intelligence AI/ML" → **Order Book Pattern Recognition Engine**.

NOT trading signals. NOT investment advice. Wave 3 after compliance.

## Institutional Decision

| Aspect | Decision |
|--------|----------|
| Original claims | ❌ Rejected (Sharpe ≥1.5, Win Rate ≥55%, etc.) |
| Renamed to | Order Book Pattern Recognition Engine |
| ML | Blocked until 6 months rule-based validation + legal review |
| Output | Historical pattern match — `pattern_match_score` ≠ profit probability |

## Compliance Rules

| Rule | Implementation |
|------|----------------|
| No financial claims | Sharpe, drawdown, win rate banned |
| Disclaimer mandatory | Non-hideable on all outputs |
| No "signals" | `not_a_signal`, `not_a_recommendation` on every match |
| pattern_match_score | Structural similarity only |
| Explainability | `explainability_reasons` on every match |
| Rule-based first | Phase 1 active; ML deferred |
| Backtest | ≥2 years documented, historical only |

## APIs

| Endpoint | Description |
|----------|-------------|
| `GET /api/platform/intelligence-ledger/pattern-recognition/status` | Engine status + compliance gate |
| `GET /api/platform/intelligence-ledger/pattern-recognition` | Pattern match panel per asset |

## Disclaimer

"Past performance does not indicate future results. No forward performance guarantee."
