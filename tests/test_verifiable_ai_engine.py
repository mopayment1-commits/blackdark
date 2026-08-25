"""Tests — #230 Verifiable AI Engine (Evidence-Linked Intelligence)."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from bd_platform import verifiable_ai_engine as vai


@pytest.fixture
def isolated_seed(tmp_path, monkeypatch):
    seed = tmp_path / "verifiable_ai_engine_seed.json"
    seed.write_text(
        json.dumps({
            "audit_retention_days": 90,
            "fail_closed": True,
            "no_model_only_facts": True,
            "all_tiers": True,
            "source_links": {
                "oracle": "/api/v1/platform/oracle?asset={asset}",
                "price": "/api/v1/platform/price?asset={asset}",
            },
        }),
        encoding="utf-8",
    )
    audit = tmp_path / "audit_trail.jsonl"
    monkeypatch.setattr(vai, "_SEED_PATH", seed)
    monkeypatch.setattr(vai, "_AUDIT_LOG", audit)
    return seed


@pytest.fixture
def mock_oracle_envelope():
    return {
        "ok": True,
        "asset": "BTC",
        "data": {
            "verdict": "WAIT",
            "confidence_score": 62.0,
            "headline": "WAIT — confidence 62%",
        },
        "metadata": {"fetched_at": "2026-08-25T13:20:00+00:00", "source": "decision_intelligence_engine"},
        "timestamp": "2026-08-25T13:20:00+00:00",
    }


@pytest.fixture
def mock_price_envelope():
    return {
        "ok": True,
        "asset": "BTC",
        "data": {
            "price_usd": 98500.0,
            "change_24h_pct": 1.2,
        },
        "metadata": {"fetched_at": "2026-08-25T13:20:00+00:00", "source": "binance_futures_public"},
        "timestamp": "2026-08-25T13:20:00+00:00",
    }


@pytest.mark.asyncio
async def test_blackdark_data_tool_returns_evidence(
    isolated_seed, mock_oracle_envelope, mock_price_envelope, monkeypatch
):
    monkeypatch.setattr(
        "bd_platform.unified_api_platform.fetch_oracle",
        AsyncMock(return_value=mock_oracle_envelope),
    )
    monkeypatch.setattr(
        "bd_platform.unified_api_platform.fetch_price",
        AsyncMock(return_value=mock_price_envelope),
    )
    monkeypatch.setattr(
        vai,
        "_freshness_for_asset",
        lambda asset, feed_id="oracle": {"latency_ms": 120, "stale": False},
    )

    result = await vai.blackdark_data_tool("BTC")
    assert result["ok"] is True
    assert len(result["evidence"]) == 2
    assert result["evidence"][0]["source_api"] == "Oracle API v2.1"
    assert result["evidence"][0]["freshness_ms"] == 120
    assert "/api/v1/platform/oracle?asset=BTC" in result["evidence"][0]["source_link"]


@pytest.mark.asyncio
async def test_fail_closed_no_data(isolated_seed, monkeypatch):
    monkeypatch.setattr(
        "bd_platform.unified_api_platform.fetch_oracle",
        AsyncMock(return_value={"ok": False, "data": {}}),
    )
    monkeypatch.setattr(
        "bd_platform.unified_api_platform.fetch_price",
        AsyncMock(return_value={"ok": False, "data": {}}),
    )

    result = await vai.ground_ai_response("What is the BTC price?", asset="BTC")
    assert result["fail_closed"] is True
    assert "don't have verified data" in result["answer"].lower()
    assert result["confidence_badge"] == "Simulated"
    assert result["evidence"] == []


@pytest.mark.asyncio
async def test_no_model_only_facts_with_evidence(
    isolated_seed, mock_oracle_envelope, mock_price_envelope, monkeypatch
):
    monkeypatch.setattr(
        "bd_platform.unified_api_platform.fetch_oracle",
        AsyncMock(return_value=mock_oracle_envelope),
    )
    monkeypatch.setattr(
        "bd_platform.unified_api_platform.fetch_price",
        AsyncMock(return_value=mock_price_envelope),
    )
    monkeypatch.setattr(
        vai,
        "_freshness_for_asset",
        lambda asset, feed_id="oracle": {"latency_ms": 80, "stale": False},
    )

    result = await vai.ground_ai_response("Analyze BTC verdict", asset="BTC", answer="BTC looks neutral.")
    assert result["no_model_only_facts"] is True
    assert len(result["evidence"]) >= 1
    assert result["confidence_badge"] in ("Verified", "Partial")
    assert result["disclaimer_hideable"] is False
    assert "financial advice" in result["disclaimer"].lower()


def test_mandatory_disclaimer(isolated_seed):
    payload = vai.attach_verifiable_ai({"reply": "test"}, evidence=[], query="hi")
    assert payload["disclaimer_hideable"] is False
    assert "financial advice" in payload["disclaimer"].lower()


def test_not_standalone(isolated_seed):
    status = vai.verifiable_ai_status()
    assert status["standalone"] is False
    assert status["feature_id"] == 230
    assert status["fail_closed"] is True
    assert status["no_model_only_facts"] is True
    assert status["all_tiers"] is True


def test_audit_trail_retention(isolated_seed):
    vai.attach_verifiable_ai({"reply": "a"}, evidence=[], query="q1")
    vai.attach_verifiable_ai({"reply": "b"}, evidence=[], query="q2")
    trail = vai.get_audit_trail(limit=10)
    assert trail["audit_retention_days"] == 90
    assert trail["count"] == 2
    assert trail["entries"][-1]["query"] == "q2"


def test_system_prompt_requires_tool_grounding(isolated_seed):
    assert "BLACKDARK data tool" in vai.SYSTEM_PROMPT
    assert "don't have current data" in vai.SYSTEM_PROMPT.lower()


@pytest.mark.asyncio
async def test_oracle_envelope_enrichment(isolated_seed, monkeypatch):
    monkeypatch.setattr(
        vai,
        "_freshness_for_asset",
        lambda asset, feed_id="oracle": {"latency_ms": 100, "stale": False},
    )
    envelope = {
        "ok": True,
        "data": {"verdict": "BUY", "confidence_score": 75},
        "metadata": {"fetched_at": "2026-08-25T13:20:00+00:00"},
    }
    enriched = await vai.enrich_oracle_envelope(envelope, "BTC")
    assert enriched["verifiable_ai"]["feature_id"] == 230
    assert enriched["verifiable_ai"]["confidence_badge"] == "Verified"
    assert len(enriched["verifiable_ai"]["evidence"]) == 1
    assert enriched["verifiable_ai"]["disclaimer_hideable"] is False


@pytest.mark.asyncio
async def test_chat_service_integration(isolated_seed, mock_oracle_envelope, mock_price_envelope, monkeypatch):
    monkeypatch.setattr(
        "bd_platform.unified_api_platform.fetch_oracle",
        AsyncMock(return_value=mock_oracle_envelope),
    )
    monkeypatch.setattr(
        "bd_platform.unified_api_platform.fetch_price",
        AsyncMock(return_value=mock_price_envelope),
    )
    monkeypatch.setattr(
        vai,
        "_freshness_for_asset",
        lambda asset, feed_id="oracle": {"latency_ms": 50, "stale": False},
    )
    monkeypatch.setattr(
        "chat_service._gather_market_context",
        AsyncMock(return_value={"symbol": "BTC", "oracle": {"verdict": "WAIT", "score": 62}}),
    )

    from chat_service import process_chat

    result = await process_chat("What should I do with BTC?")
    assert "evidence" in result
    assert result["no_model_only_facts"] is True
    assert result["confidence_badge"] in ("Verified", "Partial")
    assert result["reply"]


def test_api_routes(isolated_seed):
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    assert c.get("/api/platform/verifiable-ai/status").status_code == 200
    status = c.get("/api/platform/verifiable-ai/status").json()
    assert status["feature_id"] == 230
    assert c.get("/api/platform/verifiable-ai/audit").status_code == 200


def test_full_seed_exists():
    seed = json.loads(Path("data/verifiable_ai_engine_seed.json").read_text(encoding="utf-8"))
    assert seed["feature_id"] == 230
    assert seed["standalone"] is False
    assert seed["audit_retention_days"] == 90
