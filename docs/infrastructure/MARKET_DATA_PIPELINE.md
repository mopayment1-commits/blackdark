# Market Data Pipeline — Quote (#90) + Tick Trade (#96)

Silent Sprint 1 data-layer foundations. Users see clean signals and charts — not standalone products.

## Feature #90 — Quote Data

**Module:** `blackdark/data/quote_normalizer.py` + `market_data_pipeline.ingest_quote()`

| Check | Implementation |
|-------|----------------|
| Bid < ask sanity | `validate_bid_ask_sanity()` — rejects inverted/wide spreads |
| Stale flags | `quote_stale_flag()` — age_ms + exchange clock skew |
| Quote stream | `price_stream_engine.emit_tick()` → normalized payload with `quote_meta` |

Ingress paths:
- `price_stream_engine.emit_tick()` (full pipeline)
- `exchange_ws_hub` (sanity gate on WS book updates)
- `cap646/fallbacks.resolve_order_book()` (enriched with `quote_meta`)

## Feature #96 — Tick Trade Data

**Module:** `blackdark/data/trade_normalizer.py` + `market_data_pipeline.ingest_trade()`

| Field | Implementation |
|-------|----------------|
| Exchange timestamp | `exchange_ts_ms` preserved |
| Canonical timestamp | `ts_ms` + `ts_utc` (UTC ISO) |
| Taker side | `taker_side` from `is_buyer_maker` or `side` |
| Trade stream | In-memory ring buffer per symbol (`get_trade_stream()`) |

Supports Binance aggTrade fields (`p`, `q`, `T`, `m`, `a`, `s`) and generic `{price, qty, side}`.

## Pipeline stats (internal)

```python
from market_data_pipeline import pipeline_stats
```

## Tests

```bash
pytest tests/test_silent_quote_tick_data.py -v
```
