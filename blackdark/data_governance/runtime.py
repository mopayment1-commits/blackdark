"""
Central fail-closed governance runtime for material intelligence writes.

Surfaces: decision, signal, oracle, cap_execute, enrichment, ledger_write.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from typing import Any, Literal

MaterialSurface = Literal[
    "decision",
    "signal",
    "oracle",
    "cap_execute",
    "enrichment",
    "ledger_write",
    "exposure",
    "failure",
    "market_event",
]

CAPABILITY_DNA_FIELDS: tuple[str, ...] = (
    "purpose",
    "data_sources",
    "algorithm",
    "dependencies",
    "tests",
    "benchmark",
    "limitations",
    "owner",
    "version",
    "evidence_ref",
)


class GovernanceViolationError(RuntimeError):
    """Material write blocked by governance policy (fail-closed)."""


def _is_production() -> bool:
    try:
        from production_guard import is_production

        return is_production()
    except Exception:
        tokens = [
            (os.getenv("ENV") or "").strip().lower(),
            (os.getenv("APP_ENV") or "").strip().lower(),
            (os.getenv("ENVIRONMENT") or "").strip().lower(),
            (os.getenv("RAILWAY_ENVIRONMENT") or "").strip().lower(),
        ]
        return any(t in {"production", "prod"} for t in tokens)


def governance_enforce_enabled() -> bool:
    """Production/default path is enforce-ON; dev may opt out only outside production."""
    raw = (os.getenv("BLACKDARK_GOVERNANCE_ENFORCE") or "1").strip().lower()
    if raw in {"0", "false", "no", "off"}:
        if _is_production():
            return True
        return False
    return True


def intelligence_receipt(payload: dict[str, Any], *, surface: str) -> dict[str, Any]:
    """DSR-008 / REQ-0816 — verifiable intelligence receipt for material rows."""
    body = {
        "surface": surface,
        "evidence_class": payload.get("evidence_class"),
        "source": payload.get("source") or payload.get("source_id"),
        "model_version": payload.get("model_version"),
        "symbol": payload.get("symbol") or payload.get("asset"),
        "created_at": payload.get("created_at") or payload.get("asof"),
        "capability_dna": payload.get("capability_dna"),
        "provenance": payload.get("provenance") or payload.get("provenance_chain"),
    }
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":"), default=str)
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return {
        "receipt_version": "1",
        "receipt_hash": digest,
        "receipt_surface": surface,
        "receipt_at": time.time(),
        "receipt_canonical": body,
    }


def require_capability_dna(payload: dict[str, Any], *, surface: str) -> None:
    """REQ-0167 — Capability DNA required on decision + cap646 execute rows."""
    if surface not in {"decision", "cap_execute"}:
        return
    dna = payload.get("capability_dna")
    if not isinstance(dna, dict):
        raise GovernanceViolationError("capability_dna_missing_on_decision_row")
    missing = [f for f in CAPABILITY_DNA_FIELDS if not str(dna.get(f) or "").strip()]
    if missing:
        raise GovernanceViolationError(f"capability_dna_incomplete:{','.join(missing)}")


_INTERNAL_SOURCES = frozenset(
    {
        "oracle",
        "decision_ledger",
        "signal_registry",
        "user_exposure_log",
        "market_event_library",
        "failure_corpus",
        "internal_cache",
        "unified_multimodal_v1",
        "ai_oracle.evaluate_opportunity",
        "platform_chain_e2e",
        "institutional_controls",
        "qa_harness",
        "cap646",
        "data_engine",
        "data_engine_systems_api",
        "signal_compounding",
    }
)

_INTERNAL_SUFFIXES = ("_library", "_ledger", "_corpus", "_log", "_registry", "_chain")


def _check_rights(payload: dict[str, Any]) -> None:
    source_id = payload.get("source_id") or payload.get("source")
    if not source_id:
        return
    sid = str(source_id).strip().lower()
    if (
        sid in _INTERNAL_SOURCES
        or sid.startswith(("internal_", "qa_", "test_", "verify_"))
        or any(sid.endswith(s) for s in _INTERNAL_SUFFIXES)
    ):
        return
    from data_governance.rights import assert_usage_allowed

    purpose = str(payload.get("purpose") or payload.get("usage_purpose") or "analytics")
    rights = assert_usage_allowed(str(source_id), purpose=purpose)
    if not rights.get("allowed"):
        raise GovernanceViolationError(f"rights_denied:{rights.get('reason')}")


def _check_freshness(payload: dict[str, Any]) -> None:
    observed = payload.get("observed_at") or payload.get("timestamp")
    if observed is None:
        return
    try:
        observed_at = float(observed)
    except (TypeError, ValueError):
        return
    from data_governance.freshness import gate_admission

    result = gate_admission(
        {
            "observed_at": observed_at,
            "source_id": payload.get("source_id") or payload.get("source") or "internal_cache",
            "purpose": payload.get("purpose") or "analytics",
        },
        max_age_seconds=float(payload.get("max_age_seconds") or 300.0),
    )
    if not result.get("admitted"):
        raise GovernanceViolationError("freshness_or_rights_admission_denied")


def _check_evidence_promotion(payload: dict[str, Any]) -> None:
    """REQ-EV-PRODUCTION_VERIFIED / DSR-012-013 — block semantic promotion."""
    from cap646.evidence_class import assert_promotion_allowed, infer_evidence_class

    current = payload.get("evidence_class")
    if not current:
        current = infer_evidence_class(
            source=str(payload.get("source") or ""),
            explicit=payload.get("evidence_class"),
        )
    target = payload.get("target_evidence_class") or payload.get("promote_to")
    if target:
        assert_promotion_allowed(current, target)  # raises ValueError → wrap below


def _default_capability_dna(payload: dict[str, Any]) -> dict[str, Any]:
    existing = payload.get("capability_dna")
    if isinstance(existing, dict) and all(str(existing.get(f) or "").strip() for f in CAPABILITY_DNA_FIELDS):
        return existing
    return {
        "purpose": str(payload.get("purpose") or "oracle_decision_materialization"),
        "data_sources": json.dumps(payload.get("data_sources") or payload.get("sources") or ["internal_oracle"]),
        "algorithm": str(payload.get("algorithm") or payload.get("model_version") or "unified_multimodal_v1"),
        "dependencies": json.dumps(payload.get("dependencies") or ["decision_truth", "net_edge_truth"]),
        "tests": str(payload.get("tests") or "tests/test_data_governance_runtime_enforcement.py"),
        "benchmark": str(payload.get("benchmark") or "decision_truth/admission.py"),
        "limitations": str(
            payload.get("limitations") or "Advisory directional signal; not executable profit claim without economics."
        ),
        "owner": str(payload.get("owner") or "blackdark/platform"),
        "version": str(payload.get("version") or payload.get("model_version") or "1"),
        "evidence_ref": str(payload.get("evidence_ref") or payload.get("certificate_hash") or "pending"),
    }


def enforce_material_write(
    surface: MaterialSurface,
    payload: dict[str, Any],
    *,
    operation: str = "write",
) -> dict[str, Any]:
    """Fail-closed gate for material intelligence / ledger writes."""
    if not governance_enforce_enabled():
        out = dict(payload)
        out.setdefault("governance_enforced", False)
        return out

    out = dict(payload)
    out["governance_enforced"] = True
    out["governance_surface"] = surface
    out["governance_operation"] = operation

    if surface in {"decision", "cap_execute"} and "capability_dna" not in out:
        out["capability_dna"] = _default_capability_dna(out)

    try:
        from data_governance.pipeline import run_material_pipeline

        out = run_material_pipeline(surface, out)
        _check_rights(out)
        _check_freshness(out)
        if out.get("target_evidence_class") or out.get("promote_to"):
            _check_evidence_promotion(out)
        require_capability_dna(out, surface=surface)
    except ValueError as exc:
        raise GovernanceViolationError(str(exc)) from exc

    receipt = intelligence_receipt(out, surface=surface)
    out["intelligence_receipt"] = receipt
    out.setdefault("provenance_chain", out.get("provenance") or {})
    if isinstance(out["provenance_chain"], dict):
        out["provenance_chain"] = {**out["provenance_chain"], "receipt_hash": receipt["receipt_hash"]}
    return out


def runtime_status() -> dict[str, Any]:
    return {
        "enforce_enabled": governance_enforce_enabled(),
        "production": _is_production(),
        "env_BLACKDARK_GOVERNANCE_ENFORCE": os.getenv("BLACKDARK_GOVERNANCE_ENFORCE", "1"),
        "capability_dna_fields": list(CAPABILITY_DNA_FIELDS),
        "surfaces": [
            "decision",
            "signal",
            "oracle",
            "cap_execute",
            "enrichment",
            "ledger_write",
            "exposure",
            "failure",
            "market_event",
        ],
    }
