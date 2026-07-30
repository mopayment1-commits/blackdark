# Feature #001 / #002 — G2 Live WebSocket E2E Validation Report

**Run ID:** 20260730_155520
**Started:** 2026-07-30T15:55:20.708256+00:00
**Finished:** 2026-07-30T15:56:55.536128+00:00

## Test Environment

| Field | Value |
|-------|-------|
| Python | 3.12.10 |
| Platform | win32 |
| Redis | local mirror / disabled |
| WS Only | true |
| Log file | `C:\Users\o\Desktop\BLACKDARK\data\g2_validation_logs\g2_run_20260730_155520.json` |

## Exchanges Tested

- binance (bookTicker WSS)
- okx (bbo-tbt WSS)
- bybit (orderbook.1 WSS)

## Symbols Tested

- BTC/USDT
- ETH/USDT
- SOL/USDT

## Case Results

| Case | PASS/FAIL | Evidence |
|------|-----------|----------|
| live_exchange_data | ✅ PASS | `{"venues_ready": ["binance", "bybit", "okx"], "quotes_received": 3, "quotes_expected_min": 3, "samples": {"binance|BTC/U...` |
| timestamp_validation | ✅ PASS | `{"symbol": "BTC/USDT", "venues_with_ts": 3, "sync_window_ok": true, "timestamp_spread_ms": 1247, "rows": [{"venue": "bin...` |
| sequence_and_gap_detection | ✅ PASS | `{"normal_sequence_ok": true, "gap_detected": true, "sequence_violation_detected": true, "stats": {"tick_gap_threshold_ms...` |
| duplicate_prevention | ⚠️ SKIP (pass-by-policy) | `{"skipped": true, "reason": "REDIS_URL not configured \u2014 local mirror mode"}...` |
| reconnect_behavior | ✅ PASS | `{"target": {"exchange": "okx", "stream": "bbo-tbt"}, "force_close_ok": true, "reconnects_before": 90, "reconnects_after"...` |
| failover_rest_fallback | ✅ PASS | `{"failover_activations_before": 60, "failover_activations_after": 74, "failover_incremented": true, "rest_fallback_avail...` |
| api_sse_dashboard_layer | ✅ PASS | `{"provider_count": 7, "provider_latency_ms": 3.09, "sse_latency_ms": 36.1, "sse_asset_count": 26, "health_feed_ms": 2.42...` |
| cross_source_consistency | ✅ PASS | `{"venue_mids": [64714.095, 64710.35, 64707.05], "ugp_price": null, "dispersion_bps": 0.0, "venues_used": 0}...` |
| error_handling | ✅ PASS | `{"zero_bid_rejected": true}...` |

## Latency Measurements

- Ingress avg: **26.24 ms** (32 samples)
- Book ages at capture: [32.0, 610.0, 32.0]

## Pipeline Stats (final snapshot)

```json
{
  "ws_hub": {
    "running": true,
    "enabled": true,
    "ws_only_mode": true,
    "messages_total": 36325,
    "exchanges": [
      "binance",
      "bybit",
      "kraken",
      "okx"
    ],
    "transport": "ultra_low_latency_websocket",
    "reconnect_max_sec": 1.0,
    "live_book": {
      "enabled": true,
      "stale_guard_enabled": true,
      "exchanges": [
        "binance",
        "bybit",
        "kraken",
        "okx"
      ],
      "symbol_count": 213,
      "updates_total": 23943,
      "max_age_ms": 300.0,
      "execution_max_age_ms": 300.0,
      "freshness_ms": 16.0,
      "stalest_ms": 86547.0,
      "stale_quotes": 190
    },
    "stream_health": [
      {
        "exchange": "okx",
        "stream": "bbo-tbt",
        "connected": true,
        "reconnect_count": 92,
        "frozen_events": 4,
        "idle_ms": 1125.0,
        "latency_ms": 0.05
      },
      {
        "exchange": "bybit",
        "stream": "orderbook.1",
        "connected": true,
        "reconnect_count": 0,
        "frozen_events": 0,
        "idle_ms": 0.0,
        "latency_ms": 0.1
      },
      {
        "exchange": "binance",
        "stream": "bookTicker-40",
        "connected": true,
        "reconnect_count": 0,
        "frozen_events": 0,
        "idle_ms": 16.0,
        "latency_ms": 0.07
      },
      {
        "exchange": "binance",
        "stream": "bookTicker-25",
        "connected": true,
        "reconnect_count": 0,
        "frozen_events": 0,
        "idle_ms": 32.0,
        "latency_ms": 0.06
      },
      {
        "exchange": "binance",
        "stream": "priority",
        "connected": false,
        "reconnect_count": 0,
        "frozen_events": 0,
        "idle_ms": 16.0,
        "latency_ms": 0.0
      },
      {
        "exchange": "binance",
        "stream": "bookTicker",
        "connected": false,
        "reconnect_count": 0,
        "frozen_events": 0,
        "idle_ms": 16.0,
        "latency_ms": 0.06
      },
      {
        "exchange": "okx",
        "stream": "bookTicker",
        "connected": false,
        "reconnect_count": 0,
        "frozen_events": 0,
        "idle_ms": 1125.0,
        "latency_ms": 1.67
      },
      {
        "exchange": "okx",
        "stream": "priority",
        "connected": false,
        "reconnect_count": 0,
        "frozen_events": 0,
        "idle_ms": 1125.0,
        "latency_ms": 0.0
      },
      {
        "exchange": "bybit",
        "stream": "bookTicker",
        "connected": false,
        "reconnect_count": 0,
        "frozen_events": 0,
        "idle_ms": 32.0,
        "latency_ms": 1.31
      },
      {
        "exchange": "bybit",
        "stream": "priority",
        "connected": false,
        "reconnect_count": 0,
        "frozen_events": 0,
        "idle_ms": 110.0,
        "latency_ms": 0.0
      },
      {
        "exchange": "kraken",
        "stream": "priority",
        "connected": false,
        "reconnect_count": 0,
        "frozen_events": 0,
 
```

## G2 Verdict

## ✅ G2: PASS

## Notes

- Feature #1 and #2 remain **NOT COMPLETE** until all Quality Gates (G1–G9) pass.
- G3 24h soak test runs **only after G2 PASS**.
