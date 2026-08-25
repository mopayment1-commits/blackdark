# Market Pair Intelligence — #270 (ARCHIVED standalone)

**REJECTED as standalone backend feature.** Converted to frontend requirement for **Market Radar Sprint 2**.

#270 = view on #268 Instrument Master. The map (#268) and the view (#270) are one thing.

## Institutional Decision

| Aspect | Decision |
|--------|----------|
| Standalone #270 | 🔴 Rejected |
| Backend | View/query over #268 — no separate pipeline or database |
| Frontend | Market Radar Sprint 2 requirement card |
| New ingestion | ❌ None |

## What #270 Is NOT

- Not a separate pipeline
- Not a separate database
- Not a backend feature ticket
- Not "Market page + exchange comparison" as a product module

## What #270 IS

- SQL query + frontend over #268 instrument mappings
- Pair normalization = work of #268
- Market quality scoring = work of Intelligence Ledger (Sprint 2)

## Quality Gates

| Gate | Rule |
|------|------|
| Stale | No trades > 24h = flagged |
| Low volume | < $10K daily = greyed out + confidence warning |
| New pairs | < 7 days = unverified flag |
| Delisted | Archived after 30 days |
| Premium/discount | Calculated vs VWAP reference |

## APIs (view layer only)

| Endpoint | Description |
|----------|-------------|
| `GET /api/v1/data/market-pairs/status` | Archived ticket status |
| `GET /api/v1/data/market-pairs` | Pair views over #268 |
| `GET /api/v1/data/market-pairs/compare/{base}` | Cross-venue comparison |

## Related

- `blackdark/data/market_pair_view.py` — view layer (no ingestion)
- `blackdark/data/instrument_master.py` — #268 source of truth
- Market Radar (Sprint 2) — frontend destination
