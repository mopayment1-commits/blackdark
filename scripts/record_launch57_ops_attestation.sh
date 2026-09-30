#!/usr/bin/env bash
# Record ops closure gate results (see record_launch57_ops_attestation.py).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export LAUNCH57_OPS_OPERATOR="${LAUNCH57_OPS_OPERATOR:-$(whoami)}"
exec python3 scripts/record_launch57_ops_attestation.py "$@"
