#!/usr/bin/env bash
# Wave 01 — Institutional production proof runner (ISO 29148 / QA-004)
# Usage:
#   PROD=https://blackdark-production.up.railway.app bash scripts/wave_01_institutional_proof.sh
#   ADMIN_KEY=... PROD=... bash scripts/wave_01_institutional_proof.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PROD="${PROD:-https://blackdark-production.up.railway.app}"
OUT="${WAVE_01_PROOF_OUT:-/opt/cursor/artifacts/wave_01_institutional}"
TS="$(date -u +%Y%m%dT%H%M%SZ)"
LOG="$OUT/proof_${TS}.log"
JSON="$OUT/proof_${TS}.json"

mkdir -p "$OUT"
exec > >(tee -a "$LOG") 2>&1

pass() { echo "PASS  $1"; }
fail() { echo "FAIL  $1"; FAILED=1; }
skip() { echo "SKIP  $1 — $2"; }
warn() { echo "WARN  $1"; }

FAILED=0
PROVENANCE_ID=""

echo "== Wave 01 Institutional Proof =="
echo "target: $PROD"
echo "timestamp_utc: $TS"
echo "governing: BLACKDARK_CONTEXT.md"
echo ""

# 5.0 — institutional audit surface
echo "--- 5.0 GET /api/v1/data/wave-01 ---"
W01="$(curl -sS -w "\n__HTTP__%{http_code}" "$PROD/api/v1/data/wave-01")"
W01_BODY="${W01%__HTTP__*}"
W01_CODE="${W01##*__HTTP__}"
echo "$W01_BODY" | python3 -m json.tool 2>/dev/null || echo "$W01_BODY"
if [[ "$W01_CODE" == "200" ]] && echo "$W01_BODY" | python3 -c "import sys,json; sys.exit(0 if json.load(sys.stdin).get('institutional_verdict')=='NOT READY' else 1)"; then
  pass "5.0 wave-01 institutional surface (honest NOT READY)"
else
  fail "5.0 wave-01 institutional surface (HTTP $W01_CODE)"
fi
echo ""

# 5.1 — seed sources (admin)
echo "--- 5.1 POST /api/v1/admin/seed-sources ---"
if [[ -n "${ADMIN_KEY:-}" ]]; then
  S1="$(curl -sS -w "\n__HTTP__%{http_code}" -X POST "$PROD/api/v1/admin/seed-sources" \
    -H "Content-Type: application/json" -H "X-Admin-Key: $ADMIN_KEY" -d '{}')"
  S1_BODY="${S1%__HTTP__*}"
  S1_CODE="${S1##*__HTTP__}"
  echo "$S1_BODY"
  [[ "$S1_CODE" == "200" ]] && pass "5.1 seed-sources" || fail "5.1 seed-sources HTTP $S1_CODE"
else
  skip "5.1 seed-sources" "ADMIN_KEY not set — EXTERNAL EVIDENCE required"
fi
echo ""

# 5.2 — trigger ingest (admin)
echo "--- 5.2 POST /api/v1/data/ingest ---"
if [[ -n "${ADMIN_KEY:-}" ]]; then
  S2="$(curl -sS -w "\n__HTTP__%{http_code}" -X POST "$PROD/api/v1/data/ingest" \
    -H "Content-Type: application/json" -H "X-Admin-Key: $ADMIN_KEY" \
    -d '{"source":"binance","symbols":["BTCUSDT"],"intervals":["1h"],"backfill_days":1}')"
  S2_BODY="${S2%__HTTP__*}"
  S2_CODE="${S2##*__HTTP__}"
  echo "$S2_BODY"
  [[ "$S2_CODE" == "202" ]] && pass "5.2 ingest queued" || fail "5.2 ingest HTTP $S2_CODE"
else
  skip "5.2 ingest" "ADMIN_KEY not set — bootstrap ingest used instead"
fi
echo ""

# 5.3 — OHLCV
echo "--- 5.3 GET /api/v1/data/ohlcv ---"
O3="$(curl -sS "$PROD/api/v1/data/ohlcv?symbol=BTCUSDT&interval=1h&limit=5")"
echo "$O3" | python3 -m json.tool
O3_COUNT="$(echo "$O3" | python3 -c "import sys,json; print(json.load(sys.stdin).get('count',0))")"
O3_STATE="$(echo "$O3" | python3 -c "import sys,json; print(json.load(sys.stdin).get('data_state',''))")"
PROVENANCE_ID="$(echo "$O3" | python3 -c "import sys,json; d=json.load(sys.stdin); print((d.get('data') or [{}])[0].get('provenance_id',''))" 2>/dev/null || true)"
if [[ "$O3_COUNT" -gt 0 && "$O3_STATE" == "LIVE" ]]; then
  pass "5.3 ohlcv LIVE count=$O3_COUNT provenance_id=$PROVENANCE_ID"
else
  fail "5.3 ohlcv count=$O3_COUNT state=$O3_STATE"
fi
echo ""

# 5.4 — funding (expect MISSING on geo-blocked host)
echo "--- 5.4 GET /api/v1/data/funding ---"
F4="$(curl -sS "$PROD/api/v1/data/funding?symbol=BTCUSDT&limit=5")"
echo "$F4" | python3 -m json.tool
F4_STATE="$(echo "$F4" | python3 -c "import sys,json; print(json.load(sys.stdin).get('data_state',''))")"
if [[ "$F4_STATE" == "MISSING" ]]; then
  pass "5.4 funding explicit MISSING (D-01 — not confused with zero)"
else
  fail "5.4 funding data_state=$F4_STATE"
fi
echo ""

# 5.5 — open interest
echo "--- 5.5 GET /api/v1/data/open-interest ---"
OI5="$(curl -sS "$PROD/api/v1/data/open-interest?symbol=BTCUSDT&limit=5")"
echo "$OI5" | python3 -m json.tool
OI5_STATE="$(echo "$OI5" | python3 -c "import sys,json; print(json.load(sys.stdin).get('data_state',''))")"
if [[ "$OI5_STATE" == "MISSING" ]]; then
  pass "5.5 open-interest explicit MISSING (D-01)"
else
  fail "5.5 open-interest data_state=$OI5_STATE"
fi
echo ""

# 5.6 — status
echo "--- 5.6 GET /api/v1/data/status ---"
ST6="$(curl -sS "$PROD/api/v1/data/status")"
echo "$ST6" | python3 -m json.tool
ST6_TOTAL="$(echo "$ST6" | python3 -c "import sys,json; print(json.load(sys.stdin).get('total_records',0))")"
[[ "$ST6_TOTAL" -gt 0 ]] && pass "5.6 status total_records=$ST6_TOTAL" || fail "5.6 status total_records=$ST6_TOTAL"
echo ""

# 5.7 — events
echo "--- 5.7 GET /api/v1/data/events ---"
E7="$(curl -sS "$PROD/api/v1/data/events?limit=5")"
echo "$E7" | python3 -m json.tool
E7_STATE="$(echo "$E7" | python3 -c "import sys,json; print(json.load(sys.stdin).get('data_state',''))")"
[[ -n "$E7_STATE" ]] && pass "5.7 events data_state=$E7_STATE" || fail "5.7 events missing data_state"
echo ""

# 5.8 — provenance chain (DAT-001)
echo "--- 5.8 GET /api/v1/data/provenance/{id} ---"
if [[ -n "$PROVENANCE_ID" ]]; then
  P8="$(curl -sS -w "\n__HTTP__%{http_code}" "$PROD/api/v1/data/provenance/$PROVENANCE_ID")"
  P8_BODY="${P8%__HTTP__*}"
  P8_CODE="${P8##*__HTTP__}"
  echo "$P8_BODY" | python3 -m json.tool 2>/dev/null || echo "$P8_BODY"
  if [[ "$P8_CODE" == "200" ]] && echo "$P8_BODY" | grep -q '"source"'; then
    pass "5.8 provenance chain DAT-001"
  else
    fail "5.8 provenance HTTP $P8_CODE"
  fi
else
  fail "5.8 provenance — no provenance_id from 5.3"
fi
echo ""

# Health cross-check
echo "--- health/live ---"
curl -sS "$PROD/health/live"
echo ""
pass "health/live"
echo ""

# Summary JSON
python3 - <<PY
import json, pathlib
pathlib.Path("$JSON").write_text(json.dumps({
  "timestamp_utc": "$TS",
  "target": "$PROD",
  "institutional_verdict": "NOT READY",
  "proof_log": "$LOG",
  "failed": bool($FAILED),
}, indent=2))
PY

echo "== Summary =="
echo "log: $LOG"
echo "json: $JSON"
if [[ "$FAILED" -eq 0 ]]; then
  echo "RESULT: PROOF PASS (wave scope — institutional platform NOT READY)"
  exit 0
else
  echo "RESULT: PROOF FAIL — see log"
  exit 1
fi
