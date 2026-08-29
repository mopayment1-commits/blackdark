# Intelligence & Market Extensions Layer (#217–#227)

## #217 SaaS Multi-Broker Auto-Router — REJECTED

Alternative: `GET /intelligence/best-venue-analysis` — venue price/depth/slippage comparison. No routing.

## #218 Order Lifecycle Management — Manual Journal

`GET/POST /portfolio/journal/orders` — extends Journal (#76). Manual order states: Planned/Submitted/Filled/Cancelled.

## #219 NLP Sentiment

`GET /radar/sentiment/nlp` — rule-based keyword dictionary + sentiment score. ML deferred.

## #220 ROI Probability — Pattern Outcome

`GET /intelligence/backtest/pattern-outcome` — extends Backtest (#74). Historical outcome distribution, not profit probability.

## #221 Execution Quality — REJECTED

Alternative: `GET /radar/technical/slippage-analysis` — market-wide slippage, not personal fill monitoring.

## #222 Exchange Latency

`GET /admin/monitoring/exchange-latency` — extends #101 + #167 + #176 + #187. RTT ranking every 60s.

## #223 DeFi Fundamentals

`GET /oracle/on-chain/defi/fundamentals` — P/S ratio from on-chain protocol fees.

## #224 Token DCF

`GET /intelligence/valuation/dcf-token` — DCF model with visible assumptions + sensitivity (Wave 3 activation).

## #225 Desktop/Mobile — DEFERRED

PWA alternative in Sprint 2. Native apps Wave 3+ only.

## #226 Launch Arbitrage — REJECTED

Alternative: `GET /radar/events/launch-analysis` — new token launch risk analysis.

## #227 ETF Arbitrage — REJECTED

Alternative: `GET /intelligence/etf-premium` — premium/discount analysis.

## E2E

```
GET /api/platform/intelligence-market-extensions/e2e  (admin)
pytest tests/test_intelligence_market_extensions_batch217_227.py -q
```
