"""Open Graph / Twitter Card social preview metadata on public pages."""

from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("SOFT_LAUNCH", "1")

from fastapi.testclient import TestClient

from dashboard import app

client = TestClient(app)
OG_IMAGE = "/static/img/blackdark-og-social-1200x630.jpg"
ROOT = Path(__file__).resolve().parent.parent
OG_PATH = ROOT / "static" / "img" / "blackdark-og-social-1200x630.jpg"


def test_og_image_file_is_1200x630():
    assert OG_PATH.is_file()
    out = os.popen(f"identify -format '%w %h' {OG_PATH}").read().strip()
    w, h = out.split()
    assert w == "1200" and h == "630"


def _assert_social_meta(html: str) -> None:
    assert 'property="og:site_name" content="BLACKDARK"' in html
    assert f'property="og:image" content="{OG_IMAGE}"' in html
    assert f'name="twitter:image" content="{OG_IMAGE}"' in html
    assert 'name="twitter:card" content="summary_large_image"' in html


def test_landing_social_meta():
    html = client.get("/").text
    assert 'property="og:title"' in html
    _assert_social_meta(html)


def test_oracle_accuracy_social_meta():
    html = client.get("/oracle-accuracy").text
    assert 'property="og:title"' in html
    _assert_social_meta(html)
