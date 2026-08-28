# Intelligence & UX Extensions Layer (#228–#241)

## #228 Portfolio Insurance — REJECTED

Alternative: `GET /portfolio/hedge-simulation` — drawdown hedging analysis only.

## #229 Reasoning Explanation

`GET /intelligence/explain` — extends #151 with rule-based template reasoning.

## #230 Cross-Exchange Arbitrage — merged #153

`GET /intelligence/arbitrage/cross-exchange` — activation only, no duplicate build.

## #231 Triangular Arbitrage — merged #153/#214

`GET /intelligence/arbitrage/triangular` — path analysis only.

## #232 Price Comparison Engine

`GET /intelligence/price-comparison` — extends #153 multi-venue aggregation.

## #233 Heat Map

`GET /radar/heatmap` — UI component data for Market Radar + Command Center (#179).

## #234 Live Dashboard — merged #179

Activation only — Command Center + WebSocket (#158).

## #235 Whale Intelligence — merged #71

Activation only — Whale Narrative.

## #236 Subscription Tiers — merged #60

Activation only — Stripe 3-tier policy.

## #237 One Sentence Oracle

`GET /intelligence/summary` — rule-based market synthesis sentence.

## #238 Market Scan — extends #11

`GET /radar/scan` — opportunity detection, no buy signals.

## #239 Live TA — merged #3/#158/#179

Activation only.

## #240 Stock-to-Flow

`GET /oracle/on-chain/s2f` + `GET /radar/technical/s2f`

## #241 FRED API

`GET /intelligence/multi-dim/macro/fred` — extends Macro Dimension (#133/#171).

## E2E

```
GET /api/platform/intelligence-ux-extensions/e2e  (admin)
pytest tests/test_intelligence_ux_extensions_batch228_241.py -q
```
