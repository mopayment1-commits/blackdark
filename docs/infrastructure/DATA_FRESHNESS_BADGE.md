# Data Freshness Badge (#1030)

Cross-cutting UI component — NOT standalone. Translates backend provenance metadata into a unified visual badge on every data-displaying surface.

## States (5)

| State | Condition |
|-------|-----------|
| **Live** | `actual_delay_ms` < expected interval |
| **Delayed** | `actual_delay_ms` ≥ expected interval (confidence → Medium) |
| **Stabilized** | PIT final (#950) |
| **Provisional** | May change (#950) |
| **Recovered** | Gap backfill (#1028) |

## Timestamp

Exact UTC ISO 8601 required. Relative time (`45s ago`) allowed as supplement only — never as sole indicator.

## Badge format

`[state] · [source_name] · [timestamp_iso] · (relative)`

Clickable → #945 Provenance detail view.

## Thresholds (versioned 1.0.0)

| Category | Live if |
|----------|---------|
| Price | < 5 minutes |
| Volume | < 1 hour |
| On-chain | < 1 block (~12s) |
| Governance | < 24 hours |

Delayed when > expected; confidence degraded to Medium when > 2× threshold.

## API freshness object

```json
{
  "state": "Live",
  "timestamp": "2026-08-28T12:00:00+00:00",
  "source": "binance",
  "expected_interval_ms": 300000,
  "actual_delay_ms": 45000,
  "confidence": "High",
  "badge": { ... }
}
```

## Surfaces

Market Radar · Portfolio AI · Intelligence Ledger · On-Chain Extension · Research Portal (#997)

## Sprint rollout

| Sprint | Scope |
|--------|-------|
| **1** | UI component + design system |
| **2** | Enforcement across all systems |

## API

```
GET /api/platform/freshness-badge/status
GET /api/platform/freshness-badge/component-gate
GET /api/platform/freshness-badge/e2e
```

## Design system assets

- `static/css/data-freshness-badge.css`
- `static/js/data-freshness-badge.js`
- `templates/partials/data_freshness_badge.html`
