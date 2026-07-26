"""
تفعيل 100 منصة — Excel plan priority #1.

Usage:
  python scripts/activate_100_exchanges.py
  python scripts/activate_100_exchanges.py --probe
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _configure_stdio() -> None:
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
        except (AttributeError, OSError, ValueError):
            pass


async def _probe(symbol: str) -> None:
    from ccxt_market_fetcher import probe_phase_b_exchanges
    from coingecko_cex_fetcher import probe_coingecko_exchanges

    print("\n⏳ Probing CCXT venues...")
    b = await probe_phase_b_exchanges(sample_symbol=symbol)
    print(f"   CCXT: {b.get('ok_count', 0)}/{b.get('total', 0)} OK")
    print("\n⏳ Probing CoinGecko proxy venues...")
    cg = await probe_coingecko_exchanges(sample_symbol=symbol)
    print(f"   CoinGecko: {cg.get('ok_count', 0)}/{cg.get('total', 0)} OK")


async def main() -> int:
    _configure_stdio()
    parser = argparse.ArgumentParser(description="Activate 100-exchange universe")
    parser.add_argument("--probe", action="store_true", help="Probe CCXT/CoinGecko after activate")
    parser.add_argument("--symbol", default="BTC/USDT")
    args = parser.parse_args()

    from universe_rollout import activate_full_universe, live_rollout_status

    print("=" * 58)
    print("BLACKDARK — تفعيل 100 منصة")
    print("=" * 58)

    result = activate_full_universe(save=True)
    print(f"\n✅ {result['message_ar']}")
    print(f"   Manifest: {result['manifest_path']}")
    print(f"   Fetchers: {result['fetchers_registered']}")
    print(f"   Symbols:  {result['symbols']}")

    if args.probe:
        await _probe(args.symbol)

    try:
        live = await live_rollout_status()
        print(f"\n📡 Live health: {live['healthy_exchanges']}/{live['target_exchanges']} "
              f"({live['coverage_percent']}%) — يتحسن بعد تشغيل السيرفر")
    except Exception as exc:
        print(f"\n📡 Live health: unavailable ({exc})")

    print("\nالتالي: python run_service.py all --port 8080")
    print("        أو start_blackdark.bat")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
