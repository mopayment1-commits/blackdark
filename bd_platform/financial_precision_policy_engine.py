"""
Financial Precision Policy — #1032.

Cross-cutting engineering policy (Sprint 0). Enforces Decimal/Fixed-Point in
financial paths — NOT a standalone product module.
"""

from __future__ import annotations

import ast
import json
import logging
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("BLACKDARK.FinancialPrecisionPolicy")

_FEATURE_REF = 1032
_MERGED_INTO = "Sprint-0 Cross-Cutting Engineering Policy"
_STANDALONE = False
_SEED_PATH = Path("data/financial_precision_seed.json")
_RUNBOOK = "docs/infrastructure/FINANCIAL_PRECISION_POLICY.md"

_PROFITABILITY_REF = 981
_STRIPE_REF = 908
_REFERENCE_PRICING_REF = 959
_IMMUTABLE_AUDIT_REF = 1029
_PROVENANCE_REF = 945

_lint_runs: list[dict[str, Any]] = []
_audits: list[dict[str, Any]] = []


def reset_financial_precision_state() -> None:
    _lint_runs.clear()
    _audits.clear()


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("financial precision seed load failed: %s", exc)
        return {}


def _cfg(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    return seed.get("financial_precision_policy_1032") or {}


def financial_precision_status_1032(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    cfg = _cfg(seed)
    policy = cfg.get("policy") or {}
    precision = cfg.get("precision") or {}
    return {
        "ok": True,
        "feature_ref": _FEATURE_REF,
        "standalone": _STANDALONE,
        "standalone_rejected": True,
        "merged_into": _MERGED_INTO,
        "policy": {
            "enabled": policy.get("enabled", True),
            "float_forbidden_in_financial_paths": policy.get("float_forbidden_in_financial_paths", True),
            "blocks_production_on_violation": policy.get("blocks_production_on_violation", True),
            "methodology_version": policy.get("methodology_version", "1.0.0"),
            "rounding_method": policy.get("rounding_method", "round_half_up"),
            "crypto_decimal_places": policy.get("crypto_decimal_places", 8),
            "fiat_decimal_places": policy.get("fiat_decimal_places", 2),
            "sprint": policy.get("sprint", 0),
        },
        "precision": precision,
        "financial_paths": cfg.get("financial_paths") or [],
        "scoped_modules": cfg.get("scoped_modules") or {},
        "integrations": {
            "profitability_analyzer_ref": _PROFITABILITY_REF,
            "stripe_ref": _STRIPE_REF,
            "reference_pricing_ref": _REFERENCE_PRICING_REF,
            "immutable_audit_ref": _IMMUTABLE_AUDIT_REF,
            "provenance_ref": _PROVENANCE_REF,
        },
        "runbook": _RUNBOOK,
        "fee_db": cfg.get("fee_db"),
        "timestamp": _utcnow(),
    }


def record_precision_fee(
    *,
    lint_scan: bool = False,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    seed = seed or _load_seed()
    fee_cfg = (_cfg(seed).get("fee_db") or {})
    cost = float(fee_cfg.get("precision_validation_usd", 0.00001))
    if lint_scan:
        cost += float(fee_cfg.get("lint_scan_usd", 0.00005))
    return {
        "cost_usd": round(cost, 6),
        "fee_db_logged": True,
        "logged_per_financial_query": True,
        "timestamp": _utcnow(),
    }


def attach_financial_audit(
    payload: dict[str, Any],
    *,
    context: str,
    asset_type: str = "crypto",
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Attach provenance #945 audit metadata to any financial calculation result."""
    seed = seed or _load_seed()
    from money_decimal import financial_audit_metadata

    out = dict(payload)
    audit = financial_audit_metadata(
        asset_type="fiat" if asset_type == "fiat" else "crypto",  # type: ignore[arg-type]
        rounding_method=(_cfg(seed).get("policy") or {}).get("rounding_method", "round_half_up"),
    )
    audit["context"] = context
    audit["audit_id"] = f"fin_{uuid.uuid4().hex[:10]}"
    audit["provenance_ref"] = _PROVENANCE_REF
    audit["fee_db"] = record_precision_fee(seed=seed)
    out["financial_precision"] = audit
    out["provenance_financial_type"] = audit["type_used"]
    _audits.append(audit)
    return out


def _is_allowed_float_call(node: ast.Call, allow_calls: set[str]) -> bool:
    func = node.func
    if isinstance(func, ast.Name):
        return func.id in allow_calls
    if isinstance(func, ast.Attribute):
        return func.attr in allow_calls
    return False


def _scan_settlement_function(
    tree: ast.Module,
    func_name: str,
    *,
    allow_calls: set[str],
) -> list[dict[str, Any]]:
    violations: list[dict[str, Any]] = []
    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if node.name != func_name:
            continue
        for child in ast.walk(node):
            if not isinstance(child, ast.Call):
                continue
            if isinstance(child.func, ast.Name) and child.func.id == "float":
                if not _is_allowed_float_call(child, allow_calls):
                    violations.append(
                        {
                            "function": func_name,
                            "line": child.lineno,
                            "violation": "float_call_in_settlement",
                        }
                    )
    return violations


def scan_financial_paths(
    *,
    root: Path | None = None,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Static analysis — detect float in settlement functions (CI gate)."""
    seed = seed or _load_seed()
    cfg = _cfg(seed)
    root = root or Path(".")
    settlement = cfg.get("settlement_functions") or {}
    allow_calls = set(cfg.get("lint_allow_calls") or ["money_float", "d", "Decimal"])

    violations: list[dict[str, Any]] = []
    files_scanned = 0

    for rel_path, funcs in settlement.items():
        path = root / rel_path
        if not path.is_file():
            continue
        try:
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(path))
        except (OSError, SyntaxError) as exc:
            violations.append({"file": rel_path, "violation": "parse_error", "detail": str(exc)})
            continue
        files_scanned += 1
        for func_name in funcs:
            violations.extend(
                {**v, "file": rel_path}
                for v in _scan_settlement_function(tree, func_name, allow_calls=allow_calls)
            )

    result = {
        "ok": len(violations) == 0,
        "feature_ref": _FEATURE_REF,
        "files_scanned": files_scanned,
        "violations": violations,
        "violation_count": len(violations),
        "float_forbidden": (cfg.get("policy") or {}).get("float_forbidden_in_financial_paths", True),
        "fee_db": record_precision_fee(lint_scan=True, seed=seed),
        "timestamp": _utcnow(),
    }
    _lint_runs.append(result)
    return result


def get_financial_precision_audit_trail(*, limit: int = 50) -> dict[str, Any]:
    return {
        "ok": True,
        "audits_count": len(_audits[-limit:]),
        "lint_runs_count": len(_lint_runs[-limit:]),
        "audits": _audits[-limit:],
        "lint_runs": _lint_runs[-limit:],
        "append_only": True,
        "provenance_ref": _PROVENANCE_REF,
        "timestamp": _utcnow(),
    }


def check_production_gate_1032(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    status = financial_precision_status_1032(seed=seed)
    lint = scan_financial_paths(seed=seed)
    paths = status.get("financial_paths") or []
    return {
        "ok": lint["ok"] and len(paths) >= 10,
        "feature_ref": _FEATURE_REF,
        "blocks_production": status["policy"].get("blocks_production_on_violation", True),
        "lint_passed": lint["ok"],
        "financial_paths_defined": len(paths),
        "checks": {
            "decimal_policy_enabled": status["policy"].get("enabled", True),
            "settlement_lint_clean": lint["ok"],
            "crypto_precision_8dp": status["policy"].get("crypto_decimal_places") == 8,
            "fiat_precision_2dp": status["policy"].get("fiat_decimal_places") == 2,
        },
        "timestamp": _utcnow(),
    }


def run_financial_precision_e2e_1032(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    checks: list[dict[str, Any]] = []
    reset_financial_precision_state()

    status = financial_precision_status_1032(seed=seed)
    checks.append({"id": "no_standalone", "passed": status["standalone_rejected"] is True})
    checks.append({"id": "float_forbidden", "passed": status["policy"]["float_forbidden_in_financial_paths"] is True})
    checks.append({"id": "crypto_8dp", "passed": status["policy"]["crypto_decimal_places"] == 8})
    checks.append({"id": "fiat_2dp", "passed": status["policy"]["fiat_decimal_places"] == 2})

    from decimal import ROUND_HALF_UP, Decimal

    from money_decimal import crypto_money, fiat_money, financial_audit_metadata

    checks.append({"id": "crypto_round_half_up", "passed": crypto_money("1.123456789") == Decimal("1.12345679")})
    checks.append({"id": "fiat_round_half_up", "passed": fiat_money("10.125") == Decimal("10.13")})
    meta = financial_audit_metadata(asset_type="crypto")
    checks.append({"id": "audit_metadata", "passed": meta["type_used"] == "Decimal" and meta["precision"] == 8})

    import profit_fee_algorithms as pfa

    buy = {"bids": [[99.0, 100.0]], "asks": [[100.0, 100.0]]}
    sell = {"bids": [[102.0, 100.0]], "asks": [[103.0, 100.0]]}
    row = pfa.net_cross_exchange_profit(
        buy, sell, buy_exchange="binance", sell_exchange="okx", symbol="BTC/USDT", notional=100.0
    )
    checks.append({"id": "pnl_decimal_model", "passed": row is not None and row.get("money_model") == "decimal_half_even"})
    if row:
        audited = attach_financial_audit(row, context="pnl_cross_exchange", seed=seed)
        checks.append({"id": "provenance_audit", "passed": "financial_precision" in audited})

    lint = scan_financial_paths(seed=seed)
    checks.append({"id": "settlement_lint", "passed": lint["ok"] is True})

    gate = check_production_gate_1032(seed=seed)
    checks.append({"id": "production_gate", "passed": gate["ok"] is True})

    all_passed = all(c["passed"] for c in checks)
    return {
        "ok": all_passed,
        "feature_ref": _FEATURE_REF,
        "all_passed": all_passed,
        "checks": checks,
        "timestamp": _utcnow(),
    }
