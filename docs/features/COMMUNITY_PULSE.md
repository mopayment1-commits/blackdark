# Community Pulse — #272 + #287 + #290 + #292 (Sprint 2)

**#287 rejected as standalone** — merged into #272 cluster as NLP sentiment sub-task.

| Ticket | Role |
|--------|------|
| #272 | Mindshare Intelligence |
| #287 | NLP sentiment classification (sub-task) |
| #290 | Social Dominance (absorbed) |
| #292 | Social Volume (absorbed) |

Purchased feed (LunarCrush/Kaito API) — **no NLP team**, no raw scraper.

## #287 Acceptance (within cluster)

| Criterion | Implementation |
|-----------|----------------|
| Model/version visible | `model`, `model_version` on sentiment block |
| Source coverage visible | `source_coverage_pct` |
| Sarcasm handling | Confidence reduced to low when detected |
| Low volume handling | Insufficient mentions → greyed out |

## APIs

| Endpoint | Description |
|----------|-------------|
| `GET /api/platform/intelligence-ledger/community-pulse/status` | Cluster status |
| `GET /api/platform/intelligence-ledger/community-pulse` | Panel per asset |

## Disclaimer

"Sentiment = feed classification — not profit probability."
