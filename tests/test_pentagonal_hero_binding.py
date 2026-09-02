"""Tests for pentagonal template + six-hero binding deliverable."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def pentagonal_template() -> dict:
    path = ROOT / "docs" / "PENTAGONAL_TEMPLATE_1_100.json"
    if not path.exists():
        pytest.skip("Run scripts/generate_pentagonal_hero_binding_report.py first")
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def hero_report() -> dict:
    path = ROOT / "docs" / "HERO_SIX_BINDING_REPORT.json"
    if not path.exists():
        pytest.skip("Run scripts/generate_pentagonal_hero_binding_report.py first")
    return json.loads(path.read_text(encoding="utf-8"))


def test_pentagonal_row_count_100(pentagonal_template: dict) -> None:
    assert pentagonal_template["row_count"] == 100
    assert len(pentagonal_template["rows"]) == 100


def test_pentagonal_checksum_valid(pentagonal_template: dict) -> None:
    import hashlib

    rows = pentagonal_template["rows"]
    canonical = json.dumps(rows, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    expected = hashlib.sha256(canonical.encode()).hexdigest()
    assert pentagonal_template["checksum_sha256"] == expected


def test_pentagonal_ids_1_to_100(pentagonal_template: dict) -> None:
    ids = [r["capability_id"] for r in pentagonal_template["rows"]]
    assert ids == list(range(1, 101))


def test_ai_drift_column_present(pentagonal_template: dict) -> None:
    ai_ids = {24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 66, 69, 99, 100}
    for row in pentagonal_template["rows"]:
        cid = row["capability_id"]
        if cid in ai_ids:
            assert row["ai_drift_status"] == "MONITORED"
            assert "baseline" in row
            assert "alert_threshold" in row
        else:
            assert row["ai_drift_status"] == "N/A"


def test_six_heroes_present(hero_report: dict) -> None:
    expected = {
        "Single-Sentence Oracle",
        "Public Accuracy Ledger",
        "Arbitrage Scanner",
        "Whale Signal vs Noise",
        "Stealth Advisor",
        "B2B Feed",
    }
    assert set(hero_report["heroes"]) == expected
    assert len(hero_report["hero_sections"]) == 6


def test_hero_binding_checksum(hero_report: dict) -> None:
    import hashlib

    rows = []
    for section in hero_report["hero_sections"]:
        rows.extend(section["1_feed_map"])
    canonical = json.dumps(rows, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    expected = hashlib.sha256(canonical.encode()).hexdigest()
    assert hero_report["binding_checksum_sha256"] == expected


def test_hero_feeds_scope_1_100(hero_report: dict) -> None:
    for section in hero_report["hero_sections"]:
        for feed in section["1_feed_map"]:
            assert 1 <= feed["capability_id"] <= 100


def test_lookahead_all_pass(hero_report: dict) -> None:
    summary = hero_report["lookahead_summary"]
    assert summary["failed"] == 0
    assert summary["passed"] == summary["total_caps_checked"]


def test_prior_issues_documented(hero_report: dict) -> None:
    issues = hero_report["9_prior_issue_impact"]
    issue_ids = {i["issue"] for i in issues}
    assert "#69 dual-path" in issue_ids
    assert "GET Entitlement Bypass" in issue_ids


@pytest.mark.asyncio
async def test_local_hero_endpoints() -> None:
    from fastapi.testclient import TestClient
    from dashboard import app

    client = TestClient(app)
    endpoints = [
        ("/api/whale/signal-vs-noise", "GET"),
        ("/api/oracle/audit-chain/verify", "GET"),
        ("/api/oracle/net-edge-truth", "GET"),
        ("/api/ledger/share-kit", "GET"),
    ]
    for path, method in endpoints:
        resp = client.get(path) if method == "GET" else client.post(path, json={})
        assert resp.status_code == 200, f"{path} returned {resp.status_code}"

    stealth = client.post("/api/whale/stealth-advisor", json={"asset": "BTC", "notional_usd": 5000})
    assert stealth.status_code == 200
