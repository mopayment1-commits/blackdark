"""Public Accuracy Ledger — misses section markup."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_oracle_accuracy_misses_section_prominent():
    from dashboard import app

    html = TestClient(app).get("/oracle-accuracy").text
    assert 'id="misses-honesty-banner"' in html
    assert "We publish misses publicly" in html
    assert 'id="misses-verified-count"' in html
    assert 'id="misses-recent-table"' in html
    assert 'id="losing"' in html
