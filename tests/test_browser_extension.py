"""Sanity checks for H1 browser extension package."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "browser_extension"


def test_extension_manifest_and_files():
    manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["manifest_version"] == 3
    assert "content_scripts" in manifest
    assert (ROOT / "src" / "popup.html").is_file()
    assert (ROOT / "src" / "content.js").is_file()
    assert (ROOT / "src" / "background.js").is_file()
    assert (ROOT / "src" / "api.js").is_file()
    assert (ROOT / "icons" / "icon128.png").is_file()
    api = (ROOT / "src" / "api.js").read_text(encoding="utf-8")
    assert "blackdark-production.up.railway.app" in api
    assert "ORACLE_LOOKUP" in (ROOT / "src" / "background.js").read_text(encoding="utf-8")
