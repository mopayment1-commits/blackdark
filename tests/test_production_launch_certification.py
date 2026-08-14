"""Production launch certification — NO-GO unless unconditional GO criteria are actually met."""

from __future__ import annotations

ALLOWED = {"PASS", "FAIL", "NOT_TESTED", "NOT_APPLICABLE"}
GO = {"GO", "CONDITIONAL GO", "NO-GO"}
FEAT = {"PUBLIC-DEMO-READY", "LIVE-PRODUCTION-READY", "LIVE-MONEY-READY", "NOT-READY"}
FORBIDDEN_CERT = {"PRODUCTION-READY", "NOT PRODUCTION-READY"}


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
    assert cert["schema"] == "production_launch_certification.v2"
    assert cert["product_complete"] is False
    assert cert["live_money_ready"] is False
    assert cert["live_production_ready"] is False
    tracks = cert["tracks"]
    assert tracks["LIVE-MONEY-READY"] is False
    assert tracks["LIVE-PRODUCTION-READY"] is False
    v = cert["final_production_verdict"]
    assert v["decision"] == "NO-GO"
    assert v["unconditional_go_criteria_met"] is False
    assert v["critical_open"] >= 1
    assert v["high_open"] >= 1
    assert v["untested_launch_critical_requirements"] == 0
    assert v["unknown_launch_blockers"] == []
    assert v.get("unverified_launch_critical_assumptions") == []
    for d in cert["domains"]:
        assert d["verdict"] in ALLOWED, d
        if d["launch_critical"]:
            assert d["verdict"] != "NOT_TESTED", d
    for c in cert["capabilities"]:
        assert c["certification"] in FEAT, c
        assert c["certification"] not in FORBIDDEN_CERT, c
    live = next(c for c in cert["capabilities"] if c["id"] == "EX-LIVE")
    assert live["certification"] == "NOT-READY"
    tg = next(c for c in cert["capabilities"] if c["id"] == "AL-TG")
    assert tg["certification"] == "NOT-READY"
    assert all(c["certification"] != "PRODUCTION-READY" for c in cert["capabilities"])
    assert v["decision"] in GO
    live = cert.get("operator_live_probes") or {}
    assert live.get("engineer_cannot_close") is True
    assert live.get("wallet_funded") is False
    assert (live.get("binance_testnet") or {}).get("ok") is False
    assert (live.get("binance_mainnet") or {}).get("ok") is False


def test_launch_cert_api_never_implies_complete():
    from fastapi.testclient import TestClient

    from dashboard import app

    client = TestClient(app, follow_redirects=False)
    r = client.get("/api/product/production-launch-cert")
    assert r.status_code == 200
    body = r.json()
    assert body["product_complete"] is False
    assert body["live_money_ready"] is False
    assert body.get("live_production_ready") in {False, None}
    assert body.get("decision") in GO | {None}
    if body.get("ok"):
        assert body["decision"] == "NO-GO"
        assert body.get("LIVE-MONEY-READY") is False or body.get("tracks", {}).get("LIVE-MONEY-READY") is False
    g = client.get("/api/product/operator-go-gates")
    assert g.status_code == 200
    gates = g.json()
    assert gates.get("decision") in GO | {None}
    if gates.get("ok"):
        assert gates["decision"] == "NO-GO"
        assert gates["LIVE-PRODUCTION-READY"] is False
        assert gates["LIVE-MONEY-READY"] is False
        ids = {row["id"] for row in (gates.get("gates") or [])}
        assert "D07" in ids
        assert "live_probes" in gates
