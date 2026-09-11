"""CAP646 extension slot handlers (phantom registry remediation)."""

from __future__ import annotations

from typing import Any

_EXTENSION_IDS = frozenset({704, 708, 725, 812, 813, 814, 815})


async def handle_extension_capability(capability_id: int, *, params: dict[str, Any]) -> dict[str, Any]:
    if capability_id not in _EXTENSION_IDS:
        raise KeyError(f"not an extension capability: {capability_id}")
    symbol = str(params.get("symbol") or params.get("asset") or "BTC")
    return {
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
