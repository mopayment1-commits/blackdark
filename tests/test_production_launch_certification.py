"""Production launch certification — NO-GO unless unconditional GO criteria are actually met."""

from __future__ import annotations

ALLOWED = {"PASS", "FAIL", "NOT_TESTED", "NOT_APPLICABLE"}
GO = {"GO", "CONDITIONAL GO", "NO-GO"}
FEAT = {"PRODUCTION-READY", "NOT PRODUCTION-READY"}


def test_integrity_eleven_cases_and_no_illegal_verdicts():
    from production_launch_certification import (
        run_financial_integrity_cases,
        run_three_am_scenarios,
    )

    integ = run_financial_integrity_cases()
    assert integ["case_count"] == 11
    assert integ["verdict"] in ALLOWED
    assert integ["fail_ids"] == []
    for c in integ["cases"]:
        assert c["verdict"] in ALLOWED, c
    three = run_three_am_scenarios()
    assert len(three["scenarios"]) == 10
    for s in three["scenarios"]:
        assert s["verdict"] in ALLOWED, s
        for k in ("detects", "blocks_bad_decision", "fails_safe", "alert", "recovers", "preserves_data"):
            assert k in s, k


def test_build_cert_is_nogo_and_counts_opens():
    from production_launch_certification import build_certification

    cert = build_certification()
    assert cert["product_complete"] is False
    assert cert["live_money_ready"] is False
    v = cert["final_production_verdict"]
    assert v["decision"] == "NO-GO"
    assert v["unconditional_go_criteria_met"] is False
    assert v["critical_open"] >= 1
    assert v["high_open"] >= 1
    assert v["untested_launch_critical_requirements"] >= 1
    assert v["unknown_launch_blockers"] == []
    for d in cert["domains"]:
        assert d["verdict"] in ALLOWED, d
    for c in cert["capabilities"]:
        assert c["certification"] in FEAT, c
    live = next(c for c in cert["capabilities"] if c["id"] == "EX-LIVE")
    assert live["certification"] == "NOT PRODUCTION-READY"
    tg = next(c for c in cert["capabilities"] if c["id"] == "AL-TG")
    assert tg["certification"] == "NOT PRODUCTION-READY"
    assert v["decision"] in GO


def test_launch_cert_api_never_implies_complete():
    from fastapi.testclient import TestClient

    from dashboard import app

    client = TestClient(app, follow_redirects=False)
    r = client.get("/api/product/production-launch-cert")
    assert r.status_code == 200
    body = r.json()
    assert body["product_complete"] is False
    assert body["live_money_ready"] is False
    assert body.get("decision") in GO | {None}
    if body.get("ok"):
        assert body["decision"] == "NO-GO"
