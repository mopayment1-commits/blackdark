#!/usr/bin/env python3
"""Gate 1 baseline probe — Batch04 #151-#200. Repository reality only."""

from __future__ import annotations

import asyncio
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

HERO_BINDINGS: dict[int, tuple[str, str]] = {}
DISPATCH_OVERRIDES = {151, 159, 161, 162, 183, 189}
BATCH01_OVERLAP = {175}


def _commit() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def _branch() -> str:
    return subprocess.check_output(["git", "branch", "--show-current"], cwd=ROOT, text=True).strip()


def _load_hero_bindings() -> dict[int, tuple[str, str]]:
    import cap646.batch04_hero_bridge as hb
    return {k: (v[0], v[1]) for k, v in hb._HERO_BINDINGS.items()}


def _canonical_module(cap_id: int) -> str:
    if cap_id == 175:
        return "cap646.batch01_production.execute → cap646.handlers.ai.handle_ai_capability"
    if cap_id == 151:
        return "cap646.batch04_dedicated._cap151 → cap646.batch04_quarterly_protocol.build_quarterly_protocol_report"
    if cap_id == 183:
        return "cap646.batch04_dedicated._cap183 → cap646.batch04_whale_transaction.build_whale_transaction_intelligence"
    if cap_id in DISPATCH_OVERRIDES:
        return f"cap646.batch04_dedicated._cap{cap_id}"
    if cap_id in HERO_BINDINGS:
        mod, fn = HERO_BINDINGS[cap_id]
        return f"cap646.batch04_dedicated._cap_hero_bridge → {mod}.{fn}"
    return f"cap646.batch04_dedicated._cap{cap_id}"


def _classify_state(cap_id: int, payload_keys: set[str], hero_mod: str | None) -> str:
    stub_only = payload_keys <= {"ok", "feature_ref", "symbol", "catalog_goal"}
    if cap_id in DISPATCH_OVERRIDES or cap_id == 175:
        return "BROWNFIELD"
    if hero_mod:
        return "BROWNFIELD"
    if stub_only:
        return "STUB_TEMPLATE"
    return "BROWNFIELD"


def _semantic_miswire(cap_id: int, name: str, hero_fn: str | None) -> str | None:
    """Detect catalog name vs hero function semantic mismatch."""
    checks = {
        192: ("network_activity", "analyze_funding_rate"),
        193: ("transaction_volume", "auto_arbitrage_rejected"),
        194: ("nvt", "compute_cvd"),
        195: ("mvrv", "strategy_simulator"),
        196: ("realized_cap", "ingest_yahoo_finance"),
        197: ("daily_active", "ingest_alpha_vantage"),
        198: ("age_consumed", "ingest_binance_research"),
        199: ("mean_dollar", "ingest_messari_research"),
        160: ("pay_per_request", "detect_volatility_squeeze"),
        161: ("entitlements", "alert_delivery"),  # override uses institutional
        162: ("provenance", "data_grid_ui"),  # override uses provenance
        164: ("token_unlock", "liquidity_impact"),
        165: ("fundraising", "hashrate_capitulation"),
        166: ("research_confidence", "brokerage_rejected"),
        167: ("social_volume", "validate_time_sync"),
    }
    if cap_id == 175:
        return "MISWIRE: catalog surface=social_sentiment_intelligence; runtime surface=sentiment_ai (batch01)"
    if cap_id not in checks:
        return None
    expected_token, hero_token = checks[cap_id]
    if hero_fn and hero_token not in hero_fn:
        return f"MISWIRE: catalog expects {expected_token}; hero={hero_fn}"
    if cap_id in DISPATCH_OVERRIDES and cap_id == 161:
        return "MISWIRE: catalog entitlements; runtime uses handle_institutional_capability(161)"
    if cap_id in DISPATCH_OVERRIDES and cap_id == 162:
        return "MISWIRE: hero=data_grid_ui_status_162; runtime uses provenance_hot_storage (#106)"
    return f"MISWIRE: catalog expects {expected_token}; hero binding may not match purpose"


async def _probe(cap_id: int, acc_row: dict) -> dict[str, Any]:
    from cap646.batch04_dedicated import EXPECTED_SURFACE
    from cap646.runtime import execute_capability

    params: dict[str, Any] = {"symbol": "BTC", "tier": "pro", "amount_usd": 1_000_000}
    try:
        result = await execute_capability(cap_id, skip_entitlement=True, params=params)
    except Exception as exc:
        return {"success": False, "error": str(exc), "surface": None, "payload_keys": []}

    surface = result.get("surface")
    root = acc_row.get("payload_root") or EXPECTED_SURFACE.get(cap_id, surface)
    payload = result.get(root) or result.get(surface) or result.get(EXPECTED_SURFACE.get(cap_id, "")) or {}
    if isinstance(payload, dict):
        keys = set(payload.keys())
    else:
        keys = set()
    return {
        "success": result.get("success"),
        "surface": surface,
        "production_spine": result.get("production_spine"),
        "payload_keys": sorted(keys),
        "payload_key_count": len(keys),
        "classification_runtime": result.get("classification"),
        "blocker": result.get("blocker"),
        "catalog_link": result.get("catalog_link"),
    }


def _duplication(cap_id: int) -> dict[str, str]:
    if cap_id == 175:
        return {"state": "REUSED_ALIAS", "compared": "batch01/175", "canonical": "cap646.batch01_production"}
    if cap_id == 162:
        return {"state": "REUSED_LINK", "compared": "106", "canonical": "batch03 #106 provenance"}
    if cap_id == 159:
        return {"state": "OVERLAP_PARTIAL", "compared": "103", "canonical": "batch03 #103 (OVERLAP-PARTIAL)"}
    if cap_id == 183:
        return {"state": "DISTINCT", "compared": "130", "canonical": "cap646.batch04_whale_transaction"}
    if cap_id in {151, 152, 153, 156}:
        return {"state": "OVERLAP_PARTIAL", "compared": "hero-layer", "canonical": f"cap646.batch04_dedicated._cap{cap_id}"}
    return {"state": "DISTINCT", "compared": "", "canonical": f"cap646.batch04_dedicated"}


def _blocker(cap_id: int, probe: dict) -> dict[str, str | None]:
    if cap_id == 159:
        return {"blocker": "BLOCKER-159-103", "type": "CROSS_BATCH_DEPENDENCY"}
    if cap_id == 175:
        return {"blocker": "BATCH01_OVERLAP", "type": "REUSED_ALIAS"}
    if cap_id == 162:
        return {"blocker": None, "type": "REUSED_LINK"}
    return {"blocker": probe.get("blocker"), "type": None}


async def main() -> None:
    global HERO_BINDINGS
    HERO_BINDINGS = _load_hero_bindings()
    commit = _commit()
    branch = _branch()

    acceptance = json.loads((ROOT / "docs/BATCH04_ACCEPTANCE_151_200.json").read_text())
    acc = {r["capability_id"]: r for r in acceptance["rows"]}

    rows: list[dict[str, Any]] = []
    for cap_id in range(151, 201):
        a = acc[cap_id]
        probe = await _probe(cap_id, a)
        hero = HERO_BINDINGS.get(cap_id)
        hero_fn = hero[1] if hero else None
        hero_mod = hero[0] if hero else None
        if cap_id in DISPATCH_OVERRIDES:
            hero_fn = None  # runtime override
        payload_keys = set(probe.get("payload_keys") or [])
        state = _classify_state(cap_id, payload_keys, hero_fn)
        dup = _duplication(cap_id)
        blk = _blocker(cap_id, probe)
        miswire = _semantic_miswire(cap_id, a["capability_name"], hero_fn)

        # Functional evidence — honest, not PASS from ok alone
        has_domain_fields = len(payload_keys - {"ok", "feature_ref", "symbol", "catalog_goal"}) >= 1
        completeness = "NOT_VERIFIED" if not probe.get("success") else ("PARTIAL" if cap_id == 159 else ("VERIFIED_LOCAL" if has_domain_fields else "STUB_ONLY"))
        correctness = "NOT_VERIFIED"
        if probe.get("success") and probe.get("surface") == a["expected_surface"]:
            correctness = "NOT_VERIFIED" if miswire else "VERIFIED_LOCAL"
        elif cap_id == 175:
            correctness = "NOT_VERIFIED"
        appropriateness = "NOT_VERIFIED" if miswire or cap_id in (159, 175) else ("VERIFIED_LOCAL" if has_domain_fields else "STUB_ONLY")

        route = f"/api/cap646/{cap_id}"
        if cap_id == 175:
            route = "/api/cap646/175 (batch01 spine)"

        row = {
            "id": cap_id,
            "capability": a["capability_name"],
            "gate1_state": state,
            "business_purpose": a.get("requirement_contract", {}).get("business_objective", a["capability_name"]),
            "canonical_module_function": _canonical_module(cap_id),
            "canonical_route": route,
            "data_source_owner": a.get("hero_underlying", "NOT_VERIFIED"),
            "acceptance_criteria": f"docs/BATCH04_ACCEPTANCE_151_200.json domain_rules for #{cap_id}",
            "expected_output_domain": a.get("requirement_contract", {}).get("expected_output") or f"{a['expected_surface']} with domain-specific fields per catalog goal",
            "functional_completeness": completeness,
            "functional_correctness": correctness,
            "functional_appropriateness": appropriateness,
            "duplication_state": dup["state"],
            "duplication_compared": dup["compared"],
            "duplication_canonical": dup["canonical"],
            "blocker": blk["blocker"],
            "blocker_type": blk["type"],
            "semantic_miswire": miswire,
            "evidence_path": f"cap646/batch04_dedicated.py + runtime probe @ {commit}",
            "evidence_commit": commit,
            "runtime_probe": probe,
            "hero_underlying": a.get("hero_underlying"),
            "expected_surface": a["expected_surface"],
        }
        rows.append(row)

    # Mechanical counts
    states = [r["gate1_state"] for r in rows]
    dups = [r["duplication_state"] for r in rows]
    summary = {
        "total": 50,
        "gate1_state": {k: states.count(k) for k in sorted(set(states))},
        "duplication_state": {k: dups.count(k) for k in sorted(set(dups))},
        "semantic_miswire_count": sum(1 for r in rows if r["semantic_miswire"]),
        "blocker_count": sum(1 for r in rows if r["blocker"]),
        "independent_canonical": sum(1 for r in rows if r["duplication_state"] == "DISTINCT" and not r["blocker"]),
        "reused_alias": [r["id"] for r in rows if r["duplication_state"] in ("REUSED_ALIAS", "REUSED_LINK")],
    }

    rtm = {
        "generated_at": datetime.now(UTC).isoformat(),
        "gate": "G1_BASELINE_ONLY",
        "branch": branch,
        "commit": commit,
        "baseline_commit": "cf475c9",
        "scope": "Batch04 IDs 151-200",
        "official_batch": "batch04",
        "batch04_independent": 0,
        "progress_826": 148,
        "build_phase": "BUILD_PHASE_HOLD",
        "summary": summary,
        "rows": rows,
    }

    out = ROOT / "docs/BATCH04_RTM_151_200.json"
    out.write_text(json.dumps(rtm, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"branch": branch, "commit": commit, "summary": summary}, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
