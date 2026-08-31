# Liquidity Intelligence Engine — #280 (Sprint 1 Core)

**NOT a dashboard** — intelligence **layer** only. Absorbs #277, #278, #279.

| Ticket | Role |
|--------|------|
| #277 | Market Depth (depth/spread/imbalance/slippage curves) |
| #278 | Trade-correlated book analytics (L2/L3 + trades) |
| #279 | Resilience & freshness layer |
| #280 | Order Book Intelligence (umbrella layer) |

UI = embedded in **asset page** + **Screener filter** (deferred).

## Institutional Rules

| Rule | Implementation |
|------|----------------|
| Layer not dashboard | Engine only — no standalone Order Book dashboard |
| Sprint 1 Core | Liquidity Intelligence Engine in Data Engine |
| Absorbs #277–#279 | Single unified layer |
| UI deferred | Asset page embedded + Screener filter |

## Acceptance Criteria

| Criterion | Implementation |
|-----------|----------------|
| Sequence-gap detection | Via underlying `order_book_liquidity` (#269+#277) |
| Crossed-book handling | `detect_crossed_book()` — reject invalid snapshots |
| Latency/freshness visible | `build_freshness_block()` — always on panel output |
| Replay tests | Spread + sequence replay via underlying engine |
| Liquidity warnings | Backend warnings for asset page / Screener |
| Resilience scoring | #279 gap recovery + depth stability + uptime |

## Metrics

| Metric | Source |
|--------|--------|
| Depth | L2/L3 order book snapshots |
| Spread | Best bid/ask |
| Imbalance | Bid vs ask depth ratio |
| Slippage curves | Order book walk simulation |
| Resilience | Gap recovery, depth stability, uptime |
| Trade correlation | Buy/sell flow vs book imbalance |

## APIs

| Endpoint | Description |
|----------|-------------|
| `GET /api/v1/data/liquidity-intelligence/status` | Engine status + acceptance criteria |
| `GET /api/v1/data/liquidity-intelligence/panel` | Full intelligence panel per pair/venue |
| `GET /api/v1/data/liquidity-intelligence/warnings` | Liquidity warnings |

## Related

- `blackdark/data/liquidity_intelligence_engine.py` — #280 layer
- `blackdark/data/order_book_liquidity.py` — underlying #269+#277 engine
- `docs/features/ORDER_BOOK_LIQUIDITY.md` — infrastructure docs
