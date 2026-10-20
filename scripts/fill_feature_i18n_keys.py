#!/usr/bin/env python3
"""Translate bounty/sealed/arb/ledger feature keys via MyMemory HTTP API."""

from __future__ import annotations

import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from i18n_service import EN, LOCALES, _load_json_catalog
from scripts.build_locale_json import ALLOW_IDENTICAL

LANGPAIR: dict[str, str] = {
    "es": "es",
    "ar": "ar",
    "pt": "pt",
    "fr": "fr",
    "de": "de",
    "zh-CN": "zh-CN",
    "zh-TW": "zh-TW",
    "ja": "ja",
    "ko": "ko",
    "hi": "hi",
    "tr": "tr",
    "ru": "ru",
    "id": "id",
    "vi": "vi",
    "th": "th",
    "fil": "tl",
    "it": "it",
    "bn": "bn",
    "ur": "ur",
    "fa": "fa",
    "ms": "ms",
    "pl": "pl",
    "nl": "nl",
    "he": "he",
}


def _feature_key(key: str) -> bool:
    if key.startswith(
        ("bounty.", "sealed.", "arb.", "ledger.panel.", "ledger.js.", "about.")
    ):
        return True
    return key in {
        "ledger.cta.bounty_log",
        "ledger.cta.sealed_markets",
        "ledger.cta.audit_challenge",
        "ledger.cta.mev_report",
        "ledger.cta.locked_predictions",
        "meta.title.bounty_log",
        "meta.title.sealed_markets",
        "meta.title.about",
        "nav.about",
        "footer.link.about",
        "footer.link.contact",
    }


FEATURE_KEYS = tuple(sorted(k for k in EN if _feature_key(k)))


def mm_translate(text: str, target: str, cache: dict[tuple[str, str], str]) -> str:
    if not text or not text.strip():
        return text
    ck = (target, text)
    if ck in cache:
        return cache[ck]
    pair = f"en|{target}"
    q = urllib.parse.quote(text[:500])
    url = f"https://api.mymemory.translated.net/get?q={q}&langpair={pair}"
    out = text
    for attempt in range(5):
        try:
            with urllib.request.urlopen(url, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            cand = str((data.get("responseData") or {}).get("translatedText") or "").strip()
            if cand and cand.upper() != text.upper():
                out = cand
                break
        except Exception:
            time.sleep(1.5 * (attempt + 1))
        time.sleep(0.35)
    cache[ck] = out
    return out


def main() -> None:
    locales_dir = ROOT / "locales"
    cache: dict[tuple[str, str], str] = {}
    stats: dict[str, int] = {}
    (locales_dir / "en.json").write_text(
        json.dumps(dict(EN), ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    for code in LOCALES:
        if code == "en":
            continue
        target = LANGPAIR.get(code)
        path = locales_dir / f"{code}.json"
        cat = dict(_load_json_catalog(code) or {})
        for k in EN:
            cat.setdefault(k, EN[k])
        pending = [k for k in FEATURE_KEYS if cat.get(k, EN[k]) == EN[k] and k not in ALLOW_IDENTICAL]
        n = 0
        if target:
            for key in pending:
                translated = mm_translate(EN[key], target, cache)
                cat[key] = translated
                if translated != EN[key]:
                    n += 1
                time.sleep(0.2)
        path.write_text(json.dumps(cat, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        stats[code] = n
        print(f"{code}: translated {n}/{len(pending)} feature keys", flush=True)
    print("STATS", json.dumps(stats))


if __name__ == "__main__":
    main()
