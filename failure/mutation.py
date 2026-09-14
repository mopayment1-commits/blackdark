"""Indeterminate mutation outcomes and reconciliation lifecycle (ERR-006, ERR-046)."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from failure.states import MutationOutcome, ReconciliationState

_STORE = Path(__file__).resolve().parents[1] / "data" / "failure_mutation_outcomes.jsonl"


def _append(record: dict[str, Any]) -> None:
    _STORE.parent.mkdir(parents=True, exist_ok=True)
    with _STORE.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")


def record_mutation(
    *,
    operation_id: str,
    correlation_id: str,
    outcome: MutationOutcome,
    reconciliation: ReconciliationState | None = None,
    component: str,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    rec = {
        "operation_id": operation_id,
        "correlation_id": correlation_id,
        "outcome": outcome.value,
        "reconciliation": (reconciliation or ReconciliationState.REQUESTED).value,
        "component": component,
        "recorded_at": time.time(),
        "metadata": metadata or {},
    }
    _append(rec)
    return rec


def mark_indeterminate(*, operation_id: str, correlation_id: str, component: str) -> dict[str, Any]:
    return record_mutation(
        operation_id=operation_id,
        correlation_id=correlation_id,
        outcome=MutationOutcome.INDETERMINATE,
        reconciliation=ReconciliationState.INDETERMINATE,
        component=component,
    )


def resolve_reconciliation(
    *,
    operation_id: str,
    correlation_id: str,
    component: str,
    final_outcome: MutationOutcome,
) -> dict[str, Any]:
    recon = (
        ReconciliationState.CONFIRMED_SUCCESS
        if final_outcome == MutationOutcome.CONFIRMED_SUCCESS
        else ReconciliationState.CONFIRMED_FAILURE
    )
    return record_mutation(
        operation_id=operation_id,
        correlation_id=correlation_id,
        outcome=final_outcome,
        reconciliation=recon,
        component=component,
    )
