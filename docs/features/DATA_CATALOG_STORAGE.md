# Data Catalog + Storage Infrastructure — #214 + #215 (merged, not standalone)

Per institutional guidance, both features are **NOT standalone tickets**.

## #214 — Metric Availability Registry → Data Catalog

Merged into **API Documentation + Data Catalog** (Sprint 0).

| Rule | Implementation |
|------|----------------|
| Not standalone | `standalone: false`, merged into data catalog |
| Production truth | Registry generated from `unified_api_platform` contracts + seed |
| Metric metadata | category, frequency, stabilization, mutability, access, assets |
| Searchable matrix | `/data-catalog/search` |
| Automated parity tests | `/data-catalog/parity-test` |

## #215 — Multi-Tier Data Storage → Storage Infrastructure

Merged into **Data Storage Infrastructure** (Sprint 0).

| Rule | Implementation |
|------|----------------|
| Not standalone | `standalone: false`, wraps `storage_tier_manager` |
| No silent loss | Migration safety check enforced |
| Deterministic retrieval | Restore test with checksum verification |
| Retention versioned | `Retention Policy v1.2.0` |
| Restore test | `/data-storage/restore-test` |
| Cost/latency evidence | Tier status with cost guard metadata |

## APIs

### Data Catalog (#214 merged)

| Endpoint | Description |
|----------|-------------|
| `GET /api/platform/data-catalog/status` | Catalog status |
| `GET /api/platform/data-catalog/registry` | Production-truth metric registry |
| `GET /api/platform/data-catalog/search` | Availability matrix search |
| `GET /api/platform/data-catalog/metrics/{id}` | Metric detail |
| `POST /api/platform/data-catalog/parity-test` | Automated parity tests |

### Data Storage (#215 merged)

| Endpoint | Description |
|----------|-------------|
| `GET /api/platform/data-storage/status` | Infrastructure status |
| `GET /api/platform/data-storage/tiers` | Tier status + cost/latency evidence |
| `GET /api/platform/data-storage/retention-policy` | Versioned retention policy |
| `POST /api/platform/data-storage/restore-test` | Deterministic restore test |
| `POST /api/platform/data-storage/migration-safety` | No silent loss check |

## Related

- `bd_platform/unified_api_platform.py` — API contracts (production truth)
- `storage_tier_manager.py` — multi-tier storage orchestrator
- `hot_storage.py` — hot tier pipeline
