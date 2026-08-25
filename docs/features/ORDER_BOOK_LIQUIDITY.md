# Order Book & Liquidity + Market Depth — #269 + #277 (Sprint 1 Data Engine)

**NOT standalone** — merged into **Wave 01 Data Engine / Liquidity Layer**.

| Ticket | Role |
|--------|------|
| #269 | Infrastructure layer (snapshots, liquidity gaps, replay QA) |
| #277 | Market depth engine (L2/L3 depth, spread, imbalance, slippage, sequence gaps) |

Engine = Sprint 1. UI = **Screener panel inside Market Radar Pro** (deferred — no standalone dashboard).

## Institutional Decision

| Aspect | Decision |
|--------|----------|
| Standalone #277 | ❌ Merged into #269 |
| Merge target | Liquidity Layer + Market Radar Pro |
| Dashboard | Screener panel (deferred) |
| DEX AMM | Separate pipeline |

## Scope Lock

```
Crypto spot + perp order books (L2/L3 where available) |
DEX liquidity (AMM pools) = separate pipeline |
Resilience = calculated on top 100 pairs only |
Replay = daily batch, not real-time |
UI = Screener panel (no standalone dashboard)
```

## Gap Detection

### Liquidity gaps (#269)

```
Gap: [timestamp, venue, pair, expected_depth, actual_depth, gap%, duration, root_cause]
Root causes: API_down | stale_data | venue_maintenance
```

### Sequence gaps (#277)

```
Sequence gap: [timestamp, venue, pair, book_level, expected_seq, received_seq, gap_size, recovered]
Recovery: snapshot_resync | delta_replay
```

## Market Depth Metrics (#277)

| Metric | Description |
|--------|-------------|
| Depth | Bid/ask depth USD (top N levels) |
| Spread | Best bid/ask spread in bps |
| Imbalance | (bid - ask) / (bid + ask) |
| Slippage | Order book walk simulation by size |
| Depth curve | Cumulative depth by distance from mid (heatmap backend) |

## Acceptance Criteria

| Criterion | Target |
|-----------|--------|
| Liquidity gap detection latency | < 5 min |
| Sequence gap detection latency | < 500 ms |
| Replay test coverage | Top 100 pairs weekly |
| Sequence replay tests | Daily batch |
| Spread accuracy | < 1 bps variance vs exchange |
| Depth heatmap UI | Deferred to Screener panel |

## APIs

| Endpoint | Description |
|----------|-------------|
| `GET /api/v1/data/order-book-liquidity/status` | Module status (#269+#277) |
| `GET /api/v1/data/order-book-liquidity/gaps` | Liquidity gap records |
| `GET /api/v1/data/order-book-liquidity/replay-tests` | Spread replay QA |
| `GET /api/v1/data/order-book-liquidity/sequence-gaps` | Sequence gap detection |
| `GET /api/v1/data/order-book-liquidity/sequence-replay-tests` | Sequence replay QA |
| `GET /api/v1/data/order-book-liquidity/market-depth` | Depth/spread/imbalance/slippage panel |

## Related

- `blackdark/data/order_book_liquidity.py` — core module (#269+#277)
- `database.py` — `order_books` table (reused)
- `#268` Instrument Master — instrument identity for pairs
