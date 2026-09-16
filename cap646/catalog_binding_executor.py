"""Execute official backend_registry binding — Path A real logic (not keyword-routed invoke_underlying)."""

from __future__ import annotations

import importlib
import inspect
from typing import Any

from cap646.backend_registry import binding_for, resolve_binding


def _await_if_needed(result: Any) -> Any:
    return result


async def _call_bound(fn: Any, *, style: str, symbol: str, address: str, params: dict[str, Any]) -> Any:
    sym = str(params.get("symbol") or symbol or "BTC").upper()
    addr = str(params.get("address") or address or "").strip()

    attempts: list[tuple[tuple[Any, ...], dict[str, Any]]] = []
    if style == "none":
        attempts.append(((), {}))
    elif style == "address":
        attempts.extend([((addr,), {}), ((), {"address": addr})])
    elif style == "symbol":
        attempts.extend([((sym,), {}), ((), {"symbol": sym})])
    elif style == "message":
        msg = str(params.get("message") or params.get("query") or sym)
        attempts.extend([((msg,), {}), ((), {"message": msg})])
    elif style == "quote":
        attempts.extend([((sym,), {}), ((), {"symbol": sym}), ((), {"quote": sym})])
    elif style == "assets":
        assets = params.get("assets") or [sym]
        attempts.append(((), {"assets": assets}))
    elif style in {"cert", "payload", "dict"}:
        attempts.append(((), {"payload": params}))
        attempts.append((params,))
    else:
        attempts.append(((), dict(params)))

    # Universal fallbacks
    attempts.extend([
        ((), {"symbol": sym}),
        ((sym,), {}),
        ((), {}),
    ])

    seen: set[tuple[tuple[Any, ...], tuple[tuple[str, Any], ...]]] = set()
    last_exc: Exception | None = None
    for args, kwargs in attempts:
        key = (args, tuple(sorted(kwargs.items())))
        if key in seen:
            continue
        seen.add(key)
        try:
            result = fn(*args, **kwargs)
            if inspect.isawaitable(result):
                result = await result
            return result
        except Exception as exc:
            last_exc = exc
            continue
    if last_exc is not None:
        raise last_exc
    return {"success": False, "error": "no compatible call signature"}


async def execute_catalog_binding(
    capability_id: int,
    *,
    symbol: str = "BTC",
    address: str = "",
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Call the SSOT module.entrypoint from backend_registry for this capability."""
    params = dict(params or {})
    binding = resolve_binding(capability_id)
    mod = importlib.import_module(binding.module)
    fn = getattr(mod, binding.entrypoint)

    try:
        if binding.param_style == "cert":
            cert_payload = {
                "symbol": str(params.get("symbol") or symbol or "BTC"),
                "capability_id": capability_id,
                "tier": str(params.get("tier") or "pro"),
            }
            result = fn(cert_payload)
        else:
            result = await _call_bound(fn, style=binding.param_style, symbol=symbol, address=address, params=params)
    except Exception as exc:
        return {
            "success": False,
            "error": str(exc),
            "capability_id": capability_id,
            "binding": binding_for(capability_id),
        }

    if not isinstance(result, dict):
        payload: dict[str, Any] = {"success": bool(result), "result": result}
    else:
        payload = dict(result)
        if "success" not in payload and not payload.get("error"):
            payload["success"] = True

    payload.setdefault("capability_id", capability_id)
    payload["binding_source"] = binding.source
    payload["backend_module"] = binding.module
    payload["backend_entrypoint"] = binding.entrypoint
    payload["methodology"] = {
        "framework": "Path A — catalog_binding_executor (SSOT backend_registry)",
        "implementation": f"{binding.module}.{binding.entrypoint}",
        "methodology_status": "DOCUMENTED",
        "binding_source": binding.source,
    }
    return payload
