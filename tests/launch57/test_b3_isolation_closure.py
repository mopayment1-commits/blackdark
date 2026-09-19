"""Launch-57 B3 isolation closure — zero legacy evidence-class runtime deps."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

PROHIBITED = {
    "cap646.evidence_class",
    "decision_truth.evidence_taxonomy",
}

B3_FILES = [
    Path("launch57/evidence_class_common.py"),
    Path("launch57/batch3_isolation.py"),
    Path("launch57/b3_evidence_bridge.py"),
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


def test_b3_zero_prohibited_imports():
    leaked: list[str] = []
    for path in B3_FILES:
        mods = _imports(path)
        for mod in mods:
            if any(mod == p or mod.startswith(p + ".") for p in PROHIBITED):
                leaked.append(f"{path}:{mod}")
    assert leaked == []


def test_b3_bridge_activated_pending_verification():
    from launch57.b3_evidence_bridge import (
        B3_EVIDENCE_RECONCILIATION_ACTIVATED,
        b3_evidence_reconciliation_state,
    )

    assert B3_EVIDENCE_RECONCILIATION_ACTIVATED is True
    state = b3_evidence_reconciliation_state()
    assert state["status"] == "PENDING_VERIFICATION"
    assert state["binding_status"] == "ACTIVATED_BOUND_TO_LAUNCH57_6"


def test_b3_bridge_inert_when_deactivated():
    from launch57 import b3_evidence_bridge as bridge

    original = bridge.B3_EVIDENCE_RECONCILIATION_ACTIVATED
    bridge.B3_EVIDENCE_RECONCILIATION_ACTIVATED = False
    try:
        out = bridge.apply_b3_evidence_reconciliation({"success": True})
        assert any(p.get("launch_number") == 6 for p in out.get("temporal_dependency_pending", []))
        assert "evidence_display" not in out
    finally:
        bridge.B3_EVIDENCE_RECONCILIATION_ACTIVATED = original
