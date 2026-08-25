# Order Book & Liquidity Data Layer — #269 (Sprint 1 Data Engine)

**NOT standalone** — merged into **Wave 01 Data Engine**. Dashboard deferred to Sprint 2.

#269 = the road (infrastructure), not the destination (dashboard).

## Institutional Decision

| Aspect | Decision |
|--------|----------|
| Standalone #269 | ❌ Archived |
| Merge target | Wave 01 Data Engine |
| Dashboard | Sprint 2 Intelligence Ledger / Market Radar |
| DEX AMM | Separate pipeline |

## Scope Lock

```
Crypto spot + perp order books only | DEX liquidity (AMM pools) = separate pipeline |
Resilience = calculated on top 100 pairs only | Replay = daily batch, not real-time
```

## Gap Detection Schema

```
Gap: [timestamp, venue, pair, expected_depth, actual_depth, gap%, duration, root_cause]
Root causes: API_down | stale_data | venue_maintenance
Alert threshold: configurable | No gap = no alert fatigue
```

## Separation of Concerns

| Layer | Owner |
|-------|-------|
| Ingestion | Wave 01 Data Engine (#269) |
| Analytics | Intelligence Ledger (Sprint 2) |
| Dashboard | Market Radar (Sprint 2) |

## Cost Gate

| Tier | Retention |
|------|-----------|
| Top 50 pairs (L1/L2) | 1 year |
| Others | 30 days |
| Policy | Compression mandatory, auto-delete beyond retention |

## Acceptance Criteria

| Criterion | Target |
|-----------|--------|
| Gap detection latency | < 5 min |
| Replay test coverage | Top 100 pairs weekly |
| Spread accuracy | < 1 bps variance vs exchange |

## APIs

| Endpoint | Description |
|----------|-------------|
| `GET /api/v1/data/order-book-liquidity/status` | Module status |
| `GET /api/v1/data/order-book-liquidity/gaps` | Gap detection records |
| `GET /api/v1/data/order-book-liquidity/replay-tests` | Daily replay QA |
| `GET /api/v1/data/status` | Includes `order_book_liquidity_269` summary |

## Related

- `blackdark/data/order_book_liquidity.py` — core module
- `database.py` — `order_books` table (reused, no duplicate pipeline)
- `#268` Instrument Master — instrument identity for pairs
