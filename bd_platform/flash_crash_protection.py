"""Flash-crash protection composite (PDF #49)."""

from __future__ import annotations

from typing import Any


def flash_crash_protection_status_49(*, symbol: str = "BTC") -> dict[str, Any]:
    from bd_platform.drawdown_guard import drawdown_status
    import risk_manager

    frozen = risk_manager.is_trading_frozen()
    dd = drawdown_status()
  # noqa: E501
    forecast: dict[str, Any] = {}
    try:
        from obi_predictor import forecast_flash_crash

        sym = symbol.upper()
        forecast = forecast_flash_crash(
            asset=sym,
            exchange="binance",
            symbol=f"{sym}/USDT",
            current_obi=0.0,
            history=[],
        )
    except Exception as exc:
        forecast = {"ok": False, "error": str(exc)}

    return {
        "ok": True,
        "success": True,
        "capability_id": 49,
        "symbol": symbol.upper(),
        "trading_frozen": frozen,
        "drawdown": dd,
        "flash_crash_forecast": forecast,
    }
