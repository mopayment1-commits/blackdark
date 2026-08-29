# Data Sources & Intelligence Layer (#140–#152)

## #140 White Label — DEFERRED (duplicate #90)

`GET /institution/white-label-status` — merged into Institution Portal (#90), Wave 3 only.

## #141 CoinDesk RSS Feed

`GET /radar/sentiment/feeds/coindesk` — rule-based RSS parsing with deduplication.

## #142 Santiment Free Tier

`GET /radar/sentiment/sources/santiment` + `GET /oracle/on-chain/sources/santiment` — free tier metrics only.

## #143 CryptoRank Event Calendar

`GET /radar/events/calendar` — context-only upcoming events (unlocks, governance, listings).

## #144 Whale Alert API

`GET /oracle/on-chain/sources/whale-alert` — supplementary whale flow with cross-validation.

## #145 CoinMarketCap API

`GET /oracle/sources/cmc` — secondary oracle redundancy (Sprint 1).

## #146 Coinbase Advanced API

`GET /oracle/sources/coinbase` — regulated secondary oracle source.

Oracle consensus: `GET /oracle/consensus` — validates CMC + Coinbase against primary (#101).

## #147 AI Trading Engine — REJECTED

Alternative: `GET /signal-engine/status` — Signal Engine (#11) with Opportunity/Neutral/Risk.

## #148 Blockchain.com API

`GET /oracle/on-chain/sources/blockchain-com` — secondary RPC redundancy.

## #149 DefiLlama API

`GET /oracle/on-chain/defi/defillama` + `GET /radar/defi` — TVL, yields, protocol metrics.

## #150 Opportunity Score

`GET /intelligence/score` — composite 0–100 score with visible weights.

Embedded in Daily Top 3 (`/intelligence/daily-top3`).

## #151 Explaining Opportunities

`GET /intelligence/explain` — dynamic rule-based breakdown (CVD, liquidity, funding, etc.).

## #152 Auto-Trading — REJECTED

Alternative: existing alerts (#65, #75). `GET /alerts/execution-status`.

## E2E

```
GET /api/platform/data-sources/e2e  (admin)
pytest tests/test_data_sources_batch140_152.py -q
```
