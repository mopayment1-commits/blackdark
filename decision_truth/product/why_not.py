"""DTS-020 — Why NOT Engine (machine-readable + user-facing)."""

from __future__ import annotations

from typing import Any


def build_why_not_engine(payload: dict[str, Any]) -> dict[str, Any]:
    """Build structured Why NOT from canonical decision facts."""
    dt = payload.get("decision_truth") or {}
    contract = dt.get("contract") or {}
    codes = list(contract.get("why_not") or [])
    state = str(payload.get("decision_truth_state") or contract.get("decision_state") or "UNAVAILABLE")
    net_edge = contract.get("net_edge") or payload.get("net_edge_truth") or {}
    exec_feas = contract.get("execution_feasibility") or {}
    risk = contract.get("risk") or {}
    lifecycle = dt.get("evidence_lifecycle") or payload.get("evidence_lifecycle") or {}

    machine = {
        "reason_codes": codes,
        "blocking_gates": _blocking_gates(codes, contract),
        "economic_state": _economic_state(net_edge),
        "execution_state": _execution_state(exec_feas),
        "risk_state": _risk_state(risk),
        "evidence_state": _evidence_state(contract, lifecycle),
        "freshness_state": _freshness_state(contract),
        "uncertainty_calibration_state": _uncertainty_state(contract, lifecycle),
    }

    message_keys = _human_message_keys(state, codes, machine, contract)
    return {
        "machine_readable": machine,
        "human_explanation": None,
        "message_keys": message_keys,
        "codes": codes,
        "decision_state": state,
        "derived_from": "canonical_decision_contract",
        "presentation_boundary": "decision_truth.cross_cutting.i18n",
        "methodology_version": "dts-p5-why-not-1.0",
    }


def _blocking_gates(codes: list[str], contract: dict[str, Any]) -> list[str]:
    gates: list[str] = []
    for code in codes:
        gates.append(code)
    fa = contract.get("field_availability") or {}
    for field, meta in fa.items():
        if isinstance(meta, dict) and meta.get("available") is False and meta.get("not_applicable") is not True:
            gates.append(f"field_unavailable:{field}")
    return gates


def _economic_state(net_edge: dict[str, Any]) -> dict[str, Any]:
    return {
        "state": net_edge.get("state") or ("AVAILABLE" if net_edge.get("expected_net_edge_bps") is not None else "UNAVAILABLE"),
        "gross_edge_bps": net_edge.get("gross_edge_bps"),
        "expected_net_edge_bps": net_edge.get("expected_net_edge_bps"),
        "realizable_net_edge_bps": net_edge.get("realizable_net_edge_bps"),
        "cost_autopsy": net_edge.get("cost_autopsy") or net_edge.get("components"),
    }


def _execution_state(exec_feas: dict[str, Any]) -> dict[str, Any]:
    return {
        "state": exec_feas.get("state") or "UNAVAILABLE",
        "score": exec_feas.get("score"),
        "reason_codes": list(exec_feas.get("reason_codes") or []),
        "liquidity_ok": exec_feas.get("liquidity_ok"),
    }


def _risk_state(risk: dict[str, Any]) -> dict[str, Any]:
    return {
        "state": risk.get("state") or ("AVAILABLE" if risk.get("ok") is not None else "UNAVAILABLE"),
        "ok": risk.get("ok"),
        "pre_impact": risk.get("pre_impact") or risk.get("portfolio_pre_impact"),
        "reverse_stress": risk.get("reverse_stress"),
    }


def _evidence_state(contract: dict[str, Any], lifecycle: dict[str, Any]) -> dict[str, Any]:
    grade = contract.get("grade")
    return {
        "grade": grade,
        "evidence_class": contract.get("evidence_class"),
        "lifecycle_state": lifecycle.get("state"),
        "simulation": lifecycle.get("simulation"),
        "calibration": lifecycle.get("calibration"),
    }


def _freshness_state(contract: dict[str, Any]) -> dict[str, Any]:
    fresh = contract.get("freshness") or {}
    return {
        "state": fresh.get("state") or fresh.get("freshness_state") or "UNKNOWN",
        "quote_age_ms": fresh.get("quote_age_ms"),
        "as_of": fresh.get("as_of"),
    }


def _uncertainty_state(contract: dict[str, Any], lifecycle: dict[str, Any]) -> dict[str, Any]:
    unc = contract.get("uncertainty") or {}
    cal = lifecycle.get("calibration") or {}
    return {
        "uncertainty": unc,
        "calibration_state": cal.get("state"),
        "high_uncertainty": unc.get("high"),
    }


def _human_message_keys(
    state: str,
    codes: list[str],
    machine: dict[str, Any],
    contract: dict[str, Any],
) -> list[dict[str, Any]]:
    if state == "AVAILABLE":
        return [{"key": "dts.why.admitted", "params": {}}]
    keys: list[dict[str, Any]] = [{"key": "dts.why.generic_blocked", "params": {"state": state}}]
    econ = machine.get("economic_state") or {}
    if econ.get("expected_net_edge_bps") is not None:
        keys.append({"key": "dts.why.net_edge", "params": {"bps": econ["expected_net_edge_bps"]}})
    exec_s = machine.get("execution_state") or {}
    if exec_s.get("score") is not None:
        keys.append({"key": "dts.why.execution", "params": {"score": exec_s["score"]}})
    fresh = machine.get("freshness_state") or {}
    if fresh.get("state") in {"STALE", "UNKNOWN"}:
        keys.append({"key": "dts.why.freshness", "params": {}})
    if any("conflict" in c.lower() for c in codes):
        keys.append({"key": "dts.why.conflict", "params": {}})
    if codes:
        keys.append({"key": "dts.why.blocking", "params": {"reasons": ",".join(codes[:5])}})
    inv = contract.get("invalidation_condition")
    if inv:
        keys.append({"key": "dts.why.invalidation", "params": {"condition": inv}})
    return keys
