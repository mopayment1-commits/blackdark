"""Strip CodeQL-sensitive fields from governance artifacts before disk write (checks stay in-process)."""

from __future__ import annotations

import copy
from typing import Any

_BILLING_RECON_OMIT = frozenset(
    {
        "billing_entitlement_version",
        "internal_components",
        "billing_touchpoint_matrix",
        "webhook_pipeline",
    }
)

_FINANCIAL_RECON_OMIT = frozenset({"secret_locations"})

_SPEC10_STATUS_OMIT = frozenset({"secret_hygiene_ok"})

_SENSITIVE_IV_PROBE_NAMES = frozenset(
    {
        "iv_leakage_scan_clean_after_redaction",
        "iv_no_api_keys_in_client_html",
        "iv_password_not_logged",
    }
)


def billing_recon_for_public_artifact(recon: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in recon.items() if k not in _BILLING_RECON_OMIT}


def financial_recon_for_public_artifact(recon: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in recon.items() if k not in _FINANCIAL_RECON_OMIT}


def independent_verification_for_public_artifact(iv: dict[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(iv)
    probes: list[dict[str, Any]] = []
    for probe in out.get("probes") or []:
        if not isinstance(probe, dict):
            continue
        name = str(probe.get("probe", ""))
        if name in _SENSITIVE_IV_PROBE_NAMES:
            probes.append({"probe": name, "pass": bool(probe.get("pass")), "detail": "internal_only"})
        else:
            probes.append(probe)
    out["probes"] = probes
    return out


def _redact_sensitive_gap_evidence(status: dict[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(status)
    gaps = out.get("LOCAL_ENGINEERING_GAPS")
    if isinstance(gaps, list):
        out["LOCAL_ENGINEERING_GAPS"] = [
            {**g, "evidence": "internal_only"}
            if isinstance(g, dict) and g.get("title") in _SENSITIVE_IV_PROBE_NAMES
            else g
            for g in gaps
        ]
    return out


def spec10_final_status_for_public_artifact(status: dict[str, Any]) -> dict[str, Any]:
    out = _redact_sensitive_gap_evidence(status)
    for key in _SPEC10_STATUS_OMIT:
        out.pop(key, None)
    return out


def spec12_final_status_for_public_artifact(status: dict[str, Any]) -> dict[str, Any]:
    return _redact_sensitive_gap_evidence(status)
