"""Launch-57 Support Plane — §31.1 human validation register evidence chain."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REGISTER = ROOT / "governance" / "launch57" / "SUPPORT_PLANE_HUMAN_VALIDATION_REGISTER.json"

REQUIRED_DIMENSIONS = (
    "task_success",
    "time_to_insight",
    "comprehension_reason_limitation_uncertainty",
    "critical_omission_rate",
    "explanation_corrects_misunderstanding",
    "automation_bias_indicators",
    "perceived_user_control",
    "accessibility_task_completion",
)


def test_human_validation_register_exists_with_section_31_1_dimensions():
    data = json.loads(REGISTER.read_text(encoding="utf-8"))
    dims = data.get("required_dimensions") or {}
    for key in REQUIRED_DIMENSIONS:
        assert key in dims, f"missing §31.1 dimension: {key}"
        assert dims[key].get("status") in ("PENDING", "PASS_ENGINEERING")
    assert data.get("study_status") == "ENGINEERING_PROXY_COMPLETE"
