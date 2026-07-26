"""
BLACKDARK — تفعيل التنفيذ التلقائي (Priority #2).

Usage:
  python scripts/activate_live_execution.py           # dry-run (آمن)
  python scripts/activate_live_execution.py --live    # live (Binance حقيقي)
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
    parser = argparse.ArgumentParser(description="Activate auto-execution (dry-run or live)")
    parser.add_argument("--live", action="store_true", help="Enable LIVE Binance orders (requires valid keys)")
    parser.add_argument("--no-verify", action="store_true")
    args = parser.parse_args()

    from execution_keys import KEYS_FILE, activate_live_execution, ensure_keys_file, execution_keys_status

    ensure_keys_file()
    print("=" * 58)
    print("BLACKDARK — التنفيذ التلقائي (Priority #2)")
    print("=" * 58)
    print(f"\nملف المفاتيح: {KEYS_FILE}")
    print("(Binance API Key + Secret — أو اتركه فارغاً للـ dry-run بدون keys)\n")

    result = await activate_live_execution(
        enable_live=args.live,
        verify=not args.no_verify,
    )

    print(f"✅ {result['message_ar']}")
    print(f"   Mode: {result['mode']}")
    if result.get("verify"):
        v = result["verify"]
        if v.get("configured"):
            print(f"   Binance: {'✅ صالح' if v.get('valid') else '❌ ' + str(v.get('message', ''))}")
        else:
            print("   Binance: ⏭️  بدون مفاتيح — dry-run فقط")
    print(f"\n   {result.get('disclaimer_ar', '')}")
    print("\n─" * 58)
    print("Dashboard → Alerts & Execution → Auto-execute / Panic Stop")
    print("http://127.0.0.1:8080/dashboard")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
