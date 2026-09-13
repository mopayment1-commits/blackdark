#!/usr/bin/env python3
"""Register genuine external/live evidence gates (§34)."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "institutional_due_diligence_2026/DATA_GOV_COMPLIANCE"

GATES = [
    {
        "requirement": "DATA-054 provider contractual SLA",
        "local_engineering_completed": True,
        "external_dependency": "Vendor contractual SLA documents",
        "why_external": "Cannot invent contractual SLA; local SLO framework and PROVIDER_SLA=NONE implemented",
        "future_evidence_procedure": "Attach signed SLA artifact per source when obtained",
        "pass_criterion": "SLA artifact on file or PROVIDER_SLA=NONE with measured internal SLO",
        "NO_LOCAL_ENGINEERING_REMAINS": True,
        "status": "GENUINE_EXTERNAL_DEPENDENCY_GATED",
    },
    {
        "requirement": "DATA-077 redistribution/licensing legal evidence",
        "local_engineering_completed": True,
        "external_dependency": "Provider terms / legal review for redistribution",
        "why_external": "Legal conclusions cannot be manufactured locally",
        "future_evidence_procedure": "Rights registry entry with counsel-reviewed classification",
        "pass_criterion": "rights_state != UNDOCUMENTED for production redistribution",
        "NO_LOCAL_ENGINEERING_REMAINS": True,
        "status": "GENUINE_EXTERNAL_DEPENDENCY_GATED",
    },
    {
        "requirement": "Live provider reliability SLO measurement",
        "local_engineering_completed": True,
        "external_dependency": "Production traffic over real time",
        "why_external": "Measured live reliability requires production operation",
        "future_evidence_procedure": "Prometheus/Grafana SLO dashboard from production",
        "pass_criterion": "30d measured availability/freshness meets internal SLO",
        "NO_LOCAL_ENGINEERING_REMAINS": True,
        "status": "LIVE_PRODUCTION_EVIDENCE_GATED",
    },
    {
        "requirement": "Production backup/restore drill",
        "local_engineering_completed": True,
        "external_dependency": "Production environment restore",
        "why_external": "Local restore test completed; production drill requires prod infra",
        "future_evidence_procedure": "Quarterly production restore drill log",
        "pass_criterion": "RTO/RPO met in production drill",
        "NO_LOCAL_ENGINEERING_REMAINS": True,
        "status": "LIVE_PRODUCTION_EVIDENCE_GATED",
    },
    {
        "requirement": "DATA-092 GLBA applicability",
        "local_engineering_completed": True,
        "external_dependency": "Professional legal applicability determination",
        "why_external": "GLBA applicability is documented determination not assumed requirement",
        "future_evidence_procedure": "Legal memo in institutional_due_diligence",
        "pass_criterion": "Applicability register entry with counsel sign-off",
        "NO_LOCAL_ENGINEERING_REMAINS": True,
        "status": "GENUINE_EXTERNAL_DEPENDENCY_GATED",
    },
]


def main() -> int:
    invalid = [g for g in GATES if not g.get("NO_LOCAL_ENGINEERING_REMAINS")]
    payload = {
        "EXTERNAL_GATES_COUNT": len(GATES),
        "EXTERNAL_GATES_CONTAIN_NO_LOCAL_ENGINEERING": len(invalid) == 0,
        "PASS_LIVE_NOT_CLAIMED": True,
        "gates": GATES,
    }
    (OUT_DIR / "DATA_GOV_EXTERNAL_GATES.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in payload.items() if k != "gates"}, indent=2))
    return 0 if not invalid else 1


if __name__ == "__main__":
    raise SystemExit(main())
