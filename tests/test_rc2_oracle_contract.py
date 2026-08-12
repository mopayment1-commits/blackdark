"""RC2 oracle authority contract (F-ARC-01)."""

from pathlib import Path


def test_oracle_unified_is_documented_canonical():
    arch = Path("ARCHITECTURE.md").read_text(encoding="utf-8")
    assert "oracle_unified.py" in arch
    assert "Canonical" in arch or "canonical" in arch
    assert "ai_oracle.py" in arch


def test_dashboard_imports_unified_oracle():
    src = Path("dashboard.py").read_text(encoding="utf-8")
    assert "oracle_unified" in src or "compute_unified_oracle" in src


def test_ai_oracle_wraps_unified_helpers():
    src = Path("ai_oracle.py").read_text(encoding="utf-8")
    assert "oracle_unified" in src or "apply_unified" in src or "finalize_unified" in src
