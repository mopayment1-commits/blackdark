"""Phase 2 remediation — capability-specific semantic oracle tests (workset 153)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

POST_BASELINE_IDS = list(range(827, 979))
WORKSET_IDS = [644] + POST_BASELINE_IDS
ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("capability_id", POST_BASELINE_IDS)
@pytest.mark.asyncio
async def test_post_baseline_semantic_oracle(capability_id, tmp_path, monkeypatch):
    import config
    import database

    monkeypatch.setattr(config, "DB_PATH", str(tmp_path / f"semantic-{capability_id}.db"))
    monkeypatch.setenv("SERVICE_BUS_LOCAL", "true")

    await database.init_db()

    from cap978.post_baseline_semantic import validate_semantic_oracle
    from cap978.verify import execute_extension

    result = await execute_extension(
        capability_id,
        user={"email": "semantic@blackdark.local", "tier": "elite"},
        params={
            "symbol": "BTC",
            "tier": "whale",
            "coin_id": "bitcoin",
            "address": "0x0000000000000000000000000000000000000001",
        },
    )
    assert result.get("success") is True, result.get("error") or result
    ok, oracle_key, detail = validate_semantic_oracle(capability_id, result)
    assert ok, f"capability {capability_id} oracle={oracle_key} detail={detail}"


@pytest.mark.asyncio
async def test_cap_0644_production_capacity_evidence():
    from cap646.institutional_official_production import execute
    from institutional_assurance import get_signed_capacity, verify_signed_capacity

    signed = get_signed_capacity()
    assert signed is not None
    assert verify_signed_capacity(signed)
    assert signed.get("environment") == "production"
    assert signed.get("load_test", {}).get("script") == "scripts/load_test_concurrent.py"
    assert not str(signed.get("operator", "")).startswith("pytest")

    result = await execute(644, params={"symbol": "BTC", "tier": "elite"})
    assert result.get("success") is True
    payload = result.get("capacity_load_evidence") or {}
    envelope = payload.get("safe_operating_envelope") or {}
    assert envelope.get("p50_ms") is not None
    assert envelope.get("p95_ms") is not None
    assert envelope.get("error_rate") is not None
    assert payload.get("capacity_verified") is True


@pytest.mark.asyncio
async def test_cap_0644_evidence_artifact_matches_runtime():
    from cap646.institutional_official_production import execute

    artifact = json.loads((ROOT / "data" / "institutional_assurance" / "signed_capacity.json").read_text())
    result = await execute(644, params={"symbol": "BTC", "tier": "elite"})
    signed = (result.get("capacity_load_evidence") or {}).get("signed_capacity") or {}
    assert signed.get("capacity_id") == artifact.get("capacity_id")
    assert signed.get("environment") == "production"


def test_workset_semantic_test_count():
    assert len(WORKSET_IDS) == 153
