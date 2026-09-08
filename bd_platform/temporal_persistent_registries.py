"""Temporal persistent registries — event store, outcomes, evidence, shadow, champion/challenger."""

from __future__ import annotations

import json
import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from cap646.evidence_class import infer_evidence_class
from reproducibility_manifest import build_reproducibility_manifest

_DATA = Path("data")
_LOCK = threading.Lock()


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _append(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")


def _read(path: Path, *, limit: int = 2000) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines()[-limit:]:
        if line.strip():
            rows.append(json.loads(line))
    return rows


_EVENTS = _DATA / "temporal_canonical_events.jsonl"
_OUTCOMES = _DATA / "temporal_outcome_factory.jsonl"
_EVIDENCE = _DATA / "temporal_evidence_ledger.jsonl"
_SHADOW = _DATA / "temporal_forward_shadow.jsonl"
_CHAMPION = _DATA / "temporal_champion_challenger.jsonl"
_REGIME = _DATA / "temporal_regime_registry.jsonl"
_SURPRISE = _DATA / "temporal_surprise_events.jsonl"
_ABSTAIN = _DATA / "temporal_abstention_events.jsonl"


def register_canonical_event(
    *,
    source_id: str,
    event_time: str,
    observed_time: str,
    available_time: str,
    processing_time: str | None = None,
    payload: dict[str, Any] | None = None,
    schema_version: str = "temporal_v1",
) -> dict[str, Any]:
    row = {
        "event_id": f"tev_{uuid4().hex[:16]}",
        "source_id": source_id,
        "event_time": event_time,
        "observed_time": observed_time,
        "available_time": available_time,
        "processing_time": processing_time or _utcnow(),
        "schema_version": schema_version,
        "payload": payload or {},
        "immutable": True,
        "registered_at": _utcnow(),
    }
    with _LOCK:
        _append(_EVENTS, row)
    return row


def list_canonical_events(*, source_id: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
    rows = _read(_EVENTS, limit=limit)
    if source_id:
        rows = [r for r in rows if r.get("source_id") == source_id]
    return rows


def register_outcome_observation(
    *,
    prediction_id: str,
    decision_id: str | None,
    horizon_sec: int,
    label: str,
    quality_score: float,
    delayed: bool = False,
    corrected: bool = False,
) -> dict[str, Any]:
    row = {
        "outcome_id": f"out_{uuid4().hex[:14]}",
        "prediction_id": prediction_id,
        "decision_id": decision_id,
        "horizon_sec": horizon_sec,
        "label": label,
        "quality_score": quality_score,
        "delayed": delayed,
        "corrected": corrected,
        "evidence_class": infer_evidence_class(source="historical_replay"),
        "live_promotion": False,
        "registered_at": _utcnow(),
    }
    with _LOCK:
        _append(_OUTCOMES, row)
    return row


def register_evidence_record(
    *,
    chain_stage: str,
    object_id: str,
    version: str,
    evidence_class: str,
    manifest_id: str | None = None,
    meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    manifest = build_reproducibility_manifest(dataset_id=object_id, seed=1, evidence_class=evidence_class)
    row = {
        "evidence_id": f"evd_{uuid4().hex[:14]}",
        "chain_stage": chain_stage,
        "object_id": object_id,
        "version": version,
        "evidence_class": evidence_class,
        "manifest_id": manifest_id or manifest.get("manifest_id"),
        "meta": meta or {},
        "registered_at": _utcnow(),
    }
    with _LOCK:
        _append(_EVIDENCE, row)
    return row


def register_forward_shadow_record(
    *,
    decision_snapshot: dict[str, Any],
    expected_evidence_class: str = "FORWARD_SHADOW",
) -> dict[str, Any]:
    row = {
        "shadow_id": f"fsh_{uuid4().hex[:14]}",
        "decision_snapshot": decision_snapshot,
        "expected_evidence_class": expected_evidence_class,
        "elapsed_evidence": False,
        "live_promotion": False,
        "registered_at": _utcnow(),
    }
    with _LOCK:
        _append(_SHADOW, row)
    return row


def register_champion_challenger_comparison(
    *,
    champion_id: str,
    challenger_id: str,
    evaluation_criteria: dict[str, Any],
    promotion_allowed: bool = False,
) -> dict[str, Any]:
    row = {
        "comparison_id": f"cc_{uuid4().hex[:14]}",
        "champion_id": champion_id,
        "challenger_id": challenger_id,
        "evaluation_criteria": evaluation_criteria,
        "promotion_allowed": promotion_allowed,
        "verified_production": False,
        "registered_at": _utcnow(),
    }
    with _LOCK:
        _append(_CHAMPION, row)
    return row


def register_regime_label(
    *,
    regime: str,
    as_of: str,
    confidence: float,
    version: str = "regime_v1",
) -> dict[str, Any]:
    row = {
        "regime_id": f"reg_{uuid4().hex[:12]}",
        "regime": regime,
        "as_of": as_of,
        "confidence": confidence,
        "version": version,
        "production_accuracy_claim": False,
        "registered_at": _utcnow(),
    }
    with _LOCK:
        _append(_REGIME, row)
    return row


def register_surprise_event(*, source: str, reason: str, linked_decision_id: str | None = None) -> dict[str, Any]:
    row = {
        "surprise_id": f"sur_{uuid4().hex[:12]}",
        "source": source,
        "reason": reason,
        "linked_decision_id": linked_decision_id,
        "registered_at": _utcnow(),
    }
    with _LOCK:
        _append(_SURPRISE, row)
    return row


def register_abstention_event(*, reason_code: str, decision_context: dict[str, Any]) -> dict[str, Any]:
    row = {
        "abstention_id": f"abs_{uuid4().hex[:12]}",
        "reason_code": reason_code,
        "decision_context": decision_context,
        "registered_at": _utcnow(),
    }
    with _LOCK:
        _append(_ABSTAIN, row)
    return row


def registry_status() -> dict[str, Any]:
    return {
        "canonical_events": {"store": str(_EVENTS), "count": len(_read(_EVENTS, limit=5000))},
        "outcome_factory": {"store": str(_OUTCOMES), "count": len(_read(_OUTCOMES, limit=5000))},
        "evidence_ledger": {"store": str(_EVIDENCE), "count": len(_read(_EVIDENCE, limit=5000))},
        "forward_shadow": {"store": str(_SHADOW), "count": len(_read(_SHADOW, limit=5000))},
        "champion_challenger": {"store": str(_CHAMPION), "count": len(_read(_CHAMPION, limit=5000))},
        "regime": {"store": str(_REGIME), "count": len(_read(_REGIME, limit=5000))},
        "surprise": {"store": str(_SURPRISE), "count": len(_read(_SURPRISE, limit=5000))},
        "abstention": {"store": str(_ABSTAIN), "count": len(_read(_ABSTAIN, limit=5000))},
    }


def bootstrap_temporal_registries() -> dict[str, Any]:
    if not list_canonical_events(limit=1):
        register_canonical_event(
            source_id="temporal_seed",
            event_time="2026-01-01T00:00:00+00:00",
            observed_time="2026-01-01T00:00:01+00:00",
            available_time="2026-01-01T00:00:01+00:00",
        )
    if not _read(_OUTCOMES, limit=1):
        register_outcome_observation(
            prediction_id="pred_seed",
            decision_id=None,
            horizon_sec=3600,
            label="pending",
            quality_score=0.5,
        )
    if not _read(_EVIDENCE, limit=1):
        register_evidence_record(
            chain_stage="signal",
            object_id="temporal_seed",
            version="v1",
            evidence_class="HISTORICAL_REPLAY",
        )
    if not _read(_SHADOW, limit=1):
        register_forward_shadow_record(decision_snapshot={"symbol": "BTC", "action": "shadow"})
    if not _read(_CHAMPION, limit=1):
        register_champion_challenger_comparison(
            champion_id="champ_v1",
            challenger_id="chall_v1",
            evaluation_criteria={"metric": "replay_fidelity"},
            promotion_allowed=False,
        )
    if not _read(_REGIME, limit=1):
        register_regime_label(regime="neutral", as_of="2026-01-01T00:00:00+00:00", confidence=0.6)
    return registry_status()
