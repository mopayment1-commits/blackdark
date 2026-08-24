# Due Diligence Report Engine — Feature #173 (BLACKDARK Research)

Premium/Institution tier. Auto-generated reports first; human analyst review when unknowns present.

## Methodology

Version **v2.1** — cited on every report.

## Standards

1. **Every claim sourced** — no unsourced assertions (e.g. no "strong team" without names/LinkedIn)
2. **Unknown explicitly marked** — `UNKNOWN` values flagged as red flags
3. **Methodology versioned** — `methodology_version: "2.1"` on all outputs
4. **Review workflow** — `human_review_required` when unknowns/red flags present

## API

| Endpoint | Tier | Description |
|----------|------|-------------|
| `GET /api/platform/research/dd-report?asset=BTC&mode=one_page` | Institution | One-page summary |
| `GET /api/platform/research/dd-report?asset=BTC&mode=full` | Institution | Full claim list |
| `GET /api/platform/research/dd-report/status` | Public | Engine status |

## Report sections

- Fundamentals (price aggregation)
- Market data (market health)
- Tokenomics (MVRV/NVT proxies)
- Governance (UNKNOWN until verified)
- Team (UNKNOWN until verified)
- Security (data validation)
- Events (confidence score)

## CLI

```bash
blackdark dd BTC one_page
blackdark dd ETH full --json
```
