"""Public Intelligence Product builders — AV §5–§6."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from anonymous_visitor.licensing import assert_license_public_display


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _freshness_envelope(
    *,
    widget: str,
    upstream_provider: str | None,
    source_event_time: str | None,
    source_received_at: str | None = None,
    computed_at: str | None = None,
    freshness_slo_sec: int = 300,
    fallback_state: str | None = None,
) -> dict[str, Any]:
    served_at = _utcnow()
    computed = computed_at or served_at
    age_sec: float | None = None
    if source_event_time:
        try:
            evt = datetime.fromisoformat(source_event_time.replace("Z", "+00:00"))
            srv = datetime.fromisoformat(served_at.replace("Z", "+00:00"))
            age_sec = max(0.0, (srv - evt).total_seconds())
        except Exception:
            age_sec = None
    proven = source_event_time is not None and age_sec is not None
    fresh_pass = proven and age_sec is not None and age_sec <= freshness_slo_sec
    return {
        "widget": widget,
        "UPSTREAM_PROVIDER": upstream_provider,
        "SOURCE_EVENT_TIME": source_event_time,
        "SOURCE_RECEIVED_AT": source_received_at,
        "COMPUTED_AT": computed,
        "SERVED_AT": served_at,
        "AGE_AT_SERVE": age_sec,
        "FRESHNESS_SLO": f"{freshness_slo_sec}s",
        "FRESHNESS_PASS": fresh_pass if proven else False,
        "FALLBACK_STATE": fallback_state or ("UNPROVEN_SOURCE_TIME" if not proven else None),
        "source_event_time_available": proven,
    }


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
    fresh_raw = pulse.get("freshness") or {}
    source_event = fresh_raw.get("source_event_time") or fresh_raw.get("as_of") or fresh_raw.get("timestamp")
    freshness = _freshness_envelope(
        widget="Decision Truth",
        upstream_provider="trust_pulse",
        source_event_time=source_event,
        source_received_at=fresh_raw.get("received_at"),
        computed_at=fresh_raw.get("computed_at"),
        fallback_state=fresh_raw.get("label") or fresh_raw.get("state"),
    )
    body = {
        "ok": True,
        "surface": "decision_truth_pulse_public",
        "symbol": symbol,
        "asset": pulse.get("symbol") or symbol,
        "decision_state": pulse.get("action") or pulse.get("decision_state") or "WAIT",
        "confidence": pulse.get("confidence"),
        "evidence_alignment": pulse.get("evidence_alignment") or (pulse.get("why") or {}).get("headline"),
        "data_quality": pulse.get("data_quality") or pulse.get("quality"),
        "freshness": freshness,
        "freshness_legacy": pulse.get("freshness"),
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
        from oracle_audit_chain import chain_summary, temporal_integrity_summary

        temporal = temporal_integrity_summary()
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
            "total_records": temporal.get("TOTAL_RECORDS", chain.get("total_records")),
            "recent_hit_rate_percent": chain.get("recent_hit_rate_percent"),
            "recent_records": chain.get("recent_records") or [],
            "methodology_href": "/methodology",
            "accuracy_href": "/oracle-accuracy",
        },
        "accuracy": {
            "TOTAL_RECORDS": temporal.get("TOTAL_RECORDS"),
            "TOTAL_ELIGIBLE_FOR_SCORING": temporal.get("TOTAL_ELIGIBLE_FOR_SCORING"),
            "TOTAL_MATURED": temporal.get("TOTAL_MATURED"),
            "TOTAL_RESOLVED": temporal.get("TOTAL_RESOLVED"),
            "TOTAL_UNRESOLVED": temporal.get("TOTAL_UNRESOLVED"),
            "TOTAL_ABSTAINED": temporal.get("TOTAL_ABSTAINED"),
            "TOTAL_CORRECT": temporal.get("TOTAL_CORRECT"),
            "TOTAL_INCORRECT": temporal.get("TOTAL_INCORRECT"),
            "LEGACY_TEMPORAL_PROOF_UNAVAILABLE": temporal.get("LEGACY_TEMPORAL_PROOF_UNAVAILABLE"),
            "TEMPORALLY_PROVABLE_PREDICTIONS": temporal.get("TEMPORALLY_PROVABLE_PREDICTIONS"),
            "ACCURACY_NUMERATOR": temporal.get("ACCURACY_NUMERATOR"),
            "ACCURACY_DENOMINATOR": temporal.get("ACCURACY_DENOMINATOR"),
            "ACCURACY_DENOMINATOR_DEFINITION": temporal.get("ACCURACY_DENOMINATOR_DEFINITION"),
            "ACCURACY_RATE": temporal.get("ACCURACY_RATE"),
            "PUBLIC_ACCURACY_UI_DENOMINATOR_VISIBLE": True,
        },
        "freshness": _freshness_envelope(
            widget="Accuracy",
            upstream_provider="oracle_audit_chain",
            source_event_time=temporal.get("LATEST_TIMESTAMP"),
            computed_at=_utcnow(),
            fallback_state="LEGACY_TEMPORAL_PROOF_UNAVAILABLE" if temporal.get("LEGACY_TEMPORAL_PROOF_UNAVAILABLE") else None,
        ),
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
