# #238 Dev Health Score

**Sprint 2 — Intelligence | Replaces #722**

## Overview

Institutional development continuity intelligence measuring whether a project is actively built — not marketed — via composite scoring of repository activity, contributors, releases, issues, and community health.

Integrated into **#705 Asset Metadata** as a profile field. **Not** a standalone dashboard.

## Acceptance Criteria

| Criterion | Implementation |
|-----------|----------------|
| Repo ownership verified | `ownership.status == "Verified"` required; unverified repos return no score |
| Bot/fork filtering | Bots excluded via author pattern + email domain; forks excluded at repo level |
| No commit-count-only score | Composite weighted score across 5 components |
| Contributor concentration | Top-3 %, concentration risk, bus factor |
| Release cadence | Last release, average cadence days, regularity |
| Issue activity | Open/closed counts, response time, bug-to-feature ratio |
| Methodology versioned | `Dev Health Methodology v2.1` with documented weights |
| Trend + evidence | Direction inferred from prior score; evidence strings required |
| Non-hideable disclaimer | `disclaimer_hideable: false` |
| Analysis only | Context display: "Your research required" — no buy signals |

## Component Weights

| Component | Weight |
|-----------|--------|
| Activity | 30% |
| Contributors | 25% |
| Releases | 20% |
| Issues | 15% |
| Community | 10% |

## API Endpoints

- `GET /api/platform/connectors/assets/{symbol}/dev-health` — per-asset dev health block
- `GET /api/platform/dev-health/status` — module status

## Integration (#705)

`canonical_asset_registry._enrich_asset()` adds `dev_health` to asset profiles when ownership is verified:

```
Dev Health: 7.2/10 | Methodology: v2.1
```

## Files

- `bd_platform/dev_health_score.py` — core module
- `data/dev_health_seed.json` — seed data (BTC, ETH, SOL)
- `bd_platform/canonical_asset_registry.py` — #705 integration
- `tests/test_dev_health_score.py` — acceptance tests

## Disclaimer

> Dev Health measures project development activity. It is not a valuation metric. A high score does not guarantee project success. Not investment advice.
