"""DIG closure tests — pipeline modules + bypass wiring (L1)."""

from __future__ import annotations

import pytest

from blackdark.data_governance.runtime import GovernanceViolationError, enforce_material_write


@pytest.mark.parametrize(
    "module_path,func_name",
    [
        ("data_governance.normalization", "normalize_payload"),
        ("data_governance.streaming", "validate_stream_event"),
        ("data_governance.quality", "score_quality"),
        ("data_governance.reliability", "source_reliability_score"),
        ("data_governance.provenance", "attach_provenance"),
        ("data_governance.methodology", "get_methodology"),
        ("data_governance.gates", "evaluate_material_gates"),
        ("data_governance.legal", "legal_applicability"),
        ("data_governance.fallback", "resolve_fallback"),
        ("data_governance.slo", "slo_status"),
        ("data_governance.l2_l3", "l2_l3_policy"),
        ("data_governance.order_book", "order_book_policy"),
        ("data_governance.historical_depth", "assert_historical_depth"),
        ("data_governance.raw_landing", "record_raw_landing"),
        ("data_governance.retention", "apply_retention_class"),
        ("data_governance.schema_evolution", "validate_schema_version"),
        ("data_governance.timestamps", "ensure_canonical_timestamps"),
        ("data_governance.rate_limit", "check_rate_quota"),
        ("data_governance.observability", "emit_governance_event"),
        ("data_governance.decision_surface", "build_decision_surface"),
        ("data_governance.pipeline", "run_material_pipeline"),
        ("decision_truth.change", "record_material_change"),
        ("decision_truth.half_life", "compute_half_life"),
        ("bd_platform.v4_v2_persistent_registries", "get_registry"),
        ("bd_platform.data_governance_source_driven_engineering", "live_verification_register"),
        ("failure.quality", "score_failure_quality"),
        ("timezone.format", "format_utc_instant"),
    ],
)
def test_dig_module_importable(module_path: str, func_name: str):
    import importlib

    mod = importlib.import_module(module_path)
    assert callable(getattr(mod, func_name))


def test_pipeline_runs_on_material_write():
    row = enforce_material_write(
        "signal",
        {
            "signal_type": "test",
            "asset": "BTC",
            "source_id": "internal_cache",
            "purpose": "analytics",
        },
    )
    assert row.get("pipeline_enforced") is True
    assert row.get("intelligence_receipt")


def test_pipeline_removal_fails(monkeypatch):
    def _boom(*_a, **_k):
        raise RuntimeError("pipeline_bypass_detected")

    monkeypatch.setattr("data_governance.pipeline.run_material_pipeline", _boom)
    with pytest.raises(RuntimeError, match="pipeline_bypass"):
        enforce_material_write(
            "signal",
            {"signal_type": "t", "asset": "BTC", "source_id": "internal_cache", "purpose": "analytics"},
        )


def test_cap646_execute_governance():
    row = enforce_material_write(
        "cap_execute",
        {"capability_id": 1, "source": "cap646", "purpose": "capability_execute"},
    )
    assert row.get("capability_dna")
    assert row.get("governance_enforced") is True


def test_sql_bridge_governs_decision():
    from blackdark.data.governance_bridge import govern_sql_write

    row = govern_sql_write("decision", {"decision_id": "d1", "symbol": "BTC", "source": "data_engine"})
    assert row.get("pipeline_enforced") is True


@pytest.mark.asyncio
async def test_signal_compounding_governed():
    from signal_compounding import store_signal

    row = await store_signal(
        symbol="BTC",
        signal_type="test",
        value=1.0,
        confidence=0.5,
        source="internal_cache",
    )
    assert row.get("signal_id")
