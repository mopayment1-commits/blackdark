# Market Conditions Context Monitor — #565

## Decision

Renamed from **Market Compass / Market Regime Engine** → **Market Conditions Context Monitor** (Sprint 2 Intelligence Layer).

| Rule | Implementation |
|------|----------------|
| No unified regime score | Factor alignment indicators per lens |
| Descriptive labels only | Defensive / Neutral / Expansion conditions observed |
| No buy/sell claim | Banned terms enforced programmatically |
| Stale data penalty | Confidence reduced when freshness exceeds threshold |
| Deterministic | Output hash for replay validation |
| Formula documented | Version 1.0 with lens weights |

## Factor Alignment Lenses

| Lens | Source |
|------|--------|
| Liquidity | Global liquidity index |
| Volatility | Cross-asset volatility regime |
| Breadth | Market breadth index |
| Macro | Macro intelligence hub |
| On-chain | On-chain metrics suite |
| Derivatives | Derivatives cross-signal |
| Profitability | Protocol economics layer |

## Acceptance Criteria

| Criterion | Implementation |
|-----------|----------------|
| Formula/version documented | `build_formula_documentation()` |
| Deterministic | `deterministic_output_hash` |
| No buy/sell claim | `_BANNED_TERMS` + `no_buy_sell_claim` |
| Stale-data penalty | `freshness_penalty()` on each lens |
| Unit/integration/E2E/backtest | Reconciliation tests + historical metric validation |

## API

```
GET /api/platform/intelligence-ledger/intelligence-layer/market-conditions/status
GET /api/platform/intelligence-ledger/intelligence-layer/market-conditions?market_id=crypto_aggregate
GET /api/platform/intelligence-ledger/intelligence-layer/market-conditions/reconciliation-tests
```
