"""
BLACKDARK — CEX↔DEX scan + dry-run execute (Priority #3).

Usage:
  python scripts/activate_cex_dex.py
  python scripts/activate_cex_dex.py --execute
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


async def main() -> int:
    _configure_stdio()
    parser = argparse.ArgumentParser(description="CEX↔DEX scan and optional dry-run execute")
    parser.add_argument("--execute", action="store_true", help="Dry-run execute top opportunity")
    parser.add_argument("--quote", type=float, default=1000)
    args = parser.parse_args()

    from bd_platform.cex_dex_arbitrage import scan_cex_dex_opportunities
    from bd_platform.cex_dex_executor import run_cex_dex_cycle

    print("=" * 58)
    print("BLACKDARK — CEX ↔ DEX (Priority #3)")
    print("=" * 58)

    scan = await scan_cex_dex_opportunities(quote_usd=args.quote)
    print(f"\n📡 Scan: {scan['count']} opportunities · {scan['profitable_count']} profitable")
    for o in (scan.get("opportunities") or [])[:5]:
        print(f"   {o['asset']}: {o['buy_venue']}→{o['sell_venue']} · {o['net_spread_bps']} bps · ${o.get('estimated_profit_usd', 0)}")

    if args.execute:
        print("\n⏳ Dry-run execute top…")
        result = await run_cex_dex_cycle(quote_usd=args.quote)
        if result.get("skipped"):
            print(f"   ⏭️  {result.get('reason')}")
        else:
            ex = result.get("executed", {})
            print(f"   ✅ {ex.get('asset')} · {ex.get('mode')} · {len(ex.get('legs') or [])} legs")

    print("\nPlatform: http://127.0.0.1:8080/platform → CEX↔DEX")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
