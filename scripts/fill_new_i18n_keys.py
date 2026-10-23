#!/usr/bin/env python3
"""Fill only keys missing from locale JSON (or still equal to EN)."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from deep_translator import GoogleTranslator
from deep_translator.exceptions import TooManyRequests

from i18n_service import EN, LOCALES, _load_json_catalog
from scripts.build_locale_json import ALLOW_IDENTICAL, TRANSLATE_TARGETS, translate_value

NEW_KEYS = (
    "waitlist.title",
    "waitlist.sub",
    "waitlist.email_aria",
    "waitlist.email_placeholder",
    "waitlist.submit",
    "waitlist.stats_aria",
    "waitlist.page.title",
    "waitlist.page.h1",
    "waitlist.page.body",
    "waitlist.page.back",
    "waitlist.page.submit",
    "waitlist.msg.submitting",
    "waitlist.msg.error",
    "waitlist.msg.network",
    "waitlist.msg.generic",
    "waitlist.msg.welcome",
    "tg.start_free_suffix",
    "oracle.field.audience",
    "oracle.field.experience",
    "oracle.field.symbol",
    "oracle.mode.decision_pro",
    "oracle.freshness.title",
    "oracle.share.facebook",
    "oracle.share.instagram",
    "oracle.share.whatsapp",
    "oracle.share.telegram",
    "oracle.share.reddit",
)


def main() -> None:
    cache: dict[tuple[str, str], str] = {}
    locales_dir = ROOT / "locales"
    for code in LOCALES:
        if code == "en":
            (locales_dir / "en.json").write_text(
                json.dumps(dict(EN), ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
            continue
        cat = dict(_load_json_catalog(code) or {})
        cat.update({k: EN[k] for k in EN if k not in cat})
        target = TRANSLATE_TARGETS.get(code)
        pending = [
            k
            for k in NEW_KEYS
            if k in EN
            and (cat.get(k) is None or cat.get(k) == EN[k])
            and k not in ALLOW_IDENTICAL
        ]
        if target and pending:
            print(f"{code}: {len(pending)} new keys", flush=True)
            for key in pending:
                en_val = EN[key]
                translated = en_val
                for attempt in range(10):
                    try:
                        translated = translate_value(en_val, target, cache)
                    except TooManyRequests:
                        translated = en_val
                    if translated != en_val or key in ALLOW_IDENTICAL:
                        break
                    wait = min(90, 8 * (attempt + 1))
                    print(f"  retry {code}.{key} in {wait}s", flush=True)
                    time.sleep(wait)
                cat[key] = translated
                time.sleep(1.5)
        else:
            for key in NEW_KEYS:
                if key in EN:
                    cat.setdefault(key, EN[key])
        (locales_dir / f"{code}.json").write_text(
            json.dumps(cat, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    print("done")


if __name__ == "__main__":
    main()
