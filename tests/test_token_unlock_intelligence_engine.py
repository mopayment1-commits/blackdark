"""Tests — #707 Token Unlock Intelligence Engine (#703+#704+#708 merged)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import token_unlock_intelligence_engine as tui


@pytest.fixture
def isolated_seed(tmp_path, monkeypatch):
    seed = tmp_path / "token_unlock_intelligence_seed.json"
    seed.write_text(
        json.dumps({
            "calibration": {"price_declined_pct_of_time": 60.0},
            "events": [
                {
                    "event_id": "arb-test",
                    "asset": "ARB",
                    "name": "Arbitrum",
                    "unlock_date": "2026-08-16",
                    "unlock_amount_native": 92500000,
                    "unlock_usd": 98000000,
                    "unlock_pct_circulating": 2.8,
                    "circulating_supply_usd": 3500000000,
                    "adv_usd": 180000000,
                    "recipient_type": "team_vesting",
                    "exchange_inflow_signal": 0.35,
                    "volatility_context": 0.55,
                    "sentiment_context": 0.62,
                    "historical_similarity": 0.72,
                    "primary_source_url": "https://docs.arbitrum.foundation",
                    "assumptions": ["test assumption"],
                    "revision_history": [{"date": "2026-06-01", "change": "initial"}],
                    "comparable_events": [{"asset": "OP", "drawdown_pct": -12.3}],
                },
                {
                    "event_id": "pending",
                    "asset": "NEW",
                    "name": "New",
                    "unlock_date": "2026-09-15",
                    "unlock_amount_native": None,
                    "unlock_usd": None,
                    "recipient_type": "unknown",
                    "primary_source_url": "https://example.com",
                    "assumptions": [],
                    "revision_history": [],
                },
            ],
        }),
        encoding="utf-8",
    )
    monkeypatch.setattr(tui, "_SEED_PATH", seed)
    return seed


def test_merged_tickets(isolated_seed):
    status = tui.token_unlock_intelligence_status()
    assert status["feature_id"] == 707
    assert 703 in status["feature_ids"]
    assert 704 in status["feature_ids"]
    assert 708 in status["feature_ids"]


def test_formula_documented(isolated_seed):
    formula = tui.build_formula_documentation()
    assert formula["formula_version"] == "1.0"
    assert formula["unlock_not_sell_signal"] is True


def test_no_guaranteed_direction(isolated_seed):
    panel = tui.build_impact_panel("ARB")
    assert panel["impact"]["no_guaranteed_price_direction"] is True
    assert panel["not_a_signal"] is True


def test_historical_calibration(isolated_seed):
    cal = tui.build_historical_calibration()
    assert cal["calibrated_historically"] is True
    assert cal["price_declined_pct_of_time"] == 60.0


def test_703_actionability_absorbed(isolated_seed):
    panel = tui.build_actionability_panel("ARB")
    assert panel["sub_task"] == "#703"
    assert panel["archived_standalone"] is True
    assert "actionability_score" in panel["actionability"]
    assert panel["actionability"]["unlock_not_automatic_sell_signal"] is True
    assert isinstance(panel["actionability"]["reasons"], list)


def test_704_calendar_absorbed(isolated_seed):
    cal = tui.build_unlock_calendar()
    assert cal["sub_task"] == "#704"
    assert cal["no_missing_as_zero"] is True
    assert cal["revisions_tracked"] is True
    pending = next(e for e in cal["calendar"] if e["asset"] == "NEW")
    assert pending["missing_unlock_treated_as_zero"] is False
    assert pending["missing_data"] is True


def test_708_dashboard(isolated_seed):
    dash = tui.build_unlock_dashboard()
    assert dash["feature_id"] == 708
    assert dash["surface"] == "token_unlock_dashboard"
    assert len(dash["calendar"]) >= 1
    entry = next(e for e in dash["calendar"] if e["asset"] == "ARB")
    assert "impact" in entry
    assert "actionability" in entry
    if entry["asset"] == "ARB":
        assert entry["magnitude"] is not None


def test_primary_source_and_revisions(isolated_seed):
    normalized = tui.normalize_unlock_event({
        "asset": "ARB",
        "unlock_date": "2026-08-16",
        "unlock_amount_native": 100,
        "primary_source_url": "https://example.com",
        "assumptions": ["a"],
        "revision_history": [{"date": "2026-01-01", "change": "init"}],
    })
    assert normalized["primary_source_url"] == "https://example.com"
    assert normalized["revisions_tracked"] is True


def test_api_routes(isolated_seed):
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    assert c.get("/api/platform/intelligence-ledger/token-unlock/status").status_code == 200
    assert c.get("/api/platform/intelligence-ledger/token-unlock/dashboard").status_code == 200
    resp = c.get("/api/platform/intelligence-ledger/token-unlock/impact?asset=ARB")
    assert resp.status_code == 200
    assert resp.json()["impact"]["impact_score"] > 0


def test_full_seed_exists():
    seed = json.loads(Path("data/token_unlock_intelligence_seed.json").read_text(encoding="utf-8"))
    assert seed["feature_id"] == 707
    assert 703 in seed["feature_ids"]
