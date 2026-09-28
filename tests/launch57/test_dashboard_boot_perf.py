"""Dashboard boot perceived-performance guards — single command-home, skeleton, deferred work."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DASHBOARD = ROOT / "templates" / "dashboard.html"


def _boot_block() -> str:
    dash = DASHBOARD.read_text(encoding="utf-8")
    return dash.split("function boot()", 1)[1].split("if (document.readyState", 1)[0]


def test_boot_calls_command_home_once():
    dash = DASHBOARD.read_text(encoding="utf-8")
    sched = dash.split("function scheduleCommandHome()", 1)[1].split("function boot()", 1)[0]
    assert sched.count("loadCommandHome(true)") == 1
    boot = _boot_block()
    assert "scheduleCommandHome()" in boot


def test_load_command_home_dedupes_inflight():
    dash = DASHBOARD.read_text(encoding="utf-8")
    assert "commandHomeInflight" in dash
    block = dash.split("async function loadCommandHome(force)", 1)[1].split("function renderLaunch57Decision", 1)[0]
    assert "commandHomeInflight && commandHomeInflightKey" in block


def test_trust_pulse_skeleton_while_loading():
    dash = DASHBOARD.read_text(encoding="utf-8")
    assert 'id="trust-pulse" class="tp-loading"' in dash
    assert "setTrustPulseLoading" in dash
    sched = DASHBOARD.read_text(encoding="utf-8").split("function scheduleCommandHome()", 1)[1].split("function boot()", 1)[0]
    assert "requestAnimationFrame" in sched


def test_boot_does_not_block_on_command_home_before_paint():
    boot = _boot_block()
    assert "loadCommandHome(true)" not in boot
    assert "scheduleCommandHome()" in boot


def test_secondary_boot_work_deferred():
    boot = _boot_block()
    assert "runDeferredBoot" in boot
    assert "requestIdleCallback" in boot
    assert "initChart()" not in boot
    deferred = DASHBOARD.read_text(encoding="utf-8").split("function runDeferredBoot()", 1)[1].split("function boot()", 1)[0]
    assert "initChart()" in deferred
    assert "loadMarket()" in deferred
