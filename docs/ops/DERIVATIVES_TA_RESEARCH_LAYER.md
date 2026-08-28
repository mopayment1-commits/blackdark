# Derivatives, TA & Research Layer (#192–#203)

## #192 Funding Rate Analysis

`GET /radar/derivatives/funding` — annualized funding, premium vs spot, directional pressure.

## #193 Auto-Arbitrage — REJECTED

Alternative: Arbitrage Opportunity Alert (#153).

## #194 Cumulative Volume Delta (CVD)

`GET /radar/technical/cvd` — order flow delta and divergence detection.

## #195 DCA/Grid Execution — REJECTED

Alternative: `GET /intelligence/strategy-simulator` — simulation only.

## #196 Yahoo Finance Macro

`GET /intelligence/multi-dim/macro/yahoo` — extends Macro Dimension (#133).

## #197 Alpha Vantage Macro

`GET /intelligence/multi-dim/macro/alpha-vantage` — macro backup redundancy.

## #198 Binance Research

`GET /radar/sentiment/research/binance` — research report ingestion.

## #199 Messari Research

`GET /radar/sentiment/research/messari`

## #200 CoinGecko Reports

`GET /radar/sentiment/research/coingecko`

## #201 Quantitative Analysis Framework

`GET /radar/technical/quant` + `GET /intelligence/quant` — analysis only, no quantitative trading.

## #202 Hidden Opportunities

`GET /intelligence/discovery/low-volume` — low-volume high-quality discovery filter.

## #203 CryptoCompare Oracle

`GET /oracle/sources/cryptocompare` — 4-of-N oracle consensus extension.

## E2E

```
GET /api/platform/derivatives-ta-research/e2e  (admin)
pytest tests/test_derivatives_ta_research_batch192_203.py -q
```
