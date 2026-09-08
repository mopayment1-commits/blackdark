"""Extension provider local contracts for Batch13 #647–#650."""

from __future__ import annotations

import pytest

from bd_platform.extension_providers import EXTENSION_PROVIDER_CONTRACTS
from bd_platform.extension_providers.bi_connectors import default_config as bi_default, health_status as bi_health
from bd_platform.extension_providers.datashare import default_config as ds_default, health_status as ds_health
from bd_platform.extension_providers.dbt_connector import default_config as dbt_default, health_status as dbt_health
from bd_platform.extension_providers.real_time_feed import default_config as rtf_default, health_status as rtf_health


@pytest.mark.parametrize("cap_id", [647, 648, 649, 650])
def test_provider_contract_fail_closed_without_credentials(cap_id: int) -> None:
    contract_fn = EXTENSION_PROVIDER_CONTRACTS[cap_id]
    out = contract_fn(symbol="ETH")
    assert out["ok"] is False
    assert out["classification"] == "EXTERNAL_DEPENDENCY_BLOCKED"
    assert out["provider"]


@pytest.mark.parametrize("cap_id", [647, 648, 649, 650])
def test_provider_contract_ready_with_credentials(cap_id: int) -> None:
    contract_fn = EXTENSION_PROVIDER_CONTRACTS[cap_id]
    configs = {
        647: {**rtf_default(), "enabled": True, "credential_ref": "vault://rtf"},
        648: {**ds_default(), "enabled": True, "credential_ref": "vault://ds", "warehouse_id": "wh-1"},
        649: {**dbt_default(), "enabled": True, "credential_ref": "vault://dbt", "project_ref": "proj-1"},
        650: {**bi_default(), "enabled": True, "credential_ref": "vault://bi"},
    }
    out = contract_fn(symbol="ETH", config=configs[cap_id])
    assert out["ok"] is True
    assert out["dependency_status"] == "ready"


def test_health_status_blocked_by_default() -> None:
    assert rtf_health().ready is False
    assert ds_health().ready is False
    assert dbt_health().ready is False
    assert bi_health().ready is False
