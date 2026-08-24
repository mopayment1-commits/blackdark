# QuickTake / Analyst Insight Feed — Feature #184

**BLACKDARK Daily Brief** — evidence-linked analyst insights.

## Insight structure

Each insight requires:
1. **Claim** — e.g. "Liquidity is declining"
2. **Evidence** — chart link or API reference
3. **Source** — data collection timestamp
4. **Confidence** — score 0-100

## Moderation

States: `draft` → `pending_moderation` → `published` | `rejected`

No ungrounded quantitative claims — numbers without evidence are rejected.

## APIs

| Endpoint | Auth | Description |
|----------|------|-------------|
| `GET /api/platform/insights/feed` | Public | Published insights |
| `POST /api/platform/insights/submit` | User | Submit for moderation |
| `POST /api/platform/insights/{id}/moderate` | Admin | Approve/reject |
| `POST /api/platform/insights/generate` | Admin | Auto-generate daily brief |
| `GET /api/platform/insights/status` | Public | Feed status |

## Acceptance

- Every quantitative claim traceable to evidence
- Moderation required before publish
- Timestamp + source on all claims
- No ungrounded claims
