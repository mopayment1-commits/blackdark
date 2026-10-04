"""Launch-57 Phase A — decision ledger recommendation appendix."""

from __future__ import annotations

import decision_ledger_appendix as appendix


def test_appendix_recommendation_row_default_horizon_and_empty_outcome(monkeypatch):
    persisted: list[dict] = []

    def _capture(row: dict) -> None:
        persisted.append(dict(row))

    monkeypatch.setattr(appendix, "_persist", _capture)

    row = appendix.recommendation_row_from_oracle_enrichment(
        {"symbol": "BTC", "verdict": "WAIT", "opportunity_score": 72},
        asset="BTC",
        verdict="WAIT",
        decision_id="dec_test_phase_a_001",
        user_id="user-ref-42",
        tier="pro",
        event_time="2026-10-04T18:00:00+00:00",
    )

    assert row["outcome_horizon"] == "24h"
    assert row["actual_outcome"] == ""
    assert row["label"] == ""

    assert len(persisted) == 1
    assert persisted[0]["outcome_horizon"] == "24h"
    assert persisted[0]["actual_outcome"] == ""
