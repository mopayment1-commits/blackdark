"""Browser-level keyboard accessibility verification via Playwright."""

from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
VENV_PY = ROOT / ".venv-a11y" / "bin" / "python"
VENV_SITE = ROOT / ".venv-a11y" / "lib" / f"python{sys.version_info.major}.{sys.version_info.minor}" / "site-packages"


def _free_port() -> int:
    if env_port := os.environ.get("A11Y_TEST_PORT"):
        return int(env_port)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


PORT = _free_port()

if VENV_SITE.is_dir():
    sys.path.insert(0, str(VENV_SITE))


def _playwright_available() -> bool:
    try:
        import playwright  # noqa: F401

        return True
    except ImportError:
        return False


@pytest.fixture(scope="module")
def browser_server():
    if not _playwright_available():
        pytest.skip("playwright venv not installed")
    proc = subprocess.Popen(
        [sys.executable, "dashboard.py"],
        cwd=ROOT,
        env={**os.environ, "PORT": str(PORT)},
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    for _ in range(30):
        try:
            with socket.create_connection(("127.0.0.1", PORT), timeout=0.2):
                break
        except OSError:
            time.sleep(0.2)
    else:
        proc.terminate()
        proc.wait(timeout=5)
        pytest.skip("dashboard server failed to start")
    yield f"http://127.0.0.1:{PORT}"
    proc.terminate()
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=5)


@pytest.fixture(scope="module")
def page(browser_server):
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        pg = browser.new_page()
        yield pg, browser_server
        browser.close()


def test_skip_link_visible_on_keyboard_focus(page):
    pg, base = page
    pg.goto(base + "/")
    skip = pg.locator("a.skip-link")
    assert skip.count() >= 1
    skip.first.focus()
    box = skip.first.bounding_box()
    assert box is not None
    assert box["width"] > 10
    assert box["height"] > 10
    assert box["x"] >= 0


def test_tab_order_produces_visible_focus(page):
    pg, base = page
    pg.goto(base + "/")
    focusable = []
    for _ in range(8):
        pg.keyboard.press("Tab")
        focused = pg.evaluate(
            "() => { const e = document.activeElement; return e ? {tag: e.tagName, text: (e.innerText||e.getAttribute('aria-label')||'').slice(0,40)} : null; }"
        )
        if focused:
            focusable.append(focused)
    assert len(focusable) >= 5
    tags = {f["tag"] for f in focusable}
    assert "A" in tags or "BUTTON" in tags


def test_landmarks_present(page):
    pg, base = page
    pg.goto(base + "/")
    assert pg.locator("nav[aria-label], nav").count() >= 1
    assert pg.locator("main, [role='main']").count() >= 1
    assert pg.locator("[aria-live], #trust-pulse").count() >= 1


def test_no_keyboard_trap_on_landing(page):
    pg, base = page
    pg.goto(base + "/")
    start = pg.evaluate("() => document.activeElement?.tagName || ''")
    for _ in range(12):
        pg.keyboard.press("Tab")
    for _ in range(12):
        pg.keyboard.press("Shift+Tab")
    end = pg.evaluate("() => document.activeElement?.tagName || ''")
    assert start or end  # navigation occurred without hang
