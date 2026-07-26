"""HaasCloud-style multi-service deploy manifest loader."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

MANIFEST_PATH = Path(__file__).resolve().parent.parent / "haascloud.json"


def load_manifest() -> dict[str, Any]:
    if MANIFEST_PATH.exists():
        return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    return {"name": "BLACKDARK Cloud", "services": [], "deploy": {}}


def deploy_summary() -> dict[str, Any]:
    m = load_manifest()
    return {
        "name": m.get("name"),
        "version": m.get("version"),
        "services_count": len(m.get("services") or []),
        "infrastructure": m.get("infrastructure"),
        "deploy": m.get("deploy"),
        "manifest_path": str(MANIFEST_PATH),
    }
