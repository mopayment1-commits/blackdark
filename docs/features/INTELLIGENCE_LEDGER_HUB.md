# Intelligence Ledger Hub — Institutional Launch UI

## Purpose

Unified consumer surface for **100+ Intelligence Ledger modules** (184 API routes) that were previously API-only.

Governing compliance:
- `INSTITUTIONAL_GOVERNING_REFERENCE.md` — UX-001, evidence on outputs
- `DATA_PLATFORM_GOVERNING_REFERENCE.md` — evidence class separation
- User directive — Zero-to-Finish, no placeholder UI, dark theme

## User Journey

1. Navigate to `/intelligence-ledger`
2. Browse modules by layer (On-Chain, Data, Portfolio, etc.)
3. Search modules by name
4. Select module → auto-load panel with query params
5. View formatted output with evidence class badge
6. Toggle raw JSON for power users

## Evidence Classes

Every panel response is tagged:
- **BACKTESTED** — seed/analytical panels (default for Intelligence Ledger)
- **SHADOW_LIVE_FORWARD** — live oracle/signals
- **PRODUCTION_VERIFIED** — post-launch verified (requires `BLACKDARK_PRODUCTION=true`)
- **SIMULATED** — paper/synthetic

## Launch Readiness

`GET /api/intelligence-ledger/launch-readiness` returns binary verdict:
- **VERIFIED COMPLETE** — all internal + external checks pass
- **NOT READY** — honest assessment (pentest, PSP keys = external evidence)

## API

```
GET /intelligence-ledger                          # Hub UI page
GET /api/intelligence-ledger/hub                # Full context (catalog + readiness)
GET /api/intelligence-ledger/catalog              # Module catalog
GET /api/intelligence-ledger/launch-readiness     # Institutional readiness report
```

## Files

| File | Role |
|------|------|
| `bd_platform/intelligence_ledger_hub.py` | Catalog parser, evidence wrap, readiness |
| `templates/intelligence_ledger.html` | Dark theme hub UI |
| `static/js/intelligence_ledger.js` | Panel loader, formatted renderer |
| `tests/test_intelligence_ledger_hub_batch.py` | Unit + integration + page tests |

## Navigation Integration

Linked from: `/dashboard`, `/platform`, `/cap646`, `/launch-center`

## Institutional Standards

All Intelligence Ledger API responses are wrapped with evidence metadata via middleware.
See `AGENTS.md` and `bd_platform/institutional_standards.py`.

## Launch Center

`/launch-center` — unified user entry with journeys, engineering readiness, live market strip.
