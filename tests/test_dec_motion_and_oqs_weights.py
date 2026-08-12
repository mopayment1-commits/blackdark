"""DEC-0025 motions + DEC-0309 OQS weight verification."""

from __future__ import annotations

from pathlib import Path

import weight_aggregator


ROOT = Path(__file__).resolve().parents[1]


def test_design_system_defines_exactly_three_motions():
    css = (ROOT / "static" / "css" / "trust-os.css").read_text(encoding="utf-8")
    for name in ("pulseIn", "flipFlash", "sharePop"):
        assert name in css
    for keyframe in ("bdPulseIn", "bdFlipFlash", "bdSharePop"):
        assert f"@keyframes {keyframe}" in css
    assert "pulseIn · flipFlash · sharePop" in css


def test_dashboard_uses_pulse_motion_not_motion_soup():
    dash = (ROOT / "templates" / "dashboard.html").read_text(encoding="utf-8")
    assert "pulseIn" in dash
    # Reject generic AI motion spam keywords as brand animations
    assert "animate-bounce" not in dash
    assert "animate-ping" not in dash


def test_oqs_weights_are_40_35_25():
    weights = weight_aggregator._CORE_WEIGHTS
    assert abs(float(weights["profit"]) - 0.40) < 1e-9
    assert abs(float(weights["liquidity"]) - 0.35) < 1e-9
    assert abs(float(weights["stability"]) - 0.25) < 1e-9
    assert abs(sum(float(v) for v in weights.values()) - 1.0) < 1e-9
    # Public accessor mirrors core defaults when nothing is persisted.
    public = weight_aggregator.get_core_score_weights()
    assert public == weights


def test_oqs_score_independent_expected_value():
    """Independent recomputation of weighted OQS components."""
    components = {"profit": 80.0, "liquidity": 60.0, "stability": 40.0}
    # Map keys to aggregator schema
    raw = {
        "profit": components["profit"],
        "liquidity": components["liquidity"],
        "stability": components["stability"],
    }
    expected = 80 * 0.40 + 60 * 0.35 + 40 * 0.25
    w = weight_aggregator.get_core_score_weights()
    got = sum(float(raw[k]) * float(w[k]) for k in w)
    assert abs(got - expected) < 1e-6
