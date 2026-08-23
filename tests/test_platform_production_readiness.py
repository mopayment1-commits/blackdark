"""Platform production readiness tests."""

from __future__ import annotations


def test_platform_production_readiness_surface():
    from platform_production_readiness import platform_production_readiness

    report = platform_production_readiness()
    assert report["surface"] == "platform_production_readiness"
    assert report["verdict"] in {"PRODUCTION_READY_FOR_USERS", "NOT_READY"}
    assert "user_journeys" in report
    assert report["user_journeys"]["anonymous_oracle"]["status"] == "PASS"
    assert report["user_journeys"]["paid_upgrade"]["status"] == "EXTERNAL DEPENDENCY"


def test_closure_status_uses_rvm_snapshot():
    import asyncio

    from cap646.closure import get_closure_status

    status = asyncio.run(get_closure_status(full_scan=False))
    assert status.get("source") == "rvm_snapshot"
    assert status.get("total", 0) > 0
