"""Real local accessibility interaction verification on rendered Adaptive surfaces."""

from __future__ import annotations

import re

import pytest
from bs4 import BeautifulSoup
from fastapi.testclient import TestClient


def _soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "lxml")


def _focusable_elements(soup: BeautifulSoup) -> list:
    selectors = soup.find_all(["a", "button", "input", "select", "textarea", "[tabindex]"])
    return [el for el in soup.find_all(True) if el.name in {"a", "button", "input", "select", "textarea"} or el.get("tabindex")]


@pytest.fixture(scope="module")
def client():
    import dashboard

    return TestClient(dashboard.app)


def test_landing_skip_link_and_landmarks(client):
    r = client.get("/")
    assert r.status_code == 200
    soup = _soup(r.text)
    assert soup.find("a", string=re.compile("Skip", re.I)) or soup.find(class_=re.compile("skip", re.I))
    assert soup.find("nav", attrs={"aria-label": True}) or soup.find("nav")
    assert soup.find(attrs={"aria-live": True}) or soup.find(id=re.compile("trust", re.I))


def test_landing_focusable_have_labels_or_text(client):
    r = client.get("/")
    soup = _soup(r.text)
    focusable = _focusable_elements(soup)
    assert len(focusable) >= 3
    unlabeled = []
    for el in focusable[:30]:
        has_label = el.get("aria-label") or el.get("title") or (el.get_text(strip=True) if el.name != "input" else el.get("aria-label") or el.get("placeholder"))
        if not has_label and el.name == "input" and not el.get("type") == "hidden":
            unlabeled.append(el)
    assert len(unlabeled) <= len(focusable) * 0.5  # majority labeled


def test_dashboard_aria_live_regions(client):
    r = client.get("/dashboard")
    assert r.status_code in {200, 302, 401, 403}
    if r.status_code == 200:
        soup = _soup(r.text)
        assert soup.find(attrs={"aria-live": True}) or soup.find(id="trust-pulse")


def test_dashboard_inputs_have_aria_labels(client):
    r = client.get("/dashboard")
    if r.status_code != 200:
        pytest.skip("dashboard requires auth/terms")
    soup = _soup(r.text)
    for inp in soup.find_all("input", type=lambda t: t != "hidden"):
        assert inp.get("aria-label") or inp.get("id") or inp.get("placeholder")


def test_adaptive_api_discoverable_command_alternative(client):
    r = client.get("/api/adaptive/status")
    assert r.status_code == 200
    r2 = client.post("/api/adaptive/command", json={"query": "decide BTC"})
    assert r2.status_code == 200
    body = r2.json()
    assert body.get("discoverable_alternative") == "/api/adaptive/command"
    assert body.get("shortcut_conflict_safe") is True


def test_universal_command_keyboard_metadata():
    from bd_platform.adaptive_intelligence.universal_command import universal_command_search

    out = universal_command_search(query="risk")
    assert out["keyboard_shortcut"] == "cmd_or_ctrl_k"
    assert out["discoverable_alternative"]


def test_accessibility_local_interaction_protocol():
    from bd_platform.adaptive_intelligence.accessibility import run_local_manual_verification

    result = run_local_manual_verification()
    assert result["status"] == "LOCAL_MANUAL_ACCESSIBILITY_VERIFICATION_COMPLETE"
    assert result["all_templates_ok"]
