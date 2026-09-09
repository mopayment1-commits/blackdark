"""FINAL LOCAL EVIDENCE + GAP CLOSURE V2 targeted tests."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def av_client(tmp_path, monkeypatch):
    db = tmp_path / "av-gap.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db}")
    monkeypatch.setenv("ENV", "development")
    monkeypatch.setenv("COOKIE_SECURE", "false")
    monkeypatch.setenv("SECRETS_MASTER_KEY", "unit-test-vault-key-for-av-gap")
    monkeypatch.setenv("SESSION_TOKEN_PEPPER", "unit-test-session-pepper-av-gap")
    from dashboard import app

    return TestClient(app)


def test_enterprise_alias_maps_to_institutional():
    from billing.plan_registry import normalize_plan
    from anonymous_visitor.states import ProductAuthState, resolve_product_state

    assert normalize_plan("enterprise") == "institutional"
    assert resolve_product_state({"tier": "enterprise"}) == ProductAuthState.INSTITUTIONAL


def test_landing_anonymous_load_does_not_call_private_dashboard_apis():
    html = Path("templates/landing.html").read_text(encoding="utf-8")
    load_block = html.split("window.addEventListener('load'", 1)[-1]
    forbidden_on_load = [
        "/api/analytics/view",
        "/api/discipline-mirror/me",
        "/api/user/",
        "/api/privacy/",
        "/api/admin/",
    ]
    hits = [p for p in forbidden_on_load if p in load_block.split("consultOracle", 1)[0]]
    assert hits == [], f"anonymous load invokes private APIs: {hits}"


def test_discipline_mirror_gated_without_session():
    html = Path("templates/landing.html").read_text(encoding="utf-8")
    assert "bdHasAuthSession()" in html
    assert "Sign in to save private Discipline Mirror" in html


def test_reconciliation_sha_semantics_fields_present():
    from anonymous_visitor.reconciliation import reconciliation_semantics_valid

    sem = reconciliation_semantics_valid()
    assert "implementation_sha" in sem
    assert "evidence_generated_from_sha" in sem
    assert "artifact_commit_sha" in sem
    assert sem.get("SELF_REFERENTIAL_COMMIT_HASH") is False or sem.get("stale_fields")


def test_traceability_separate_from_satisfaction():
    from anonymous_visitor.traceability import build_traceability_report

    report = build_traceability_report()
    assert report["TOTAL_SPEC_REQUIREMENTS"] == 153
    assert report["TRACEABILITY_ACCOUNTED_COUNT"] == 153
    assert report["TRACEABILITY_ACCOUNTED_PERCENT"] == 100.0
    assert report["PARTIAL_REQUIREMENTS"] > 0
    assert report["SATISFIED_PERCENT"] < report["TRACEABILITY_ACCOUNTED_PERCENT"]


def test_public_docs_no_full_openapi_link():
    html = Path("templates/docs_public.html").read_text(encoding="utf-8")
    assert "/api/docs/openapi.json" not in html


def test_bandit_sha1_protocol_narrow_resolution():
    from identity.breached_passwords import sha1_prefix_suffix

    prefix, suffix = sha1_prefix_suffix("blackdark-test-password")
    assert len(prefix) == 5
    assert len(suffix) == 35


def test_stream_runtime_controls_proven():
    from anonymous_visitor.streams import audit_stream_runtime_controls

    audit = audit_stream_runtime_controls()
    assert audit["UNPROVEN"] == []


def test_av08_accuracy_denominator_visible(av_client):
    r = av_client.get("/api/anonymous-visitor/public-intelligence/accuracy")
    assert r.status_code == 200
    data = r.json()
    acc = data.get("accuracy") or {}
    assert acc.get("PUBLIC_ACCURACY_UI_DENOMINATOR_VISIBLE") is True
    assert "ACCURACY_DENOMINATOR" in acc
    assert "ACCURACY_DENOMINATOR_DEFINITION" in acc
