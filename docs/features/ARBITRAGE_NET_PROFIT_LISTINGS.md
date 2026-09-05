# Arbitrage Scanner + Net Profit + New Listings — Features #112, #113, #114

## #113 Net Profit Engine (foundational)

Every profit/opportunity display flows through:

```
Gross Gap → − Gas → − Slippage → − Trading Fees → − Withdrawal = Net Profit
```

| Component | Module |
|-----------|--------|
| Trading fees (#130) | `fee_matrix` |
| Gas | `gas_oracle` |
| Slippage | `dex_slippage` / explicit bps |
| Withdrawal/deposit | `fee_matrix` |

API: `GET /api/platform/net-profit/breakdown`  
Fee DB: `GET /api/platform/fees/database`

## #112 Arbitrage Scanner

CEX↔DEX scan with **mandatory** net profit waterfall — never gross gap alone.

API:
- `GET /api/platform/arb/scanner`
- `GET /api/platform/arb/scanner/status`
- `GET /api/platform/arb/cex-dex` (now routes through scanner)

## #114 New Listings Alert Engine

Event-only alerts — NOT buy recommendations.

Sources: Binance symbol diff, DexScreener recent pairs.

Example headline:
> New pair on pancakeswap — TEST — initial liquidity $2,000,000 — Contract Verified

API:
- `GET /api/platform/market-radar/new-listings`
- `GET /api/platform/market-radar/new-listings/alerts`

Market Radar narrative includes `new_listings` block.

## Acceptance

| Criterion | Target |
|-----------|--------|
| API latency | ≤2s (`sla_met`) |
| Net profit | Required on #112 — incomplete flagged |
| Mode (#114) | `event_only` |
