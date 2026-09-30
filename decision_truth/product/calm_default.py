"""DTS-007 — Calm default with optional Command View density."""

from __future__ import annotations

from typing import Any


def build_calm_default(*, command_view_enabled: bool = False) -> dict[str, Any]:
    """Progressive disclosure: calm default, optional high density."""
    return {
        "default_mode": "calm",
        "default_surface": "six_heroes",
        "progressive_disclosure": True,
        "command_view_enabled": command_view_enabled,
        "command_view_optional": True,
        "command_view_not_default": not command_view_enabled,
        "all_metrics_at_once": False,
        "critical_risk_evidence_accessible": True,
        "critical_states_not_hidden": True,
        "methodology_version": "dts-p5-calm-default-1.0",
    }
