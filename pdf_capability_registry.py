"""
PDF checklist capability registry — auto-discovered dedicated functions by ID suffix.

Maps PDF row IDs (1–826) to importable callables in bd_platform layers and services.
"""

from __future__ import annotations

import importlib
import inspect
import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable, get_args, get_origin

ROOT = Path(__file__).resolve().parent
_SCAN_ROOTS = (
    ROOT / "bd_platform",
)
_SKIP_FILES = frozenset(
    {
        "pdf_capability_registry.py",
        "scripts/audit_pdf_capabilities_checklist.py",
        "scripts/complete_pdf_capabilities_826.py",
    }
)

_MANUAL: dict[int, tuple[str, str]] = {
    629: ("bd_platform.heroes_capability_layer", "single_sentence_oracle_629"),
    631: ("bd_platform.heroes_capability_layer", "unified_live_technical_analysis_631"),
    812: ("bd_platform.heroes_capability_layer", "clear_explanation_per_alert_812"),
    814: ("bd_platform.heroes_capability_layer", "public_accuracy_ledger_814"),
    815: ("bd_platform.heroes_capability_layer", "timestamped_prediction_proof_815"),
    382: ("bd_platform.heroes_capability_layer", "single_sentence_financial_button_382"),
    2: ("trade_simulator", "simulate_spot_trade"),
    18: ("bd_platform.alert_orchestration", "alert_orchestration_status_18"),
    29: ("bd_platform.retail_intelligence_layer", "compare_discipline_66"),
    31: ("bd_platform.retail_intelligence_layer", "build_discipline_tab_66"),
    49: ("bd_platform.flash_crash_protection", "flash_crash_protection_status_49"),
    111: ("bd_platform.market_analysis_layer", "compute_spx_correlation_111"),
    113: ("ma_intelligence_service", "build_ma_intelligence_report"),
    270: ("bd_platform.free_integrations", "holder_analytics"),
    288: ("bd_platform.correlation_mindshare", "compute_mindshare_correlation_288"),
    316: ("bd_platform.sse_stream", "sse_digest_status_316"),
    331: ("bd_platform.intelligence_analysis_layer", "analyze_arbitrage_opportunity_153"),
    378: ("exchange_currency_status", "deposit_currencies_open"),
    379: ("bd_platform.arbitrage_portfolio_ux_layer", "analyze_liquidity_capacity_189"),
    380: ("exchange_currency_status", "deposit_currencies_open"),
    381: ("exchange_currency_status", "withdrawal_currencies_closed"),
    390: ("bd_platform.whales_institutional_layer", "build_exchange_health_80"),
    393: ("data_sources_registry", "registry_summary"),
    396: ("bd_platform.news_classifier", "coindesk_feed"),
    409: ("bd_platform.quicktake_feed", "quicktake_feed_status_409"),
    517: ("comparison_engine", "run_comparison_engine"),
    528: ("bd_platform.market_rankings", "market_rankings"),
    627: ("comparison_engine", "run_comparison_engine"),
    630: ("bd_platform.intelligence_ux_extensions_layer", "scan_market_opportunities_238"),
    702: ("graphql_schema", "graphql_health"),
    745: ("subscription_analytics", "subscription_analytics_status_745"),
    752: ("institutional_assurance", "backup_status"),
    753: ("institutional_assurance", "ir_program"),
    816: ("dimension_conflict_guard", "dimension_conflict_status"),
    819: ("blackdark.data.db", "data_engine_available"),
}

_MODULE_ENTRYPOINTS: dict[str, str] = {
    "net_edge_truth": "compute_net_edge_truth",
    "due_diligence_bundle": "build_full_due_diligence_bundle",
    "coverage_honesty": "build_coverage_honesty_board",
    "sentiment_manipulation_guard": "sentiment_manipulation_status",
    "stale_price_guard": "guard_enabled",
    "acquisition_assets_service": "build_acquisition_assets_report",
    "retail_intelligence_layer": "compare_discipline_66",
    "risk_manager": "is_trading_frozen",
    "drawdown_guard": "drawdown_status",
    "money_decimal": "money_float",
    "data_spine": "ingestion_architecture_report",
    "free_tier_capabilities": "free_tier_live_ready",
    "auto_keys": "parse_keys_file",
    "gdpr_service": "gdpr_compliance_status",
    "billing_service": "billing_status",
    "constitution_gates": "ensure_execution_gates",
    "dimension_conflict_guard": "dimension_conflict_status",
    "didit_kyc": "didit_status",
    "finbert_sentiment": "analyze_text",
    "oneinch_connector": "fetch_oneinch_quote",
    "institutional": "handle_institutional_capability",
    "instant_alert_engine": "evaluate_instant_alert",
    "trade_simulator": "simulate_spot_trade",
    "grid_bot": "list_grids",
    "alert_service": "subscribe_alerts",
    "dashboard": "health",
    "onchain_hub": "dexscreener_pairs",
    "data_sources_registry": "registry_summary",
    "defi_arbitrage_engine": "defi_engine_stats",
    "service_bus": "bus_stats",
    "graphql_schema": "graphql_health",
    "news_classifier": "classify_headlines",
    "market_event_library": "event_library_stats",
    "commercial_sla": "commercial_sla_status",
    "telegram_agent": "handle_agent_message",
    "scale_readiness": "scale_readiness_report",
    "audience_routing": "audience_entry",
    "arbitrage_engine": "scan_arbitrage_opportunities",
    "footprint_analytics": "footprint_snapshot",
    "whale_story": "build_whale_story",
    "derivatives_hub": "derivatives_overview",
    "token_unlocks": "unlock_calendar",
    "gas_oracle": "current_gas_gwei",
    "slippage_tolerance_optimizer": "optimize_slippage_tolerance",
    "pairs_trading": "pairs_trading_signal",
    "reconciliation_engine": "reconcile_against_reference",
    "feature_flags": "is_enabled",
    "vendor_risk_monitor": "vendor_risk_score",
    "data_lineage_viz": "build_lineage_graph",
    "experiment_registry": "register_experiment",
    "accessibility_audit_service": "run_accessibility_audit",
}

_FUNC_NAME_INDEX: dict[str, tuple[str, str]] | None = None


def _annotation_name(annotation: Any) -> str:
    if annotation is inspect.Parameter.empty:
        return ""
    if get_origin(annotation) is not None:
        args = get_args(annotation)
        return " ".join(_annotation_name(a) for a in args).lower()
    return str(annotation).replace("typing.", "").lower()


@lru_cache(maxsize=1)
def discover_bindings() -> dict[int, tuple[str, str]]:
    """Return {cap_id: (module_path, function_name)} from _NNN suffix convention."""
    out: dict[int, tuple[str, str]] = dict(_MANUAL)
    pat = re.compile(r"^(?:async\s+)?def\s+([a-zA-Z_][a-zA-Z0-9_]*)_(\d+)\s*\(")
    for base in _SCAN_ROOTS:
        if not base.is_dir():
            continue
        for path in base.rglob("*.py"):
            if path.name in _SKIP_FILES:
                continue
            if "tests" in path.parts or ".venv" in path.parts:
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except OSError:
                continue
            rel = path.relative_to(ROOT).as_posix().replace("/", ".")[:-3]
            for line in text.splitlines():
                m = pat.match(line.strip())
                if not m:
                    continue
                fn, cid = m.group(1), int(m.group(2))
                if 1 <= cid <= 826:
                    if cid not in out or rel.startswith("bd_platform"):
                        out[cid] = (rel, f"{fn}_{cid}")
    return out


@lru_cache(maxsize=1)
def discover_function_index() -> dict[str, tuple[str, str]]:
    """Map bare function name -> (module_path, function_name)."""
    global _FUNC_NAME_INDEX
    if _FUNC_NAME_INDEX is not None:
        return _FUNC_NAME_INDEX
    idx: dict[str, tuple[str, str]] = {}
    pat = re.compile(r"^def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(")
    for base in _SCAN_ROOTS:
        if not base.is_dir():
            continue
        for path in base.rglob("*.py"):
            if "tests" in path.parts or ".venv" in path.parts:
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except OSError:
                continue
            rel = path.relative_to(ROOT).as_posix().replace("/", ".")[:-3]
            for line in text.splitlines():
                m = pat.match(line.strip())
                if m:
                    fn = m.group(1)
                    if fn not in idx or rel.startswith("bd_platform"):
                        idx[fn] = (rel, fn)
    _FUNC_NAME_INDEX = idx
    return idx


@lru_cache(maxsize=1)
def discover_platform_api_route_kwargs() -> dict[int, dict[str, Any]]:
    """Parse platform_api.py route handlers for *_NNN call kwargs."""
    path = ROOT / "platform_api.py"
    if not path.is_file():
        return {}
    text = path.read_text(encoding="utf-8")
    out: dict[int, dict[str, Any]] = {}
    for m in re.finditer(
        r"return\s+([a-zA-Z_][a-zA-Z0-9_]*)_(\d+)\(([^)]*)\)",
        text,
    ):
        fn_base, cid_s, args = m.group(1), int(m.group(2)), m.group(3)
        kwargs: dict[str, Any] = {}
        for part in args.split(","):
            part = part.strip()
            if not part or "=" not in part:
                continue
            key, val = part.split("=", 1)
            key = key.strip()
            val = val.strip()
            if val in {"True", "False"}:
                kwargs[key] = val == "True"
            elif re.match(r"^-?\d+(\.\d+)?$", val):
                kwargs[key] = float(val) if "." in val else int(val)
            elif (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                kwargs[key] = val[1:-1]
        if kwargs:
            out[cid_s] = kwargs
    return out


def resolve_evidence_binding(evidence: str) -> tuple[str, str] | None:
    """Resolve module.function from checklist evidence string."""
    ev = evidence.strip()
    if not ev:
        return None

    m = re.search(r"([a-zA-Z_][a-zA-Z0-9_]*)_(\d{1,3})\b", ev)
    if m:
        fn = f"{m.group(1)}_{m.group(2)}"
        hit = discover_function_index().get(fn)
        if hit:
            return hit

    m = re.search(r"([a-zA-Z0-9_/]+\.py)(?::([a-zA-Z_][a-zA-Z0-9_.]*))?", ev)
    if m:
        rel = m.group(1).replace("/", ".").removesuffix(".py")
        if rel.startswith("bd_platform."):
            mod_path = rel
        elif rel.startswith("bd_platform/"):
            mod_path = rel.replace("/", ".")
        elif rel.startswith("cap646/"):
            mod_path = rel.replace("/", ".")
        else:
            mod_path = rel
        if rel.startswith("cap646."):
            mod_path = rel
        if m.group(2):
            func = m.group(2).split(".")[-1]
            return mod_path, func
        stem = Path(m.group(1)).stem
        entry = _MODULE_ENTRYPOINTS.get(stem)
        if entry:
            return mod_path, entry

    m = re.search(r"(bd_platform/[a-z_]+|cap646/handlers/[a-z_]+)", ev)
    if m:
        mod_path = m.group(1).replace("/", ".")
        stem = mod_path.split(".")[-1]
        entry = _MODULE_ENTRYPOINTS.get(stem)
        if entry:
            return mod_path, entry
        if stem == "onchain_hub":
            return mod_path, "lookintobitcoin_macro"
        if stem == "free_tier_capabilities":
            return mod_path, "etf_flow_intelligence"

    for stem, entry in _MODULE_ENTRYPOINTS.items():
        if f"{stem}.py" in ev:
            mod_path = stem if "." in stem else stem
            return mod_path, entry

    return None


def _import_callable(module_path: str, func_name: str) -> Callable[..., Any] | None:
    try:
        mod = importlib.import_module(module_path)
        fn = getattr(mod, func_name, None)
        return fn if callable(fn) else None
    except Exception:
        return None


def _infer_param_default(name: str, annotation: Any) -> Any:
    nl = name.lower()
    ann = _annotation_name(annotation)

    if "dict[" in ann or ann.endswith("dict") or nl in {
        "payload",
        "body",
        "data",
        "seed",
        "answer",
        "positions",
        "context",
    }:
        if nl == "payload":
            return {"symbol": "BTC", "tier": "elite", "ok": True}
        if nl == "answer":
            return {"text": "audit answer", "confidence": 0.72}
        if nl in {"positions", "holdings"}:
            return [{"asset": "BTC", "usd": 10_000.0, "qty": 0.1}]
        return {}

    if "list" in ann or nl in {"holdings", "wallets", "price_history", "trades", "entries"}:
        if "wallet" in nl:
            return [{"address": "0x0000000000000000000000000000000000000001", "usd": 5000}]
        if "history" in nl or "trade" in nl or "entr" in nl:
            return [{"price": 50_000.0, "ts": "2026-01-01T00:00:00Z"}]
        if "hold" in nl:
            return [{"asset": "BTC", "usd": 10_000.0}]
        return [{}]

    if nl in {"price", "opportunity_level"}:
        return 50_000.0 if nl == "price" else 0.75
    if nl in {"side"}:
        return "buy"
    if nl in {"limit"}:
        return 10
    if nl in {"amount_usd"}:
        return 100.0
    if nl in {"verdict"}:
        return "Neutral"
    if nl in {"reasons"}:
        return [{"point": "audit smoke", "weight": 1.0, "rule_based": True}]
    if "usd" in nl or nl in {"order_usd", "depth_usd", "notional", "notional_usdt", "swap_usd"}:
        return 1_000.0
    if nl in {"value", "amount"}:
        return 100.0
    if "pct" in nl or nl.endswith("_pct") or "percent" in nl:
        return 5.0
    if nl in {"preset_name", "entry_id", "event", "message", "term", "protocol", "pair"}:
        return "BTC" if nl in {"pair", "protocol"} else "audit_preset"
    if nl in {"org_role", "venue", "locale", "asset", "exchange", "symbol", "tier", "user_tier"}:
        return {
            "org_role": "analyst",
            "venue": "binance",
            "locale": "en",
            "asset": "BTC",
            "exchange": "binance",
            "symbol": "BTC",
            "tier": "elite",
            "user_tier": "elite",
        }.get(nl, "BTC")
    if nl in {"email", "user_id"}:
        return "audit@blackdark.local"
    if nl in {"address"}:
        return "0x0000000000000000000000000000000000000001"
    if nl in {"coin_id"}:
        return "bitcoin"
    if nl in {"wall"}:
        return "bid"
    if nl in {"leverage", "risk_score", "volume_zscore", "btc_shock_pct"}:
        return {"leverage": 3.0, "risk_score": 0.4, "volume_zscore": 1.2, "btc_shock_pct": -10.0}.get(nl, 1.0)
    if "float" in ann:
        return 1.0
    if "int" in ann:
        return 1
    if "bool" in ann or nl.startswith("is_"):
        return False
    if "str" in ann:
        return "audit"
    return None


def _default_kwargs(fn: Callable[..., Any], capability_id: int | None = None) -> dict[str, Any]:
    route_defaults = discover_platform_api_route_kwargs()
    preset = route_defaults.get(capability_id or -1, {})
    sig = inspect.signature(fn)
    kwargs: dict[str, Any] = dict(preset)
    for name, param in sig.parameters.items():
        if name in kwargs:
            continue
        if param.default is not inspect.Parameter.empty:
            continue
        inferred = _infer_param_default(name, param.annotation)
        if inferred is not None:
            kwargs[name] = inferred
    if capability_id == 167:
        import time

        now = time.time() * 1000
        kwargs.setdefault("source_a_ts_ms", now - 500)
        kwargs.setdefault("source_b_ts_ms", now - 800)
        kwargs.setdefault("server_ts_ms", now)
    return kwargs


async def execute_binding(module_path: str, func_name: str, *, capability_id: int | None = None) -> dict[str, Any]:
    fn = _import_callable(module_path, func_name)
    if fn is None:
        return {"ok": False, "error": "import_failed", "module": module_path, "function": func_name}
    kwargs = _default_kwargs(fn, capability_id)
    try:
        if inspect.iscoroutinefunction(fn):
            result = await fn(**kwargs)
        else:
            result = fn(**kwargs)
        if isinstance(result, dict):
            result.setdefault("capability_id", capability_id)
            result.setdefault("binding", f"{module_path}.{func_name}")
            if "ok" not in result:
                result["ok"] = result.get("success", True) is not False
            return result
        return {
            "ok": True,
            "capability_id": capability_id,
            "binding": f"{module_path}.{func_name}",
            "result": result,
        }
    except Exception as exc:
        return {
            "ok": False,
            "error": str(exc),
            "capability_id": capability_id,
            "binding": f"{module_path}.{func_name}",
        }


async def execute_capability(capability_id: int) -> dict[str, Any]:
    bindings = discover_bindings()
    if capability_id in bindings:
        mod_path, func_name = bindings[capability_id]
        return await execute_binding(mod_path, func_name, capability_id=capability_id)
    return {"ok": False, "error": "no_binding", "capability_id": capability_id}


async def execute_evidence(capability_id: int, evidence: str) -> dict[str, Any]:
    binding = resolve_evidence_binding(evidence)
    if binding:
        return await execute_binding(binding[0], binding[1], capability_id=capability_id)
    return await execute_capability(capability_id)


def batch_test_module_for(capability_id: int) -> str | None:
    """Map capability ID to existing batch test file if in a known range."""
    hero_manifest = ROOT / "scripts" / "partial_batches" / "batch_hero_01.json"
    if hero_manifest.is_file():
        import json

        hero_ids = json.loads(hero_manifest.read_text(encoding="utf-8")).get("capability_ids", [])
        if capability_id in hero_ids:
            return "tests/test_hero_batch_01_capabilities.py"
    batch02 = ROOT / "scripts" / "partial_batches" / "batch_02_101_200.json"
    if batch02.is_file():
        import json

        batch02_ids = json.loads(batch02.read_text(encoding="utf-8")).get("capability_ids", [])
        if capability_id in batch02_ids:
            return "tests/test_hero_batch_02_capabilities.py"
    if capability_id in (113, 380, 381, 627):
        return "tests/test_missing_capabilities_closure.py"
    ranges = [
        (57, 66, "tests/test_legal_retail_batch57_66.py"),
        (67, 76, "tests/test_pro_trader_batch67_76.py"),
        (77, 86, "tests/test_whales_institutional_batch77_86.py"),
        (87, 94, "tests/test_institutional_b2b_batch87_94.py"),
        (95, 104, "tests/test_infra_intelligence_batch95_104.py"),
        (105, 116, "tests/test_market_analysis_batch105_116.py"),
        (117, 128, "tests/test_advanced_ta_risk_batch117_128.py"),
        (129, 139, "tests/test_onchain_platform_batch129_139.py"),
        (140, 152, "tests/test_data_sources_batch140_152.py"),
        (153, 163, "tests/test_intelligence_analysis_batch153_163.py"),
        (164, 176, "tests/test_risk_infrastructure_batch164_176.py"),
        (177, 191, "tests/test_arbitrage_portfolio_ux_batch177_191.py"),
        (192, 203, "tests/test_derivatives_ta_research_batch192_203.py"),
        (204, 216, "tests/test_onchain_defi_sources_batch204_216.py"),
        (217, 227, "tests/test_intelligence_market_extensions_batch217_227.py"),
        (228, 241, "tests/test_intelligence_ux_extensions_batch228_241.py"),
        (242, 261, "tests/test_security_trust_data_batch242_261.py"),
    ]
    for lo, hi, path in ranges:
        if lo <= capability_id <= hi:
            return path if (ROOT / path).is_file() else None
    return None
