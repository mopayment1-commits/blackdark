#!/usr/bin/env bash
# Optional container SBOM (FINDING-11). Requires syft on PATH.
set -euo pipefail
IMAGE="${1:-blackdark:launch-57}"
OUT="${2:-docs/data-room/sbom/cyclonedx-container.json}"
if ! command -v syft >/dev/null 2>&1; then
  echo "syft not installed — see docs/security/SBOM_SCOPE_STATEMENT.md" >&2
  exit 2
fi
syft "$IMAGE" -o cyclonedx-json > "$OUT"
echo "Wrote $OUT"
