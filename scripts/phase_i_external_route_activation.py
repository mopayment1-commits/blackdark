#!/usr/bin/env python3
"""Generate Phase I external route activation readiness matrix."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "institutional_due_diligence_2026/DATA_GOV_COMPLIANCE/PHASE_I_EXTERNAL_ROUTE_ACTIVATION_READINESS.json"

from data_governance.phase_i_external_clients import (  # noqa: E402
    build_external_route_activation_readiness,
    verify_external_route_activation_gate,
)


def main() -> int:
    payload = build_external_route_activation_readiness()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    gate = verify_external_route_activation_gate()
    summary = {k: v for k, v in payload.items() if k != "rows"}
    print(json.dumps(summary, indent=2))
    return 0 if gate["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
