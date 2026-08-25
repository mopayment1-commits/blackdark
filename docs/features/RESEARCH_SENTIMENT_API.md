# Research Portal, Unified API & Unique Social Volume — #187, #188, #195

## #187 — BLACKDARK Research Portal

Searchable library of sector/protocol research reports.

| Feature | Implementation |
|---------|----------------|
| Tagging | Sector, Asset, Date, Author on every report |
| Search | `fulltext` + `semantic` (Arabic/English expansion) |
| Version archive | Previous versions stored on update |
| Saved items | Per-user saved report list |
| Seed data | 25 internal reports in `data/research_portal_seed.json` |

### APIs

| Endpoint | Auth | Description |
|----------|------|-------------|
| `GET /api/platform/research/search` | Public | Search with filters |
| `GET /api/platform/research/reports/{id}` | Public | Get report (optional `?version=N`) |
| `PUT /api/platform/research/reports/{id}` | User | Update + archive version |
| `POST /api/platform/research/saved/{id}` | User | Save report |
| `GET /api/platform/research/saved` | User | List saved |

---

## #188 — SanAPI-Style Data Access (merged into #162)

**Principle:** What you see in UI = what you get in API.

| Tier | Daily quota |
|------|-------------|
| Free | 100 |
| Pro | 1,000 |
| Institutional | 10,000 |

### New endpoints

| Endpoint | Metric |
|----------|--------|
| `GET /api/v1/platform/social-volume` | raw/unique/weighted volume |
| `GET /api/v1/platform/onchain` | MVRV, SOPR, NVT |
| `GET /api/v1/platform/financial` | VaR, NVT, MVRV, SOPR |
| `POST /api/v1/platform/graphql` | Pro+ optional GraphQL |
| `GET /api/v1/platform/quotas` | Tier quota info |

REST is mandatory for all tiers. GraphQL is optional for Pro+.

---

## #195 — Unique Social Volume (layer in #139)

Quality layer within Sentiment Engine — not a separate product.

```
Social Volume: 50,000 (raw) → 3,200 (unique) → 1,800 (weighted by quality)
```

| Layer | Logic |
|-------|-------|
| Deduplication | Same content hash = count once |
| Bot discount | ≥50 posts/day → 0.1 weight |
| Source QA | institutional 1.0, unknown 0.3 |

Integrated into `analyze_asset_sentiment()` as `social_volume` block.
