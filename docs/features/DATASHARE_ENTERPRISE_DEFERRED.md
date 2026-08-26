# Datashare Enterprise — #730 (Wave 3 — DEFERRED)

**Decision:** 🟢 Wave 3 — Datashare Enterprise (after Sprint 2)

**Status:** NOT built in Sprint 2. Institutional market needs foundation first.

## Future Requirements (documented)

| Rule | Requirement |
|------|-------------|
| Schema contracts | Breaking changes announced 30 days in advance |
| Platform rollout | Snowflake → BigQuery → Databricks |
| Pricing | Per-seat or per-GB-shared |
| Freshness | Same as API tier (no sub-second except Enterprise) |
| Compliance | SOC2 + encryption in transit + at rest before launch |

## API (status only)

`GET /api/platform/intelligence-ledger/datashare/status` — returns deferred status + contracts
