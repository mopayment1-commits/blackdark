#!/usr/bin/env bash
# Institutional validation suite (includes @pytest.mark.slow tests excluded from default pytest.ini).
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTEST_ADDOPTS=""
exec python -m pytest tests/cap646/ -n1 --timeout=600 -q --tb=short "$@"
