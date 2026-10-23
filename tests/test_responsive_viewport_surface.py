"""Public surface responsive baseline — viewport meta, touch targets, no overflow traps."""

from __future__ import annotations

import re

import pytest

VIEWPORT_RE = re.compile(
    r'<meta[^>]+name=["\']viewport["\'][^>]+content=["\'][^"\']*width=device-width[^"\']*["\']',
    re.I,
)
VIEWPORT_FIT_RE = re.compile(r"viewport-fit=cover", re.I)

PUBLIC_PAGES = (
    "/",
    "/login",
    "/pricing",
    "/oracle-accuracy",
    "/platform",
    "/terms",
)


@pytest.fixture()
def client():
    from starlette.testclient import TestClient

    from dashboard import app

    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client


@pytest.mark.parametrize("path", PUBLIC_PAGES)
def test_viewport_meta_device_width(client, path: str):
    res = client.get(path, headers={"Accept": "text/html"})
    assert res.status_code == 200, path
    html = res.text
    assert VIEWPORT_RE.search(html), f"missing width=device-width viewport on {path}"


def test_landing_viewport_fit_cover_for_ios_notch(client):
    res = client.get("/", headers={"Accept": "text/html"})
    assert res.status_code == 200
    assert VIEWPORT_FIT_RE.search(res.text)


def test_trust_os_responsive_baseline_css_linked(client):
    res = client.get("/static/css/trust-os.css")
    assert res.status_code == 200
    css = res.text
    assert "overflow-x: clip" in css or "overflow-x:hidden" in css.replace(" ", "")
    assert "100dvh" in css
    assert "safe-area-inset" in css
    assert "min-height: 44px" in css


def test_landing_mobile_nav_touch_targets_in_css(client):
    res = client.get("/static/css/landing.css")
    assert res.status_code == 200
    assert "max-width: 768px" in res.text
    assert "min-height: 44px" in res.text
    assert "safe-area-inset" in res.text
