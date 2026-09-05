"""Tests for security_trust_data_layer strangler builders (Batch05 Wave 5: #242–244, #246–250)."""

from __future__ import annotations

import pytest

from bd_platform import security_trust_data_layer as std
from cap646.batch05_dedicated import EXPECTED_SURFACE, execute
from cap646.batch05_strangler_spine import STRANGLER_BUILDERS

WAVE5_IDS = [242, 243, 244, 246, 247, 248, 249, 250]


@pytest.fixture(autouse=True)
def reset_watchlist():
    std.reset_security_trust_data_state()
    yield
    std.reset_security_trust_data_state()


@pytest.mark.parametrize("capability_id", WAVE5_IDS)
def test_wave5_builder_registered(capability_id: int):
    assert capability_id in STRANGLER_BUILDERS


@pytest.mark.parametrize("capability_id", WAVE5_IDS)
@pytest.mark.asyncio
async def test_wave5_execute_surface(capability_id: int):
    result = await execute(capability_id, params={"symbol": "BTC", "tier": "pro"})
    root = EXPECTED_SURFACE[capability_id]
    assert result["success"] is True
    assert result["surface"] == root
    assert result[root]["feature_ref"] == capability_id


@pytest.mark.asyncio
async def test_wave5_cap243_bybit_oracle():
    result = await execute(243, params={"symbol": "ETH"})
    payload = result["correlation_matrix"]
    assert payload["bybit_oracle"]["source"] == "bybit"
    assert payload["normalized_oracle_format"] is True


@pytest.mark.asyncio
async def test_wave5_cap244_articles_present():
    result = await execute(244, params={"symbol": "BTC"})
    payload = result["new_listings_intelligence"]
    assert payload["article_count"] >= 1
    assert payload["rule_based_filtering"] is True


@pytest.mark.asyncio
async def test_wave5_cap247_digest_not_recommendation():
    result = await execute(247, params={"symbol": "BTC"})
    payload = result["public_rest_api"]
    assert payload["ai_reports_rejected"] is True
    assert payload["summary_not_recommendation"] is True
