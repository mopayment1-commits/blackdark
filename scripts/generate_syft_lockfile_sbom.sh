#!/usr/bin/env bash
# FINDING-11 supplemental: Syft SBOM from prod lockfile (CI when syft on PATH).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LOCK="${ROOT}/requirements-prod.lock.txt"
OUT="${1:-${ROOT}/governance/launch57/evidence/syft-prod-lock.cyclonedx.json}"
if ! command -v syft >/dev/null 2>&1; then
  echo "syft not installed — skip container/lockfile SBOM" >&2
  exit 2
fi
if [[ ! -f "$LOCK" ]]; then
  echo "missing $LOCK" >&2
  exit 1
fi
mkdir -p "$(dirname "$OUT")"
syft "file:${LOCK}" -o cyclonedx-json > "$OUT"
echo "Wrote $OUT"
