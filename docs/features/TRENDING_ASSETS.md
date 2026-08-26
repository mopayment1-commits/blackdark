# Trending Assets Module — #300 (Sprint 2)

Discovers assets rising rapidly in social attention. Uses **#272 Community Pulse** data.

## Dependency Gate

**Do not start until #272 Social Signal Module is stable.**

Checks `community_pulse_seed.json` for methodology version, provider status, and asset coverage.

## Acceptance

| Criterion | Implementation |
|-----------|----------------|
| Alias collision | `BTC = Bitcoin` — documented rules, manual review top 10 |
| Low-volume protection | < 100 mentions/day excluded |
| Statistical significance | p < 0.05 required |
| Deterministic rank | Same inputs = same `rank_score` |

## APIs

| Endpoint | Description |
|----------|-------------|
| `GET /api/platform/intelligence-ledger/trending-assets/status` | Module status + dependency gate |
| `GET /api/platform/intelligence-ledger/trending-assets` | Trending leaderboard |
