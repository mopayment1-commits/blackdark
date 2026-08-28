"""Tests — Trust Core (#1064–#1068 + #1021 + #1018)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import cryptographic_timestamping as cts
from bd_platform import epistemic_humility_gate as eph
from bd_platform import falsifiability_policy as fals
from bd_platform import legal_framework_cross_cutting as legal
from bd_platform import public_accuracy_ledger as pal


@pytest.fixture
def trust_seed() -> dict:
    return json.loads(Path("data/trust_core_seed.json").read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def reset_all(trust_seed):
    fals.reset_falsifiability_state()
    pal.reset_public_ledger_state()
    cts.reset_timestamping_state()
    eph.reset_epistemic_gate_state()
    legal.reset_legal_framework_state()
    yield
    fals.reset_falsifiability_state()
    pal.reset_public_ledger_state()
    cts.reset_timestamping_state()
    eph.reset_epistemic_gate_state()
    legal.reset_legal_framework_state()


# ─── #1064 Falsifiability ─────────────────────────────────────────────────────


def test_1064_three_condition_types(trust_seed):
    conditions = fals.build_falsification_conditions(asset="BTC")
    assert "price_based" in conditions
    assert "time_based" in conditions
    assert "metric_based" in conditions


def test_1064_validate_and_block(trust_seed):
    valid = {"falsification_conditions": fals.build_falsification_conditions()}
    assert fals.validate_falsification_present_1064(valid, seed=trust_seed)["valid"] is True
    blocked = fals.enforce_falsification_on_output_1064({}, seed=trust_seed)
    assert blocked.get("suppressed") is True


def test_1064_e2e(trust_seed):
    assert fals.run_falsifiability_e2e_1064(seed=trust_seed)["all_passed"] is True


# ─── #1065 Public Ledger ───────────────────────────────────────────────────────


def test_1065_standalone(trust_seed):
    status = pal.public_accuracy_ledger_status_1065(seed=trust_seed)
    assert status["standalone"] is True
    assert status["public_url"] == "/trust/ledger"


def test_1065_errors_first(trust_seed):
    pal.feed_from_internal_ledger_987(seed=trust_seed)
    view = pal.build_public_ledger_view_1065(errors_first=True, limit=10, seed=trust_seed)
    assert view["errors_first"] is True
    assert any(e.get("outcome") == "loss" for e in view["entries"])


def test_1065_export_checksum(trust_seed):
    pal.feed_from_internal_ledger_987(seed=trust_seed)
    export = pal.export_ledger_1065()
    assert len(export["checksum_sha256"]) == 64


def test_1065_e2e(trust_seed):
    assert pal.run_public_ledger_e2e_1065(seed=trust_seed)["all_passed"] is True


# ─── #1066 Timestamping ───────────────────────────────────────────────────────


def test_1066_timestamp_and_merkle(trust_seed):
    ts = cts.timestamp_prediction_1066(
        prediction_id="p1", payload={"asset": "BTC"}, seed=trust_seed
    )
    assert ts["prediction_hash"]
    merkle = cts.batch_merkle_tree_1066(seed=trust_seed)
    assert merkle["ok"] is True


def test_1066_e2e(trust_seed):
    assert cts.run_timestamping_e2e_1066(seed=trust_seed)["all_passed"] is True


# ─── #1021+#1067 Epistemic Humility ───────────────────────────────────────────


def test_1021_blocks_low_confidence(trust_seed):
    result = eph.evaluate_epistemic_gate_1021(confidence_score=2.0, sample_size=50, seed=trust_seed)
    assert result["blocked"] is True
    assert result["output"] == "I DON'T KNOW"


def test_1021_merged_1067(trust_seed):
    status = eph.epistemic_humility_status_1021(seed=trust_seed)
    assert status["merged_feature_ref"] == 1067


def test_1021_e2e(trust_seed):
    assert eph.run_epistemic_gate_e2e_1021(seed=trust_seed)["all_passed"] is True


# ─── #1018+#1068 Legal ────────────────────────────────────────────────────────


def test_1018_forbidden_language(trust_seed):
    bad = legal.scan_forbidden_language_1018("guaranteed returns forever", seed=trust_seed)
    assert bad["passed"] is False


def test_1018_merged_1068(trust_seed):
    status = legal.legal_framework_status_1018(seed=trust_seed)
    assert status["merged_feature_ref"] == 1068


def test_1018_e2e(trust_seed):
    assert legal.run_legal_framework_e2e_1018(seed=trust_seed)["all_passed"] is True
