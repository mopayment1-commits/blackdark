# Execution Rejected Layer — Insight-Only Alternatives

BLACKDARK rejects all execution, auto-trading, brokerage, and transaction management features.
Each rejected feature has a rule-based insight-only alternative.

## Registry

```
GET /api/platform/execution-rejected/registry
```

Returns all rejected execution features (#78, #119, #126, #127, #130, #131, #139, #147, #152, #155, #164, #166, #188, #193, #195, #211–#216) with alternative routes.

## Rejected Features & Alternatives

| # | Rejected | Alternative Route | Layer |
|---|----------|-------------------|-------|
| 78 | Smart Order Routing | `/intelligence/impact-analysis` | whales_institutional |
| 119 | Gas Hold Mechanism | `/radar/on-chain/gas-alert` | advanced_ta_risk |
| 126 | Front-Running Shield | `/oracle/on-chain/dex-risk` | advanced_ta_risk |
| 127 | Order Book Exploiter | `/radar/technical/orderbook-inefficiency` | advanced_ta_risk |
| 130 | Shadow-Fork Simulation | `/oracle/on-chain/tx-risk` | onchain_platform |
| 131 | Dust Sweeper | `/portfolio/dust-analysis` | onchain_platform |
| 139 | Panic Button | `/portfolio/stress-alert` | onchain_platform |
| 147 | AI Trading Engine | `/signal-engine/status` | data_sources |
| 152 | Auto Buy/Sell | `/alerts/execution-status` | data_sources |
| 155 | Stat-Arb Execution | `/intelligence/stat-arb` | intelligence_analysis |
| 164 | Safe Liquidation | `/portfolio/liquidity-impact` | risk_infrastructure |
| 166 | Brokerage API | `/brokerage/status` | risk_infrastructure |
| 188 | Controlled Execution | `/portfolio/risk-alert` | arbitrage_portfolio_ux |
| 193 | Auto-Arbitrage | `/intelligence/arbitrage` (#153) | derivatives_ta_research |
| 195 | DCA/Grid Bot | `/intelligence/strategy-simulator` | derivatives_ta_research |
| 211 | Cross-Margin Safeguard | `/portfolio/cross-margin-risk` | onchain_defi_sources |
| 212 | Re-hedging | `/portfolio/hedge-analysis` | onchain_defi_sources |
| 213 | Auto-Balancing | `/portfolio/capital-allocation` | onchain_defi_sources |
| 214 | In-Flight Modification | embedded in #153 | onchain_defi_sources |
| 215 | Flash Loan Gas | `/oracle/on-chain/gas-profile` (#159) | onchain_defi_sources |
| 216 | Counter-Trading AI | `/oracle/on-chain/whale/behavior-analysis` | onchain_defi_sources |

## E2E

```
GET /api/platform/execution-rejected/e2e  (admin)
pytest tests/test_execution_rejected_layer.py -q
```

## Policy

- No modules named execute, order, route, exploiter, safeguard, or brokerage
- All alternatives are insight-only with disclaimers and fee_db entries
- Disclosure (#57) confirms BLACKDARK never executes trades
