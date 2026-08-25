# Social Signal & Mindshare Module — #272 (Sprint 2 Intelligence Ledger)

**NOT standalone** — merged into **Intelligence Ledger / Social Signal Layer**.

Third-party provider (LunarCrush) + filtering layer. No raw social scraper.

## Institutional Rules

| Rule | Implementation |
|------|----------------|
| No raw pipeline | LunarCrush API + filtering — cost capped monthly |
| Bot/spam filtering | Methodology documented, monthly audit sample |
| Universe documented | Versioned asset set + sources + 7-day warmup |
| Low-volume confidence | < 100 mentions/week = greyed out, no trend |
| Project mapping | Confidence score, community submissions flagged |

## APIs

| Endpoint | Description |
|----------|-------------|
| `GET /api/platform/intelligence-ledger/mindshare/status` | Module status |
| `GET /api/platform/intelligence-ledger/mindshare` | Mindshare panel per asset |

## Disclaimer

Mindshare measures relative attention — not investment advice. Non-hideable.
