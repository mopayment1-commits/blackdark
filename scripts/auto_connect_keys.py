"""
BLACKDARK — ربط تلقائي للمفاتيح بدون أي أسئلة في Terminal.

يقرأ من: keys/platform_keys.env
إن كانت فارغة → يفعّل الوضع المجاني فوراً.

Usage:
  python scripts/auto_connect_keys.py
"""

from __future__ import annotations

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
            sys.stderr.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
        except (AttributeError, OSError, ValueError):
            pass


async def main() -> int:
    _configure_stdio()
    from bd_platform.auto_keys import KEYS_FILE, auto_import_keys, ensure_keys_file

    ensure_keys_file()
    print()
    print("=" * 58)
    print("BLACKDARK — ربط تلقائي (بدون تدخل)")
    print("=" * 58)
    print(f"\nملف المفاتيح: {KEYS_FILE}")
    print("(افتحه في Cursor والصق المفاتيح بعد = ثم احفظ)\n")

    result = await auto_import_keys(verify=True)

    if result.get("mode") == "free":
        print("✅ الوضع المجاني مفعّل — لا حاجة لمفاتيح!")
        print()
        for src in result.get("free_sources", []):
            print(f"   • {src}")
        print()
        print("لإضافة مفاتيح لاحقاً:")
        print(f"   1) افتح {KEYS_FILE.name} في مجلد keys/")
        print("   2) الصق المفتاح بعد =")
        print("   3) شغّل connect_keys.bat مرة أخرى")
    else:
        imp = result.get("import", {})
        ver = result.get("verify", {})
        print(result.get("message", "تم"))
        print(f"   محفوظ: {imp.get('saved_count', 0)}")
        print(f"   صالح:  {ver.get('valid_count', 0)}/{ver.get('configured_count', 0)}")
        for row in ver.get("results", []):
            if row.get("valid"):
                icon = "✅"
            elif row.get("configured"):
                icon = "❌"
            else:
                icon = "⏭️"
            print(f"   {icon} {row.get('service')}")

    print()
    print("─" * 58)
    print("التالي: python run_service.py all --port 8080")
    print("        أو انقر start_blackdark.bat")
    print("─" * 58)
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
