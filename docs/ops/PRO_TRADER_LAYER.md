# Pro Trader & Portfolio UX Layer (#67–#76)

Cross-cutting widgets and output formats — NOT standalone modules.

## #67 Portfolio Health Score

Widget inside Portfolio AI: single score (0–100) + color (green/yellow/red). No tables by default; formula expandable.

## #68 Share Card

Reusable one-click share component: PNG/SVG metadata + UTM link + mandatory disclaimer. Applied to Portfolio, Top 3, signals.

## #69 Time to Value < 60s

Guest onboarding flow: Market Radar → first asset → Health Score within 60 seconds. Analytics event: `time_to_first_value`.

## #70 Custom Opportunity Filter

`POST /api/platform/intelligence/filter` — Pro-only custom presets. Rule-based numeric filters.

## #71 Whale Narrative

`POST /api/platform/oracle/on-chain/narrative` — pattern → narrative mapping. Privacy-first (short address).

## #72 Noise Filter

`POST /api/platform/oracle/on-chain/classify` — signal vs noise (threshold 70). ~80% rejection target.

## #73 Multi-Dimensional Analysis

`GET /api/platform/intelligence/multi-dim` — Technical + On-Chain + Sentiment + Macro composite.

## #74 Backtesting

`POST /api/platform/intelligence/backtest` — 90-day rule-based simulation. No execution.

## #75 Flexible Alerts

`GET /api/platform/alerts/policy` — Free: 3/day cost-based; Pro: unlimited.

## #76 Decision Journal

`POST /api/platform/portfolio/journal` — extends Discipline Tab #66. Manual entry, prediction vs actual.

## E2E

```
GET /api/platform/pro-trader/e2e  (admin)
pytest tests/test_pro_trader_batch67_76.py -q
```
