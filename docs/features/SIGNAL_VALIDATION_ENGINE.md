# Signal Validation Engine — #747 MTF Decision Convergence (merged)

**NOT standalone** — validation layer inside Signal Engine (Sprint 2 — Intelligence Ledger).

Multi-Timeframe Decision Convergence is a **filter**, not a separate product surface.

## Rules

| Rule | Implementation |
|------|----------------|
| Filter role | MTF convergence validates signals before trust |
| Timeframes | 15m / 1h / 4h confluence check |
| Regimes | Convergent / Divergent / Flat / Insufficient data |
| Score penalty | Conflicting frames reduce opportunity score |
| Not prediction | Validation only — no forward price claims |

## Integration

- `technical_analysis.compute_timeframe_confluence` — core MTF logic
- `oracle_unified.finalize_unified_score` — score penalty application
- `bd_platform.decision_intelligence_engine.generate_decision_signal` — validation block in output

## APIs

| Endpoint | Description |
|----------|-------------|
| `GET /api/platform/signal-engine/validation/status` | Module status |
| `GET /api/platform/signal-engine/validation/mtf` | MTF convergence validation |
| `GET /api/platform/signal-engine/validation` | Full validation with score adjustment |
