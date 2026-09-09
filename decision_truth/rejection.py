"""Opportunity rejection engine and Why NOT (DTS-019–020)."""

from __future__ import annotations

import json
import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

_LOCK = threading.Lock()
_STATS_PATH = Path(__file__).resolve().parents[1] / "data" / "decision_truth_rejections.jsonl"


def _ensure_dir() -> None:
    _STATS_PATH.parent.mkdir(parents=True, exist_ok=True)


def record_rejection(
    *,
    opportunity_id: str,
    admission_state: str,
    failed_gates: list[str],
    gross_edge: Any = None,
    expected_net_edge: Any = None,
    execution_score: Any = None,
    meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    row = {
        "recorded_at": datetime.now(UTC).isoformat(),
        "opportunity_id": opportunity_id,
        "admission_state": admission_state,
        "failed_gates": failed_gates,
        "gross_edge": gross_edge,
        "expected_net_edge": expected_net_edge,
        "execution_feasibility_score": execution_score,
        "meta": meta or {},
    }
    _ensure_dir()
    with _LOCK:
        with _STATS_PATH.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    return row


def build_why_not(
    *,
    admission: dict[str, Any],
    net_edge: dict[str, Any],
    execution: dict[str, Any],
    lang: str = "en",
) -> dict[str, Any]:
    from i18n_service import t

    state = admission.get("admission_state") or "ABSTAINED"
    failed = admission.get("failed_gates") or []
    codes = [f"gate.{g}" for g in failed]
    human = t("dts.why_not.rejected", lang) if state == "REJECTED" else t("dts.why_not.abstained", lang)
    return {
        "decision_state": state,
        "reason_codes": codes,
        "failed_gates": failed,
        "human_explanation": human,
        "gross_edge": net_edge.get("theoretical_edge_usd"),
        "expected_net_edge": net_edge.get("expected_net_edge_usd"),
        "realizable_net_edge": net_edge.get("realizable_net_edge_usd"),
        "execution_feasibility_score": execution.get("execution_feasibility_score"),
        "fill_probability": net_edge.get("fill_probability"),
    }


def rejection_stats() -> dict[str, Any]:
    detected = rejected = admitted = 0
    if _STATS_PATH.is_file():
        for line in _STATS_PATH.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            detected += 1
            st = row.get("admission_state")
            if st == "REJECTED":
                rejected += 1
            elif st == "ADMITTED":
                admitted += 1
    return {
        "detected": detected,
        "rejected": rejected,
        "admitted": admitted,
        "economically_viable": admitted,
        "evidence_gate_passed": admitted,
    }
