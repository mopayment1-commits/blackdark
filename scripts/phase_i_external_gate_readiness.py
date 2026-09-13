#!/usr/bin/env python3
"""Generate Phase I external-gate readiness matrix."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "institutional_due_diligence_2026/DATA_GOV_COMPLIANCE/PHASE_I_EXTERNAL_GATE_READINESS_MATRIX.json"

from data_governance.phase_i_external_adapters import build_external_gate_readiness_matrix  # noqa: E402


def main() -> int:
    payload = build_external_gate_readiness_matrix()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in payload.items() if k != "rows"}, indent=2))
    ok = (
        payload["EXTERNAL_GATED_ROUTES_AUDITED"] == 7
        and payload["EXTERNAL_GATED_ROUTES_WITH_LOCAL_ENGINEERING_REMAINING"] == 0
        and payload["EXTERNAL_GATED_ROUTES_WITHOUT_ACTIVATION_READINESS"] == 0
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
