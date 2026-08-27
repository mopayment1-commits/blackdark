#!/usr/bin/env bash
# Critical defects D-01..D-15 — closure proof runner
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PROD="${PROD:-https://blackdark-production.up.railway.app}"
OUT="${CRITICAL_DEFECTS_OUT:-/opt/cursor/artifacts/critical_defects_closure}"
TS="$(date -u +%Y%m%dT%H%M%SZ)"
LOG="$OUT/proof_${TS}.log"

mkdir -p "$OUT"
exec > >(tee -a "$LOG") 2>&1

pass() { echo "PASS  $1"; }
fail() { echo "FAIL  $1"; FAILED=1; }

FAILED=0

echo "== Critical Defects Closure Proof =="
echo "target: $PROD"
echo "timestamp_utc: $TS"
echo ""

echo "--- Unit tests (D-01..D-15) ---"
cd "$ROOT"
python3 -m pytest \
  tests/test_d01_data_state.py \
  tests/test_d02_secrets_vault.py \
  tests/test_d06_institutional_api.py \
  tests/test_d09_flow_filter.py \
  tests/test_d13_auth_abuse.py \
  tests/test_d15_evidence_closure.py \
  -q --tb=short
pass "pytest critical defect suite"
echo ""

echo "--- GET /api/v1/platform/critical-defects ---"
CD="$(curl -sS -w "\n__HTTP__%{http_code}" "$PROD/api/v1/platform/critical-defects")"
CD_BODY="${CD%__HTTP__*}"
CD_CODE="${CD##*__HTTP__}"
echo "$CD_BODY" | python3 -m json.tool 2>/dev/null || echo "$CD_BODY"
if [[ "$CD_CODE" == "200" ]] && echo "$CD_BODY" | python3 -c "
import sys, json
r = json.load(sys.stdin)
assert r['summary']['closed'] == 6
assert r['summary']['platform_verdict'] == 'PASS WITH RISK'
"; then
  pass "critical-defects API (6 closed, PASS WITH RISK)"
else
  fail "critical-defects API (HTTP $CD_CODE)"
fi
echo ""

echo "--- GET /api/v1/data/wave-01 ---"
W01="$(curl -sS -w "\n__HTTP__%{http_code}" "$PROD/api/v1/data/wave-01")"
W01_BODY="${W01%__HTTP__*}"
W01_CODE="${W01##*__HTTP__}"
if [[ "$W01_CODE" == "200" ]] && echo "$W01_BODY" | python3 -c "
import sys, json
r = json.load(sys.stdin)
assert r.get('institutional_verdict') == 'PASS WITH RISK'
assert r.get('open_critical_defects') == []
assert len(r.get('closed_critical_defects', [])) == 6
"; then
  pass "wave-01 institutional (PASS WITH RISK, 6 closed)"
else
  fail "wave-01 institutional (HTTP $W01_CODE)"
fi
echo ""

echo "--- GET /api/v1/onchain/flow-classification (D-09) ---"
FC="$(curl -sS -w "\n__HTTP__%{http_code}" \
  "$PROD/api/v1/onchain/flow-classification?from=addr_a&to=addr_b")"
FC_BODY="${FC%__HTTP__*}"
FC_CODE="${FC##*__HTTP__}"
if [[ "$FC_CODE" == "200" ]] && echo "$FC_BODY" | python3 -c "
import sys, json
r = json.load(sys.stdin)
assert r['classification'] in ('INTERNAL_CONFIRMED','INTERNAL_LIKELY','ECONOMIC_FLOW','UNKNOWN')
assert r['defect'] == 'D-09'
"; then
  pass "flow-classification API"
else
  fail "flow-classification API (HTTP $FC_CODE)"
fi
echo ""

if [[ "${FAILED:-0}" -eq 0 ]]; then
  echo "== ALL CRITICAL DEFECTS CLOSURE PROOF PASS =="
  exit 0
else
  echo "== CRITICAL DEFECTS CLOSURE PROOF FAILED =="
  exit 1
fi
