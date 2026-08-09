"""Unique wow surfaces — Kill-Rate, Replay, Committee, Half-Life Clock, Arena."""

from __future__ import annotations

from committee_one_pager import build_minimal_pdf, render_committee_pdf
from contradiction_replay import build_contradiction_replay, list_recent_replays
from glass_box_announce_schedule import schedule_status, set_schedule
from half_life_heat_clock import build_heat_clock, build_heat_clock_board
from kill_rate_board import build_kill_rate_board, record_kill
from proof_arena import build_week_board, submit_pick, week_id


def test_kill_rate_board_shape():
    record_kill("net_edge_truth", "residual_edge_below_threshold", meta={"asset": "BTC"})
    board = build_kill_rate_board()
    assert board["surface"] == "public_kill_rate_board"
    assert "metrics" in board
    assert "kill_rate_percent" in board["metrics"]
    assert board["verify_url"] == "/kill-rate"


def test_contradiction_replay_clip():
    card = build_contradiction_replay(
        symbol="ETH",
        conflict={
            "severity": "severe",
            "bullish": ["technical"],
            "bearish": ["sentiment", "macro"],
            "message": "test veto",
            "veto": True,
            "action": "WAIT",
        },
        score=48,
        persist=True,
    )
    assert card["duration_seconds"] == 15
    assert card["action"] == "WAIT"
    assert len(card["frames"]) == 4
    assert "whatsapp" in card["share_urls"]
    assert list_recent_replays(5)


def test_half_life_heat_clock():
    clock = build_heat_clock(
        {"kind": "cross_exchange", "asset": "BTC", "live_duration_seconds": 12}
    )
    assert clock["surface"] == "half_life_heat_clock"
    assert clock["band"]["id"] in {"critical", "high", "warm", "cool"}
    assert "<svg" in clock["svg"]
    board = build_heat_clock_board(limit=3)
    assert board["count"] >= 1


def test_proof_arena_pick_and_week():
    wid = week_id()
    out = submit_pick(user_key="tester@blackdark", symbol="BTC", direction="wait")
    assert out["ok"] is True
    week = build_week_board(wid)
    assert week["week_id"] == wid
    assert week["human"]["picks"] >= 1
    assert "not gambling" in week["rules"]["not"].lower() or "Not gambling" in week["rules"]["not"]


def test_committee_pdf_bytes():
    pdf = build_minimal_pdf(["line one", "line two"], title="BLACKDARK Test")
    assert pdf.startswith(b"%PDF")
    pack = {
        "title": "BLACKDARK — Committee One-Pager",
        "bullets": ["thesis", "kill-rate 12%"],
    }
    assert render_committee_pdf(pack).startswith(b"%PDF")


def test_glass_box_announce_schedule_product_complete():
    set_schedule(announce_at="2099-01-01T12:00:00+00:00", channel="x", note="test")
    status = schedule_status()
    assert status["product_complete"] is True
    assert status["schedule"]["scheduled"] is True
    assert status["drafts_ready"] is True


def test_router_and_template_wiring():
    from pathlib import Path

    heroes = Path("api/routers/heroes.py").read_text(encoding="utf-8")
    dash = Path("dashboard.py").read_text(encoding="utf-8")
    obs = Path("api/routers/observability.py").read_text(encoding="utf-8")
    assert "/api/public/kill-rate" in heroes
    assert "/api/contradiction-replay" in heroes
    assert "/api/oracle/half-life/heat" in heroes
    assert "/api/proof-arena/week" in heroes
    assert "/api/wow/surfaces" in heroes
    assert '"/kill-rate"' in dash or "/kill-rate" in dash
    assert "committee-one-pager" in dash
    assert "committee-one-pager" in obs
    for name in (
        "templates/kill_rate.html",
        "templates/contradiction_replay.html",
        "templates/proof_arena.html",
        "templates/committee_one_pager.html",
    ):
        assert Path(name).exists()


def test_browser_extension_present():
    from pathlib import Path

    assert Path("browser_extension/manifest.json").exists()
    assert Path("browser_extension/src/content.js").exists()


def test_whatsapp_cloud_helpers():
    from alert_service import whatsapp_alert_url, whatsapp_cloud_configured

    url = whatsapp_alert_url("+15551234567", "hello")
    assert url.startswith("https://wa.me/")
    assert isinstance(whatsapp_cloud_configured(), bool)
