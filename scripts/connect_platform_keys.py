"""
BLACKDARK — ربط مفاتيح LunarCrush + CoinMarketCal + DeBank (عملية كاملة).

يقوم بـ:
  1) عرض الحالة الحالية
  2) (اختياري) فتح صفحات التسجيل في المتصفح
  3) طلب المفاتيح أو قراءتها من سطر الأوامر
  4) التحقق الحي من كل مفتاح
  5) الحفظ في .env
  6) اختبار الـ endpoints المحلية إن كان السيرفر يعمل

Usage:
  python scripts/connect_platform_keys.py
  python scripts/connect_platform_keys.py --open-links
  python scripts/connect_platform_keys.py --lunarcrush KEY --coinmarketcal KEY
  python scripts/connect_platform_keys.py --verify-only
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None  # type: ignore


SPECS: tuple[dict[str, str], ...] = (
    {
        "id": "lunarcrush",
        "env": "LUNARCRUSH_API_KEY",
        "label": "LunarCrush",
        "signup": "https://lunarcrush.com/pricing",
        "note_ar": "مجاني Hobby — بيانات السوق 100 طلب/يوم",
        "required": "no",
    },
    {
        "id": "coinmarketcal",
        "env": "COINMARKETCAL_API_KEY",
        "label": "CoinMarketCal",
        "signup": "https://coinmarketcal.com/en/api",
        "note_ar": "مجاني Personal — سجّل واحصل على x-api-key",
        "required": "no",
    },
    {
        "id": "debank",
        "env": "DEBANK_API_KEY",
        "label": "DeBank Cloud",
        "signup": "https://cloud.debank.com/",
        "note_ar": "مدفوع (اختياري) — البديل المجاني Tracely يعمل بدون مفتاح",
        "required": "no",
    },
)


def _load_env() -> None:
    env_path = ROOT / ".env"
    if load_dotenv and env_path.exists():
        load_dotenv(env_path, override=True)


def _configure_stdio() -> None:
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
            sys.stderr.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
        except (AttributeError, OSError, ValueError):
            pass


def _print_header(title: str) -> None:
    print()
    print("=" * 62)
    print(title)
    print("=" * 62)


def _print_status() -> None:
    from bd_platform.key_manager import keys_status

    data = keys_status()
    print(f"\n📋 الحالة الحالية ({data['configured_count']}/{data['total']} مربوط):\n")
    for row in data["keys"]:
        if row["configured"]:
            print(f"  ✅ {row['label']}: {row['masked']}")
        else:
            print(f"  ⬜ {row['label']}: غير مربوط")
        print(f"     {row['tier']}")


def _open_signup_links() -> None:
    print("\n🌐 فتح صفحات التسجيل...")
    for spec in SPECS:
        url = spec["signup"]
        print(f"   → {spec['label']}: {url}")
        try:
            webbrowser.open(url)
        except OSError:
            print("     (تعذّر فتح المتصفح — افتح الرابط يدوياً)")


def _prompt_value(spec: dict[str, str], preset: str | None) -> str | None:
    if preset is not None:
        return preset.strip() or None
    print()
    print(f"── {spec['label']} ({spec['env']}) ──")
    print(f"   التسجيل: {spec['signup']}")
    print(f"   {spec['note_ar']}")
    print("   Enter = تخطي")
    value = input("   الصق المفتاح: ").strip()
    return value or None


async def _collect_keys(args: argparse.Namespace) -> dict[str, str]:
    arg_map = {
        "lunarcrush": args.lunarcrush,
        "coinmarketcal": args.coinmarketcal,
        "debank": args.debank,
    }
    payload: dict[str, str] = {}
    for spec in SPECS:
        sid = spec["id"]
        if args.skip_debank and sid == "debank":
            continue
        value = _prompt_value(spec, arg_map.get(sid))
        if value:
            payload[sid] = value
    return payload


def _icon_ok(valid: bool | None, configured: bool) -> str:
    if valid:
        return "✅"
    if configured:
        return "❌"
    return "⏭️"


async def _verify_report() -> dict:
    from bd_platform.key_manager import verify_all_keys

    return await verify_all_keys()


def _print_verify_report(data: dict) -> None:
    print(f"\n🔍 نتيجة التحقق: {data.get('valid_count', 0)}/{data.get('configured_count', 0)} صالح\n")
    for row in data.get("results", []):
        svc = row.get("service", "?")
        if row.get("valid"):
            msg = "صالح"
        elif not row.get("configured"):
            msg = "غير مربوط"
        else:
            msg = row.get("message") or row.get("reason") or "فشل"
        print(f"  {_icon_ok(row.get('valid'), row.get('configured', False))} {svc}: {msg}")
        if row.get("endpoint"):
            print(f"     endpoint: {row['endpoint']}")


async def _test_local_server(base_url: str) -> None:
    import aiohttp

    base = base_url.rstrip("/")
    print(f"\n🖥️  اختبار السيرفر المحلي: {base}")
    timeout = aiohttp.ClientTimeout(total=8)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            for path in ("/api/platform/keys/status", "/api/platform/keys/verify"):
                url = f"{base}{path}"
                try:
                    async with session.get(url) as resp:
                        ok = resp.status == 200
                        print(f"  {'✅' if ok else '❌'} GET {path} → HTTP {resp.status}")
                        if ok and path.endswith("/verify"):
                            body = await resp.json()
                            print(f"     valid_count={body.get('valid_count')} configured={body.get('configured_count')}")
                except aiohttp.ClientError as exc:
                    print(f"  ❌ GET {path} → {exc}")
    except Exception as exc:
        print(f"  ⚠️  السيرفر غير متاح: {exc}")
        print("     شغّل: python run_service.py all --port 8080")


async def run_connect(args: argparse.Namespace) -> int:
    _load_env()
    _print_header("BLACKDARK — ربط مفاتيح Platform (عملية كاملة)")

    if not (ROOT / ".env").exists():
        example = ROOT / ".env.example"
        if example.exists():
            (ROOT / ".env").write_text(example.read_text(encoding="utf-8"), encoding="utf-8")
            print("\n📄 تم إنشاء .env من .env.example")

    _print_status()

    if args.open_links:
        _open_signup_links()

    if args.verify_only:
        report = await _verify_report()
        _print_verify_report(report)
        if args.test_server:
            await _test_local_server(args.test_server)
        return 0 if report.get("valid_count", 0) > 0 else 1

    payload = await _collect_keys(args)
    if not payload:
        print("\n⚠️  لم تُدخل أي مفاتيح — لا شيء للحفظ.")
        report = await _verify_report()
        _print_verify_report(report)
        return 0

    from bd_platform.key_manager import save_platform_keys

    print("\n⏳ جاري التحقق والحفظ...")
    result = await save_platform_keys(payload, verify=not args.no_verify)

    print(f"\n💾 تم حفظ {result['saved_count']} مفتاح في {result['env_file']}")
    for row in result.get("results", []):
        env = row.get("env", row.get("service", "?"))
        if row.get("saved"):
            print(f"  ✅ {env}")
        elif row.get("configured") is not False:
            print(f"  ❌ {env}: {row.get('message') or row.get('reason')}")

    _load_env()
    report = await _verify_report()
    _print_verify_report(report)

    if args.test_server:
        await _test_local_server(args.test_server)

    print("\n" + "─" * 62)
    print("✅ انتهت العملية")
    print("   أعد تشغيل السيرفر إن كان يعمل:")
    print("   python run_service.py all --port 8080")
    print("   أو افتح: http://127.0.0.1:8080/platform")
    print("─" * 62)

    failed = [r for r in result.get("results", []) if not r.get("saved") and r.get("message")]
    return 0 if result.get("saved_count") or not failed else 1


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="ربط مفاتيح LunarCrush + CoinMarketCal + DeBank — عملية كاملة",
    )
    p.add_argument("--lunarcrush", help="LunarCrush API key (Bearer)")
    p.add_argument("--coinmarketcal", help="CoinMarketCal x-api-key")
    p.add_argument("--debank", help="DeBank AccessKey")
    p.add_argument("--skip-debank", action="store_true", help="تخطي DeBank (مدفوع)")
    p.add_argument("--open-links", action="store_true", help="فتح صفحات التسجيل في المتصفح")
    p.add_argument("--no-verify", action="store_true", help="حفظ بدون تحقق حي")
    p.add_argument("--verify-only", action="store_true", help="تحقق فقط من المفاتيح المحفوظة")
    p.add_argument(
        "--test-server",
        nargs="?",
        const="http://127.0.0.1:8080",
        default=None,
        help="اختبار endpoints المحلية (افتراضي: http://127.0.0.1:8080)",
    )
    p.add_argument("--json", action="store_true", dest="json_out", help="إخراج JSON للتحقق")
    return p


async def _main_async() -> int:
    args = _build_parser().parse_args()
    if args.json_out and args.verify_only:
        _load_env()
        from bd_platform.key_manager import verify_all_keys

        data = await verify_all_keys()
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return 0
    return await run_connect(args)


def main() -> int:
    _configure_stdio()
    return asyncio.run(_main_async())


if __name__ == "__main__":
    raise SystemExit(main())
