# Data Provenance & Lineage Layer — #1003

## 🟢 Sprint 1 Infrastructure — Cross-cutting mandatory

**#1003 = BLACKDARK's moat.** Institutional-grade end-to-end traceability vs retail "Source: Binance".

> Source: Binance API v3 → normalized via schema v2.1 → outlier filtered via Z-score v1.4 → last verified 2024-01-15 14:32 UTC

No Data Engine feature without provenance. Build provenance before features.

## Mandatory rules

1. **Every metric tagged** — `Source: [API/on-chain/subgraph] | Transformation: [formula/version] | Last verified: timestamp | Confidence: [high/medium/low]`
2. **Badge system** — UI: every number clickable → source + transformation + version. API: every response includes provenance object.
3. **Audit API** — Programmatic lineage access. Third parties can verify. Trust = verifiable.
4. **Version control** — Source schema changes versioned. Transformation logic versioned. Historical data recomputable.

## Module

`blackdark/data/provenance_lineage.py`

## API

| Endpoint | Purpose |
|----------|---------|
| `GET /api/v1/data/provenance-lineage/status` | Layer status + acceptance criteria |
| `GET /api/v1/data/provenance-lineage/metrics` | Registered metrics catalog |
| `GET /api/v1/data/provenance-lineage/lineage/{metric_id}` | Full lineage chain + badge |
| `GET /api/v1/data/provenance-lineage/audit/{metric_id}` | Third-party verifiable audit |
| `GET /api/v1/data/provenance-lineage/recompute/{metric_id}` | Historical recompute with pinned versions |

## Cross-cutting integration

- **Spot Metrics (#295)** — venue blocks carry full provenance + badge; panel enriched with `provenance_layer`
- **Historical Vault (#738)** — reproducible queries include lineage + provenance envelope

## Acceptance criteria

- End-to-end traceability ✅
- Every metric tagged ✅
- Badge system (UI + API) ✅
- Audit API (third-party verifiable) ✅
- Schema + transformation version control ✅
- Historical recomputable ✅
