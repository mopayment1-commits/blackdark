"""Sonar PR #421 — behavioral coverage for New Code outside the legacy Sonar CI suite."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest


@pytest.mark.asyncio
async def test_v6_true_institutional_external_blocked(monkeypatch):
    from cap646 import v6_true_institutional_dod as mod
    from cap646.v6_true_institutional_dod import verify_v6_true_institutional

    monkeypatch.setattr(mod, "is_external", lambda _cid: True)
    report = await verify_v6_true_institutional(176)
    assert report["verdict"] == "EXTERNAL_BLOCKED"
    assert report["PASS_ENGINEERING"] is False


@pytest.mark.asyncio
async def test_v6_true_institutional_duplicate_canonical():
    from cap646.catalog import is_duplicate
    from cap646.v6_true_institutional_dod import verify_v6_true_institutional

    dup_id = next(cid for cid in range(1, 827) if is_duplicate(cid))
    report = await verify_v6_true_institutional(dup_id)
    assert report["verdict"] == "CANONICALLY_COVERED"
    assert report["PASS_ENGINEERING"] is True


@pytest.mark.asyncio
async def test_v6_true_institutional_live_cap_reports_gates():
    from cap646.v6_true_institutional_dod import verify_v6_true_institutional

    report = await verify_v6_true_institutional(6)
    assert report["capability_id"] == 6
    assert isinstance(report.get("gates"), dict)
    assert "G01_functional_completeness" in report["gates"]
    assert report.get("binding_source")


def test_v6_true_superficial_binding_explicit_option_a():
    from cap646.v6_true_institutional_dod import _is_superficial_binding

    binding = SimpleNamespace(source="explicit_option_a", capability_id=176)
    assert _is_superficial_binding(binding) is False


def test_v6_true_gate_functional_appropriateness_bi_connector():
    from cap646.v6_true_institutional_dod import _gate_functional_appropriateness_true

    binding = SimpleNamespace(source="explicit_option_a", capability_id=1)
    ok, reason = _gate_functional_appropriateness_true(
        "BI Connectors Hub",
        {"bi_connectors": {"items": []}},
        binding,
    )
    assert ok is True
    assert reason == "bi_connector_payload"


def test_v6_true_payload_helper_nested_result():
    from cap646.v6_true_institutional_dod import _payload

    assert _payload({"result": {"surface": "x"}})["surface"] == "x"
    assert _payload({"surface": "y"})["surface"] == "y"


@pytest.mark.asyncio
async def test_v6_from_scratch_external_blocked(monkeypatch):
    from cap646.v6_from_scratch_dod import verify_from_scratch

    monkeypatch.setattr("cap646.catalog.is_external", lambda _cid: True)
    ext = await verify_from_scratch(176)
    assert ext["prebuild_state"] == "EXTERNAL_BLOCKED"
    assert ext["PASS_FROM_SCRATCH"] is False


@pytest.mark.asyncio
async def test_v6_from_scratch_duplicate_alias():
    from cap646.catalog import is_duplicate
    from cap646.v6_from_scratch_dod import verify_from_scratch

    dup_id = next(cid for cid in range(1, 827) if is_duplicate(cid))
    dup = await verify_from_scratch(dup_id)
    assert dup["prebuild_state"] == "DUPLICATE_ALIAS"
    assert dup["PASS_FROM_SCRATCH"] is True


@pytest.mark.asyncio
async def test_v6_from_scratch_live_cap_reports_handler_metadata():
    from cap646.v6_from_scratch_dod import verify_from_scratch

    report = await verify_from_scratch(176)
    assert report["capability_id"] == 176
    assert "from_scratch_gates" in report
    assert report.get("official_batch")
    assert isinstance(report.get("thin_wrapper"), bool)


def test_v6_from_scratch_handler_is_thin_wrapper_known_cap():
    from cap646.v6_from_scratch_dod import _handler_is_thin_wrapper

    thin, reason = _handler_is_thin_wrapper(176)
    assert isinstance(thin, bool)
    assert reason


@pytest.mark.asyncio
async def test_v6_strict_dod_external_blocked(monkeypatch):
    from cap646 import v6_strict_dod as mod
    from cap646.v6_strict_dod import verify_v6_strict

    monkeypatch.setattr(mod, "is_external", lambda _cid: True)
    ext = await verify_v6_strict(176)
    assert ext["PASS_ENGINEERING"] is False


@pytest.mark.asyncio
async def test_v6_strict_dod_duplicate_canonical():
    from cap646.catalog import is_duplicate
    from cap646.v6_strict_dod import verify_v6_strict

    dup_id = next(cid for cid in range(1, 827) if is_duplicate(cid))
    dup = await verify_v6_strict(dup_id)
    assert dup["verdict"] == "CANONICALLY_COVERED"


@pytest.mark.asyncio
async def test_v6_strict_dod_live_cap_reports_gate_map():
    from cap646.v6_strict_dod import verify_v6_strict

    report = await verify_v6_strict(6)
    assert report["capability_id"] == 6
    assert isinstance(report.get("gates"), dict)


def test_v6_strict_gate_data_quality_dict_without_provenance():
    from cap646.v6_strict_dod import _gate_data_quality

    assert _gate_data_quality({"result": {"symbol": "BTC"}}) is False
    assert _gate_data_quality({"result": {"data_provenance": {"score": 1}}}) is True


@pytest.mark.asyncio
async def test_monitoring_state_roundtrip(tmp_path, monkeypatch):
    import ops.monitoring_alerting as mon

    state_file = tmp_path / "data" / "monitoring_alert_state.json"
    monkeypatch.setattr(mon, "_STATE_FILE", state_file)
    monkeypatch.setattr(mon, "ROOT", tmp_path)

    mon._save_state({"consecutive_failures": 2, "last_alert_ts": 42.5, "last_signal_alerts": {"sla": 1}})
    loaded = mon._load_state()
    assert loaded["consecutive_failures"] == 2
    assert loaded["last_alert_ts"] == 42.5
    assert loaded["last_signal_alerts"] == {"sla": 1}


@pytest.mark.asyncio
async def test_institutional_official_production_batch08_cap():
    from cap646.institutional_official_production import execute, expected_surface

    result = await execute(
        176,
        params={"symbol": "BTC", "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"},
    )
    assert result["success"] is True
    assert result["surface"] == expected_surface(176)
    assert result.get("handler_module", "").endswith("batch08_dedicated")


@pytest.mark.asyncio
async def test_batch_institutional_closure_batch01_shape():
    from cap646.batch_institutional_closure import verify_batch01_institutional

    report = await verify_batch01_institutional(6)
    assert report["capability_id"] == 6
    assert "PASS_INSTITUTIONAL" in report
