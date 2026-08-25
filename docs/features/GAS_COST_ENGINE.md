# Gas Cost Engine — #247 (Sprint 1 Core + Monetization)

Chain-specific gas prediction with calibration, spike handling, fallback,
percentile bands, and Fee DB (#130) integration.

**Cost calculator — NOT a profit calculator.** Shows cost impact, leaves decision to user.

## Institutional Rules

| Rule | Implementation |
|------|----------------|
| Chain-specific model | Ethereum EIP-1559, BSC fixed, Arbitrum L2, Polygon PoS, etc. |
| Calibration | Every 100 blocks, actual vs predicted error < 10% |
| Spikes handled | N/A estimate during >3σ volatility, fallback to median |
| Fallback | Primary failed → last 10 blocks median with wider range |
| Actual-vs-predicted | Internal monitoring dashboard, weekly review |
| Percentile bands | Expected, p25, p75, p95 + confidence |
| Transaction-specific | Swap, Bridge, NFT Mint, Contract Deploy |
| Fee DB (#130) | Gross yield − gas − slippage = net after fees |
| No guaranteed profit | Cost display only — no "profitable after gas!" |
| Disclaimer | Non-hideable |
| Methodology versioned | Gas Cost Model v2.1, 8 chains |
| Pro tier | Free = median; Pro = tx-specific + bands + spike alerts |

## APIs

| Endpoint | Description |
|----------|-------------|
| `GET /api/platform/gas-cost/status` | Module status |
| `GET /api/platform/gas-cost/predict` | Gas prediction (`chain`, `tx_type`, `tier`) |
| `GET /api/platform/gas-cost/monitoring` | Internal calibration monitoring |

## Related

- `gas_oracle.py` — live RPC gas fetching
- `fee_matrix.py` — Fee DB (#130)
- `bd_platform/defi_slippage_mapper.py` — uses gas in fee impact
