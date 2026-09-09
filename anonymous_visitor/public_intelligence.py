"""Public Intelligence Product builders — AV §5–§6."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from anonymous_visitor.licensing import assert_license_public_display


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _with_license(source_id: str | None, payload: dict[str, Any]) -> dict[str, Any]:
    gate = assert_license_public_display(source_id)
    if not gate["ok"]:
        return {
            "ok": False,
            "error": "licensing_gate_blocked",
            "source_id": source_id,
            "license_public_display_pass": False,
            "degraded_state": "TEMPORARILY UNAVAILABLE",
        }
    payload["attribution"] = {
        "required": gate.get("attribution_required"),
        "text": gate.get("attribution_text"),
        "url": gate.get("attribution_url"),
    }
    payload["license_public_display_pass"] = True
    return payload


async def build_decision_truth_pulse(*, symbol: str = "BTC") -> dict[str, Any]:
    try:
        from trust_pulse import build_trust_pulse

        pulse = await build_trust_pulse(symbol=symbol, tier="free", persist=False)
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "error": "data_unavailable",
            "degraded_state": "TEMPORARILY UNAVAILABLE",
            "detail": type(exc).__name__,
        }
    body = {
        "ok": True,
        "surface": "decision_truth_pulse_public",
        "symbol": symbol,
        "asset": pulse.get("symbol") or symbol,
        "decision_state": pulse.get("action") or pulse.get("decision_state") or "WAIT",
        "confidence": pulse.get("confidence"),
        "evidence_alignment": pulse.get("evidence_alignment") or (pulse.get("why") or {}).get("headline"),
        "data_quality": pulse.get("data_quality") or pulse.get("quality"),
        "freshness": pulse.get("freshness"),
        "methodology_href": "/methodology",
        "evidence_href": "/oracle-accuracy",
        "generated_at": _utcnow(),
        "non_personal": True,
        "no_guaranteed_outcome": True,
        "legal_marker": "LEGAL_REVIEW_REQUIRED",
    }
    return _with_license("oracle_unified", body)


async def build_evidence_passport_summary() -> dict[str, Any]:
    summary: dict[str, Any] = {
        "source_coverage": None,
        "freshness": None,
        "cross_source_agreement": None,
        "provenance_status": "summary_only",
        "data_quality": None,
        "methodology_version": None,
    }
    try:
        from data_governance.registry import registry_summary

        reg = registry_summary()
        summary["source_coverage"] = reg.get("total_sources")
        summary["data_quality"] = reg.get("by_source_class")
        summary["methodology_version"] = reg.get("registry_authority")
    except Exception:
        summary["degraded"] = True
    try:
        from oracle_audit_chain import chain_summary

        chain = chain_summary(limit=20) or {}
        resolved = [r for r in (chain.get("recent_records") or []) if r.get("resolved")]
        if resolved:
            agree = sum(1 for r in resolved if r.get("label") == "correct")
            summary["cross_source_agreement"] = round(100.0 * agree / len(resolved), 1)
        summary["freshness"] = {
            "total_records": chain.get("total_records"),
            "recent_hit_rate_percent": chain.get("recent_hit_rate_percent"),
        }
    except Exception:
        pass
    body = {
        "ok": True,
        "surface": "evidence_passport_public_summary",
        "summary": summary,
        "generated_at": _utcnow(),
        "non_personal": True,
        "full_graph_requires_account": True,
    }
    return _with_license("data_governance_registry", body)


async def build_net_edge_proof(*, symbol: str = "BTC") -> dict[str, Any]:
    try:
        from trust_pulse import build_trust_pulse

        pulse = await build_trust_pulse(symbol=symbol, tier="free", persist=False)
        proof = pulse.get("proof") or {}
        body = {
            "ok": True,
            "surface": "net_edge_proof_public",
            "symbol": symbol,
            "pipeline": {
                "raw_opportunity": proof.get("raw_opportunity") or proof.get("headline"),
                "costs": proof.get("costs") or proof.get("cost_context"),
                "risk": proof.get("risk") or proof.get("risk_context"),
                "net_edge": proof.get("net_edge") or proof.get("edge_summary"),
                "blackdark_judgment": pulse.get("action") or "WAIT",
            },
            "bounded_example": True,
            "not_guaranteed_profit": True,
            "deeper_details_require_account": True,
            "generated_at": _utcnow(),
            "legal_marker": "LEGAL_REVIEW_REQUIRED",
        }
        return _with_license("oracle_unified", body)
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "error": "data_unavailable",
            "degraded_state": "LIMITED COVERAGE",
            "detail": type(exc).__name__,
        }


async def build_market_surface() -> dict[str, Any]:
    surface: dict[str, Any] = {"assets": [], "regime": None, "dominance": None}
    try:
        from market_context import fetch_binance_market_overview_pack

        pack = await fetch_binance_market_overview_pack(limit=8) or {}
        surface["assets"] = pack.get("overview") or pack.get("movers") or []
        surface["freshness"] = pack.get("freshness") or {"status": "live"}
    except Exception:
        surface["degraded_state"] = "DATA DELAYED"
    body = {
        "ok": True,
        "surface": "public_market_surface",
        "market": surface,
        "generated_at": _utcnow(),
        "non_personal": True,
    }
    return _with_license("market_context", body)


async def build_public_accuracy() -> dict[str, Any]:
    try:
        from oracle_audit_chain import chain_summary

        chain = chain_summary(limit=50) or {}
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "error": "data_unavailable",
            "degraded_state": "TEMPORARILY UNAVAILABLE",
            "detail": type(exc).__name__,
        }
    body = {
        "ok": True,
        "surface": "public_accuracy_historical_proof",
        "ledger": {
            "total_records": chain.get("total_records"),
            "recent_hit_rate_percent": chain.get("recent_hit_rate_percent"),
            "recent_records": chain.get("recent_records") or [],
            "methodology_href": "/methodology",
            "accuracy_href": "/oracle-accuracy",
        },
        "timestamped": True,
        "evidence_bound": True,
        "no_retroactive_rewrite": True,
        "generated_at": _utcnow(),
    }
    return _with_license("oracle_audit_chain", body)


def build_methodology_page_payload() -> dict[str, Any]:
    return {
        "ok": True,
        "surface": "methodology_public",
        "steps": [
            "Collect multi-source market evidence with provenance tracking",
            "Apply Decision Truth admission gates before surfacing states",
            "Publish timestamped outcomes to the public accuracy ledger",
        ],
        "limitations": [
            "Public view is summary-only — not personalized advice",
            "Coverage varies by asset and source availability",
            "Historical outcomes do not guarantee future results",
        ],
        "legal_marker": "LEGAL_REVIEW_REQUIRED",
        "generated_at": _utcnow(),
    }
