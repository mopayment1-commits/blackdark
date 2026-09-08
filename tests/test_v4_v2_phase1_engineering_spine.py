"""v4_v2 Phase-1 engineering spine tests."""

from __future__ import annotations

import json
from pathlib import Path

from bd_platform.v4_v2_phase1_engineering_spine import (
    MATURITY_GATED_REQUIREMENT_IDS,
    close_requirement,
    phase1_foundation_status,
    resolve_closure_domain,
    verify_all_domain_handlers,
)

CLOSURE_MAP_PATH = Path("docs/V4_V2_PHASE1_CLOSURE_MAP.json")
LEDGER_PATH = Path("docs/THREE_SPEC_INCREMENTAL_IMPLEMENTATION_LEDGER.json")


def _load_closure_rows() -> list[dict]:
    payload = json.loads(CLOSURE_MAP_PATH.read_text(encoding="utf-8"))
    return payload["rows"]


def _load_ledger_v4_v2_states() -> dict[str, int]:
    ledger = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
    states: dict[str, int] = {}
    for req in ledger["requirements"]:
        if req.get("spec") != "v4_v2":
            continue
        state = str(req.get("current_state"))
        states[state] = states.get(state, 0) + 1
    return states


def test_domain_handlers_verify() -> None:
    result = verify_all_domain_handlers()
    assert result["ok"] is True, result["failures"]


def test_phase1_foundation_status_non_live() -> None:
    status = phase1_foundation_status()
    assert status["live_promotion"] is False
    assert status["maturity_gated_count"] == 18
    for sample in status["sample_domains"]:
        assert sample["runtime_verified"] is True
        assert sample["implementation_paths"]


def test_closure_map_universe_complete() -> None:
    payload = json.loads(CLOSURE_MAP_PATH.read_text(encoding="utf-8"))
    assert payload["closure_universe_count"] == 498
    assert payload["V4_V2_CLOSURE_UNIVERSE_COMPLETE"] is True


def test_ledger_post_closure_arithmetic() -> None:
    states = _load_ledger_v4_v2_states()
    assert states.get("PARTIALLY_BUILT_VALID", 0) == 0
    assert states.get("LOCAL_ENGINEERING_COMPLETE", 0) == 644
    assert states.get("MATURITY_GATED", 0) == 42
    assert sum(states.values()) == 1846


def test_closure_rows_have_runtime_paths() -> None:
    rows = _load_closure_rows()
    sample = rows[0]
    assert sample["implementation_paths"]
    assert sample["closure_state"] in {"LOCAL_ENGINEERING_COMPLETE", "MATURITY_GATED"}


def test_maturity_gated_closure_rows() -> None:
    rows = {row["requirement_id"]: row for row in _load_closure_rows()}
    for rid in MATURITY_GATED_REQUIREMENT_IDS:
        assert rows[rid]["closure_state"] == "MATURITY_GATED"
        assert rows[rid]["maturity_gate"] is True


def test_replay_closure_domain_for_sample_requirement() -> None:
    rows = _load_closure_rows()
    replay_rows = [r for r in rows if r["closure_domain"] == "replay_runtime"]
    assert replay_rows
    replay = close_requirement(
        {
            "requirement_id": replay_rows[0]["requirement_id"],
            "requirement_type": "REPLAY",
            "implementation_nature": "OTHER_WITH_JUSTIFICATION",
            "shared_canonical_implementation": "temporal_leakage_firewall.py + ml/market_replay_bootstrap.py",
            "maturity_gate": False,
        }
    )
    assert replay["closure_state"] == "LOCAL_ENGINEERING_COMPLETE"
