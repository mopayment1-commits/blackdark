#!/usr/bin/env python3
"""Report visible English phrases on localized public pages (local TestClient)."""

from __future__ import annotations

import re
import sys

from fastapi.testclient import TestClient

from dashboard import app
from i18n_service import EN, LOCALES, list_locales

# Phrases that must not appear when a non-English locale is selected (not brand/SKUs).
FORBIDDEN = (
    "Search site",
    "Try Oracle Free",
    "Skip to Trust Pulse",
    "Open the lenses",
    "Compare plans",
    "For companies and funds",
    "Get Decision",
    "Share Your Signal",
    "Get early access to Trust OS",
    "Join Waitlist",
    "Telegram Free Alerts",
    "Enter your email",
    "Claim Miss Bounty",
    "Miss Bounty Log",
    "Sealed Prediction Markets",
    "View Arb Opportunities",
)

PAGES = (
    "/",
    "/pricing",
    "/login",
    "/oracle-accuracy",
    "/join-waitlist",
    "/miss-bounty-log",
    "/sealed-markets",
)


def main() -> int:
    client = TestClient(app)
    codes = [c["code"] for c in list_locales() if c["code"] != "en"]
    if not codes:
        print("no non-en complete locales")
        return 1
    failures: list[str] = []
    for code in codes:
        for path in PAGES:
            url = f"{path}?lang={code}"
            html = client.get(url).text
            if f'lang="{code}"' not in html and code not in html:
                failures.append(f"{url}: missing lang={code}")
            for phrase in FORBIDDEN:
                if phrase in html:
                    failures.append(f"{url}: found English «{phrase}»")
    if failures:
        print("I18N BLEED:")
        for line in failures:
            print(line)
        return 2
    print(f"OK: {len(codes)} locales × {len(PAGES)} pages — no forbidden English phrases")
    return 0


if __name__ == "__main__":
    sys.exit(main())
