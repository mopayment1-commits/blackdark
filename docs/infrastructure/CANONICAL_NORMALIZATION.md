# Canonical Normalization Engine (#1027)

Merged into **Data Engine** — not a standalone module. Transforms heterogeneous source data into one consistent internal schema before any calculation or display.

## Pipeline sequence

```
ingest (#1024) → normalize (#1027) → outlier check (#1026) → serve
```

## Capabilities

| Capability | Rule |
|------------|------|
| **Schema mapping** | Each source schema → canonical schema — documented + versioned — audit trail #945 |
| **Unit standardization** | Prices = USD · Volumes = native + USD · Timestamps = UTC — immutable |
| **Symbol canonicalization** | BTC = Bitcoin — #927 Asset Taxonomy — no silent remap |
| **Format unification** | JSON/XML/CSV → unified internal JSONB — schema enforced at ingest |
| **Null handling** | Missing = explicit null — no fabricated zeros — flagged in #945 |
| **Cross-source dedup** | Same event from 2 sources = one canonical record + multi-source provenance |
| **Methodology** | Rule-based only — no ML normalization in Sprint 2 |

## Provenance tag (per normalized value)

```json
{
  "raw_sources": ["binance", "coingecko"],
  "transformations_applied": ["schema_mapping", "price_usd_standardization"],
  "schema_version": "1.0.0",
  "normalization_timestamp": "2026-08-28T12:00:00+00:00"
}
```

## API

```
GET  /api/v1/data/normalization/status
GET  /api/v1/data/normalization/audit-trail
GET  /api/v1/data/normalization/production-gate
GET  /api/v1/data/normalization/e2e
```

## Integrations

- **#1024** Multi-Source Ingest — normalization is the next step after multi-source collection
- **#945** Provenance — every normalized value carries transformation metadata
- **#927** Asset Taxonomy — symbol resolution via canonical registry
- **#959** Reference Pricing — normalized prices as input
- **#986** Protocol KPIs — standardized metrics depend on normalized data
- **#1026** Outlier Detection — normalized data passes to gate after normalization

## Production gate

Blocks production if normalization engine incomplete (Sprint 0/1).

## Fee DB

Compute cost + source count + transformation complexity + schema version — per operation.
