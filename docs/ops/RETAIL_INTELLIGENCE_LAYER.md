# Retail Intelligence Layer (#62–#66)

Sprint 2 cross-cutting UX layers — NOT standalone modules.

## #62 Daily Top 3

`GET /api/platform/intelligence/daily-top3` — rule-based scoring (risk + liquidity + volume + momentum). Max 3 opportunities.

## #63 One Clear Answer

`POST /api/platform/intelligence/clear-answer` — Verdict + max 3 rule-based reasons. Insight, not recommendation.

## #64 Simple Language

`GET /api/platform/intelligence/glossary` — AR/EN glossary with tooltips. Rule-based term mapping.

## #65 Contextual Alerts

`POST /api/platform/intelligence/contextual-alert/evaluate` — alert at decision time. Free: 3/day.

## #66 Portfolio Discipline

`POST /api/platform/intelligence/discipline/compare` — manual user vs system comparison. Embedded in Portfolio AI analyze response.

## E2E

```
GET /api/platform/intelligence/retail/e2e  (admin)
```
