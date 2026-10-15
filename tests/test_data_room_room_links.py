"""Data Room (/data-room?lens=room) prove-it destinations stay wired to live APIs."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_data_room_index_lists_room_surfaces():
    util = (ROOT / "templates/utility.html").read_text(encoding="utf-8")
    block = util.split("{% elif page == 'data_room' %}", 1)[1].split("{% elif", 1)[0]
    assert "/priority-chain" in block and "CSO Priority Chain" in block
    assert "/zero-tolerance" in block
    assert "/b2b#fund-terminal" in block
    assert "/b2b#evidence" in block
    assert "/compliance" in block and "Anti-Hype" in block
    assert "/docs" in block


def test_b2b_room_hash_sections_load_api_data():
    b2b = (ROOT / "templates/b2b.html").read_text(encoding="utf-8")
    assert "/api/fund/emerging-terminal" in b2b
    assert "/api/due-diligence/evidence-pack/public-summary" in b2b
    assign = b2b.split("Object.assign(window", 1)[1][:500]
    assert "loadFundTerminal" in assign
    assert "loadEvidenceSummary" in assign
    assert "evidenceFullMsg" in b2b
    assert "csp_events.js" in b2b
    deep = b2b.split("function bootB2bDeepLinks", 1)[1][:350]
    assert "fund-terminal" in deep
    assert "evidence" in deep
