"""Human Validation infrastructure — spec §29 (EXTERNAL_HUMAN_EVIDENCE_GATED for results)."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

_EVIDENCE_PATH = Path("data/adaptive_human_validation.jsonl")
_PROTOCOL_VERSION = "hv-1.0"

TASK_PROTOCOL: tuple[dict[str, Any], ...] = (
    {"task_id": "hv-decide-btc", "goal": "Decide on BTC using oracle", "success_criteria": "user_reaches_actionable_stance"},
    {"task_id": "hv-verify-ledger", "goal": "Verify claim via accuracy ledger", "success_criteria": "user_identifies_limitation"},
    {"task_id": "hv-explore-capability", "goal": "Find capability via explorer", "success_criteria": "user_opens_correct_card"},
    {"task_id": "hv-a11y-keyboard", "goal": "Complete navigation via keyboard only", "success_criteria": "accessibility_task_completed"},
)


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
    consent: bool = True,
    protocol_version: str = _PROTOCOL_VERSION,
) -> dict[str, Any]:
    if not consent:
        raise ValueError("human_validation_requires_consent")
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
        "consent": True,
    }
    _EVIDENCE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _EVIDENCE_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row) + "\n")
    return row


def export_sessions(user_id: str | None = None) -> list[dict[str, Any]]:
    if not _EVIDENCE_PATH.is_file():
        return []
    rows = []
    for line in _EVIDENCE_PATH.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def delete_sessions() -> int:
    if not _EVIDENCE_PATH.is_file():
        return 0
    count = sum(1 for ln in _EVIDENCE_PATH.read_text(encoding="utf-8").splitlines() if ln.strip())
    _EVIDENCE_PATH.write_text("", encoding="utf-8")
    return count


def task_protocol() -> list[dict[str, Any]]:
    return [dict(t) for t in TASK_PROTOCOL]


def infrastructure_status() -> dict[str, Any]:
    return {
        "protocol_version": _PROTOCOL_VERSION,
        "task_definitions": task_protocol(),
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
        "evidence_storage": str(_EVIDENCE_PATH),
        "export_supported": True,
        "delete_supported": True,
        "consent_required": True,
        "genuine_participant_evidence_required": True,
        "implementation_complete": True,
        "status": "EXTERNAL_HUMAN_EVIDENCE_GATED",
    }
