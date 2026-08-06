"""Tests for Excel plan audit."""

from __future__ import annotations

from plan_audit import plan_audit


def test_plan_audit_structure():
    data = plan_audit()
    assert data["total_items"] >= 40
    assert 0 <= data["overall_percent"] <= 100
    assert data["complete_count"] + data["partial_count"] + data["planned_count"] == data["total_items"]
    assert len(data["items"]) == data["total_items"]


def test_plan_audit_has_core_arbitrage():
    data = plan_audit()
    titles = {i["title"] for i in data["items"]}
    assert "Cross-exchange arbitrage" in titles or "مراجحة بين المنصات" in titles
    assert "Opportunity Score 0–100" in titles or any("Opportunity" in t for t in titles)
