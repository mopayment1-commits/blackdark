# Arbitrage Probability Signal — Feature #422

## Decision

**Sprint-2 Intelligence Ledger — merged into Arbitrage Scanner (#403), NOT standalone.**

Renamed from "Predictive Arbitrage" / "5 seconds ahead" → **Arbitrage Probability Signal**

| Cancelled SLA | Replacement |
|---------------|-------------|
| Accuracy ≥95% | False Positive Rate ≤30% in backtest |
| Uptime 99% | Cancelled |
| Fixed 5-second prediction | Expected formation time **range** |
| ML v1 | Rule-based only |

## Rule Engine (v1.0.0)

Components (weighted):
- Order book imbalance (30%)
- Funding rate differential (25%)
- Volume spike z-score (25%)
- Correlation break (20%)

## Output

- `probability_score_pct` (0–100%)
- `confidence_level` (high / medium / low)
- `expected_formation_time` (range in seconds — not fixed guarantee)
- `risk_warnings`
- `component_breakdown`

## Integrations

- **#403/#429** — filter on every arbitrage opportunity (`arbitrage_probability_signal`)
- **#417** — projected net edge if opportunity forms
- **#415** — fill feasibility for projected opportunity

## Routes

```
GET /api/platform/intelligence-ledger/unified-arbitrage/probability-signals/status
GET /api/platform/intelligence-ledger/unified-arbitrage/probability-signals
GET /api/platform/intelligence-ledger/unified-arbitrage/probability-backtest
GET /api/platform/intelligence-ledger/unified-arbitrage/probability-signals/reconciliation-tests
```

## Probability Backtest

Historical false positive rate and accuracy for trust calibration — no inflated accuracy SLA claims.

## Simulation only

Near real-time analytics. No automatic execution.
