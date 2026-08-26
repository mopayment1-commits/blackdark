# Net-Edge Truth Score — Feature #417

Intelligence Ledger **Sprint-2 Core** scoring engine. Not a standalone module.

## Purpose

Compress opportunity quality into a single transparent score based on **executable net edge**, not raw gross spread. Competitors show "2% opportunity" that becomes a loss after costs; BLACKDARK shows the truth before decision.

## Formula (version 2.0.0)

```
truth_edge_usd = residual_after_crowd − latency_buffer_usd − network_cost_usdt

truth_score = 0.45×edge_score + 0.25×latency_score + 0.15×slippage_score + 0.15×fee_score − capacity_penalty

capacity_penalty = 0.15 × (100 − liquidity_score)   [when #415 depth present]

net_return_pct = (truth_edge_usd / notional_usd) × 100
```

### Component scoring

| Component | Weight | Logic |
|-----------|--------|-------|
| Residual edge | 45% | Truth edge after crowd decay + latency buffer |
| Latency freshness | 25% | Quote age penalty above 400ms; stale > 2500ms fails closed |
| Slippage quality | 15% | Bps-based drag score |
| Fee drag clarity | 15% | Withdrawal + trading fees vs net profit ratio |

### Policies (Terms of Service)

1. **Unknown costs never zero** — missing withdrawal/trading/network costs use **worst-case estimates** from documented bounds; never silently default to 0. When no bound exists, economics are **unverifiable** and the signal is rejected.
2. **Stale/unfillable fail closed** — stale depth (#415), `not_fillable` verdict, or `signal_suppressed` → automatic rejection.
3. **Negative net edge** — rejected with reason `negative_net_edge`.
4. **Formula version** — `2.0.0` embedded in every output (`formula_version` field).

## Routes

| Route | Description |
|-------|-------------|
| `GET /api/platform/intelligence-ledger/net-edge-truth/status` | Feature status + formula |
| `GET /api/platform/intelligence-ledger/net-edge-truth` | Scored opportunity panel |
| `GET /api/platform/intelligence-ledger/net-edge-truth/portfolio` | Per-asset scores (holdings + opportunities) |
| `GET /api/platform/intelligence-ledger/net-edge-truth/history` | Truth Score History (predicted vs outcome) |
| `GET /api/platform/intelligence-ledger/net-edge-truth/regression` | Deterministic regression fixtures |
| `GET /api/platform/intelligence-ledger/intelligence-layer/net-edge-truth` | Ledger integration summary |
| `GET /api/platform/intelligence-ledger/net-edge-truth/reconciliation-tests` | Acceptance checks |

## Output schema

Every evaluation returns:

- `net_edge_score` / `truth_score` (0–100)
- `net_return_pct` — executable net return on notional
- `executable_size` — from #415 depth/capacity
- `rejection_reasons` — explicit list when fail-closed
- `evidence` — formula, version, cost policies

## Integrations

- **#403/#429 Arbitrage Scanner** — every opportunity enriched via `evaluate_arbitrage_opportunity()`
- **#415 Fill Feasibility** — depth/capacity penalties + stale/unfillable gates
- **#433 Fill Risk** — risk gate uses truth reject flag
- **#449 Portfolio Intelligence** — net-edge per holding + opportunity
- **#460 Diligence Risk** — `final_rank_score = truth_score × risk adjustment`

## Truth Score History

Records each prediction (`predicted_truth_score`, `reject`, `rejection_reasons`) and later outcome (`correct` / `incorrect`) for trust calibration. Users see how often signals matched predicted economics.

## Acceptance

- [x] Formula/version documented (this file + `evidence.formula_version` in API)
- [x] Unknown costs never zero (worst-case or reject)
- [x] Stale/unfillable opportunities fail closed
- [x] Deterministic regression set (`data/net_edge_truth_seed.json` → `run_regression_fixtures()`)

## Simulation only

No real-money auto-execution. All outputs are analytics for study — not investment advice.
