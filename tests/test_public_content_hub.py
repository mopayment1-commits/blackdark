"""Tests — Public Content Hub (#177 + #182)."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from bd_platform import chart_sharing_service as css
from bd_platform import public_content_hub as pch


@pytest.fixture
def isolated_store(tmp_path, monkeypatch):
    store = tmp_path / "public_content_hub.json"
    monkeypatch.setattr(pch, "_STORE_PATH", store)
    monkeypatch.setattr("bd_platform.chart_sharing_service._STORE_PATH", store, raising=False)
    return store


def test_hub_status():
    status = pch.public_content_hub_status()
    assert status["ok"] is True
    assert 177 in status["feature_ids"]
    assert 182 in status["feature_ids"]
    assert status["public_editing"] is False
    assert "clone" in status["public_actions"]


def test_create_publish_immutable_chart(isolated_store):
    created = pch.create_content(
        owner_id="user-1",
        title="BTC breakout",
        content_type="chart",
        content_data={"symbol": "BTC", "levels": [100000, 105000]},
    )
    item_id = created["content"]["id"]
    published = pch.publish_content(item_id=item_id, owner_id="user-1", privacy="public")
    assert published["ok"] is True
    assert published["version"] == 1
    slug = published["content"]["public_slug"]
    assert published["content"]["watermark"]["text"] == "Powered by BLACKDARK"

    pch.update_content_draft(
        item_id=item_id,
        owner_id="user-1",
        content_data={"symbol": "BTC", "levels": [1, 2]},
        title="EDITED",
    )
    public = pch.get_public_view(slug)
    assert public["ok"] is True
    assert public["snapshot"]["content_data"]["levels"] == [100000, 105000]
    assert public["immutable"] is True


def test_dashboard_snapshot_publish(isolated_store):
    created = pch.create_content(
        owner_id="user-2",
        title="My Radar",
        content_type="dashboard",
        content_data={"dashboard": {"focus_asset": "ETH", "headline": "test"}},
        dashboard_metadata={"focus_asset": "ETH", "surface": "market_radar_dashboard"},
    )
    item_id = created["content"]["id"]
    published = pch.publish_content(item_id=item_id, owner_id="user-2", privacy="unlisted")
    slug = published["content"]["public_slug"]
    assert published["content"]["public_url"] == f"/share/dashboard/{slug}"

    public = pch.get_public_view(slug)
    assert public["ok"] is True
    assert public["content_type"] == "dashboard"
    assert public["permissions"]["public_editing"] is False


def test_private_content_blocked(isolated_store):
    created = pch.create_content(owner_id="user-3", title="Secret", privacy="private")
    item_id = created["content"]["id"]
    published = pch.publish_content(item_id=item_id, owner_id="user-3", privacy="private")
    slug = published["content"]["public_slug"]
    public = pch.get_public_view(slug)
    assert public["ok"] is False
    assert public["error"] == "private_content"


def test_clone_creates_private_draft(isolated_store):
    created = pch.create_content(
        owner_id="owner-a",
        title="Original",
        content_data={"x": 1},
    )
    item_id = created["content"]["id"]
    pch.publish_content(item_id=item_id, owner_id="owner-a", privacy="public")
    cloned = pch.clone_content(item_id=item_id, owner_id="user-b")
    assert cloned["ok"] is True
    assert cloned["content"]["privacy"] == "private"
    assert cloned["cloned_from"] == item_id
    listed = pch.list_user_content("user-b")
    assert listed["count"] == 1


def test_republish_increments_version(isolated_store):
    created = pch.create_content(owner_id="u", title="V test", content_data={"n": 1})
    item_id = created["content"]["id"]
    v1 = pch.publish_content(item_id=item_id, owner_id="u", privacy="public")
    pch.update_content_draft(item_id=item_id, owner_id="u", content_data={"n": 2})
    v2 = pch.publish_content(item_id=item_id, owner_id="u", privacy="public")
    assert v1["version"] == 1
    assert v2["version"] == 2
    slug = v2["content"]["public_slug"]
    public = pch.get_public_view(slug)
    assert public["version"] == 2
    assert public["snapshot"]["content_data"]["n"] == 2


def test_chart_sharing_compat_layer(isolated_store):
    created = css.create_chart_share(
        owner_id="c1",
        title="Idea",
        chart_data={"symbol": "SOL"},
    )
    share_id = created["share"]["id"]
    published = css.publish_chart_share(share_id=share_id, owner_id="c1", privacy="unlisted")
    slug = published["share"]["public_slug"]
    public = css.get_public_chart_view(slug)
    assert public["ok"] is True
    assert public["feature_id"] == 177


@pytest.mark.asyncio
async def test_capture_dashboard_snapshot(isolated_store, monkeypatch):
    monkeypatch.setattr(
        "bd_platform.market_radar_dashboard.build_market_radar_dashboard",
        AsyncMock(return_value={"ok": True, "focus_asset": "BTC", "feature_ids": [155]}),
    )
    result = await pch.capture_dashboard_snapshot(
        owner_id="dash-user",
        title="Radar BTC",
        asset="BTC",
    )
    assert result["ok"] is True
    assert result["content"]["content_type"] == "dashboard"


def test_access_denied_wrong_owner(isolated_store):
    created = pch.create_content(owner_id="owner", title="Mine")
    item_id = created["content"]["id"]
    denied = pch.publish_content(item_id=item_id, owner_id="other", privacy="public")
    assert denied["ok"] is False
    assert denied["error"] == "access_denied"
