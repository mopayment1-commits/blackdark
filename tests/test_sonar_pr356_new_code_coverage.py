"""Sonar PR #356 — behavioral coverage for New Code outside spine-suite scope.

Each test asserts at least one concrete output value (not merely "no exception").
"""

from __future__ import annotations

import hashlib
import hmac
import json
from pathlib import Path
from typing import Any

import pytest


# ---------------------------------------------------------------------------
# cap646.closure_guard
# ---------------------------------------------------------------------------


def test_write_closure_status_persists_without_hmac_for_pending(tmp_path, monkeypatch):
    import cap646.closure_guard as cg

    docs = tmp_path / "docs"
    docs.mkdir()
    manifest = docs / "INSTITUTIONAL_CLOSURE_FINAL.json"
    manifest.write_text("{}\n", encoding="utf-8")
    monkeypatch.setattr(cg, "closure_manifest_path", lambda: manifest)
    monkeypatch.delenv("INSTITUTIONAL_OWNER_APPROVAL_SECRET", raising=False)

    cg.write_closure_status("PENDING_CLOSURE")

    saved = json.loads(manifest.read_text(encoding="utf-8"))
    assert saved["closure_status"] == "PENDING_CLOSURE"


def test_write_closure_status_persists_allowlisted_manifest(tmp_path, monkeypatch):
    import cap646.closure_guard as cg

    docs = tmp_path / "docs"
    docs.mkdir()
    manifest = docs / "INSTITUTIONAL_CLOSURE_FINAL.json"
    manifest.write_text('{"closure_status":"PENDING_CLOSURE"}\n', encoding="utf-8")
    monkeypatch.setattr(cg, "closure_manifest_path", lambda: manifest)
    secret = "unit-test-secret"
    token = hmac.new(secret.encode(), b"INSTITUTIONAL_CLOSED", hashlib.sha256).hexdigest()
    monkeypatch.setenv("INSTITUTIONAL_OWNER_APPROVAL_SECRET", secret)
    monkeypatch.setenv("INSTITUTIONAL_OWNER_APPROVAL_TOKEN", token)

    cg.write_closure_status("INSTITUTIONAL_CLOSED")

    saved = json.loads(manifest.read_text(encoding="utf-8"))
    assert saved["closure_status"] == "INSTITUTIONAL_CLOSED"


def test_write_closure_status_preserves_existing_manifest_fields(tmp_path, monkeypatch):
    import cap646.closure_guard as cg

    docs = tmp_path / "docs"
    docs.mkdir()
    manifest = docs / "INSTITUTIONAL_CLOSURE_FINAL.json"
    manifest.write_text('{"closure_status":"PENDING_CLOSURE","all_verified":true}\n', encoding="utf-8")
    monkeypatch.setattr(cg, "closure_manifest_path", lambda: manifest)

    cg.write_closure_status("PENDING_CLOSURE")

    saved = json.loads(manifest.read_text(encoding="utf-8"))
    assert saved["closure_status"] == "PENDING_CLOSURE"
    assert saved["all_verified"] is True


def test_write_closure_status_rejects_unknown_status(tmp_path, monkeypatch):
    import cap646.closure_guard as cg

    docs = tmp_path / "docs"
    docs.mkdir()
    manifest = docs / "INSTITUTIONAL_CLOSURE_FINAL.json"
    manifest.write_text("{}\n", encoding="utf-8")
    monkeypatch.setattr(cg, "closure_manifest_path", lambda: manifest)

    with pytest.raises(cg.ClosureGuardError, match="unsupported closure_status"):
        cg.write_closure_status("../../../etc/passwd")


def test_closure_manifest_path_resolves_under_docs():
    import cap646.closure_guard as cg

    path = cg.closure_manifest_path()
    assert path.name == "INSTITUTIONAL_CLOSURE_FINAL.json"
    assert path.parent.name == "docs"


# ---------------------------------------------------------------------------
# cap646.parallel_invoke
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_parallel_invoke_missing_backend():
    from cap646.parallel_invoke import invoke_inventory_backend

    out = await invoke_inventory_backend("", params={"symbol": "BTC"})
    assert out["error"] == "missing_backend"
    assert out["success"] is False


@pytest.mark.asyncio
async def test_parallel_invoke_production_cap_entry(monkeypatch):
    from cap646 import parallel_invoke as pi

    async def fake_execute(cid: int, *, params: dict[str, Any]) -> dict[str, Any]:
        return {"capability_id": cid, "surface": "test_surface", "success": True}

    class FakeMod:
        execute = staticmethod(fake_execute)

    monkeypatch.setattr(pi.importlib, "import_module", lambda name: FakeMod())
    out = await pi.invoke_inventory_backend(
        "cap646.batch02_production.cap_069",
        params={"symbol": "ETH"},
    )
    assert out["surface"] == "test_surface"
    assert out["capability_id"] == 69


@pytest.mark.asyncio
async def test_parallel_invoke_generic_async_symbol_params(monkeypatch):
    import types

    from cap646 import parallel_invoke as pi

    async def fake_fn(*, symbol: str, params: dict[str, Any]) -> dict[str, Any]:
        return {"symbol": symbol, "kind": params.get("kind"), "success": True}

    fake_mod = types.ModuleType("fake_async_mod")
    fake_mod.custom_entry = fake_fn
    monkeypatch.setattr(pi.importlib, "import_module", lambda _name: fake_mod)
    out = await pi.invoke_inventory_backend("some.module.custom_entry", params={"symbol": "sol", "kind": "spot"})
    assert out["symbol"] == "SOL"
    assert out["kind"] == "spot"


@pytest.mark.asyncio
async def test_parallel_invoke_sync_fn_symbol_only(monkeypatch):
    import types

    from cap646 import parallel_invoke as pi

    def sync_fn(*, symbol: str) -> dict[str, Any]:
        return {"symbol": symbol, "sync": True}

    fake_mod = types.ModuleType("fake_sync_mod")
    fake_mod.sync_entry = sync_fn
    monkeypatch.setattr(pi.importlib, "import_module", lambda _name: fake_mod)
    out = await pi.invoke_inventory_backend("pkg.mod.sync_entry", params={"asset": "avax"})
    assert out["symbol"] == "AVAX"
    assert out["sync"] is True


# ---------------------------------------------------------------------------
# cap646.dedicated_common — holder / exchange helpers (PR #356 new lines)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_holder_analytics_bundle_returns_metrics(monkeypatch):
    from cap646.dedicated_common import holder_analytics_bundle

    async def fake_holder(symbol: str) -> dict[str, Any]:
        return {"metrics": {"locked_supply_pct": 12.5}, "available": True, "source": "unit"}

    monkeypatch.setattr("bd_platform.free_integrations.holder_analytics", fake_holder)
    dist, metrics = await holder_analytics_bundle("BTC")
    assert metrics["locked_supply_pct"] == 12.5
    assert dist["source"] == "unit"


def test_holder_analytics_footer_stamps_extra():
    from cap646.dedicated_common import holder_analytics_footer

    out = holder_analytics_footer(
        7,
        "holder_distribution",
        "BTC",
        {"available": True, "source": "unit"},
        {"locked_supply_pct": 5},
        extra={"holder_distribution": {"locked_supply_pct": 5}},
    )
    assert out["holder_distribution"]["locked_supply_pct"] == 5
    assert out["symbol"] == "BTC"
    assert out["capability_id"] == 7


@pytest.mark.asyncio
async def test_holder_analytics_locked_extracts_pct(monkeypatch):
    from cap646.dedicated_common import holder_analytics_locked

    async def fake_holder(symbol: str) -> dict[str, Any]:
        return {"metrics": {"locked_supply_pct": "18.2"}, "available": True}

    monkeypatch.setattr("bd_platform.free_integrations.holder_analytics", fake_holder)
    _dist, _metrics, locked = await holder_analytics_locked("ETH")
    assert locked == 18.2


def test_exchange_netflow_probe_and_footer(monkeypatch):
    from cap646.dedicated_common import exchange_netflow_footer, exchange_netflow_probe

    def fake_netflow(*, exchange: str, asset: str) -> dict[str, Any]:
        return {"ok": True, "netflow_proxy": 0.42, "exchange": exchange, "asset": asset}

    monkeypatch.setattr(
        "bd_platform.heroes_capability_layer.exchange_netflow_intelligence_48",
        fake_netflow,
    )
    exchange, netflow = exchange_netflow_probe({"exchange": "okx"}, "BTC")
    assert exchange == "okx"
    assert netflow["netflow_proxy"] == 0.42

    out = exchange_netflow_footer(
        15,
        "exchange_flow_intelligence",
        "BTC",
        exchange,
        netflow,
        flow_payload_key="exchange_flow",
    )
    assert out["exchange_flow"]["netflow_proxy"] == 0.42
    assert out["netflow_proxy"] == 0.42


# ---------------------------------------------------------------------------
# cap978 gate_verdict + closure namespace
# ---------------------------------------------------------------------------


def test_gate_verdict_constants_isolated_from_rtm():
    from cap978.gate_verdict import CAP978_VERIFY_VERDICT_COMPLETE, INSTITUTIONAL_GATE_FAIL, INSTITUTIONAL_GATE_PASS

    assert INSTITUTIONAL_GATE_PASS == "INSTITUTIONAL_GATE_PASS"
    assert INSTITUTIONAL_GATE_FAIL == "NOT_READY"
    assert CAP978_VERIFY_VERDICT_COMPLETE == "VERIFIED_COMPLETE"


@pytest.mark.asyncio
async def test_closure_978_emits_institutional_gate_verdict(monkeypatch):
    from cap978.closure import institutional_closure_978
    from cap978.gate_verdict import INSTITUTIONAL_GATE_PASS

    async def ok_controls() -> dict[str, Any]:
        return {"counts": {"FUNCTIONALLY_INCOMPLETE": 0, "INTERNAL_PARTIAL": 0, "INTERNAL_NOT_IMPLEMENTED": 0}}

    async def ok_chain() -> dict[str, Any]:
        return {"internal_closure": True, "verdict": "VERIFIED_COMPLETE"}

    async def ok_verify(_cid: int) -> dict[str, Any]:
        return {"verdict": "VERIFIED_COMPLETE"}

    monkeypatch.setattr("cap978.closure.verify_all_controls", ok_controls)
    monkeypatch.setattr("cap978.closure.verify_data_platform_chain", ok_chain)
    monkeypatch.setattr("cap978.closure.verify_functional_ci_deterministic", ok_verify)
    monkeypatch.setattr("cap978.closure.ci_deterministic_closure_enabled", lambda: True)

    report = await institutional_closure_978(sample=True, ci_deterministic=True)
    assert report["verdict"] == INSTITUTIONAL_GATE_PASS


# ---------------------------------------------------------------------------
# macro_correlations — degraded/fallback flags (new in PR)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_build_macro_context_safe_success_flags(monkeypatch):
    from macro_correlations import build_macro_context_safe

    async def ok_context() -> dict[str, Any]:
        return {"regime": "Neutral", "dxy_score": 0.1}

    monkeypatch.setattr("macro_correlations.build_macro_context", ok_context)
    ctx = await build_macro_context_safe()
    assert ctx["degraded"] is False
    assert ctx["fallback"] is False
    assert ctx["regime"] == "Neutral"


@pytest.mark.asyncio
async def test_build_macro_context_safe_fallback_flags(monkeypatch):
    from macro_correlations import build_macro_context_safe

    async def boom() -> dict[str, Any]:
        raise RuntimeError("network down")

    monkeypatch.setattr("macro_correlations.build_macro_context", boom)
    ctx = await build_macro_context_safe()
    assert ctx["degraded"] is True
    assert ctx["fallback"] is True
    assert ctx["fallback_reason"] == "macro_fetch_failed_using_mock_indicators"


# ---------------------------------------------------------------------------
# net_edge_truth + institutional_controls FIN-004 shared constant
# ---------------------------------------------------------------------------


def test_fin_004_demo_opportunity_constant_values():
    from net_edge_truth import FIN_004_DEMO_OPPORTUNITY

    assert FIN_004_DEMO_OPPORTUNITY["net_profit_usdt"] == 2.5
    assert FIN_004_DEMO_OPPORTUNITY["quote_amount"] == 1000.0


def test_fin_004_control_uses_shared_demo_opportunity():
    from cap646.institutional_controls import _fin_004

    sample = _fin_004()
    assert sample.get("id") == "FIN-004"
    assert sample.get("status") == "VERIFIED_COMPLETE"


# ---------------------------------------------------------------------------
# handlers lazy exports + batch route helpers
# ---------------------------------------------------------------------------


def test_handlers_lazy_export_resolves_market():
    from cap646.handlers import handle_market_capability

    assert callable(handle_market_capability)


@pytest.mark.asyncio
async def test_batch_route_delegates_execute():
    from cap646.handlers._batch_route import route_batch_capability

    async def fake_execute(capability_id: int, *, params: dict[str, Any]) -> dict[str, Any]:
        return {"capability_id": capability_id, "symbol": params["symbol"]}

    out = await route_batch_capability(fake_execute, 51, params={"symbol": "btc"})
    assert out["capability_id"] == 51
    assert out["symbol"] == "btc"


def test_normalize_symbol_strips_usdt_suffix():
    from cap646.handlers._params import normalize_symbol

    assert normalize_symbol({"asset": "eth/usdt"}) == "ETH"


# ---------------------------------------------------------------------------
# cap978 institutional_gate parallel invariant phase
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_institutional_gate_parallel_timing_field(monkeypatch):
    from cap978.institutional_gate import run_institutional_gate

    async def fast_closure(**_kwargs: Any) -> dict[str, Any]:
        return {
            "verdict": "INSTITUTIONAL_GATE_PASS",
            "cap978": {
                "counts": {
                    "FUNCTIONALLY_INCOMPLETE": 0,
                    "INTERNAL_PARTIAL": 0,
                    "INTERNAL_NOT_IMPLEMENTED": 0,
                },
                "FUNCTIONALLY_INCOMPLETE": 0,
                "INTERNAL_PARTIAL": 0,
                "INTERNAL_NOT_IMPLEMENTED": 0,
                "incomplete_sample": [],
            },
        }

    monkeypatch.setattr("cap978.closure.institutional_closure_978", fast_closure)
    report = await run_institutional_gate(sample=True, check_artifacts=False, include_commercial=False)
    assert report["verdict"] == "PASS"
    assert report["closure_verdict"] == "INSTITUTIONAL_GATE_PASS"
    assert report["timing_ms"]["parallel_invariant_phase"] >= 0


# ---------------------------------------------------------------------------
# cap646.batch_spine — enrich path
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_batch_spine_enrich_adds_capability_metadata():
    from cap646.batch_spine import execute_and_enrich_batch

    async def handler(capability_id: int, *, params: dict[str, Any]) -> dict[str, Any]:
        return {"success": True, "surface": "demo_surface"}

    row = {"capability": "Demo Cap", "track": "T01"}
    out = await execute_and_enrich_batch(handler, 6, row=row, params={"symbol": "BTC"})
    assert out["capability"] == "Demo Cap"
    assert out["track"] == "T01"
    assert out["surface"] == "demo_surface"
