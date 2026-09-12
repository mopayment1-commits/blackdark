"""Champion/Challenger promotion gates — DSR-018, D-15."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from blackdark.data_governance._paths import PROMOTION_GATES_PATH, ensure_governance_dirs


def evaluate_promotion_gate(
    *,
    champion_id: str,
    challenger_id: str,
    hypothesis: str,
    baseline_metric: float,
    challenger_metric: float,
    non_regression_pass: bool,
    sample_coverage: str,
    approver: str,
    rollback_trigger: str,
) -> dict[str, Any]:
    """Pre-defined promotion gate — no promotion without reproducible evidence."""
    ensure_governance_dirs()
    promoted = (
        challenger_metric >= baseline_metric
        and non_regression_pass
        and sample_coverage in {"adequate", "full", "regime_balanced"}
    )
    record = {
        "gate_id": f"promo_{uuid4().hex[:12]}",
        "champion_id": champion_id,
        "challenger_id": challenger_id,
        "hypothesis": hypothesis,
        "baseline_metric": baseline_metric,
        "challenger_metric": challenger_metric,
        "non_regression_pass": non_regression_pass,
        "sample_coverage": sample_coverage,
        "rollback_trigger": rollback_trigger,
        "approver": approver,
        "promoted": promoted,
        "evaluated_at": datetime.now(UTC).isoformat(),
    }
    with PROMOTION_GATES_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
    return record
