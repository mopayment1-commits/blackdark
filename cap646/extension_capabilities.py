"""CAP646 extension slot handlers (phantom registry remediation)."""

from __future__ import annotations

import inspect
from typing import Any

_EXTENSION_IDS = frozenset({704, 708, 725, 812, 813, 814, 815})


async def handle_extension_capability(capability_id: int, *, params: dict[str, Any]) -> dict[str, Any]:
    if capability_id not in _EXTENSION_IDS:
        raise KeyError(f"not an extension capability: {capability_id}")
    symbol = str(params.get("symbol") or params.get("asset") or "BTC")
    _real_backends: dict[int, tuple[str, str]] = {
        704: ("bd_platform.free_tier_capabilities", "defi_risk_radar"),
        708: ("bd_platform.free_tier_capabilities", "lending_market_risk"),
        725: ("bd_platform.onchain_hub", "defillama_raises"),
        812: ("bd_platform.heroes_capability_layer", "clear_explanation_per_alert_812"),
        813: ("bd_platform.heroes_capability_layer", "alert_constitution_explanation_813"),
        814: ("bd_platform.heroes_capability_layer", "public_accuracy_ledger_814"),
        815: ("bd_platform.heroes_capability_layer", "timestamped_prediction_proof_815"),
    }
    if capability_id in _real_backends:
        import importlib

        mod_name, ep_name = _real_backends[capability_id]
        mod = importlib.import_module(mod_name)
        fn = getattr(mod, ep_name)
        sig = inspect.signature(fn)
        kwargs: dict[str, Any] = {}
        if "symbol" in sig.parameters:
            kwargs["symbol"] = symbol
        if inspect.iscoroutinefunction(fn):
            payload = await fn(**kwargs) if kwargs else await fn()
        else:
            payload = fn(**kwargs) if kwargs else fn()
        if hasattr(payload, "model_dump"):
            payload = payload.model_dump()
        return {
            "success": True,
            "capability_id": capability_id,
            "symbol": symbol,
            "production_path": "cap646.extension_capabilities",
            "backend_module": mod_name,
            "backend_entrypoint": ep_name,
            "payload": payload,
            "evidence_class": "PRODUCTION-ALIGNED",
        }

    return {
        "success": True,
        "capability_id": capability_id,
        "status": "EXTENSION-PENDING-CAP646",
        "symbol": symbol,
        "production_path": "cap646.extension_capabilities",
        "message": "Registered on production path; full CAP978 closure pending.",
        "evidence_class": "EXTENSION_STUB",
    }


def is_extension_id(capability_id: int) -> bool:
    return capability_id in _EXTENSION_IDS


def _make_wrapper(capability_id: int):
    async def _entry(symbol: str = "BTC", **kwargs: Any) -> dict[str, Any]:
        return await handle_extension_capability(
            capability_id,
            params={"symbol": symbol, **kwargs},
        )

    _entry.__name__ = f"extension_{capability_id}"
    return _entry


extension_704 = _make_wrapper(704)
extension_708 = _make_wrapper(708)
extension_725 = _make_wrapper(725)
extension_812 = _make_wrapper(812)
extension_813 = _make_wrapper(813)
extension_814 = _make_wrapper(814)
extension_815 = _make_wrapper(815)
