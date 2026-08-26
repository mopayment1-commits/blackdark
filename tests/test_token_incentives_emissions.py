"""Tests — #298 Token Incentives & Emissions Module."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import token_incentives_emissions as tie


@pytest.fixture
def isolated_seed(tmp_path, monkeypatch):
    seed = tmp_path / "token_incentives_emissions_seed.json"
    seed.write_text(
        json.dumps({
            "current_phase": 1,
            "protocols": {"aave": {"name": "Aave", "chain": "ethereum"}},
            "emissions": [
                {
                    "protocol": "aave",
                    "token": "AAVE",
                    "emission_amount": 1000,
                    "price_at_emission_usd": 90.0,
                    "emission_timestamp_utc": "2026-08-20T00:00:00+00:00",
                    "emissions_source": "on_chain_query",
                    "emissions_source_url": "https://example.com",
                },
            ],
        }),
        encoding="utf-8",
    )
    monkeypatch.setattr(tie, "_SEED_PATH", seed)
    return seed


def test_wave_2_defi_scope(isolated_seed):
    status = tie.token_incentives_status()
    assert status["feature_id"] == 298
    assert status["wave"] == 2
    assert status["scope_lock"]["defi_only_wave_2"] is True


def test_price_at_emission_not_current(isolated_seed):
    record = tie.build_emission_record({
        "protocol": "aave",
        "token": "AAVE",
        "emission_amount": 1000,
        "price_at_emission_usd": 90.0,
        "emission_timestamp_utc": "2026-08-20T00:00:00+00:00",
        "emissions_source": "on_chain_query",
    })
    assert record["usd_value_at_emission"] == 90000.0
    assert record["no_current_price"] is True
    assert record["price_time_aligned"] is True


def test_emissions_source_documented(isolated_seed):
    emissions = tie.list_emissions(protocol="aave")
    assert emissions["emissions"][0]["emissions_source"] == "on_chain_query"
    assert emissions["price_alignment"]["emissions_source_required"] is True


def test_panel(isolated_seed):
    panel = tie.build_token_incentives_panel("aave")
    assert panel["ok"] is True
    assert panel["summary"]["total_usd_at_emission"] == 90000.0


def test_api_routes(isolated_seed):
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    assert c.get("/api/platform/intelligence-ledger/token-incentives/status").status_code == 200
    assert c.get("/api/platform/intelligence-ledger/token-incentives?protocol=aave").status_code == 200


def test_full_seed_exists():
    seed = json.loads(Path("data/token_incentives_emissions_seed.json").read_text(encoding="utf-8"))
    assert seed["feature_id"] == 298
    assert seed["current_phase"] == 1
