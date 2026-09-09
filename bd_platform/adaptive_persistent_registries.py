"""Adaptive persistent registries — workspace, playbook, My Stack, trust, validation, recommendations."""

from __future__ import annotations

import json
import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from cap646.evidence_class import infer_evidence_class

_DATA = Path("data")
_LOCK = threading.Lock()

_WORKSPACES = _DATA / "adaptive_workspaces.jsonl"
_PLAYBOOKS = _DATA / "adaptive_playbooks.jsonl"
_MY_STACK = _DATA / "adaptive_my_stack.jsonl"
_TRUST = _DATA / "adaptive_trust_status.jsonl"
_HUMAN = _DATA / "adaptive_human_validation.jsonl"
_RECOMMEND = _DATA / "adaptive_contextual_recommendations.jsonl"
_DATA_ROOM = _DATA / "adaptive_data_room_access.jsonl"
_HEROES = _DATA / "adaptive_six_heroes_disposition.jsonl"


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


def register_workspace(
    *,
    user_id: str,
    name: str,
    selected_capabilities: list[int],
    evidence_refs: list[str] | None = None,
    layout: dict[str, Any] | None = None,
) -> dict[str, Any]:
    row = {
        "workspace_id": f"ws_{uuid4().hex[:14]}",
        "user_id": user_id,
        "name": name,
        "selected_capabilities": selected_capabilities,
        "evidence_refs": evidence_refs or [],
        "layout": layout or {},
        "version": "adaptive_ws_v1",
        "registered_at": _utcnow(),
    }
    with _LOCK:
        _append(_WORKSPACES, row)
    return row


def register_playbook(
    *,
    name: str,
    steps: list[dict[str, Any]],
    prerequisites: list[str] | None = None,
    decision_checkpoints: list[str] | None = None,
) -> dict[str, Any]:
    row = {
        "playbook_id": f"pb_{uuid4().hex[:14]}",
        "name": name,
        "steps": steps,
        "prerequisites": prerequisites or [],
        "decision_checkpoints": decision_checkpoints or [],
        "version": "adaptive_pb_v1",
        "registered_at": _utcnow(),
    }
    with _LOCK:
        _append(_PLAYBOOKS, row)
    return row


def register_my_stack_entry(
    *,
    user_id: str,
    capability_id: int,
    tier: str,
    entitlement_verified: bool,
) -> dict[str, Any]:
    row = {
        "stack_id": f"stk_{uuid4().hex[:12]}",
        "user_id": user_id,
        "capability_id": capability_id,
        "tier": tier,
        "entitlement_verified": entitlement_verified,
        "version": "adaptive_stack_v1",
        "registered_at": _utcnow(),
    }
    with _LOCK:
        _append(_MY_STACK, row)
    return row


def register_trust_status(
    *,
    object_id: str,
    assurance: str,
    freshness: str,
    availability: str,
    coverage: str,
    methodology: str,
    evidence_class: str,
) -> dict[str, Any]:
    row = {
        "trust_id": f"tr_{uuid4().hex[:12]}",
        "object_id": object_id,
        "dimensions": {
            "assurance": assurance,
            "freshness": freshness,
            "availability": availability,
            "coverage": coverage,
            "methodology": methodology,
            "evidence_class": evidence_class,
        },
        "collapsed_score": None,
        "registered_at": _utcnow(),
    }
    with _LOCK:
        _append(_TRUST, row)
    return row


def register_human_validation(
    *,
    decision_context: dict[str, Any],
    review_status: str,
    reason_code: str,
    evidence_link: str | None = None,
) -> dict[str, Any]:
    row = {
        "validation_id": f"hv_{uuid4().hex[:12]}",
        "decision_context": decision_context,
        "review_status": review_status,
        "reason_code": reason_code,
        "evidence_link": evidence_link,
        "rewrites_historical_truth": False,
        "registered_at": _utcnow(),
    }
    with _LOCK:
        _append(_HUMAN, row)
    return row


def register_contextual_recommendation(
    *,
    intent: str,
    capability_id: int,
    governance: dict[str, Any],
    promotion_allowed: bool = False,
) -> dict[str, Any]:
    row = {
        "recommendation_id": f"rec_{uuid4().hex[:12]}",
        "intent": intent,
        "capability_id": capability_id,
        "governance": governance,
        "promotion_allowed": promotion_allowed,
        "personal_suitability_inferred": False,
        "registered_at": _utcnow(),
    }
    with _LOCK:
        _append(_RECOMMEND, row)
    return row


def register_data_room_access(
    *,
    tenant_id: str,
    artifact_ref: str,
    view_type: str,
    entitlement_verified: bool,
) -> dict[str, Any]:
    row = {
        "access_id": f"dr_{uuid4().hex[:12]}",
        "tenant_id": tenant_id,
        "artifact_ref": artifact_ref,
        "view_type": view_type,
        "entitlement_verified": entitlement_verified,
        "parallel_truth_system": False,
        "ssot_view_only": True,
        "registered_at": _utcnow(),
    }
    with _LOCK:
        _append(_DATA_ROOM, row)
    return row


def register_six_heroes_disposition(
    *,
    requirement_id: str,
    hero: str | None,
    surface: str,
    no_user_surface_required: bool = False,
) -> dict[str, Any]:
    row = {
        "disposition_id": f"sh_{uuid4().hex[:10]}",
        "requirement_id": requirement_id,
        "hero": hero,
        "surface": surface,
        "no_user_surface_required": no_user_surface_required,
        "registered_at": _utcnow(),
    }
    with _LOCK:
        _append(_HEROES, row)
    return row


def registry_status() -> dict[str, Any]:
    return {
        "workspaces": {"store": str(_WORKSPACES), "count": len(_read(_WORKSPACES, limit=5000))},
        "playbooks": {"store": str(_PLAYBOOKS), "count": len(_read(_PLAYBOOKS, limit=5000))},
        "my_stack": {"store": str(_MY_STACK), "count": len(_read(_MY_STACK, limit=5000))},
        "trust_status": {"store": str(_TRUST), "count": len(_read(_TRUST, limit=5000))},
        "human_validation": {"store": str(_HUMAN), "count": len(_read(_HUMAN, limit=5000))},
        "recommendations": {"store": str(_RECOMMEND), "count": len(_read(_RECOMMEND, limit=5000))},
        "data_room": {"store": str(_DATA_ROOM), "count": len(_read(_DATA_ROOM, limit=5000))},
        "six_heroes": {"store": str(_HEROES), "count": len(_read(_HEROES, limit=5000))},
    }


def bootstrap_adaptive_registries() -> dict[str, Any]:
    if not _read(_WORKSPACES, limit=1):
        register_workspace(user_id="seed", name="default", selected_capabilities=[609, 613])
    if not _read(_PLAYBOOKS, limit=1):
        register_playbook(
            name="decision_checkpoint",
            steps=[{"step": 1, "action": "review_evidence"}],
            decision_checkpoints=["evidence_review"],
        )
    if not _read(_MY_STACK, limit=1):
        register_my_stack_entry(user_id="seed", capability_id=609, tier="free", entitlement_verified=True)
    if not _read(_TRUST, limit=1):
        register_trust_status(
            object_id="seed",
            assurance="catalog_only",
            freshness="not_live_verified",
            availability="local",
            coverage="partial",
            methodology="deterministic",
            evidence_class=infer_evidence_class(source="historical_replay"),
        )
    if not _read(_HUMAN, limit=1):
        register_human_validation(
            decision_context={"goal": "seed"},
            review_status="pending",
            reason_code="initial",
        )
    if not _read(_RECOMMEND, limit=1):
        register_contextual_recommendation(
            intent="liquidation",
            capability_id=613,
            governance={"entitlement": True, "freshness": "checked", "conflict": "none"},
        )
    if not _read(_DATA_ROOM, limit=1):
        register_data_room_access(
            tenant_id="seed",
            artifact_ref="docs/V4_V2_SOURCE_DRIVEN_FINAL_FREEZE.json",
            view_type="read_only",
            entitlement_verified=True,
        )
    if not _read(_HEROES, limit=1):
        register_six_heroes_disposition(
            requirement_id="ADAPTIVE_U0006",
            hero="Oracle",
            surface="capability_explorer",
        )
    return registry_status()
