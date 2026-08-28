# Advanced TA & Risk Layer (#117–#128)

## #117 Liquidity Vacuum Spotter

`GET /radar/technical/liquidity-vacuum`

Vacuum = Gap / Mid-Price × 100. Threshold >1.5% = liquidity vacuum.

## #118 Counterparty Risk Distribution

Merged into `/radar/exchange-health` (#80/#92). Portfolio exchange allocation view.

## #119 Gas Hold — REJECTED

Alternative: `GET /radar/on-chain/gas-alert` — educational gas spike insight only.

## #120 Leverage Risk Analysis

Merged into Advanced Risk (#77). Optimization rejected — risk insight only.

## #121 PnL Attributed Drift

Merged into Journal Tab (#76). Market + Strategy + Signal + Drift decomposition.

## #122 Structural Break Analysis

`GET /radar/technical/structural-break` — Chow Test + CUSUM, rule-based (not AI).

## #123 Volume Profile POC

`GET /radar/technical/volume-profile` — POC + 70% Value Area.

## #124 Fair Value Gap Detector

`GET /radar/technical/fvg-detector` — ICT-style bullish/bearish FVG patterns.

## #125 Custody Tracking — DEFERRED Wave 3

Merged into Unified Portfolio (#81). Institution tier.

## #126 Front-Running Shield — REJECTED

Alternative: `GET /oracle/on-chain/dex-risk` — DEX slippage/MEV insight.

## #127 Exploiter — REJECTED

Alternative: `GET /radar/technical/orderbook-inefficiency` — spread analysis.

## #128 Jargon Translator

Merged into Simple Language (#64). Rule-based glossary extensions.

## E2E

```
GET /api/platform/advanced-ta-risk/e2e  (admin)
pytest tests/test_advanced_ta_risk_batch117_128.py -q
```
