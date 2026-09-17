"""
Independent B2 temporal verification — adversarial controls.

These tests assert required engineering behavior at VERIFIED_IMPLEMENTATION_SHA.
A failure here is verification evidence of a defect; do not modify implementation in-session.
"""

from __future__ import annotations

import ast
from datetime import timedelta
from pathlib import Path

import pytest

from launch57.b1_freshness_bridge import B1_TO_41_RECONCILIATION_ACTIVATED, b1_to_41_reconciliation_state
from launch57.freshness_common import (
    THRESHOLD_DELAYED_SEC,
    THRESHOLD_LIVE_SEC,
    THRESHOLD_NEAR_LIVE_SEC,
    FreshnessState,
    assess_freshness,
)
from launch57.point_in_time_common import append_observation, reset_store_for_tests, retrieve_point_in_time
from launch57.provenance_common import QualityState, build_provenance_record
from launch57.temporal_common import to_rfc3339, utc_now

B2_RUNTIME_FILES = [
    Path("launch57/data_batch2.py"),
    Path("launch57/batch2_isolation.py"),
    Path("launch57/provenance_common.py"),
    Path("launch57/freshness_common.py"),
    Path("launch57/point_in_time_common.py"),
]

PROHIBITED_ROOTS = {
    "failure",
    "failure.freshness",
    "cap646.evidence_class",
    "cap646.dedicated_common",
    "cap646.data_spine",
    "data_governance",
    "data_governance.freshness",
    "hot_storage",
    "oracle_track_record",
}


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    mods: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            mods.add(node.module)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                mods.add(alias.name)
    return mods


def test_isolation_static_imports_zero_legacy_leakage():
    leaked: list[str] = []
    for path in B2_RUNTIME_FILES:
        for mod in _imports(path):
            if any(mod == root or mod.startswith(root + ".") for root in PROHIBITED_ROOTS):
                leaked.append(f"{path}:{mod}")
    assert leaked == []


def test_isolation_no_dynamic_import_hooks_in_b2_runtime():
    tokens = []
    for path in B2_RUNTIME_FILES:
        text = path.read_text(encoding="utf-8")
        for token in ("__import__", "importlib.import_module"):
            if token in text:
                tokens.append(f"{path}:{token}")
    assert tokens == []


def test_canonical_owners_are_launch57_local_only():
    import launch57.data_batch2 as db2

    assert db2.data_quality_provenance_layer.__module__ == "launch57.data_batch2"
    assert db2.freshness_update_assurance.__module__ == "launch57.data_batch2"
    assert db2.point_in_time_immutable_metrics.__module__ == "launch57.data_batch2"
    from launch57.provenance_common import build_provenance_record as p40
    from launch57.freshness_common import assess_freshness as p41
    from launch57.point_in_time_common import retrieve_point_in_time as p39

    assert p40.__module__ == "launch57.provenance_common"
    assert p41.__module__ == "launch57.freshness_common"
    assert p39.__module__ == "launch57.point_in_time_common"


def test_provenance_missing_remains_unknown_not_upgraded():
    record, _ = build_provenance_record(symbol="BTC", params={})
    assert record.quality_state == QualityState.UNKNOWN
    assert record.quality_score is None
    assert record.source_authority is None


def test_provenance_malformed_source_time_fails_closed():
    with pytest.raises(ValueError, match="provider_timestamp_invalid"):
        build_provenance_record(symbol="BTC", params={"source_time": "not-a-timestamp"})


def test_provenance_conflicting_explicit_unknown_wins_over_source():
    record, _ = build_provenance_record(
        symbol="BTC",
        params={
            "source_authority": "exchange:a",
            "quality_state": "unknown",
            "source_time": to_rfc3339(utc_now()),
        },
    )
    assert record.quality_state == QualityState.UNKNOWN


def test_provenance_untrusted_grade_without_source_must_not_pass():
    """Caller-supplied decision_grade without source traceability must not succeed."""
    record, _ = build_provenance_record(symbol="BTC", params={"quality_state": "decision_grade"})
    assert record.source_authority is None
    assert record.quality_state != QualityState.DECISION_GRADE


@pytest.mark.asyncio
async def test_provenance_api_untrusted_grade_without_source_must_not_pass():
    from launch57.data_batch2 import data_quality_provenance_layer

    out = await data_quality_provenance_layer(symbol="BTC", params={"quality_state": "decision_grade"})
    assert out.get("provenance", {}).get("source_authority") is None
    assert out["success"] is False


def test_freshness_threshold_boundaries_are_deterministic():
    now = to_rfc3339(utc_now())
    assert assess_freshness(age_sec=THRESHOLD_LIVE_SEC, available_at=now).freshness_state == FreshnessState.LIVE
    assert assess_freshness(age_sec=THRESHOLD_LIVE_SEC + 0.01, available_at=now).freshness_state == FreshnessState.NEAR_LIVE
    assert assess_freshness(age_sec=THRESHOLD_NEAR_LIVE_SEC, available_at=now).freshness_state == FreshnessState.NEAR_LIVE
    assert assess_freshness(age_sec=THRESHOLD_NEAR_LIVE_SEC + 0.01, available_at=now).freshness_state == FreshnessState.DELAYED
    assert assess_freshness(age_sec=THRESHOLD_DELAYED_SEC, available_at=now).freshness_state == FreshnessState.DELAYED
    assert assess_freshness(age_sec=THRESHOLD_DELAYED_SEC + 0.01, available_at=now).freshness_state == FreshnessState.STALE


def test_freshness_unknown_availability_not_live():
    assessment = assess_freshness()
    assert assessment.freshness_state == FreshnessState.UNKNOWN
    assert assessment.presented_as_live is False
    assert assessment.evidence.available_at is None


def test_freshness_source_time_alone_does_not_fabricate_available_at():
    assessment = assess_freshness(source_time=to_rfc3339(utc_now() - timedelta(seconds=2)))
    assert assessment.evidence.available_at is None
    assert assessment.presented_as_live is False


def test_freshness_future_timestamp_fails_closed():
    assessment = assess_freshness(age_sec=1.0, source_time=to_rfc3339(utc_now() + timedelta(hours=2)))
    assert assessment.success is False
    assert assessment.presented_as_live is False


def test_freshness_stale_never_presented_live():
    assessment = assess_freshness(age_sec=120.0, available_at=to_rfc3339(utc_now()))
    assert assessment.freshness_state == FreshnessState.STALE
    assert assessment.presented_as_live is False


def test_pit_blocks_future_known_store_and_retrieval_leakage():
    reset_store_for_tests()
    now = utc_now()
    past = to_rfc3339(now - timedelta(minutes=30))
    as_of_mid = to_rfc3339(now - timedelta(minutes=15))
    as_of_now = to_rfc3339(now)

    append_observation(symbol="BTC", metric_key="price", value=1.0, effective_time=past, available_at=past)
    append_observation(symbol="BTC", metric_key="price", value=2.0, effective_time=as_of_now, available_at=as_of_now)

    mid_rows = retrieve_point_in_time("BTC", as_of=as_of_mid)
    now_rows = retrieve_point_in_time("BTC", as_of=as_of_now)
    assert [r["value"] for r in mid_rows] == [1.0]
    assert 2.0 in [r["value"] for r in now_rows]

    with pytest.raises(ValueError, match="available_at_after_effective_time"):
        append_observation(symbol="BTC", metric_key="x", value=9.0, effective_time=past, available_at=as_of_now)


def test_pit_retrieval_is_deterministic():
    reset_store_for_tests()
    t = to_rfc3339(utc_now())
    append_observation(symbol="ETH", metric_key="price", value=1.0, effective_time=t, available_at=t)
    a = retrieve_point_in_time("ETH", as_of=t, metric_key="price")
    b = retrieve_point_in_time("ETH", as_of=t, metric_key="price")
    assert a == b


def test_b1_bridge_prepared_not_activated_and_import_inert():
    import launch57.freshness_common  # noqa: F401

    assert B1_TO_41_RECONCILIATION_ACTIVATED is False
    state = b1_to_41_reconciliation_state()
    assert state["status"] == "PREPARED_NOT_ACTIVATED"
    assert state["auto_activate"] is False
    assert state["activated"] is False


@pytest.mark.asyncio
async def test_b1_paths_keep_pending_41_and_block_live(monkeypatch):
    from launch57.data_batch1 import real_time_prices

    async def fake_connector(*, symbol: str, params=None):
        return {"success": True, "selected_provider": "binance"}

    async def fake_ticker(pair: str):
        return {"price": 1.0, "source": "binance", "age_sec": 1.0, "timestamp": to_rfc3339(utc_now())}

    monkeypatch.setattr("launch57.data_batch1.unified_exchange_connector", fake_connector)
    monkeypatch.setattr("launch57.data_batch1.fetch_binance_ticker", fake_ticker)

    out = await real_time_prices(symbol="BTC", params={})
    assert out["b1_to_41_reconciliation"]["status"] == "PREPARED_NOT_ACTIVATED"
    assert out["presented_as_live"] is False
    assert any(p.get("launch_number") == 41 for p in out["temporal_dependency_pending"])


@pytest.mark.asyncio
async def test_b2_retains_hash6_pending_without_evidence_class_output():
    from launch57.data_batch2 import freshness_update_assurance

    out = await freshness_update_assurance(symbol="BTC", params={"quote_age_ms": 1000.0})
    assert any(p.get("launch_number") == 6 for p in out["temporal_dependency_pending"])
    assert "evidence_class" not in out
    assert "ai_compliance_footer" not in str(out)
