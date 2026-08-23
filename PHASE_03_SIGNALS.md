# PHASE 03 — Market Memory & Signal Compounding

**Status:** ✅ Complete

## Deliverables
- `market_signals` table (versioned)
- `GET /api/signals/{symbol}/history`
- `GET /api/signals/{symbol}/diff?from=&to=`
- `GET /api/signals/correlate?symbols=BTC,ETH`
- Hook: `signal_registry.register_signal()` → SQL persistence

## Verify
```bash
curl -sS "$BASE/api/compounding/_verify/phase/3"
curl -sS -X POST "$BASE/api/signals" -H 'Content-Type: application/json' \
  -d '{"symbol":"BTC","signal_type":"oracle_direction","value":0.7,"confidence":0.7,"source":"test"}'
curl -sS "$BASE/api/signals/BTC/history"
```
