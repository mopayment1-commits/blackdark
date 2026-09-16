"""
Launch-57 Phase 2 — Trust Batch 1 canonical runtime spine.

Build order: #6 evidence display → #5 CAP-0639 → #4 CAP-0640 → #3 CAP-0641 → #2 oracle sentence
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from cap646.evidence_class import EVIDENCE_CLASSES, ai_compliance_footer, attach_evidence_metadata

LAUNCH57_TRUST_BATCH1_CAP_IDS: frozenset[int] = frozenset({639, 640, 641})

LAUNCH_ITEM_BY_CAP: dict[int, int] = {
    639: 5,
    640: 4,
    641: 3,
}

# User-facing evidence taxonomy (Launch #6) — maps canonical classes to LIVE/DELAYED/SIM.
_USER_EVIDENCE_LABELS: dict[str, str] = {
    "PRODUCTION_VERIFIED": "LIVE",
    "SHADOW_LIVE_FORWARD": "LIVE",
    "BACKTESTED": "DELAYED",
    "SIMULATED": "SIM",
}

_USER_EVIDENCE_DESCRIPTIONS: dict[str, str] = {
    "LIVE": "Production or shadow-live forward evidence — not replay.",
    "DELAYED": "Historical or backtested evidence — not presented as live performance.",
    "SIM": "Simulated or synthetic — never promoted to live metrics.",
}


def _utcnow_iso() -> str:
    return datetime.now(UTC).isoformat()


def user_evidence_display(payload: dict[str, Any]) -> dict[str, Any]:
    """Launch #6 — visible evidence class (LIVE / DELAYED / SIM) for product surfaces."""
    meta = attach_evidence_metadata(dict(payload))
    canonical = str(meta.get("evidence_class") or "SHADOW_LIVE_FORWARD")
    user_label = _USER_EVIDENCE_LABELS.get(canonical, "DELAYED")
    return {
        "launch_item_id": 6,
        "canonical_evidence_class": canonical,
        "user_facing_label": user_label,
        "user_facing_description": _USER_EVIDENCE_DESCRIPTIONS.get(user_label, ""),
        "taxonomy": list(EVIDENCE_CLASSES),
        "visible": True,
        "promotion_policy": "replay_and_simulation_never_become_production_metrics",
        "methodology_version": "launch57-trust-evidence-display-1.0",
    }


def attach_trust_envelope(body: dict[str, Any]) -> dict[str, Any]:
    """Attach Launch #6 evidence display + compliance footer to trust outputs."""
    out = ai_compliance_footer(dict(body))
    out["evidence_display"] = user_evidence_display(out)
    out["evidence_class_visible"] = True
    return out


def _is_demo_opportunity(opportunity: dict[str, Any] | None) -> bool:
    if not opportunity:
        return False
    from net_edge_truth import FIN_004_DEMO_OPPORTUNITY

    if opportunity.get("demo") or opportunity.get("synthetic") or opportunity.get("source") == "demo":
        return True
    # Structural match to shared demo constant — never treat as live economics.
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
    return attach_trust_envelope(body)


async def public_accuracy_ledger(*, symbol: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Launch #4 / CAP-0640 — live ledger only; synthetic excluded from primary metrics."""
    from oracle_track_record import public_track_record

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
        "backend_module": "launch57.trust_batch1",
        "backend_entrypoint": "public_accuracy_ledger",
        "binding_source": "launch57_phase2_trust_batch1",
    }
    return attach_trust_envelope(body)


async def decision_certificate_export(*, symbol: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Launch #3 / CAP-0641 — decision certificate + hash."""
    from decision_certificate import build_decision_certificate

    p = dict(params or {})
    cert_payload = {
        "symbol": symbol,
        "tier": p.get("tier") or "free",
        "decision_action": p.get("decision_action") or p.get("verdict") or "WAIT",
        "decision_sentence": p.get("decision_sentence") or p.get("oracle"),
        "prediction_id": p.get("prediction_id"),
        "chain_hash": p.get("chain_hash"),
        "opportunity_score": p.get("opportunity_score"),
        "net_edge_truth": p.get("net_edge_truth"),
    }
    cert = build_decision_certificate(cert_payload)
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
        "backend_module": "launch57.trust_batch1",
        "backend_entrypoint": "decision_certificate_export",
        "binding_source": "launch57_phase2_trust_batch1",
    }
    return attach_trust_envelope(body)


async def single_sentence_oracle(*, symbol: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Launch #2 — Single-Sentence Oracle (ACT/WAIT/ABSTAIN) product surface."""
    p = dict(params or {})
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

    body = {
        "launch_item_id": 2,
        "surface": "single_sentence_oracle",
        "symbol": symbol,
        "success": True,
        "decision_action": action,
        "decision_sentence": sentence,
        "single_sentence_oracle": {
            "action": action,
            "sentence": sentence,
            "shareable": True,
        },
        "hero": "HERO_1_SINGLE_SENTENCE_ORACLE",
        "backend_module": "launch57.trust_batch1",
        "backend_entrypoint": "single_sentence_oracle",
        "binding_source": "launch57_phase2_trust_batch1",
    }
    return attach_trust_envelope(body)


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
