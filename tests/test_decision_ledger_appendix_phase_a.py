"""Launch-57 Phase A — decision ledger recommendation appendix."""

from __future__ import annotations

import decision_ledger_appendix as appendix


def test_appendix_recommendation_row_mandatory_fields_and_empty_outcome(monkeypatch):
    persisted: list[dict] = []

    def _capture(row: dict) -> None:
        persisted.append(dict(row))

    monkeypatch.setattr(appendix, "_persist", _capture)

    row = appendix.append_recommendation_decision_record(
        decision_id="dec_test_phase_a_001",
        tenant_id="tenant-launch57",
        user_ref="user-ref-42",
        event_time="2026-10-04T18:00:00+00:00",
        asset="BTC",
        market_state="risk_on",
        model_id="oracle_direction",
        model_version="ens20261004",
        model_confidence=0.82,
        recommendation="WAIT",
        user_action="none",
        user_override="none",
        outcome_horizon="24h",
        data_version="dg-v1",
        feature_set_version="fs-v3",
    )

    mandatory = (
        "decision_id",
        "tenant_id",
        "user_ref",
        "event_time",
        "asset",
        "market_state",
        "model_id",
        "model_version",
        "model_confidence",
        "recommendation",
        "user_action",
        "user_override",
        "outcome_horizon",
        "data_version",
        "feature_set_version",
    )
    for key in mandatory:
        assert row[key] not in (None, ""), key

    assert row["actual_outcome"] == ""
    assert row["label"] == ""

    assert len(persisted) == 1
    assert persisted[0]["decision_id"] == "dec_test_phase_a_001"
    assert persisted[0]["actual_outcome"] == ""
