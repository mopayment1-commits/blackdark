#!/usr/bin/env python3
"""Apply hand-authored social / Telegram alerts i18n to locales/*.json."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from i18n_service import EN, LOCALES, _load_json_catalog

SOCIAL_KEYS = (
    "social.link.x",
    "social.link.reddit",
    "social.link.facebook",
    "social.link.telegram",
    "social.link.linkedin",
    "social.join_telegram_alerts",
)

# fmt: off
PATCH: dict[str, dict[str, str]] = {
    "ar": {
        "social.link.telegram": "تيليجرام",
        "social.join_telegram_alerts": "انضم لتنبيهات تيليجرام",
    },
    "es": {
        "social.join_telegram_alerts": "Unirse a alertas de Telegram",
    },
    "pt": {
        "social.join_telegram_alerts": "Entrar nas alertas do Telegram",
    },
    "fr": {
        "social.join_telegram_alerts": "Rejoindre les alertes Telegram",
    },
    "de": {
        "social.join_telegram_alerts": "Telegram-Benachrichtigungen abonnieren",
    },
    "zh-CN": {
        "social.link.telegram": "Telegram",
        "social.join_telegram_alerts": "加入 Telegram 提醒",
    },
    "zh-TW": {
        "social.join_telegram_alerts": "加入 Telegram 提醒",
    },
    "ja": {
        "social.join_telegram_alerts": "Telegram アラートに参加",
    },
    "ko": {
        "social.join_telegram_alerts": "Telegram 알림 참가",
    },
    "hi": {
        "social.join_telegram_alerts": "Telegram अलर्ट से जुड़ें",
    },
    "tr": {
        "social.join_telegram_alerts": "Telegram uyarılarına katıl",
    },
    "ru": {
        "social.join_telegram_alerts": "Подписаться на оповещения Telegram",
    },
    "id": {
        "social.join_telegram_alerts": "Gabung peringatan Telegram",
    },
    "vi": {
        "social.join_telegram_alerts": "Tham gia cảnh báo Telegram",
    },
    "th": {
        "social.join_telegram_alerts": "เข้าร่วมการแจ้งเตือน Telegram",
    },
    "fil": {
        "social.join_telegram_alerts": "Sumali sa Telegram Alerts",
    },
    "it": {
        "social.join_telegram_alerts": "Iscriviti agli avvisi Telegram",
    },
    "bn": {
        "social.join_telegram_alerts": "Telegram অ্যালার্টে যোগ দিন",
    },
    "ur": {
        "social.link.telegram": "ٹیلیگرام",
        "social.join_telegram_alerts": "ٹیلیگرام الرٹس میں شامل ہوں",
    },
    "fa": {
        "social.link.telegram": "تلگرام",
        "social.join_telegram_alerts": "عضویت در هشدارهای تلگرام",
    },
    "ms": {
        "social.join_telegram_alerts": "Sertai amaran Telegram",
    },
    "pl": {
        "social.join_telegram_alerts": "Dołącz do alertów Telegram",
    },
    "nl": {
        "social.join_telegram_alerts": "Meld je aan voor Telegram-alerts",
    },
    "he": {
        "social.link.telegram": "טלגרם",
        "social.join_telegram_alerts": "הצטרפו להתראות Telegram",
    },
}
# fmt: on


def main() -> None:
    locales_dir = ROOT / "locales"
    (locales_dir / "en.json").write_text(
        json.dumps(dict(EN), ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    for code in LOCALES:
        if code == "en":
            continue
        path = locales_dir / f"{code}.json"
        cat = dict(_load_json_catalog(code) or {})
        for k in EN:
            cat.setdefault(k, EN[k])
        block = PATCH.get(code, {})
        for k in SOCIAL_KEYS:
            if k in block:
                cat[k] = block[k]
        path.write_text(json.dumps(cat, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"patched {code}: {len(block)} social keys")


if __name__ == "__main__":
    main()
