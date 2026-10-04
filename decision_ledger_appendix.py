"""
Launch-57 Phase A — recommendation appendix for the unified decision ledger.

Append-only rows; does not replace `decision_ledger.record_decision` / decision_ledger.jsonl.
"""

from __future__ import annotations

import json
import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from path_safety import ensure_under, safe_data_file

_LOCK = threading.Lock()
_APPENDIX_PATH = safe_data_file("decision_ledger_recommendation_appendix.jsonl")
_DATA_BASE = Path(__file__).resolve().parent / "data"

_APPENDIX_FIELDS = (
    "decision_id",
    "tenant_id",
    "user_ref",
    "event_time",
    "asset",
    "market_state",
    "model_id",
    "model_version",
    "model_confidence",
    "recommendation",
    "user_action",
    "user_override",
    "outcome_horizon",
    "data_version",
    "feature_set_version",
    "actual_outcome",
    "label",
)


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _persist(row: dict[str, Any]) -> None:
    path = ensure_under(_APPENDIX_PATH, _DATA_BASE)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:  # NOSONAR pythonsecurity:S2083
        fh.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")


def append_recommendation_decision_record(
    *,
    decision_id: str,
    tenant_id: str,
    user_ref: str,
    event_time: str,
    asset: str,
    market_state: str,
    model_id: str,
    model_version: str,
    model_confidence: str | float | int,
    recommendation: str,
    user_action: str,
    user_override: str,
    outcome_horizon: str,
    data_version: str,
    feature_set_version: str,
) -> dict[str, Any]:
    """Append one recommendation-time row; outcome fields stay empty at write time."""
    row = {
        "decision_id": str(decision_id),
        "tenant_id": str(tenant_id),
        "user_ref": str(user_ref),
        "event_time": str(event_time),
        "asset": str(asset).upper(),
        "market_state": str(market_state),
        "model_id": str(model_id),
        "model_version": str(model_version),
        "model_confidence": model_confidence,
        "recommendation": str(recommendation),
        "user_action": str(user_action),
        "user_override": str(user_override),
        "outcome_horizon": str(outcome_horizon),
        "data_version": str(data_version),
        "feature_set_version": str(feature_set_version),
        "actual_outcome": "",
        "label": "",
    }
    with _LOCK:
        _persist(row)
    return dict(row)


def recommendation_row_from_oracle_enrichment(
    out: dict[str, Any],
    *,
    asset: str,
    verdict: str,
    decision_id: str,
    user_id: str | None,
    tier: str | None,
    event_time: str | None = None,
) -> dict[str, Any]:
    """Map existing oracle enrichment payload to appendix schema (no new behavior probes)."""
    dg = out.get("data_governance") if isinstance(out.get("data_governance"), dict) else {}
    data_version = str(
        out.get("data_version")
        or dg.get("dataset_version")
        or dg.get("version")
        or "unknown"
    )
    return append_recommendation_decision_record(
        decision_id=decision_id,
        tenant_id=str(out.get("tenant_id") or out.get("org_id") or tier or "default"),
        user_ref=str(user_id or out.get("user_id") or "anonymous"),
        event_time=event_time or _utcnow(),
        asset=asset,
        market_state=str(
            out.get("market_state")
            or out.get("macro_regime_proxy")
            or out.get("regime")
            or "unknown"
        ),
        model_id=str(out.get("model_id") or out.get("kind") or "oracle_direction"),
        model_version=str(out.get("model_version") or "unknown"),
        model_confidence=out.get("model_confidence") or out.get("opportunity_score") or 0,
        recommendation=str(out.get("decision_action") or verdict),
        user_action=str(out.get("user_action") or ""),
        user_override=str(out.get("user_override") or ""),
        outcome_horizon=str(out.get("outcome_horizon") or ""),
        data_version=data_version,
        feature_set_version=str(out.get("feature_set_version") or out.get("feature_version") or "unknown"),
    )


def appendix_write_path() -> Path:
    return ensure_under(_APPENDIX_PATH, _DATA_BASE)
