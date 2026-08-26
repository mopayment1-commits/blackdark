"""Tests — Intelligence Ledger Hub (institutional launch UI)."""

from __future__ import annotations

import pytest

from bd_platform import intelligence_ledger_hub as ilh


def test_catalog_parses_routes():
    catalog = ilh.build_catalog(refresh=True)
    assert len(catalog) >= 50
    sample = next(m for m in catalog if m["module_id"] == "intelligence-layer/market-conditions")
    assert sample["panel_path"].endswith("/market-conditions")
    assert sample["status_path"] is not None


def test_layers_summary():
    layers = ilh.build_layers_summary()
    assert len(layers) >= 5
    assert all(l["module_count"] > 0 for l in layers)


def test_wrap_panel_adds_evidence():
    wrapped = ilh.wrap_panel_response({"ok": True, "display": "test"})
    assert wrapped["evidence_class"] in ilh.EVIDENCE_CLASSES
    assert "evidence_metadata" in wrapped


def test_launch_readiness_honest_verdict():
    report = ilh.build_launch_readiness_report()
    assert report["verdict"] in ("VERIFIED COMPLETE", "NOT READY")
    assert report["summary"]["user_can_use_intelligence_ledger"] is True
    assert any(c["id"] == "il_hub_ui" and c["passed"] for c in report["checks"])


def test_hub_status():
    status = ilh.intelligence_ledger_hub_status()
    assert status["ui_path"] == "/intelligence-ledger"
    assert status["module_count"] >= 50


def test_hub_context():
    ctx = ilh.build_hub_context()
    assert ctx["ok"] is True
    assert len(ctx["catalog"]) >= 50
    assert "launch_readiness" in ctx


def test_api_routes():
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    assert c.get("/api/intelligence-ledger/hub").status_code == 200
    assert c.get("/api/intelligence-ledger/catalog").status_code == 200
    assert c.get("/api/intelligence-ledger/launch-readiness").status_code == 200
    assert c.get("/intelligence-ledger").status_code == 200
    page = c.get("/intelligence-ledger")
    assert "Intelligence Ledger" in page.text
    assert "intelligence_ledger.js" in page.text


def test_user_error_messages_arabic():
    msg = ilh._error_to_user_message("not_found")
    assert "غير متوفر" in msg
