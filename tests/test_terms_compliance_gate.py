"""Terms acceptance + strict AI disclaimer compliance tests."""

from __future__ import annotations

from pathlib import Path

import pytest
from starlette.requests import Request


def test_get_disclaimer_is_strict():
    from regulatory_compliance_guard import ORACLE_CLASSIFICATION_LABEL, get_disclaimer

    text = get_disclaimer()
    assert "not financial advice" in text.lower()
    assert "DYOR" in text
    assert "100%" in text
    assert "Probabilistic Analysis" in ORACLE_CLASSIFICATION_LABEL


def test_apply_regulatory_adds_label_and_disclaimer():
    from regulatory_compliance_guard import apply_regulatory_compliance

    out = apply_regulatory_compliance({"verdict": "BUY", "oracle": "Buy Now BTC"})
    assert out["is_investment_advice"] is False
    assert "disclaimer" in out
    assert out["oracle_classification_label"]
    assert out["compliance_footer"]["disclaimer"]


def test_terms_and_privacy_templates_exist():
    root = Path(__file__).resolve().parents[1]
    assert (root / "templates" / "terms.html").is_file()
    assert (root / "templates" / "privacy.html").is_file()
    assert (root / "templates" / "request_deletion.html").is_file()


def test_legal_content_covers_not_advice():
    from legal_content import LEGAL_PAGES

    assert "Not Financial Advice" in LEGAL_PAGES["terms"]["html"]
    assert "do NOT sell" in LEGAL_PAGES["privacy"]["html"].lower() or "We do NOT sell" in LEGAL_PAGES["privacy"]["html"]
    assert "request-deletion" in LEGAL_PAGES["privacy"]["html"]


@pytest.mark.asyncio
async def test_enforce_terms_blocks_without_cookie(monkeypatch):
    monkeypatch.setenv("TERMS_ACCEPTANCE_REQUIRED", "true")
    import terms_consent as tc

    monkeypatch.setattr(tc, "ACCEPTANCE_REQUIRED", True)
    monkeypatch.setattr(tc, "TERMS_VERSION", "test-v1")

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/oracle/BTC",
        "headers": [],
        "query_string": b"",
        "client": ("127.0.0.1", 123),
        "server": ("test", 80),
        "scheme": "http",
    }
    request = Request(scope)
    with pytest.raises(Exception) as exc:
        await tc.enforce_terms_acceptance(request, None)
    assert exc.value.status_code == 403
    assert exc.value.detail["error"] == "terms_not_accepted"


@pytest.mark.asyncio
async def test_enforce_terms_allows_cookie(monkeypatch):
    monkeypatch.setenv("TERMS_ACCEPTANCE_REQUIRED", "true")
    import terms_consent as tc

    monkeypatch.setattr(tc, "ACCEPTANCE_REQUIRED", True)
    monkeypatch.setattr(tc, "TERMS_VERSION", "test-v1")

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/oracle/BTC",
        "headers": [(b"cookie", b"bd_terms_v=test-v1")],
        "query_string": b"",
        "client": ("127.0.0.1", 123),
        "server": ("test", 80),
        "scheme": "http",
    }
    request = Request(scope)
    await tc.enforce_terms_acceptance(request, None)


def test_compliance_footer_uses_strict_disclaimer():
    from decision_certificate import compliance_footer_block

    foot = compliance_footer_block(surface="oracle", trust_basis="ledger")
    assert "not financial advice" in foot["disclaimer"].lower()
    assert foot["classification_label"]
