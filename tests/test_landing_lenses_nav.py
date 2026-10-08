"""Landing removes feature-division block; nav exposes /lenses menu."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_landing_has_no_feature_division_section():
    from dashboard import app

    html = TestClient(app).get("/").text
    main = html.split('<main id="main"', 1)[1].split("</main>", 1)[0]
    assert 'aria-label="Feature division"' not in main
    assert 'id="lenses"' not in main
    assert "lenses.prove.body" not in main
    assert "Verify on Ledger" in html
    assert "Free Proof" in html or "data-lp-proof-open" in html


def test_nav_open_lenses_and_util_links():
    from dashboard import app

    html = TestClient(app).get("/").text
    assert 'href="/lenses"' in html
    assert 'id="bdUtilSignup"' in html
    assert 'id="bdUtilPricing"' in html


def test_lenses_page_is_name_list_only():
    from dashboard import app

    page = TestClient(app).get("/lenses")
    assert page.status_code == 200
    ul = page.text.split('<ul aria-label="Trust OS lenses">', 1)[1].split("</ul>", 1)[0]
    assert ul.count("<li>") == 4
    assert "Prove" in ul and "Operate" in ul and "Desk" in ul and "Room" in ul
    assert "command-home" not in ul
    assert "Ledger 0%" not in ul
    assert "$" not in ul
    assert 'href="/dashboard?lens=prove"' in ul
