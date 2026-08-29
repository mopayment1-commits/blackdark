"""
PDF checklist capability registry — auto-discovered dedicated functions by ID suffix.

Maps PDF row IDs (1–826) to importable callables in bd_platform layers and services.
"""

from __future__ import annotations

import ast
import importlib
import inspect
import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parent
_SCAN_ROOTS = (
    ROOT / "bd_platform",
    ROOT,
)
_SKIP_FILES = frozenset(
    {
        "pdf_capability_registry.py",
        "scripts/audit_pdf_capabilities_checklist.py",
        "scripts/complete_pdf_capabilities_826.py",
    }
)

_MANUAL: dict[int, tuple[str, str]] = {
    113: ("ma_intelligence_service", "build_ma_intelligence_report"),
    380: ("exchange_currency_status", "deposit_currencies_open"),
    381: ("exchange_currency_status", "withdrawal_currencies_closed"),
    627: ("comparison_engine", "run_comparison_engine"),
}


@lru_cache(maxsize=1)
def discover_bindings() -> dict[int, tuple[str, str]]:
    """Return {cap_id: (module_path, function_name)} from _NNN suffix convention."""
    out: dict[int, tuple[str, str]] = dict(_MANUAL)
    pat = re.compile(r"^def\s+([a-zA-Z_][a-zA-Z0-9_]*)_(\d+)\s*\(")
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
                    # prefer bd_platform over root duplicates
                    if cid not in out or rel.startswith("bd_platform"):
                        out[cid] = (rel, f"{fn}_{cid}")
    return out


def _import_callable(module_path: str, func_name: str) -> Callable[..., Any] | None:
    try:
        mod = importlib.import_module(module_path)
        fn = getattr(mod, func_name, None)
        return fn if callable(fn) else None
    except Exception:
        return None


def _default_kwargs(fn: Callable[..., Any]) -> dict[str, Any]:
    sig = inspect.signature(fn)
    kwargs: dict[str, Any] = {}
    for name, param in sig.parameters.items():
        if param.default is not inspect.Parameter.empty:
            continue
        if name in {"symbol", "asset", "pair"}:
            kwargs[name] = "BTC"
        elif name in {"email", "user_id"}:
            kwargs[name] = "audit@blackdark.local"
        elif name in {"exchange", "exchange_id"}:
            kwargs[name] = "binance"
        elif name in {"address"}:
            kwargs[name] = "0x0000000000000000000000000000000000000001"
        elif name in {"tier", "user_tier"}:
            kwargs[name] = "elite"
        elif param.annotation is bool or name.startswith("is_"):
            kwargs[name] = False
        elif param.kind == inspect.Parameter.KEYWORD_ONLY:
            pass
        elif param.kind in (inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.POSITIONAL_ONLY):
            if name not in kwargs:
                kwargs[name] = "BTC" if "symbol" in name.lower() else 0
    return kwargs


async def execute_capability(capability_id: int) -> dict[str, Any]:
    bindings = discover_bindings()
    if capability_id not in bindings:
        return {"ok": False, "error": "no_binding", "capability_id": capability_id}
    mod_path, func_name = bindings[capability_id]
    fn = _import_callable(mod_path, func_name)
    if fn is None:
        return {"ok": False, "error": "import_failed", "module": mod_path, "function": func_name}
    kwargs = _default_kwargs(fn)
    try:
        if inspect.iscoroutinefunction(fn):
            result = await fn(**kwargs)
        else:
            result = fn(**kwargs)
        if isinstance(result, dict):
            result.setdefault("capability_id", capability_id)
            result.setdefault("binding", f"{mod_path}.{func_name}")
            if "ok" not in result:
                result["ok"] = result.get("success", True) is not False
            return result
        return {"ok": True, "capability_id": capability_id, "binding": f"{mod_path}.{func_name}", "result": result}
    except Exception as exc:
        return {"ok": False, "error": str(exc), "capability_id": capability_id, "binding": f"{mod_path}.{func_name}"}


def batch_test_module_for(capability_id: int) -> str | None:
    """Map capability ID to existing batch test file if in a known range."""
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
