"""Cost guard for storage assets — §24."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from blackdark.data_governance._paths import GOVERNANCE, ensure_governance_dirs
from blackdark.data_governance.contracts import CANONICAL_CONTRACTS

COST_GUARDS_PATH = GOVERNANCE / "cost_guards.json"


def ensure_cost_guards() -> dict[str, Any]:
    ensure_governance_dirs()
    if not COST_GUARDS_PATH.exists():
        guards = {}
        for asset_id, contract in CANONICAL_CONTRACTS.items():
            tier = contract.get("storage_tier", "WARM")
            guards[asset_id] = {
                "asset_id": asset_id,
                "owner": contract.get("owner"),
                "storage_tier": tier,
                "estimated_monthly_cost_usd": {"HOT": 50, "WARM": 15, "COLD": 5}.get(tier, 10),
                "growth_rate_monthly_pct": 5 if tier == "HOT" else 2,
                "query_replay_value": "high" if "ledger" in asset_id or "registry" in asset_id else "medium",
                "deletion_compaction_strategy": contract.get("retention_class", "rc_operational_warm"),
                "review_action": "keep",
            }
        payload = {"guards": guards, "registered_at": datetime.now(UTC).isoformat()}
        COST_GUARDS_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return json.loads(COST_GUARDS_PATH.read_text(encoding="utf-8"))


def validate_cost_guard(asset_id: str) -> tuple[bool, list[str]]:
    reg = ensure_cost_guards()
    guard = reg.get("guards", {}).get(asset_id)
    if not guard:
        return False, [f"missing_cost_guard:{asset_id}"]
    required = ("owner", "storage_tier", "estimated_monthly_cost_usd", "growth_rate_monthly_pct", "query_replay_value", "deletion_compaction_strategy")
    missing = [f for f in required if f not in guard or guard[f] is None]
    return len(missing) == 0, missing
