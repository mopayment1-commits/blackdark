# Order Book Feed — #256 + #257 + #258 merged (Sprint 0)

Unified L1/L2/L3 order book feed. **NOT three products — three modes of one feed.**

| Mode | Feature | Description |
|------|---------|-------------|
| L1 | #256 | Top-of-book only |
| L2 | #257 | Top 20 depth levels |
| L3 | #258 | Order lifecycle (Enterprise only) |

## Institutional Rules

| Rule | Implementation |
|------|----------------|
| Single unified feed | One API, level selector L1/L2/L3 |
| Sequence/time QA | Sequence + timestamp + latency + gap |
| Normalization | USD price, base asset size, per venue |
| L1 top-of-book | Best bid/ask only — no extra depth |
| L2 gaps/reconnect | Auto reconnect + backfill documented |
| L3 order ID integrity | Queue + lifecycle tracking |
| No signal language | Descriptive feed only |
| Feeds #249 | Raw feeds power Global Order Book analysis |
| Latency tiers | L1/L2/L3 tier-based — no "instant" |
| Failover | Primary + fallback venue |
| L3 Enterprise only | Free max = L2 |
| L3 storage | 7d hot / 30d warm / 90d cold |

## APIs

| Endpoint | Description |
|----------|-------------|
| `GET /api/platform/order-book-feed/status` | Module status |
| `GET /api/platform/order-book-feed` | Feed (`level`, `asset`, `venue`, `tier`) |

## Integration

- **#249 Global Order Book** — aggregated analysis layer (feeds from this module)
- **Market Radar** — real-time surfaces
- **#721 Bot Activity** — L3 input for bot detection
- **#743 Market Surveillance** — L3 evidence

## Related

- `bd_platform/global_order_book.py` — #249 analysis layer
- `bd_platform/order_book_feed.py` — unified feed module
