"""Behavioral coverage for governance.launch57.generate_phase0_5_reconciliation."""

from __future__ import annotations

import json

import governance.launch57.generate_phase0_5_reconciliation as gen


def _load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_is_generic_delegate_and_prior_pass():
    cap = {"canonical_implementation": "explicit_option_a", "actual_consumer_paths": ["explicit_option_a"]}
    assert gen.is_generic_delegate(cap) is True
    assert gen.prior_pass_from_phase0(None, cap) == "NO"


def test_default_capability_reconciliation():
    caps_by_id = {
        "CAP-A": {
            "capability_id": "CAP-A",
            "canonical_implementation": "explicit_option_a",
            "actual_consumer_paths": ["explicit_option_a"],
            "runtime_entry": "cap646/runtime.py",
        }
    }
    rec = gen.default_capability_reconciliation(1, ["CAP-A"], caps_by_id)
    assert rec["canonical_decision"] == "REUSE"
    assert "GENERIC_DELEGATE" in rec["blocker"]


def test_build_reconciliation_rows_from_repo():
    ssot = _load_json(gen.SSOT_PATH)
    register = _load_json(gen.REGISTER_PATH)
    rows = gen.build_reconciliation_rows(ssot, register)
    assert len(rows) == 57
    summary = gen.summarize(rows)
    assert summary["TOTAL_LAUNCH57"] == 57
    integrity = gen.scope_integrity(ssot)
    assert integrity["LAUNCH57_COUNT"] == 57
    closure = gen.closure_verification(summary, ssot)
    assert isinstance(closure, dict)
    assert closure["ALL_57_HAVE_EXPLICIT_CANONICAL_DECISION"] in ("YES", "NO")


def test_render_report_contains_phase_label():
    ssot = _load_json(gen.SSOT_PATH)
    register = _load_json(gen.REGISTER_PATH)
    rows = gen.build_reconciliation_rows(ssot, register)
    amended: list[str] = []
    text = gen.render_report(register, rows, ssot, amended)
    assert "Phase 0.5" in text or "0.5" in text
