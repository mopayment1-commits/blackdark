"""
Launch-57 Phase 2 — Trust Batch 1 canonical runtime spine.

Build order: #6 evidence display → #5 CAP-0639 → #4 CAP-0640 → #3 CAP-0641 → #2 oracle sentence
B4: #2/#3 decision timing via launch57.decision_timing_common (SPEC §13).
B5: #4 public accuracy ledger timing via launch57.public_accuracy_common (SPEC §14).
B6: #5/#43 net-edge timing via launch57.net_edge_timing_common (SPEC §15).
"""

from __future__ import annotations

from typing import Any

from launch57.b4_decision_bridge import apply_b4_trust_envelope, finalize_b4_decision_surface
from launch57.b5_public_accuracy_bridge import finalize_b5_ledger_surface
from launch57.b6_net_edge_bridge import finalize_b6_net_edge_surface
from launch57.decision_timing_common import (
    build_decision_timing_context,
    build_launch57_decision_certificate,
    build_oracle_decision_record,
    snapshot_decision_time_evidence_state,
)
from launch57.evidence_class_common import assess_user_evidence_class
from launch57.trust_adaptive_common import (
    attach_adaptive_disclosure,
    build_level1_decision_disclosure,
    build_net_edge_safety_floor,
)

LAUNCH57_TRUST_BATCH1_CAP_IDS: frozenset[int] = frozenset({639, 640, 641})

LAUNCH_ITEM_BY_CAP: dict[int, int] = {
    639: 5,
    640: 4,
    641: 3,
}


def user_evidence_display(payload: dict[str, Any]) -> dict[str, Any]:
    """Launch #6 — visible evidence class (LIVE / DELAYED / SIM) via canonical #6 owner."""
    assessment = assess_user_evidence_class(payload)
    return assessment.to_payload()


async def evidence_class_surface(*, symbol: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Launch #6 — independent evidence-class judgment surface (launch_item_id=6)."""
    from launch57.decision_common import load_decision_spine

    p = dict(params or {})
    asset = str(symbol or p.get("symbol") or "BTC").upper().replace("/USDT", "")
    spine = await load_decision_spine(asset, p)
    payload = {
        **p,
        "symbol": asset,
        "freshness_state": spine.get("freshness_state"),
        "source": p.get("source") or (spine.get("data_spine") or {}).get("source"),
        "evidence_class": p.get("evidence_class") or p.get("canonical_evidence_class"),
    }
    display = user_evidence_display(payload)
    body = {
        "launch_item_id": 6,
        "surface": "evidence_class_visible",
        "symbol": asset,
        "success": True,
        "evidence_display": display,
        "user_facing_label": display.get("user_facing_label"),
        "canonical_evidence_class": display.get("canonical_evidence_class"),
        "freshness_state": spine.get("freshness_state"),
        "presented_as_live": spine.get("presented_as_live"),
        "backend_module": "launch57.trust_batch1",
        "backend_entrypoint": "evidence_class_surface",
        "binding_source": "launch57_phase2_trust_batch1",
    }
    return attach_trust_envelope(body)


def attach_trust_envelope(body: dict[str, Any]) -> dict[str, Any]:
    """Attach Launch #6 evidence display + compliance footer to trust outputs."""
    return apply_b4_trust_envelope(body)


def _is_demo_opportunity(opportunity: dict[str, Any] | None) -> bool:
    if not opportunity:
        return False
    from net_edge_truth import FIN_004_DEMO_OPPORTUNITY

    if opportunity.get("demo") or opportunity.get("synthetic") or opportunity.get("source") == "demo":
        return True
    demo_keys = ("net_profit_usdt", "quote_amount", "total_slippage_bps", "quote_age_ms")
    if all(opportunity.get(k) == FIN_004_DEMO_OPPORTUNITY.get(k) for k in demo_keys):
        return True
    return False


async def net_edge_truth_score(*, symbol: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Launch #5 / CAP-0639 — Net-Edge before any cost claim; no demo-as-live."""
    from net_edge_truth import compute_net_edge_truth

    p = dict(params or {})
    opportunity = p.get("opportunity")

    if not opportunity:
        body = {
            "capability_id": 639,
            "launch_item_id": 5,
            "surface": "net_edge_truth_score",
            "symbol": symbol,
            "success": False,
            "error": "opportunity_required",
            "net_edge_truth_score": None,
            "demo_path_blocked": True,
            "cost_claim_allowed": False,
            "note": "Net-Edge requires explicit opportunity payload — FIN_004 demo not used as production.",
            "backend_module": "launch57.trust_batch1",
            "backend_entrypoint": "net_edge_truth_score",
            "binding_source": "launch57_phase2_trust_batch1",
        }
        return attach_trust_envelope(body)

    if _is_demo_opportunity(opportunity):
        body = {
            "capability_id": 639,
            "launch_item_id": 5,
            "surface": "net_edge_truth_score",
            "symbol": symbol,
            "success": False,
            "error": "demo_opportunity_rejected",
            "net_edge_truth_score": None,
            "demo_path_blocked": True,
            "cost_claim_allowed": False,
            "note": "Demo/synthetic opportunity cannot produce live cost claims.",
            "backend_module": "launch57.trust_batch1",
            "backend_entrypoint": "net_edge_truth_score",
            "binding_source": "launch57_phase2_trust_batch1",
        }
        return attach_trust_envelope(body)

    score = compute_net_edge_truth(opportunity)
    cost_claim_allowed = bool(score.get("pass")) and not score.get("reject")
    body = {
        "capability_id": 639,
        "launch_item_id": 5,
        "surface": "net_edge_truth_score",
        "symbol": symbol,
        "success": True,
        "net_edge_truth_score": score,
        "cost_claim_allowed": cost_claim_allowed,
        "net_edge_before_cost_claim": True,
        "demo_path_blocked": True,
        "backend_module": "launch57.trust_batch1",
        "backend_entrypoint": "net_edge_truth_score",
        "binding_source": "launch57_phase2_trust_batch1",
    }
    finalized = finalize_b6_net_edge_surface(
        body,
        payload=p,
        opportunity=opportunity,
        display_timezone=p.get("display_timezone"),
    )
    if finalized.get("success"):
        score = finalized.get("net_edge_truth_score") or {}
        safety_floor = build_net_edge_safety_floor(score, opportunity)
        disclosure = build_level1_decision_disclosure(
            p,
            launch_item_id=5,
            surface="net_edge_truth_score",
            answer_state="NET_EDGE_EVALUATED",
            evidence_display=finalized.get("evidence_display"),
            decision_timing=finalized.get("opportunity_timing"),
            uncertainty="qualified" if score.get("reject") else "actionable_with_caveats",
        )
        finalized = attach_adaptive_disclosure(finalized, disclosure, extra={"net_edge_safety_floor": safety_floor})
        finalized["net_edge_safety_floor"] = safety_floor
    return finalized


async def public_accuracy_ledger(*, symbol: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Launch #4 / CAP-0640 — live ledger only; synthetic excluded from primary metrics."""
    from oracle_track_record import public_track_record

    p = dict(params or {})
    ledger = public_track_record()
    cumulative = ledger.get("cumulative") or {}
    synthetic = ledger.get("synthetic_demo_data") or {}

    body = {
        "capability_id": 640,
        "launch_item_id": 4,
        "surface": "public_accuracy_ledger",
        "symbol": symbol,
        "success": True,
        "ledger": ledger,
        "public_accuracy_ledger": ledger,
        "metrics_scope": cumulative.get("metrics_scope") or "live_only",
        "synthetic_excluded_from_primary": synthetic.get("excluded_from_primary_metrics", True),
        "shadow_ledger_not_production": True,
        "live_only_primary": True,
        "source": p.get("source"),
        "evidence_class": p.get("evidence_class"),
        "backend_module": "launch57.trust_batch1",
        "backend_entrypoint": "public_accuracy_ledger",
        "binding_source": "launch57_phase2_trust_batch1",
    }
    return finalize_b5_ledger_surface(body, display_timezone=p.get("display_timezone"))


async def decision_certificate_export(*, symbol: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Launch #3 / CAP-0641 — decision certificate + hash (Launch-57-local builder)."""
    p = dict(params or {})
    p["symbol"] = symbol

    timing = build_decision_timing_context(
        p,
        display_timezone=p.get("display_timezone"),
        require_authoritative_decision_time=True,
    )
    if timing is None:
        body = {
            "capability_id": 641,
            "launch_item_id": 3,
            "surface": "decision_certificate_institutional_dd_export",
            "symbol": symbol,
            "success": False,
            "error": "decision_time_required",
            "certificate": None,
            "decision_certificate": None,
            "certificate_hash": None,
            "backend_module": "launch57.trust_batch1",
            "backend_entrypoint": "decision_certificate_export",
            "binding_source": "launch57_phase2_trust_batch1",
        }
        return apply_b4_trust_envelope(body)

    evidence = snapshot_decision_time_evidence_state(p, display_timezone=p.get("display_timezone"))
    cert_source = dict(p)
    cert_source.setdefault("symbol", symbol)
    cert_source.setdefault("tier", "free")
    cert_source.setdefault("decision_action", p.get("verdict") or "WAIT")
    cert_source.setdefault("decision_sentence", p.get("oracle"))
    cert = build_launch57_decision_certificate(cert_source, timing=timing, evidence=evidence)
    governed = dict(p.get("governed_payload") or {})
    governed.setdefault("decision_time", timing.decision_time)
    governed.setdefault("issued_at", timing.issued_at)
    governed.setdefault("certificate_timestamp", timing.certificate_timestamp)
    body = {
        "capability_id": 641,
        "launch_item_id": 3,
        "surface": "decision_certificate_institutional_dd_export",
        "symbol": symbol,
        "success": bool(cert.get("certificate_hash")),
        "certificate": cert,
        "decision_certificate": cert,
        "certificate_hash": cert.get("certificate_hash"),
        "export_format": p.get("format") or "json",
        "governed_payload": governed,
        "decision_time": timing.decision_time,
        "source": p.get("source"),
        "evidence_class": p.get("evidence_class"),
        "backend_module": "launch57.trust_batch1",
        "backend_entrypoint": "decision_certificate_export",
        "binding_source": "launch57_phase2_trust_batch1",
    }
    finalized = finalize_b4_decision_surface(
        body,
        display_timezone=p.get("display_timezone"),
        require_authoritative_decision_time=False,
    )
    if finalized is None:
        body["success"] = False
        body["error"] = "decision_timing_finalize_failed"
        return apply_b4_trust_envelope(body)
    finalized["certificate"] = cert
    finalized["decision_certificate"] = cert
    finalized["certificate_hash"] = cert.get("certificate_hash")
    disclosure = build_level1_decision_disclosure(
        p,
        launch_item_id=3,
        surface="decision_certificate_institutional_dd_export",
        answer_state=str(cert.get("decision_action") or "WAIT"),
        evidence_display=finalized.get("evidence_display"),
        decision_timing=finalized.get("decision_timing"),
    )
    return attach_adaptive_disclosure(finalized, disclosure)


async def single_sentence_oracle(*, symbol: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Launch #2 — Single-Sentence Oracle (ACT/WAIT/ABSTAIN) product surface."""
    p = dict(params or {})
    p["symbol"] = symbol
    governed = p.get("governed_payload")

    if governed:
        action = str(governed.get("decision_action") or governed.get("verdict") or "WAIT").upper()
        sentence = governed.get("decision_sentence") or governed.get("oracle") or f"{symbol}: {action}"
    else:
        action = str(p.get("decision_action") or "WAIT").upper()
        if action in {"BUY", "ACT", "LONG"}:
            action = "ACT"
        elif action in {"ABSTAIN", "NO_DECISION"}:
            action = "ABSTAIN"
        else:
            action = "WAIT" if action not in {"ACT", "WAIT", "ABSTAIN", "CAUTION"} else action
        sentence = p.get("decision_sentence") or f"{symbol}: {action} — governed oracle sentence."

    timing = build_decision_timing_context(p, display_timezone=p.get("display_timezone"))
    evidence = snapshot_decision_time_evidence_state(p, display_timezone=p.get("display_timezone"))
    body = build_oracle_decision_record(
        p,
        timing=timing,
        evidence=evidence,
        action=action,
        sentence=sentence,
    )
    for key in ("source", "evidence_class", "canonical_evidence_class", "freshness_state", "governed_payload"):
        if key in p:
            body[key] = p[key]
    finalized = finalize_b4_decision_surface(body, display_timezone=p.get("display_timezone"))
    if finalized is None:
        body["success"] = False
        body["error"] = "decision_timing_finalize_failed"
        return apply_b4_trust_envelope(body)
    disclosure = build_level1_decision_disclosure(
        p,
        launch_item_id=2,
        surface="single_sentence_oracle",
        answer_state=action,
        evidence_display=finalized.get("evidence_display"),
        decision_timing=finalized.get("decision_timing"),
    )
    return attach_adaptive_disclosure(finalized, disclosure)


_DISPATCH_ENTRYPOINTS: dict[int, str] = {
    639: "net_edge_truth_score",
    640: "public_accuracy_ledger",
    641: "decision_certificate_export",
}


async def execute_launch57_trust_batch1(capability_id: int, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
    if capability_id not in LAUNCH57_TRUST_BATCH1_CAP_IDS:
        raise ValueError(f"capability {capability_id} not in Launch-57 trust batch 1")
    entrypoint = _DISPATCH_ENTRYPOINTS[capability_id]
    fn = globals()[entrypoint]
    sym = str((params or {}).get("symbol") or "BTC")
    return await fn(symbol=sym, params=dict(params or {}))
