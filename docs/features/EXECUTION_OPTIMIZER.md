# Feature #56 — AI Execution Optimizer

True-cost routing across **21 DEX + 5 CEX** venues with capacity, MEV, and gas intelligence.

## True Cost Formula

```
True Cost = Price Impact + Slippage + Fees + Gas + Bridge + MEV Risk
```

## APIs

| Endpoint | Purpose |
|----------|---------|
| `GET /api/platform/execution/optimize` | Full route comparison + recommendations |
| `GET /api/platform/execution/status` | Module health |
| `GET /api/platform/intelligence-ledger/execution` | Legacy execution intelligence (Sprint 2) |

## Route outputs

- **Best cost** — lowest `true_cost_bps`
- **Fastest** — lowest latency (CEX priority)
- **Safest** — lowest MEV risk (CowSwap / CEX)
- **Split recommendation** — for large orders (≥$50K)

## Integrations

- Decision Engine (#48): `execution_optimizer` field with `confidence_penalty`
- Trade Simulator (#94): realistic slippage from optimizer in `simulate_spot_trade`

## Capacity score (0-100)

| Score | Label | Meaning |
|-------|-------|---------|
| 90-100 | deep | $100K+ with <0.1% impact |
| 50-89 | moderate | $10K-$50K comfortable |
| 10-49 | shallow | large orders move price |
| 0-9 | illiquid | split or avoid |
