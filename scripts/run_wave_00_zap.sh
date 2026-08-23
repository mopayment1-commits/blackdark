#!/usr/bin/env bash
# Wave 0 — OWASP ZAP baseline re-scan
# Usage: RUN_ZAP=1 TARGET_URL=https://blackdark-production.up.railway.app bash scripts/run_wave_00_zap.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="${ZAP_OUT:-/opt/cursor/artifacts/wave_00_zap}"
mkdir -p "$OUT"
TARGET="${TARGET_URL:-https://blackdark-production.up.railway.app}"

echo "== Wave 0 ZAP baseline =="
echo "target: $TARGET"
echo "output: $OUT"

if ! command -v docker >/dev/null 2>&1; then
  echo "FAIL: docker required for ZAP baseline"
  exit 1
fi

sudo docker pull ghcr.io/zaproxy/zaproxy:stable

TS="$(date -u +%Y%m%dT%H%M%SZ)"
LOG="$OUT/zap_baseline_${TS}.log"
REPORT="$OUT/zap_report_${TS}.md"

sudo docker run --rm -v "$OUT:/zap/wrk:rw" -t ghcr.io/zaproxy/zaproxy:stable zap-baseline.py \
  -t "$TARGET" \
  -I \
  -r "/zap/wrk/zap_report_${TS}.md" 2>&1 | tee "$LOG"

echo ""
echo "ZAP log: $LOG"
echo "ZAP report: $REPORT"

# Summarize FAIL- counts (ZAP baseline uses WARN/FAIL in output)
FAILS=$(grep -c " FAIL " "$LOG" 2>/dev/null || echo 0)
WARNS=$(grep -c " WARN " "$LOG" 2>/dev/null || echo 0)
HIGH=$(grep -ci "High" "$LOG" 2>/dev/null || echo 0)
echo "summary: FAIL=$FAILS WARN=$WARNS HIGH_MENTIONS=$HIGH"

if grep -q "FAIL-NEW" "$LOG" 2>/dev/null; then
  echo "RESULT: NEW FAILURES DETECTED"
  exit 1
fi

echo "RESULT: PASS (no new ZAP failures; -I ignores existing baseline warnings)"
exit 0
