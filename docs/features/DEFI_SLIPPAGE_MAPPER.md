# #228 DeFi Slippage Mapper

**Sprint 2 — Intelligence**

## Overview

Liquidity pool slippage mapping across DeFi protocols. Shows the full cost picture
before entry: slippage by trade size, gas, impermanent loss, and net after fees.
Data context only — NOT investment recommendations.

## Acceptance Criteria

| Criterion | Implementation |
|-----------|----------------|
| Wash/noise policy | Wash trades excluded, $1K min volume, bot-filtered |
| Slippage per trade size | $1K / $10K / $100K / $1M curve per protocol |
| ≥10 protocols | Uniswap v2/v3, Curve, Balancer, PancakeSwap, SushiSwap, Aave, Compound, Lido, Rocket Pool, Morpho |
| Historical ≥1 year | 1Y avg slippage + volatility per protocol |
| Fee DB (#130) | Gross APY − gas − slippage − IL = net after fees |
| No best opportunity | Protocol Comparison data ordering only |
| Risk flags | Score + IL risk + smart contract risk (not vague labels) |
| Data context | Liquidity depth + slippage assessment (not "excellent entry") |
| Update every 15 min | Last Updated / Next Update timestamps |
| Methodology versioned | Slippage Methodology v1.2 |
| Data alerts only | Slippage exceeded alerts, not yield opportunities |
| Non-hideable disclaimer | `disclaimer_hideable: false` |

## API Endpoints

- `GET /api/platform/market-radar/defi/slippage-mapper/status`
- `GET /api/platform/market-radar/defi/slippage-mapper/dashboard?asset=ETH`
- `GET /api/platform/market-radar/defi/slippage-mapper/protocol/{protocol_id}`

## Files

- `bd_platform/defi_slippage_mapper.py` — core module
- `data/defi_slippage_mapper_seed.json` — 11 protocols
- `tests/test_defi_slippage_mapper.py` — acceptance tests

## Disclaimer

> DeFi slippage estimates are based on historical on-chain data. Actual execution depends on mempool state and may differ. Smart contract risks are not fully captured. Not investment advice.
