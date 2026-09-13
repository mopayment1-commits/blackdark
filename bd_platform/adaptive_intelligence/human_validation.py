"""Human Validation infrastructure — spec §29 (EXTERNAL_HUMAN_EVIDENCE_GATED for results)."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

_EVIDENCE_PATH = Path("data/adaptive_human_validation.jsonl")


def record_session(
    *,
    task_id: str,
    task_success: bool,
    time_to_insight_sec: float,
    comprehension_score: float,
    critical_omission: bool,
    decision_reversal: bool,
    over_reliance_indicator: bool,
    perceived_control: float,
    accessibility_task_completed: bool,
    protocol_version: str = "hv-1.0",
) -> dict[str, Any]:
    row = {
        "task_id": task_id,
        "task_success": task_success,
        "time_to_insight_sec": time_to_insight_sec,
        "comprehension_score": comprehension_score,
        "critical_omission": critical_omission,
        "decision_reversal_after_explanation": decision_reversal,
        "over_reliance_indicator": over_reliance_indicator,
        "perceived_control": perceived_control,
        "accessibility_task_completed": accessibility_task_completed,
        "protocol_version": protocol_version,
        "recorded_at": time.time(),
        "genuine_participant_evidence": False,
    }
    _EVIDENCE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _EVIDENCE_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row) + "\n")
    return row


def infrastructure_status() -> dict[str, Any]:
    return {
        "protocol_version": "hv-1.0",
        "metrics_supported": [
            "task_success",
            "time_to_insight",
            "comprehension",
            "critical_omission",
            "decision_reversal",
            "over_reliance",
            "perceived_control",
            "accessibility_task_completion",
        ],
        "genuine_participant_evidence_required": True,
        "implementation_complete": True,
        "status": "EXTERNAL_HUMAN_EVIDENCE_GATED",
    }
