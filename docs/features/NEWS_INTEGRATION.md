# News Integration — #575

## Decision

**Merge into AI Content Engine (#511, #512) — Sprint 2. Rule-based.**

NOT a standalone ticket or UI module.

| Rule | Implementation |
|------|----------------|
| Source links preserved | `source_link_preserved` per article |
| No duplicate spam | `_dedupe_news_items()` by `dedupe_key` |
| Entity mapping | Asset filter + optional `entity_refs` |
| Not investment advice | Disclaimer on all outputs |

## Pipeline Position

```
rank(#513) → evidence(#511) → digest(#512) → news(#575)
```

## API

```
GET /api/platform/intelligence-ledger/intelligence-layer/ai-content/news?asset=BTC&limit=10
```

## Acceptance Criteria

| Criterion | Implementation |
|-----------|----------------|
| Source links preserved | `source_links_preserved` flag |
| No duplicate spam | Dedupe by `dedupe_key` |
| Merged not standalone | `standalone_rejected: true` |
