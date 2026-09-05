"""Unit tests for cap646.dedicated_common — IEEE 1012 regression guard for Extract Function."""

from __future__ import annotations

import pytest

from cap646.dedicated_common import addr, execute_dedicated_caps, make_wrap_binding, provenance_hot_storage_payload, seed, success_from, sym, wrap


def test_sym_normalizes_asset():
    assert sym({"asset": "eth/usdt"}) == "ETH"


def test_addr_default_wallet():
    assert addr({}).startswith("0x")


def test_success_from_dict_flags():
    assert success_from({"success": True}) is True
    assert success_from({"success": False}) is False
    assert success_from({"ok": True}) is True


def test_wrap_stamps_surface():
    surfaces = {1: "demo_surface"}
    out = wrap(1, expected_surface=surfaces, symbol="BTC", payload_key="data", payload={"x": 1})
    assert out["surface"] == "demo_surface"
    assert out["capability_id"] == 1


def test_make_wrap_binding():
    binding = make_wrap_binding({2: "bound"})
    out = binding(2, symbol="BTC", payload_key="k", payload={})
    assert out["surface"] == "bound"


def test_seed_returns_dict():
    assert isinstance(seed(), dict)


@pytest.mark.asyncio
async def test_execute_dedicated_caps_dispatches():
    async def _fn(*, symbol: str, address: str, params: dict):
        return {"symbol": symbol, "ok": True}

    out = await execute_dedicated_caps(
        7,
        params={"symbol": "BTC"},
        dedicated_ids=frozenset({7}),
        overlap_batch01_ids=frozenset(),
        dispatch={7: _fn},
        overlap_error="overlap",
        not_dedicated_error="missing",
    )
    assert out["symbol"] == "BTC"


def test_success_from_non_dict():
    assert success_from(True) is True
    assert success_from(False) is False


def test_wrap_with_extra():
    surfaces = {1: "demo_surface"}
    out = wrap(1, expected_surface=surfaces, symbol="BTC", payload_key="data", payload={"x": 1}, extra={"tag": "y"})
    assert out["tag"] == "y"


@pytest.mark.asyncio
async def test_execute_dedicated_caps_not_dedicated_error():
    with pytest.raises(ValueError, match="missing"):
        await execute_dedicated_caps(
            99,
            params={},
            dedicated_ids=frozenset({7}),
            overlap_batch01_ids=frozenset(),
            dispatch={},
            overlap_error="overlap",
            not_dedicated_error="missing",
        )


def test_seed_missing_file_returns_empty_dict(monkeypatch, tmp_path):
    import cap646.dedicated_common as dc

    monkeypatch.setattr(dc, "_SEED_PATH", tmp_path / "missing.json")
    assert dc.seed() == {}


@pytest.mark.asyncio
async def test_execute_dedicated_caps_overlap_error():
    with pytest.raises(ValueError, match="overlap"):
        await execute_dedicated_caps(
            55,
            params={},
            dedicated_ids=frozenset({55}),
            overlap_batch01_ids=frozenset({55}),
            dispatch={},
            overlap_error="overlap",
            not_dedicated_error="missing",
        )


def test_provenance_hot_storage_payload():
    payload = provenance_hot_storage_payload("BTC")
    assert "provenance" in payload
    assert "hot_storage" in payload
