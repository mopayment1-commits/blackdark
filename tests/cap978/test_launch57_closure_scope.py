"""Launch-57 accountable closure scope vs parked extension 647–978."""

from __future__ import annotations

import pytest


def test_launch57_launch_items_are_1_through_57():
    from cap978.launch57_closure_scope import launch57_launch_item_ids

    assert launch57_launch_item_ids() == frozenset(range(1, 58))


def test_extension_parked_excludes_launch57_bound_916():
    from cap978.launch57_closure_scope import is_extension_parked_outside_launch57

    assert is_extension_parked_outside_launch57(647) is True
    assert is_extension_parked_outside_launch57(916) is False


@pytest.mark.asyncio
async def test_closure_reports_dual_verdicts(tmp_path, monkeypatch):
    import config
    import database

    monkeypatch.setattr(config, "DB_PATH", str(tmp_path / "dual.db"))
    monkeypatch.setenv("SERVICE_BUS_LOCAL", "true")
    monkeypatch.setenv("BLACKDARK_CI_DETERMINISTIC_CLOSURE", "true")
    await database.init_db()

    from cap978.closure import institutional_closure_978
    from cap978.gate_verdict import INSTITUTIONAL_GATE_PASS

    closure = await institutional_closure_978(ci_deterministic=True)
    assert closure["launch57_closure_verdict"] == INSTITUTIONAL_GATE_PASS
    assert closure["cap978_full_catalog_verdict"] == INSTITUTIONAL_GATE_PASS
    assert closure["extension_647_978_parked"]["informational_only"] is True
    assert closure["launch57_closure"]["accountable_incomplete_count"] == 0
