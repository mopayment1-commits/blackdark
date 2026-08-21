"""Execute CAP646 capabilities through institutional backend bindings."""

from __future__ import annotations

import importlib
import inspect
from typing import Any

from cap646.backend_registry import BackendBinding, resolve_binding
from cap646.catalog import catalog_by_id
from cap646.evidence_class import ai_compliance_footer
from data_provenance_score import attach_provenance, compute_data_provenance_score


def _import_attr(module_path: str, entrypoint: str):
    mod = importlib.import_module(module_path)
    return getattr(mod, entrypoint)


async def _call_entrypoint(fn: Any, *, params: dict[str, Any], binding: BackendBinding) -> Any:
    symbol = str(params.get("symbol") or params.get("asset") or "BTC").upper().replace("/USDT", "")
    tier = str(params.get("tier") or "pro")
    style = binding.param_style

    if style == "none":
        return fn() if not inspect.iscoroutinefunction(fn) else await fn()
    if style == "symbol":
        return fn(symbol) if not inspect.iscoroutinefunction(fn) else await fn(symbol)
    if style == "pair":
        pair = f"{symbol}USDT"
        return fn(pair) if not inspect.iscoroutinefunction(fn) else await fn(pair)
    if style == "symbol_tier":
        return await fn(symbol, lang=str(params.get("lang") or "en"), tier=tier) if inspect.iscoroutinefunction(fn) else fn(symbol)
    if style == "quote":
        kw = {"quote_amount": float(params.get("quote_amount") or 1000.0), "profitable_only": False}
        return await fn(**kw) if inspect.iscoroutinefunction(fn) else fn(**kw)
    if style == "symbols":
        return await fn([symbol]) if inspect.iscoroutinefunction(fn) else fn([symbol])
    if style == "chain":
        return await fn(str(params.get("chain") or "ethereum")) if inspect.iscoroutinefunction(fn) else fn("ethereum")
    if style == "address":
        addr = str(params.get("address") or "")
        return await fn(addr) if inspect.iscoroutinefunction(fn) else fn(addr)
    if style == "email":
        email = str(params.get("email") or "anonymous")
        return await fn(user_email=email) if "user_email" in inspect.signature(fn).parameters else fn(email)
    if style == "assets":
        return await fn(assets=[symbol], min_samples=1)
    if style == "books":
        from live_book_hub import get_live_books_if_fresh

        live = get_live_books_if_fresh()
        books = live[0] if live else {}
        sym = f"{symbol}/USDT"
        return fn(books, sym)
    if style == "edge":
        from net_edge_truth import compute_net_edge_truth

        payload = {
            "symbol": f"{symbol}/USDT",
            "buy_exchange": "binance",
            "sell_exchange": "okx",
            "expected_edge_bps": float(params.get("expected_edge_bps") or 12.0),
            "notional_usdt": float(params.get("notional_usdt") or 1000.0),
        }
        return compute_net_edge_truth(payload)
    if style == "cert":
        from decision_certificate import build_decision_certificate

        return build_decision_certificate(
            {
                "symbol": symbol,
                "prediction_id": params.get("prediction_id") or f"cap646-{binding.capability_id}",
                "decision_action": "WAIT",
                "decision_sentence": catalog_by_id()[binding.capability_id]["capability"],
                "tier": tier,
            }
        )
    if style == "limit":
        return await fn(limit=int(params.get("limit") or 20))
    if style == "message":
        text = str(params.get("message") or params.get("text") or "status")
        return await fn(text)
    if style == "hub":
        hub = fn()
        stats = {"hub": str(type(hub).__name__)}
        if hasattr(hub, "client_count"):
            stats["client_count"] = hub.client_count()
        return stats
    if style == "opportunity":
        from ai_oracle import evaluate_opportunity

        opp = {"asset": symbol, "symbol": f"{symbol}/USDT"}
        return await evaluate_opportunity(opp)

    return fn(symbol) if not inspect.iscoroutinefunction(fn) else await fn(symbol)


def _success_from_result(result: Any) -> bool:
    if result is None:
        return False
    if isinstance(result, dict):
        if result.get("success") is False:
            return False
        # Rankings / list-shaped payloads executed even when vendor empty
        if "coins" in result and isinstance(result["coins"], list):
            return True
        if result.get("available") is False and not result.get("pairs") and not result.get("data") and "coins" not in result:
            return False
        return True
    if isinstance(result, (list, tuple)):
        return True  # backend executed; empty collection is valid in cold env
    if isinstance(result, bool):
        return result
    return True


async def execute_binding(capability_id: int, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
    params = dict(params or {})
    binding = resolve_binding(capability_id)
    row = catalog_by_id()[capability_id]
    symbol = str(params.get("symbol") or "BTC").upper().replace("/USDT", "")

    try:
        fn = _import_attr(binding.module, binding.entrypoint)
        result = await _call_entrypoint(fn, params=params, binding=binding)
        ok = _success_from_result(result)
    except Exception as exc:
        prov = compute_data_provenance_score(symbol=symbol)
        payload = attach_provenance(
            {
                "capability_id": capability_id,
                "capability": row["capability"],
                "track": row["track"],
                "surface": binding.surface,
                "backend_module": binding.module,
                "backend_entrypoint": binding.entrypoint,
                "binding_source": binding.source,
                "success": False,
                "error": "backend_execution_failed",
                "primary_error": str(exc),
            }
        )
        return ai_compliance_footer(payload)

    payload: dict[str, Any] = {
        "capability_id": capability_id,
        "capability": row["capability"],
        "track": row["track"],
        "surface": binding.surface,
        "backend_module": binding.module,
        "backend_entrypoint": binding.entrypoint,
        "binding_source": binding.source,
        "result": result,
        "success": ok,
    }

    if binding.module.startswith("data_") or "provenance" in binding.entrypoint:
        payload = attach_provenance(payload)

    return ai_compliance_footer(payload)


async def handle_registry_capability(capability_id: int, *, params: dict[str, Any]) -> dict[str, Any]:
    """Institutional registry executor — replaces generic platform hash routing."""
    return await execute_binding(capability_id, params=params)
