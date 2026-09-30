"""Shared helpers for Launch-57 governing-spec closure engines (*_spec_common.py)."""

from __future__ import annotations

import subprocess
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any


def git_sha(repo_root: Path, short: bool = True) -> str:
    try:
        flag = ["--short"] if short else []
        return subprocess.check_output(
            ["git", "rev-parse", *flag, "HEAD"], cwd=repo_root, text=True
        ).strip()
    except Exception:
        return "unknown"


def git_branch(repo_root: Path) -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=repo_root, text=True
        ).strip()
    except Exception:
        return "unknown"


def resolve_spec_path(candidates: Sequence[Path]) -> Path | None:
    for path in candidates:
        if path.exists():
            return path
    return None


def http_client():
    from starlette.testclient import TestClient

    from dashboard import app

    return TestClient(app, raise_server_exceptions=False)


def build_runtime_truth_table(
    requirements_register: Callable[[], list[dict[str, Any]]],
    probe_by_req: Mapping[str, Callable[[], tuple[Any, str]]],
    truth_status_cls: Any,
) -> list[dict[str, Any]]:
    rows = []
    for req in requirements_register():
        rid = req["req_id"]
        probe = probe_by_req.get(rid)
        if probe:
            status, evidence = probe()
        else:
            status, evidence = truth_status_cls.PARTIAL, "no automated probe"
        rows.append(
            {
                "req_id": rid,
                "title": req["title"],
                "spec_section": req["spec_section"],
                "status": status.value,
                "evidence": evidence,
                "owner_modules": req["owner_modules"],
                "tests": req["tests"],
            }
        )
    return rows


def run_targeted_pytest(repo_root: Path, pytest_args: Sequence[str]) -> dict[str, Any]:
    cmd = ["python3", "-m", "pytest", *pytest_args, "-q", "--tb=no"]
    proc = subprocess.run(cmd, cwd=repo_root, capture_output=True, text=True)
    tail = (proc.stdout or "") + (proc.stderr or "")
    passed_line = [ln for ln in tail.splitlines() if "passed" in ln]
    return {
        "command": " ".join(cmd),
        "exit_code": proc.returncode,
        "passed": proc.returncode == 0,
        "summary": passed_line[-1] if passed_line else tail[-400:],
    }


def probe_launch_scope_parked_pair(
    verify_scope: Callable[[int], dict[str, Any]],
    truth_status_cls: Any,
    *,
    success_evidence: str = "parked rejected",
) -> tuple[Any, str]:
    for probe_id, want_in_scope in ((25, True), (999, False)):
        parked = verify_scope(probe_id)
        if parked["launch_item_id"] != probe_id or parked["in_launch57_scope"] != want_in_scope:
            return truth_status_cls.NO, str(parked)
        if not want_in_scope and not parked["parked_contamination"]:
            return truth_status_cls.NO, str(parked)
    return truth_status_cls.YES, success_evidence
