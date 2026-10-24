"""Public /errors route — misses-only view."""

from __future__ import annotations

from pathlib import Path


def test_errors_route_renders_misses_only_page():
    dash = Path("dashboard.py").read_text(encoding="utf-8")
    assert '@app.get("/errors", response_class=HTMLResponse)' in dash
    assert "errors_only" in dash
    assert "RedirectResponse(url=\"/oracle-accuracy#losing\"" not in dash

    html = Path("templates/oracle_accuracy.html").read_text(encoding="utf-8")
    assert "ERRORS_ONLY_PAGE = {{ 'true' if errors_only else 'false' }}" in html
    assert "{% if errors_only %}" in html
    assert 'href="/errors"' in html
    assert 'id="losing"' in html


def test_oracle_accuracy_template_still_has_full_sections():
    html = Path("templates/oracle_accuracy.html").read_text(encoding="utf-8")
    assert "Proof Chain" in html
    assert "Glass Box Challenge" in html
    assert "{% if not errors_only %}" in html
