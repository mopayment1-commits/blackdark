"""Strategic correction — expert quality standard for inflated report pastes."""

from __future__ import annotations

from pathlib import Path


def test_four_layers_and_expanded_denylist():
    from trust_os import OVERCLAIM_DENYLIST, VALUE_LAYERS, strategy_correction_manifest, trust_os_manifest

    assert len(VALUE_LAYERS) == 4
    claims = " ".join(row["claim"] for row in OVERCLAIM_DENYLIST).upper()
    assert "ARENA" in claims
    assert "NEURO" in claims
    assert "15" in claims or "FIFTEEN" in claims.upper() or "15 separately" in " ".join(
        row["claim"] for row in OVERCLAIM_DENYLIST
    )
    assert "IFRS" in claims
    assert "100" in claims or "INDICATOR" in claims
    assert "KAFKA" in claims or "RUST" in claims
    m = trust_os_manifest()
    assert len(m["five_outcomes"]) == 5
    assert m["success_metric"]["bar"] == "60_second_grasp"
    corr = strategy_correction_manifest()
    assert corr["value_layers_count"] == 4
    assert corr["heroes_count"] == 6
    assert "viral_arena" in corr["not_building"]


def test_intent_router_maps_to_heroes_only():
    from intent_router import INTENTS, REJECTED_INTENTS, intent_router_manifest, resolve_intent

    man = intent_router_manifest()
    assert man["question"] == "What do you want to do today?"
    assert len(INTENTS) >= 5
    paths = " ".join(i["path"] for i in INTENTS)
    assert "/oracle-accuracy" in paths
    assert "/dashboard" in paths
    assert "arena" not in paths.lower()
    assert resolve_intent("get_decision")["ok"] is True
    assert resolve_intent("blackdark_arena")["rejected"] is True
    assert any(r["id"] == "predict_guaranteed" for r in REJECTED_INTENTS)


def test_binding_doc_and_ui_wire():
    root = Path(__file__).resolve().parents[1]
    assert (root / "docs" / "STRATEGIC_CORRECTION_BINDING.md").is_file()
    text = (root / "docs" / "STRATEGIC_CORRECTION_BINDING.md").read_text(encoding="utf-8")
    assert "Four value layers" in text or "four value layers" in text.lower()
    assert "ARENA" in text
    dash = (root / "templates" / "dashboard.html").read_text(encoding="utf-8")
    assert "What do you want to do today?" in dash
    assert "intent/router" in dash or "loadIntentRouter" in dash
    util = (root / "templates" / "utility.html").read_text(encoding="utf-8")
    assert "Strategic correction" in util or "five_outcomes" in util
    heroes = (root / "docs" / "HEROES_STRATEGY_BINDING.md").read_text(encoding="utf-8")
    assert "Strategic correction" in heroes


def test_heroes_router_exposes_correction_endpoints():
    from api.routers import heroes as heroes_router

    paths = {getattr(r, "path", None) for r in heroes_router.router.routes}
    assert "/api/strategy/correction" in paths
    assert "/api/intent/router" in paths
    assert "/api/intent/resolve" in paths


def test_no_guaranteed_accuracy_in_denylist_truth():
    from trust_os import OVERCLAIM_DENYLIST

    row = next(r for r in OVERCLAIM_DENYLIST if "65" in r["claim"] or "accuracy" in r["claim"].lower())
    assert "guarantee" in row["truth"].lower() or "never" in row["truth"].lower()
