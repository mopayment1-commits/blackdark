"""Expert execution closure — canonical binding + FalconAI rejection."""

from __future__ import annotations

from pathlib import Path


def test_canonical_binding_doc():
    root = Path(__file__).resolve().parents[1]
    path = root / "docs" / "CANONICAL_BINDING.md"
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    assert "Four value layers" in text or "4" in text
    assert "FalconAI" in text
    assert "Rejected" in text or "rejected" in text.lower()


def test_execution_closure_manifest():
    from expert_execution import execution_closure_manifest, glass_box_announce_drafts

    m = execution_closure_manifest()
    assert m["canonical_docs_complete"] is True
    assert m["value_layers"] == 4
    assert m["heroes_count"] == 6
    assert any(f["id"] == "falconai_16_120" for f in m["superseded_frames"])
    assert "blackdark_arena" in m["not_executing"]
    drafts = glass_box_announce_drafts()
    assert "x_en" in drafts["drafts"]
    assert "human_only_fields" in drafts


def test_denylist_includes_falconai_frame():
    from trust_os import OVERCLAIM_DENYLIST, strategy_correction_manifest

    claims = " ".join(r["claim"] for r in OVERCLAIM_DENYLIST)
    assert "FalconAI" in claims
    corr = strategy_correction_manifest()
    assert "falconai_16_120_valuation" in corr["not_building"]
    assert corr["canonical_binding"] == "docs/CANONICAL_BINDING.md"


def test_router_exposes_closure_endpoints():
    from api.routers import heroes as heroes_router

    paths = {getattr(r, "path", None) for r in heroes_router.router.routes}
    assert "/api/execution/closure" in paths
    assert "/api/acceptance/60s" in paths
    assert "/api/glass-box/announce-drafts" in paths


def test_deferred_human_points_to_announce_api():
    root = Path(__file__).resolve().parents[1]
    text = (root / "docs" / "DEFERRED_HUMAN_STEPS.md").read_text(encoding="utf-8")
    assert "announce-drafts" in text
    assert "acceptance/60s" in text or "acceptance_60s" in text


def test_live_book_top_of_book_compat():
    from live_book_hub import get_best_price, get_top_of_book, update_top_of_book

    update_top_of_book(
        "binance",
        "ETH/USDT",
        bid=2000.0,
        bid_qty=2.0,
        ask=2001.0,
        ask_qty=2.0,
    )
    assert get_top_of_book("binance", "ETHUSDT") is not None
    assert get_top_of_book("ETHUSDT") is not None
    assert get_best_price("binance", "ETH/USDT")["mid"] > 0
