"""Free human-ops playbook artifacts (no paid services)."""

from __future__ import annotations

from pathlib import Path


def test_free_human_ops_artifacts():
    assert Path("docs/FREE_HUMAN_OPS_PLAYBOOK_AR.md").is_file()
    assert Path("scripts/bootstrap_free_human_ops.py").is_file()
    deferred = Path("docs/DEFERRED_HUMAN_STEPS.md").read_text(encoding="utf-8")
    assert "FREE_HUMAN_OPS_PLAYBOOK_AR.md" in deferred
    assert "bootstrap_free_human_ops.py" in deferred


def test_bootstrap_script_dry_structure():
    src = Path("scripts/bootstrap_free_human_ops.py").read_text(encoding="utf-8")
    assert "SOFT_LAUNCH" in src
    assert "ADMIN_TOTP_SECRET" in src
    assert "secrets_printed" in src
    assert "EXPOSE_B2B_DEMO_KEY" in src
