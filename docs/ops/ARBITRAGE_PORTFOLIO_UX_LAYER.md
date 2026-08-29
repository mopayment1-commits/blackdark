# Arbitrage, Portfolio & UX Layer (#177–#191)

## #177 Fee, Slippage and Capacity Analysis

`GET /intelligence/arbitrage/cost-analysis` — extends Arbitrage Mind (#153) with full cost breakdown.

## #178 Scenario and Drawdown Analysis

`GET /portfolio/risk/advanced/scenarios` + `GET /intelligence/backtest/scenarios` — embedded in #77 and #74.

## #179 Command Center Dashboard

`GET /dashboard` — unified widget dashboard (Top 3, Health Score, Alerts).

## #180 Whale Flow Visualization

`GET /oracle/on-chain/whale/visualization` — extends Whale Narrative (#71).

## #181 Committee Packets — MERGED into #87

## #182 White-Label Infrastructure — MERGED into #90 (Wave 3)

## #183 B2B Fund Integration — MERGED into #85+#83+#88 (Wave 3 activation)

## #184 Fund Reporting — MERGED into #87

## #185 Acquisition Evidence Package — DEFERRED (BD document assembly)

## #186 Continuous Learning — MERGED into #97

## #187 Latency Monitoring — MERGED into #101+#167+#176

## #188 Controlled Execution — REJECTED

Alternative: `GET /portfolio/risk-alert` — risk alert + journal (#76).

## #189 Liquidity Capacity

`GET /intelligence/arbitrage/capacity` + `GET /portfolio/liquidity-capacity`

## #190 Geographic Arbitrage

`GET /intelligence/arbitrage/geographic` — extends #153

## #191 Withdrawal Suspension Alert

`GET /radar/exchange-health/withdrawal-alert` — "exploitation" language rejected.

## E2E

```
GET /api/platform/arbitrage-portfolio-ux/e2e  (admin)
pytest tests/test_arbitrage_portfolio_ux_batch177_191.py -q
```
