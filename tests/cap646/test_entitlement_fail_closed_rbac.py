"""Fail-closed regression tests for cap646 entitlement RBAC evaluation gates."""

from __future__ import annotations

import pytest

from cap646.entitlements import EntitlementEngine


def _elite_entitlements() -> dict:
    return {
        "effective_plan": "elite",
        "entitlement_allowed": True,
        "subscription_status": "active",
        "payment_status": "paid",
    }


@pytest.fixture
def engine() -> EntitlementEngine:
    return EntitlementEngine()


@pytest.fixture
def elite_user() -> dict:
    return {"id": 42, "email": "owner@institutional.test", "tier": "elite"}


@pytest.fixture
def pro_user() -> dict:
    return {"id": 7, "email": "pro@institutional.test", "tier": "pro"}


@pytest.fixture
def patch_entitlement_context(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _subscription(_user):
        return {"status": "active", "entitlements_version": 1}

    async def _resolve(_user_id: int):
        return _elite_entitlements()

    monkeypatch.setattr("cap646.entitlements._subscription_for_user", _subscription)
    monkeypatch.setattr("cap646.entitlements.resolve_entitlements_for_user", _resolve)


class TestExternalCatalogCheckFailClosed:
    """cap646/entitlements.py gate: external_catalog_check (corpus line 74)."""

    @pytest.mark.asyncio
    async def test_authorized_path_succeeds(self, engine, monkeypatch):
        monkeypatch.setattr(
            "cap978.catalog.is_external",
            lambda capability_id: False,
            raising=False,
        )
        result = await engine.check(650, user={"id": 1, "tier": "free"})
        assert result["allowed"] is True

    @pytest.mark.asyncio
    async def test_unauthorized_external_blocked(self, engine, monkeypatch):
        monkeypatch.setattr(
            "cap978.catalog.is_external",
            lambda capability_id: True,
            raising=False,
        )
        result = await engine.check(650, user={"id": 1, "tier": "free"})
        assert result["allowed"] is False
        assert result["reason"] == "external_blocked"

    @pytest.mark.asyncio
    async def test_forced_exception_denied(self, engine, monkeypatch):
        def _boom(_capability_id: int):
            raise RuntimeError("catalog unavailable")

        monkeypatch.setattr("cap978.catalog.is_external", _boom, raising=False)
        result = await engine.check(650, user={"id": 1, "tier": "free"})
        assert result["allowed"] is False
        assert result["reason"] == "authorization_evaluation_failed"
        assert result["gate"] == "external_catalog_check"

    @pytest.mark.asyncio
    async def test_exception_cannot_grant_entitlement(self, engine, monkeypatch):
        calls = {"count": 0}

        def _raise_once(_capability_id: int):
            calls["count"] += 1
            raise RuntimeError("forced")

        monkeypatch.setattr("cap978.catalog.is_external", _raise_once, raising=False)
        result = await engine.check(650, user={"id": 1, "tier": "elite"})
        assert calls["count"] == 1
        assert result["allowed"] is False
        assert result["reason"] != "external_blocked"


class TestOrgRbacPermissionFailClosed:
    """cap646/entitlements.py gate: org_rbac_permission (corpus line 129)."""

    @pytest.mark.asyncio
    async def test_authorized_path_succeeds(
        self, engine, elite_user, patch_entitlement_context, monkeypatch
    ):
        monkeypatch.setattr("org_rbac.has_permission", lambda *_args: True, raising=False)
        result = await engine.check(161, user=elite_user, org_id="org-1")
        assert result["allowed"] is True

    @pytest.mark.asyncio
    async def test_unauthorized_missing_permission(
        self, engine, elite_user, patch_entitlement_context, monkeypatch
    ):
        monkeypatch.setattr("org_rbac.has_permission", lambda *_args: False, raising=False)
        result = await engine.check(161, user=elite_user, org_id="org-1")
        assert result["allowed"] is False
        assert result["reason"] == "missing_org_permission"

    @pytest.mark.asyncio
    async def test_forced_exception_denied(
        self, engine, elite_user, patch_entitlement_context, monkeypatch
    ):
        def _boom(*_args, **_kwargs):
            raise RuntimeError("rbac store unavailable")

        monkeypatch.setattr("org_rbac.has_permission", _boom, raising=False)
        result = await engine.check(161, user=elite_user, org_id="org-1")
        assert result["allowed"] is False
        assert result["reason"] == "authorization_evaluation_failed"
        assert result["gate"] == "org_rbac_permission"

    @pytest.mark.asyncio
    async def test_exception_cannot_grant_entitlement(
        self, engine, elite_user, patch_entitlement_context, monkeypatch
    ):
        def _forced_rbac_error(*_args, **_kwargs):
            raise RuntimeError("forced")

        monkeypatch.setattr("org_rbac.has_permission", _forced_rbac_error, raising=False)
        result = await engine.check(161, user=elite_user, org_id="org-1")
        assert result["allowed"] is False
        assert result["reason"] == "authorization_evaluation_failed"


class TestFeatureAllowedFailClosed:
    """cap646/entitlements.py gate: feature_allowed (corpus line 143)."""

    @pytest.fixture
    def catalog_with_feature(self, monkeypatch: pytest.MonkeyPatch):
        base = __import__("cap646.entitlements", fromlist=["catalog646_by_id"]).catalog646_by_id()

        def _catalog():
            rows = dict(base)
            rows[47] = {**rows.get(47, {}), "id": 47, "feature_key": "journal"}
            return rows

        monkeypatch.setattr("cap646.entitlements.catalog646_by_id", _catalog)

    @pytest.mark.asyncio
    async def test_authorized_path_succeeds(
        self, engine, pro_user, catalog_with_feature, monkeypatch
    ):
        async def _subscription(_user):
            return {"status": "active"}

        async def _resolve(_user_id: int):
            return {"effective_plan": "pro", "entitlement_allowed": True}

        monkeypatch.setattr("cap646.entitlements._subscription_for_user", _subscription)
        monkeypatch.setattr("cap646.entitlements.resolve_entitlements_for_user", _resolve)
        monkeypatch.setattr("auth_service.feature_allowed", lambda _user, _feature: True, raising=False)
        result = await engine.check(47, user=pro_user)
        assert result["allowed"] is True

    @pytest.mark.asyncio
    async def test_unauthorized_feature_disabled(
        self, engine, pro_user, catalog_with_feature, monkeypatch
    ):
        async def _subscription(_user):
            return {"status": "active"}

        async def _resolve(_user_id: int):
            return {"effective_plan": "pro", "entitlement_allowed": True}

        monkeypatch.setattr("cap646.entitlements._subscription_for_user", _subscription)
        monkeypatch.setattr("cap646.entitlements.resolve_entitlements_for_user", _resolve)
        monkeypatch.setattr("auth_service.feature_allowed", lambda _user, _feature: False, raising=False)
        result = await engine.check(47, user=pro_user)
        assert result["allowed"] is False
        assert result["reason"] == "feature_disabled"

    @pytest.mark.asyncio
    async def test_forced_exception_denied(
        self, engine, pro_user, catalog_with_feature, monkeypatch
    ):
        async def _subscription(_user):
            return {"status": "active"}

        async def _resolve(_user_id: int):
            return {"effective_plan": "pro", "entitlement_allowed": True}

        def _boom(_user, _feature):
            raise RuntimeError("feature registry unavailable")

        monkeypatch.setattr("cap646.entitlements._subscription_for_user", _subscription)
        monkeypatch.setattr("cap646.entitlements.resolve_entitlements_for_user", _resolve)
        monkeypatch.setattr("auth_service.feature_allowed", _boom, raising=False)
        result = await engine.check(47, user=pro_user)
        assert result["allowed"] is False
        assert result["reason"] == "authorization_evaluation_failed"
        assert result["gate"] == "feature_allowed"

    @pytest.mark.asyncio
    async def test_exception_cannot_grant_entitlement(
        self, engine, pro_user, catalog_with_feature, monkeypatch
    ):
        async def _subscription(_user):
            return {"status": "active"}

        async def _resolve(_user_id: int):
            return {"effective_plan": "pro", "entitlement_allowed": True}

        monkeypatch.setattr("cap646.entitlements._subscription_for_user", _subscription)
        monkeypatch.setattr("cap646.entitlements.resolve_entitlements_for_user", _resolve)
        def _forced_feature_error(_user, _feature):
            raise RuntimeError("forced")

        monkeypatch.setattr("auth_service.feature_allowed", _forced_feature_error, raising=False)
        result = await engine.check(47, user=pro_user)
        assert result["allowed"] is False
        assert result["reason"] == "authorization_evaluation_failed"
