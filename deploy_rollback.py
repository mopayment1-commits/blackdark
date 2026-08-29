"""
BLACKDARK — Deploy rollback automation (record + revert last deploy marker).
"""

from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path
from typing import Any

import config

_HISTORY = config.DATA_DIR / "deploy_history.jsonl"
_ROLLBACK_STATE = config.DATA_DIR / "deploy_rollback_state.json"


def _git_head() -> str:
    try:
        return (
            subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=config.ROOT_DIR, text=True)
            .strip()
        )
    except Exception:
        return "unknown"


def record_deploy(*, environment: str, notes: str = "", operator: str = "system") -> dict[str, Any]:
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": time.time(),
        "commit": _git_head(),
        "environment": environment,
        "notes": notes,
        "operator": operator,
    }
    with _HISTORY.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry) + "\n")
    return entry


def latest_deploy() -> dict[str, Any] | None:
    if not _HISTORY.exists():
        return None
    lines = [ln for ln in _HISTORY.read_text(encoding="utf-8").splitlines() if ln.strip()]
    if not lines:
        return None
    return json.loads(lines[-1])


def initiate_rollback(*, reason: str, operator: str = "system") -> dict[str, Any]:
    """Mark rollback requested; ops must checkout previous commit on host."""
    latest = latest_deploy()
    if not latest:
        return {"success": False, "reason": "no_deploy_history"}
    state = {
        "requested_at": time.time(),
        "reason": reason,
        "operator": operator,
        "rollback_from_commit": latest.get("commit"),
        "status": "pending_checkout",
        "instructions": [
            "git fetch origin",
            "git checkout <previous-good-commit>",
            "restart services / redeploy Railway",
        ],
    }
    _ROLLBACK_STATE.write_text(json.dumps(state, indent=2), encoding="utf-8")
    record_deploy(environment="rollback", notes=reason, operator=operator)
    return {"success": True, **state}


def rollback_status() -> dict[str, Any]:
    if not _ROLLBACK_STATE.exists():
        return {"status": "idle"}
    return json.loads(_ROLLBACK_STATE.read_text(encoding="utf-8"))
