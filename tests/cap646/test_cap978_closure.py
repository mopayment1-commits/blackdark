"""CAP978 — 978-capability institutional closure tests."""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_cap978_catalog_total():
    from cap978.catalog import load_catalog

    rows = load_catalog()
    assert len(rows) == 978
    assert rows[0]["id"] == 1
    assert rows[-1]["id"] == 978
    assert rows[646]["id"] == 647
    assert rows[646]["scope"] == "extension_647_978"


@pytest.mark.asyncio
async def test_cap978_extension_sample(tmp_path, monkeypatch):
    import config
    import database

    monkeypatch.setattr(config, "DB_PATH", str(tmp_path / "cap978.db"))
    monkeypatch.setenv("SERVICE_BUS_LOCAL", "true")
    await database.init_db()

    from cap978.verify import verify_functional_978

    for cid in (647, 700, 750, 800, 850, 900, 978):
        report = await verify_functional_978(cid)
        assert report["verdict"] in {"VERIFIED_COMPLETE", "EXTERNAL_BLOCKED", "CANONICALLY_COVERED"}, report


@pytest.mark.asyncio
async def test_cap978_full_closure(tmp_path, monkeypatch):
    import config
    import database

    monkeypatch.setattr(config, "DB_PATH", str(tmp_path / "cap978_full.db"))
    monkeypatch.setenv("SERVICE_BUS_LOCAL", "true")
    await database.init_db()

    from cap978.closure import institutional_closure_978

    report = await institutional_closure_978()
    assert report["total"] == 978
    assert report["cap978"]["FUNCTIONALLY_INCOMPLETE"] == 0
    assert report["cap978"]["INTERNAL_PARTIAL"] == 0
    assert report["cap978"]["INTERNAL_NOT_IMPLEMENTED"] == 0
    assert report["data_platform_chain"]["verdict"] == "VERIFIED_COMPLETE"
    assert report["governing_controls"]["internal_closure"] is True
