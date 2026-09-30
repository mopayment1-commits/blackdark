#!/usr/bin/env python3
"""Generate Phase I source/route runtime reconciliation artifact."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from data_governance.phase_i_runtime import write_phase_i_runtime_reconciliation  # noqa: E402


def main() -> int:
    payload = write_phase_i_runtime_reconciliation()
    print(json.dumps({k: v for k, v in payload.items() if k != "rows"}, indent=2))
    ok = (
        payload["FULLY_ACCOUNTED_PHASE_I_SOURCE_ROUTES"] == payload["PHASE_I_SELECTED_SOURCE_ROUTES"]
        and payload["INCOMPLETE_LOCAL_PHASE_I_SOURCE_ROUTES"] == 0
        and payload["UNEXPLAINED_PHASE_I_ROWS"] == 0
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
