#!/usr/bin/env python3
"""Collect honest evidence for the four remaining institutional blockers.

Never claims PASS/COMPLETE without real evidence. Secrets are never printed.
"""

from __future__ import annotations

import asyncio
import json
import os
from datetime import UTC, datetime
from pathlib import Path


def _present(name: str) -> dict[str, object]:
    v = os.getenv(name, "")
    return {"present": bool(v.strip()), "len": len(v.strip())}


async def main() -> dict:
    from execution_engine import probe_binance_order_host_connectivity
    from full_catalog_mesh_proof import prove_full_catalog_health
    from jupiter_dex_adapter import prove_jupiter_submit_path, prove_jupiter_wallet_sign
    from live_data_truth_probe import CORE_PUBLIC_CEX_MESH, prove_multi_venue_live
    from ops_recovery import prove_cloud_multi_az_ha, prove_postgres_streaming_ha_rpo_rto
    from venue_fill_proof import prove_fill_lifecycle

    secrets = {
        k: _present(k)
        for k in (
            "BINANCE_API_KEY",
            "BINANCE_API_SECRET",
            "BINANCE_TESTNET",
            "AUTO_EXECUTION_ENABLED",
            "AUTO_EXECUTION_DRY_RUN",
            "SOLANA_PRIVATE_KEY",
            "JUPITER_LIVE_EXECUTION",
        )
    }
    # Always probe Spot Testnet order host connectivity (geo evidence), then restore.
    prev_tn = os.environ.get("BINANCE_TESTNET")
    os.environ["BINANCE_TESTNET"] = "true"
    try:
        order_host = await probe_binance_order_host_connectivity()
    finally:
        if prev_tn is None:
            os.environ.pop("BINANCE_TESTNET", None)
        else:
            os.environ["BINANCE_TESTNET"] = prev_tn
    fill = await prove_fill_lifecycle(
        org_id="four_blockers_fill",
        prefer_testnet=True,
        arm_testnet_live=bool(
            secrets["BINANCE_API_KEY"]["present"] and secrets["BINANCE_API_SECRET"]["present"]
        ),
    )
    wallet_sign = await prove_jupiter_wallet_sign(
        attempt_broadcast=True,
        arm_live_execution=bool(secrets["SOLANA_PRIVATE_KEY"]["present"]),
    )
    jup_submit = await prove_jupiter_submit_path()
    catalog = await prove_full_catalog_health(concurrency=6)
    mesh = await prove_multi_venue_live(full_mesh=True)
    cloud = prove_cloud_multi_az_ha()
    local_ha = prove_postgres_streaming_ha_rpo_rto()

    out = {
        "proved_at": datetime.now(UTC).isoformat(),
        "secrets_presence": secrets,
        "blocker_1_live_venue_fill": {
            "live_fill": fill.get("live_fill"),
            "verified_complete": fill.get("verified_complete"),
            "mode": fill.get("mode"),
            "ok": fill.get("ok"),
            "external_block": (fill.get("fill_readiness") or {}).get("external_block"),
            "order_host": {
                "ok": order_host.get("ok"),
                "geo_blocked": order_host.get("geo_blocked"),
                "external_block": order_host.get("external_block"),
                "hosts": order_host.get("hosts"),
            },
            "fill_readiness_blocking": (fill.get("fill_readiness") or {}).get("blocking"),
        },
        "blocker_2_jupiter_live_signature": {
            "signed_local": wallet_sign.get("signed_local"),
            "broadcast": wallet_sign.get("broadcast"),
            "executed": wallet_sign.get("executed"),
            "rpc_signature": bool(wallet_sign.get("rpc_signature")),
            "verified_complete": wallet_sign.get("verified_complete"),
            "external_block": wallet_sign.get("external_block") or jup_submit.get("external_block"),
            "rpc_reason": (wallet_sign.get("rpc_reason") or "")[:200],
            "wallet_funding": wallet_sign.get("wallet_funding"),
            "wallet_pubkey": wallet_sign.get("wallet_pubkey"),
            "submit_path_ok": jup_submit.get("ok"),
        },
        "blocker_3_full_mesh_100": {
            "catalog_price_health_pct": catalog.get("coverage_percent"),
            "institutional_l2_exchanges": catalog.get("institutional_l2_exchanges"),
            "institutional_l2_coverage_percent": catalog.get("institutional_l2_coverage_percent"),
            "full_mesh_l2_complete": catalog.get("full_mesh_l2_complete"),
            "depth_breakdown": catalog.get("depth_breakdown"),
            "external_block": catalog.get("external_block_full_mesh_l2"),
            "core_mesh_target": len(CORE_PUBLIC_CEX_MESH),
            "mesh_live_count": mesh.get("live_count"),
            "mesh_l2_count": len(mesh.get("l2_venues") or []),
        },
        "blocker_4_cloud_multi_az_ha": {
            "cloud_multi_az": cloud.get("cloud_multi_az"),
            "ok": cloud.get("ok"),
            "external_block": cloud.get("external_block"),
            "verified_complete": cloud.get("verified_complete"),
            "local_streaming_ha_vc": local_ha.get("verified_complete"),
            "local_ha_class": local_ha.get("ha_class"),
            "local_cloud_multi_az": local_ha.get("cloud_multi_az"),
        },
        "integrity": {
            "never_claim_without_evidence": True,
            "synthetic_mid_is_not_institutional_l2": True,
            "local_streaming_is_not_cloud_multi_az": True,
            "local_wallet_sign_is_not_rpc_signature_vc": True,
        },
    }
    out_path = Path("docs/dd/BLACKDARK_FOUR_BLOCKERS_EVIDENCE.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return out


if __name__ == "__main__":
    asyncio.run(main())
