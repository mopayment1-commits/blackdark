"""Tests — Chart / Idea Sharing (#177)."""

from __future__ import annotations

import pytest

from bd_platform.chart_sharing_service import (
    create_chart_share,
    get_public_chart_view,
    list_user_chart_shares,
    publish_chart_share,
    update_chart_share,
)


@pytest.fixture
def isolated_store(tmp_path, monkeypatch):
    store = tmp_path / "chart_shares.json"
    monkeypatch.setattr("bd_platform.chart_sharing_service._STORE_PATH", store)
    return store


def test_create_and_list_share(isolated_store):
    created = create_chart_share(
        owner_id="user-1",
        title="BTC breakout idea",
        chart_data={"symbol": "BTC", "levels": [100000, 105000]},
        notes="Watch resistance",
    )
    assert created["ok"] is True
    share_id = created["share"]["id"]

    listed = list_user_chart_shares("user-1")
    assert listed["count"] == 1
    assert listed["shares"][0]["id"] == share_id
    assert listed["shares"][0]["privacy"] == "private"


def test_publish_immutable_snapshot(isolated_store):
    created = create_chart_share(
        owner_id="user-2",
        title="ETH chart",
        chart_data={"symbol": "ETH", "price": 3000},
    )
    share_id = created["share"]["id"]
    published = publish_chart_share(share_id=share_id, owner_id="user-2", privacy="public")
    assert published["ok"] is True
    slug = published["share"]["public_slug"]
    assert published["share"]["watermark"]["text"] == "Powered by BLACKDARK"

    # Edit original — published snapshot must not change
    update_chart_share(
        share_id=share_id,
        owner_id="user-2",
        chart_data={"symbol": "ETH", "price": 9999},
        title="ETH chart EDITED",
    )
    public = get_public_chart_view(slug)
    assert public["ok"] is True
    assert public["snapshot"]["chart_data"]["price"] == 3000
    assert public["immutable"] is True
    assert public["watermark"]["signup_url"]


def test_private_share_not_public(isolated_store):
    created = create_chart_share(owner_id="user-3", title="Secret", privacy="private")
    share_id = created["share"]["id"]
    published = publish_chart_share(share_id=share_id, owner_id="user-3", privacy="private")
    slug = published["share"]["public_slug"]
    public = get_public_chart_view(slug)
    assert public["ok"] is False
    assert public["error"] == "private_share"


def test_unlisted_public_view(isolated_store):
    created = create_chart_share(owner_id="user-4", title="Unlisted chart", chart_data={"x": 1})
    share_id = created["share"]["id"]
    published = publish_chart_share(share_id=share_id, owner_id="user-4", privacy="unlisted")
    slug = published["share"]["public_slug"]
    public = get_public_chart_view(slug)
    assert public["ok"] is True
    assert public["privacy"] == "unlisted"


def test_access_denied_wrong_owner(isolated_store):
    created = create_chart_share(owner_id="owner-a", title="Mine")
    share_id = created["share"]["id"]
    denied = publish_chart_share(share_id=share_id, owner_id="owner-b", privacy="public")
    assert denied["ok"] is False
    assert denied["error"] == "access_denied"
