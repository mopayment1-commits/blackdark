# Fill Feasibility Simulator — Feature #415

Liquidity Depth Analyzer integrated into Intelligence Ledger + Arbitrage Scanner (#403). Simulation only — no execution.

## Endpoints

| Route | Description |
|-------|-------------|
| `GET /api/platform/intelligence-ledger/fill-feasibility/status` | Feature status |
| `GET /api/platform/intelligence-ledger/fill-feasibility` | Fill simulation panel |
| `GET /api/platform/intelligence-ledger/fill-feasibility/heatmap` | Liquidity heatmap per venue |
| `GET /api/platform/intelligence-ledger/fill-feasibility/arbitrage` | Arbitrage + volume feasibility |
| `GET /api/platform/intelligence-ledger/fill-feasibility/market-radar` | Market Radar integration |

## Output

- Verdict: `full_fill` / `partial_fill` / `not_fillable`
- Max executable size + weighted fill price
- Expected slippage + liquidity score (0–100)
- Volume feasibility on arbitrage opportunities

## Acceptance

- Deterministic order-book replay
- Stale depth rejected (>5s snapshot age)
- Missing depth never treated as executable
- Partial fills supported as analysis (not execution)
