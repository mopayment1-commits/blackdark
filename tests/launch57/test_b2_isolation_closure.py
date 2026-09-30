"""Launch-57 B2 isolation closure — zero legacy runtime deps."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

PROHIBITED = {
    "failure.freshness",
    "cap646.evidence_class",
    "cap646.dedicated_common",
    "cap646.data_spine",
    "data_governance.freshness",
    "hot_storage",
    "oracle_track_record",
}

B2_FILES = [
    Path("launch57/data_batch2.py"),
    Path("launch57/batch2_isolation.py"),
    Path("launch57/provenance_common.py"),
    Path("launch57/freshness_common.py"),
    Path("launch57/point_in_time_common.py"),
]


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    mods: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            mods.add(node.module)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                mods.add(alias.name)
    return mods


def test_b2_zero_prohibited_imports():
    leaked: list[str] = []
    for path in B2_FILES:
        mods = _imports(path)
        for mod in mods:
            if any(mod == p or mod.startswith(p + ".") for p in PROHIBITED):
                leaked.append(f"{path}:{mod}")
    assert leaked == []


@pytest.mark.asyncio
async def test_freshness_owner_is_launch57_local():
    from launch57.data_batch2 import freshness_update_assurance

    out = await freshness_update_assurance(symbol="BTC", params={"quote_age_ms": 30_000.0})
    assert out["freshness_owner"] == "launch57.freshness_common"
    assert out["legacy_runtime_dependencies"] == 0
    assert out["b2_isolation_leakage"] == 0
