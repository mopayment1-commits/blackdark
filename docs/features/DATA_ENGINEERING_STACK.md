# Data Engineering Stack — #223 dbt Connector (Sprint 0, merged)

**NOT standalone** — internal tooling. #223 closed as separate ticket.

## Institutional Rules

| Rule | Implementation |
|------|----------------|
| Not standalone | Merged into Data Engineering Stack |
| Model tests | `not_null`, `unique` on staging + mart models |
| Lineage | `ingestion_snapshots → stg_ingestion_snapshots → mart_ingestion_daily` |
| Workflow | Dune warehouse + dbt models → production pipeline |

## APIs

| Endpoint | Description |
|----------|-------------|
| `GET /api/platform/data-engineering/status` | Stack status (includes dbt) |
| `GET /api/platform/data-engineering/lineage` | Model lineage |
| `GET /api/platform/data-engineering/model-tests` | Model test definitions |
| `POST /api/platform/data-engineering/pipeline/run` | Run dbt pipeline (admin) |

## Related

- `dbt_connector.py` — underlying dbt execution
- `bd_platform/data_catalog.py` — #214 metric registry
- `bd_platform/data_storage_infrastructure.py` — #215 storage tiers
