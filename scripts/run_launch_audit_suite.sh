#!/usr/bin/env bash
# BLACKDARK — free + deep launch audit suite (Soft Launch gate).
# Usage: bash scripts/run_launch_audit_suite.sh
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
OUT="${AUDIT_OUT:-/tmp/blackdark-launch-audit}"
mkdir -p "$OUT"
PY="${PYTHON:-python3}"
echo "== BLACKDARK launch audit suite =="
echo "output: $OUT"

status_set() {
  local tool_name="$1"
  local result="$2"
  printf '%s\n' "$result" >"${OUT}/${tool_name}.status"
}

run() {
  local name="$1"
  shift
  echo ""
  echo "### ${name}"
  if "$@" >"${OUT}/${name}.log" 2>&1; then
    echo "PASS ${name}"
    status_set "${name}" PASS
  else
    echo "FAIL ${name} (see ${OUT}/${name}.log)"
    status_set "${name}" FAIL
  fi
}

$PY -m pip install -q "pip-audit==2.9.0" "bandit==1.8.6" "detect-secrets==1.5.0" ruff 2>/dev/null || true

# A — dependencies
run pip_audit $PY -m pip_audit -r requirements.hashes.txt --desc

# B — static security
run bandit $PY -m bandit -q -ll \
  -r path_safety.py anti_hype_mode.py since_you_left.py kill_rate_board.py \
  sealed_desk_duel.py trust_debt_score.py enterprise_sso.py org_tenant.py \
  institutional_assurance.py institutional_commerce.py industry_silence_index.py \
  proof_gated_alert_passport.py ml/experience_log.py opportunity_tracker.py \
  liquidity_discovery.py aggregator.py audience_routing.py trust_os_lenses.py

if $PY -m semgrep --version >/dev/null 2>&1; then
  run semgrep $PY -m semgrep --config=p/python --config=p/owasp-top-ten --error --quiet .
else
  echo "SKIP semgrep"
  status_set semgrep SKIP
fi

# C — secrets
run detect_secrets $PY -m detect_secrets scan --all-files --exclude-files '.venv/|data/|\.git/|.*\.joblib$|.*\.parquet$'
if command -v gitleaks >/dev/null 2>&1; then
  run gitleaks gitleaks detect --source . --no-git -v
else
  echo "SKIP gitleaks"
  status_set gitleaks SKIP
fi

# D — container / FS
if command -v trivy >/dev/null 2>&1; then
  run trivy_fs trivy fs --severity HIGH,CRITICAL --exit-code 1 .
else
  echo "SKIP trivy"
  status_set trivy_fs SKIP
fi
if command -v hadolint >/dev/null 2>&1; then
  run hadolint hadolint Dockerfile
else
  echo "SKIP hadolint"
  status_set hadolint SKIP
fi

# E — lint
run ruff $PY -m ruff check path_safety.py trust_os_lenses.py audience_routing.py scripts/lock_requirements.py

# F — behavioral / product closure
run pytest_security $PY -m pytest \
  tests/test_security.py tests/test_security_hardening.py \
  tests/test_production_guard.py tests/test_radical_dd_scale_closure.py \
  -q --tb=line
run pytest_closure $PY -m pytest \
  tests/test_f1_f10_unique_full_ship.py tests/test_dd_radical_institutional_closure.py \
  tests/test_heroes_strategy.py \
  -q --tb=line

# G — dynamic ZAP (needs live URL)
if [[ "${RUN_ZAP:-0}" == "1" && -n "${TARGET_URL:-}" ]] && command -v docker >/dev/null 2>&1; then
  run zap_baseline docker run --rm -t ghcr.io/zaproxy/zaproxy:stable zap-baseline.py -t "$TARGET_URL" -I
else
  echo "SKIP zap_baseline (set RUN_ZAP=1 TARGET_URL=...)"
  status_set zap_baseline SKIP
fi

# H — Lighthouse (needs live URL + npx)
if [[ "${RUN_LIGHTHOUSE:-0}" == "1" && -n "${TARGET_URL:-}" ]] && command -v npx >/dev/null 2>&1; then
  run lighthouse npx --yes lighthouse@12.2.1 "$TARGET_URL" --quiet --chrome-flags="--headless --no-sandbox" --output=json --output-path="${OUT}/lighthouse.json"
else
  echo "SKIP lighthouse (set RUN_LIGHTHOUSE=1 TARGET_URL=...)"
  status_set lighthouse SKIP
fi

echo ""
echo "== SUMMARY =="
pass=0
fail=0
skip=0
for s in "${OUT}"/*.status; do
  [[ -f "$s" ]] || continue
  name="$(basename "$s" .status)"
  st="$(cat "$s")"
  printf '%-18s %s\n' "$name" "$st"
  case "$st" in
    PASS) pass=$((pass + 1)) ;;
    FAIL) fail=$((fail + 1)) ;;
    SKIP) skip=$((skip + 1)) ;;
    *) echo "WARN unknown status for ${name}: ${st}" ;;
  esac
done
echo "pass=${pass} fail=${fail} skip=${skip}"
echo "${pass} ${fail} ${skip}" >"${OUT}/summary.txt"
exit "${fail}"
