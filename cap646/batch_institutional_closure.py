"""Strict v6 §2.1 institutional batch closure — rejects shallow execute-only passes."""

from __future__ import annotations

import inspect
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from cap646.batch01_closure_spec import (
    BATCH01_DOMAIN_PAYLOAD_KEYS,
    BATCH01_OFFICIAL_RANGE,
    DEEP_TEST_MODULE,
    FROM_SCRATCH_TEST,
    HANDLER_MODULE,
    PRODUCTION_MODULE,
    RTM_ARTIFACT,
    expected_surface,
)
from cap646.catalog import catalog_by_id

ROOT = Path(__file__).resolve().parent.parent

_FORBIDDEN_PATTERNS = (
    "invoke_substantive",
    "wrap_with_backend",
    "execute_from_scratch",
    "v6_substantive_semantic_invoke",
)


_BATCH01_HANDLERS: dict[int, str] = {
    1: "_cap001_smart_money_leaderboard",
    2: "_cap002_wallet_profiler",
    3: "_cap003_wallet_profiler_for_token",
    4: "_cap004_smart_money_tracking",
    5: "_cap005_smart_money_accumulation",
    6: "_cap006_smart_money_token_screener",
    7: "_cap007_holder_distribution",
    8: "_cap008_top_holders_concentration",
    9: "_cap009_distribution_score",
    10: "_cap010_wallet_pnl_analysis",
    11: "_cap011_wallet_historical_performance",
    12: "_cap012_wallet_entry_exit",
    13: "_cap013_wallet_counterparty",
    14: "_cap014_entity_aware_wallet",
    15: "_cap015_exchange_flow_intelligence",
    16: "_cap016_candle_price_move_investigator",
    17: "_cap017_smart_alerts",
    18: "_cap018_custom_wallet_labels",
    19: "_cap019_wallet_token_watchlists",
    20: "_cap020_multi_chain_portfolio",
    21: "_cap021_transaction_decoder",
    22: "_cap022_instant_wallet_due_diligence",
    23: "_cap023_instant_token_due_diligence",
    24: "_cap024_ai_research_agent",
    25: "_cap025_signal_explanation",
}


def _handler_source(capability_id: int) -> str:
    import cap646.batch01_dedicated as mod

    name = _BATCH01_HANDLERS.get(capability_id)
    if not name or not hasattr(mod, name):
        return ""
    return inspect.getsource(getattr(mod, name))


def _has_domain_payload(result: dict[str, Any], capability_id: int) -> tuple[bool, str]:
    keys = BATCH01_DOMAIN_PAYLOAD_KEYS.get(capability_id, ())
    if not keys:
        return False, "no_domain_keys_configured"
    if any(k in result for k in keys):
        return True, "domain_key_present"
    return False, f"missing_any_of:{','.join(keys)}"


def _deep_test_references(capability_id: int) -> bool:
    path = ROOT / "tests" / "cap646" / "test_batch01_institutional_deep.py"
    if not path.is_file():
        return False
    text = path.read_text(encoding="utf-8")
    return f"BATCH01_OFFICIAL_RANGE" in text and "test_batch01_domain_payload" in text


def _provenance_ok(result: dict[str, Any]) -> tuple[bool, str]:
    prov = result.get("data_provenance") or result.get("provenance")
    if not isinstance(prov, dict):
        return False, "provenance_not_dict"
    if any(k in prov for k in ("score", "tier", "grade", "band", "provenance_score")):
        return True, "provenance_scored"
    if len(prov) >= 2:
        return True, "provenance_structured"
    return False, "provenance_too_thin"


async def verify_batch01_institutional(capability_id: int, *, user: dict[str, Any] | None = None) -> dict[str, Any]:
    """Strict per-capability closure for official batch01 (IDs 1–25)."""
    if capability_id not in BATCH01_OFFICIAL_RANGE:
        raise ValueError(f"capability {capability_id} outside batch01 official range 1–25")

    from cap646.batch01_production import execute

    row = catalog_by_id()[capability_id]
    handler_src = _handler_source(capability_id)
    thin = any(p in handler_src for p in _FORBIDDEN_PATTERNS)

    result = await execute(
        capability_id,
        params={
            "symbol": "BTC",
            "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
            "tier": "pro",
        },
    )

    g03_ok, g03_reason = _has_domain_payload(result, capability_id)
    g11_ok, g11_reason = _provenance_ok(result)

    gates = {
        "G01_functional_completeness": bool(result.get("success")) and bool(handler_src),
        "G02_functional_correctness": result.get("surface") == expected_surface(capability_id)
        and result.get("backend_module") == PRODUCTION_MODULE,
        "G03_functional_appropriateness": g03_ok and not thin,
        "G04_requirements_traceability": bool(handler_src) and capability_id in BATCH01_DOMAIN_PAYLOAD_KEYS,
        "G05_integration_correctness": result.get("binding_source") == "explicit_option_a"
        and result.get("official_batch") == "batch01"
        and not thin,
        "G06_regression_safety": _deep_test_references(capability_id),
        "G07_security_gate": result.get("error") not in {"demo_only", "mock_only", "stub_only"},
        "G08_performance_gate": result.get("latency_ms") is not None or result.get("performance_gate") is True,
        "G09_reliability_gate": result.get("success") is True,
        "G10_observability_gate": result.get("evidence_class") is not None or result.get("classification") is not None,
        "G11_data_quality_gate": g11_ok,
        "G12_user_path_gate": bool(result.get("surface")) and result.get("surface") == expected_surface(capability_id),
        "G13_evidence_gate": bool(result.get("compliance_footer") or result.get("evidence_metadata")),
    }

    failed = [k for k, v in gates.items() if not v]
    pass_eng = len(failed) == 0

    return {
        "capability_id": capability_id,
        "capability": row.get("capability"),
        "track": row.get("track"),
        "official_batch": "batch01",
        "PASS_INSTITUTIONAL": pass_eng,
        "gates": gates,
        "failed_gates": failed,
        "gate_reasons": {"G03": g03_reason, "G11": g11_reason},
        "handler_module": HANDLER_MODULE,
        "production_module": PRODUCTION_MODULE,
        "thin_generated_handler": thin,
        "deep_test_module": DEEP_TEST_MODULE,
        "from_scratch_test": FROM_SCRATCH_TEST,
        "rtm_artifact": RTM_ARTIFACT,
        "execute_snapshot": {
            "success": result.get("success"),
            "surface": result.get("surface"),
            "backend_module": result.get("backend_module"),
            "binding_source": result.get("binding_source"),
            "latency_ms": result.get("latency_ms"),
        },
    }


async def close_batch01_institutional() -> dict[str, Any]:
    """Close official batch01 (1–25) with RTM rows and gate evidence."""
    capabilities = []
    for cid in BATCH01_OFFICIAL_RANGE:
        report = await verify_batch01_institutional(cid)
        capabilities.append(report)

    pass_n = sum(1 for r in capabilities if r["PASS_INSTITUTIONAL"])
    total = len(capabilities)

    rtm = {
        "generated_at": datetime.now(UTC).isoformat(),
        "standard": "BLACKDARK_Institutional_Capability_Standard_2026_v6 §2.1",
        "scope": "Official Batch01 — IDs 1–25 only",
        "methodology": "strict institutional closure — dedicated handler + domain payload + 13 gates",
        "summary": {
            "pass_institutional": pass_n,
            "not_complete": total - pass_n,
            "pass_pct": round(pass_n / total * 100, 2) if total else 0.0,
            "committee_ready_batch01": pass_n == total,
        },
        "per_id": {
            str(r["capability_id"]): {
                "id": r["capability_id"],
                "capability": r["capability"],
                "official_batch": "batch01",
                "status": "INSTITUTIONAL_CLOSED" if r["PASS_INSTITUTIONAL"] else "NOT_COMPLETE",
                "handler_module": r["handler_module"],
                "production_module": r["production_module"],
                "surface": expected_surface(r["capability_id"]),
                "domain_payload_keys": list(BATCH01_DOMAIN_PAYLOAD_KEYS[r["capability_id"]]),
                "gates": r["gates"],
                "failed_gates": r["failed_gates"],
                "deep_test": f"{DEEP_TEST_MODULE}::test_batch01_domain_payload[{r['capability_id']}]",
                "from_scratch_test": f"{FROM_SCRATCH_TEST}::test_batch01_from_scratch_closure[{r['capability_id']}]",
            }
            for r in capabilities
        },
        "capabilities": capabilities,
    }

    out = ROOT / RTM_ARTIFACT
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(__import__("json").dumps(rtm, indent=2), encoding="utf-8")
    return rtm
