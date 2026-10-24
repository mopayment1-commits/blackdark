"""
BLACKDARK — Public UI i18n (25 locales).

English is the default and source of truth. Locale catalogs live in locales/*.json.
RTL: Arabic, Hebrew, Urdu, Persian/Farsi.
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable
from functools import lru_cache
from pathlib import Path
from typing import Any

# Sonar S1192: duplicated string literals
KEY_DECISION_ACT = 'decision.act'
KEY_DECISION_WAIT = 'decision.wait'
STR_PUBLIC_ACCURACY_LEDGER = 'Public Accuracy Ledger'
STR_TRY_ORACLE_FREE = 'Try Oracle Free'

# code -> metadata
LOCALES: dict[str, dict[str, str]] = {
    "en": {"code": "en", "name": "English", "native": "English", "dir": "ltr", "group": "core"},
    "es": {"code": "es", "name": "Spanish", "native": "Español", "dir": "ltr", "group": "core"},
    "ar": {"code": "ar", "name": "Arabic", "native": "العربية", "dir": "rtl", "group": "core"},
    "pt": {"code": "pt", "name": "Portuguese (Brazilian)", "native": "Português (Brasil)", "dir": "ltr", "group": "core"},
    "fr": {"code": "fr", "name": "French", "native": "Français", "dir": "ltr", "group": "core"},
    "de": {"code": "de", "name": "German", "native": "Deutsch", "dir": "ltr", "group": "core"},
    "zh-CN": {"code": "zh-CN", "name": "Chinese (Simplified)", "native": "简体中文", "dir": "ltr", "group": "core"},
    "zh-TW": {"code": "zh-TW", "name": "Chinese (Traditional)", "native": "繁體中文", "dir": "ltr", "group": "core"},
    "ja": {"code": "ja", "name": "Japanese", "native": "日本語", "dir": "ltr", "group": "core"},
    "ko": {"code": "ko", "name": "Korean", "native": "한국어", "dir": "ltr", "group": "core"},
    "hi": {"code": "hi", "name": "Hindi", "native": "हिन्दी", "dir": "ltr", "group": "core"},
    "tr": {"code": "tr", "name": "Turkish", "native": "Türkçe", "dir": "ltr", "group": "edge"},
    "ru": {"code": "ru", "name": "Russian", "native": "Русский", "dir": "ltr", "group": "edge"},
    "id": {"code": "id", "name": "Indonesian", "native": "Bahasa Indonesia", "dir": "ltr", "group": "edge"},
    "vi": {"code": "vi", "name": "Vietnamese", "native": "Tiếng Việt", "dir": "ltr", "group": "edge"},
    "th": {"code": "th", "name": "Thai", "native": "ไทย", "dir": "ltr", "group": "edge"},
    "fil": {"code": "fil", "name": "Filipino", "native": "Filipino", "dir": "ltr", "group": "edge"},
    "it": {"code": "it", "name": "Italian", "native": "Italiano", "dir": "ltr", "group": "edge"},
    "bn": {"code": "bn", "name": "Bengali", "native": "বাংলা", "dir": "ltr", "group": "edge"},
    "ur": {"code": "ur", "name": "Urdu", "native": "اردو", "dir": "rtl", "group": "edge"},
    "fa": {"code": "fa", "name": "Persian / Farsi", "native": "فارسی", "dir": "rtl", "group": "edge"},
    "ms": {"code": "ms", "name": "Malay", "native": "Bahasa Melayu", "dir": "ltr", "group": "edge"},
    "pl": {"code": "pl", "name": "Polish", "native": "Polski", "dir": "ltr", "group": "edge"},
    "nl": {"code": "nl", "name": "Dutch", "native": "Nederlands", "dir": "ltr", "group": "edge"},
    "he": {"code": "he", "name": "Hebrew", "native": "עברית", "dir": "rtl", "group": "edge"},
}

DEFAULT_LANG = "en"
_ALIASES = {
    "zh": "zh-CN",
    "zh-cn": "zh-CN",
    "zh_cn": "zh-CN",
    "zh-hans": "zh-CN",
    "zh-tw": "zh-TW",
    "zh_tw": "zh-TW",
    "zh-hant": "zh-TW",
    "pt-br": "pt",
    "pt_br": "pt",
    "pt-pt": "pt",
    "en-us": "en",
    "en-gb": "en",
    "ara": "ar",
    "heb": "he",
    "iw": "he",
    "fa-ir": "fa",
    "pes": "fa",
    "fil-ph": "fil",
    "tl": "fil",
    "tagalog": "fil",
    "ms-my": "ms",
    "ind": "id",
    "urd": "ur",
    "ben": "bn",
    "ita": "it",
    "nld": "nl",
    "pol": "pl",
}


def normalize_lang(value: str | None) -> str:
    raw = (value or DEFAULT_LANG).strip().replace("_", "-")
    if not raw:
        return DEFAULT_LANG
    lower = raw.lower()
    if lower in _ALIASES:
        return _ALIASES[lower]
    # exact / case variants
    for code in LOCALES:
        if code.lower() == lower:
            return code
    # language subtag only
    primary = lower.split("-", 1)[0]
    if primary in _ALIASES:
        return _ALIASES[primary]
    for code in LOCALES:
        if code.lower() == primary or code.lower().startswith(primary + "-"):
            return code
    return DEFAULT_LANG


def locale_meta(lang: str | None) -> dict[str, str]:
    code = normalize_lang(lang)
    return dict(LOCALES[code])


def is_rtl(lang: str | None) -> bool:
    return locale_meta(lang)["dir"] == "rtl"


LOGIN_UI_KEYS: tuple[str, ...] = (
    "login.tab.login",
    "login.tab.signup",
    "login.email",
    "login.pass_label",
    "login.password",
    "login.remember",
    "login.confirm_password",
    "login.submit",
    "login.name",
    "auth.google",
    "login.msg.google_not_configured",
    "auth.signup_submit",
    "auth.divider_email",
    "nav.login",
    "nav.signup",
    "nav.logout",
    "nav.profile",
    "lang.label",
)

# Keys that may match English (brand SKUs, tier names, universal acronyms).
ALLOW_IDENTICAL: frozenset[str] = frozenset(
    {
        "brand",
        "action.ACT",
        "action.WAIT",
        "pricing.pro",
        "pricing.public.col.pro",
        "pricing.public.col.plus",
        "pricing.public.tier.pro.name",
        "pricing.public.tier.plus.name",
        "pricing.whale",
        "pricing.decision_pro",
        "pricing.decision_desk",
        "stats.telegram",
        "footer.status",
        "login.name",
        "pricing.public.name",
        "pulse.live",
        "ledger.cta.json_api",
        "footer.col.product",
        "footer.link.dashboard",
        "common.anti_hype",
        "oracle.mode.pro",
        "oracle.audience.pro",
        "oracle.audience.whale",
        "oracle.audience.fund",
        "oracle.audience.retail",
        "lenses.prove.title",
        "lenses.operate.title",
        "lenses.desk.title",
        "lenses.room.title",
        "oracle.mode.decision_pro",
        "oracle.share.facebook",
        "oracle.share.instagram",
        "oracle.share.whatsapp",
        "oracle.share.telegram",
        "oracle.share.reddit",
        "social.link.linkedin",
        "social.link.facebook",
        "social.link.reddit",
        "social.link.telegram",
        "social.link.x",
        "dash.operate.markdown",
        "dash.ux.pro",
    }
)

_TEMPLATE_I18N_KEY_RE = re.compile(r"\{\{\s*t\('([^']+)'\)")

_EXTRA_PUBLIC_SURFACE_KEYS: tuple[str, ...] = (
    "a11y.skip_trust_pulse",
    "a11y.trust_pulse",
    "pulse.stale",
    "pulse.verify_ledger",
    "pulse.free_proof",
    "pulse.no_cert",
    "pulse.cert_prefix",
    "pulse.fallback_sentence",
    "pulse.share_default",
    "pulse.conditions_met_review",
    "pulse.model_state",
    "pulse.model_state_conditions",
    "seal.stamp_prefix",
    "footer.col.product",
    "footer.col.trust",
    "footer.col.company",
    "footer.col.legal",
    "footer.follow",
    "footer.tagline",
    "footer.story",
    "footer.ledger",
    "footer.status",
    "footer.disclaimer",
    "footer.link.trust_pulse",
    "footer.link.decide",
    "footer.link.verify",
    "footer.link.dashboard",
    "footer.link.pricing",
    "footer.link.profile",
    "footer.link.chat",
    "footer.link.about",
    "footer.link.contact",
    "meta.title.about",
    "about.title",
    "about.lead",
    "about.p1",
    "about.p2",
    "about.capabilities.title",
    "about.capability.1",
    "about.capability.2",
    "about.capability.3",
    "about.capability.4",
    "about.capability.5",
    "about.capability.6",
    "about.capability.7",
    "about.capability.8",
    "about.capability.9",
    "about.capability.10",
    "about.capability.11",
    "about.disclaimer",
    "about.follow",
    "about.explore",
    "nav.about",
    "social.link.x",
    "social.link.reddit",
    "social.link.facebook",
    "social.link.telegram",
    "social.link.linkedin",
    "social.join_telegram_alerts",
    "ledger.hero.badge",
    "ledger.hero.title",
    "ledger.hero.engine_rules",
    "ledger.hero.engine_checking",
    "ledger.hero.lead",
    "ledger.hero.alias",
    "ledger.cta.verify_chain",
    "ledger.cta.misses",
    "ledger.cta.glass",
    "ledger.cta.mirror",
    "ledger.cta.docs",
    "ledger.proof_chain.title",
    "ledger.proof_chain.loading",
    "ledger.footer",
    "ledger.cta.dashboard",
    "ledger.cta.json_api",
    "ledger.cta.evidence",
)


@lru_cache(maxsize=1)
def public_surface_keys() -> tuple[str, ...]:
    root = Path(__file__).resolve().parent
    found: set[str] = set(_EXTRA_PUBLIC_SURFACE_KEYS)
    for rel in (
        "templates/landing.html",
        "templates/login.html",
        "templates/pricing.html",
        "templates/partials/site_top_nav.html",
        "templates/partials/lang_switcher.html",
        "templates/partials/site_footer.html",
        "templates/oracle_accuracy.html",
        "templates/join_waitlist.html",
        "templates/docs_public.html",
        "templates/discipline.html",
        "templates/utility.html",
        "templates/miss_bounty_log.html",
        "templates/sealed_markets.html",
        "templates/oracle_decision_market.html",
        "templates/dashboard.html",
        "templates/partials/oracle_workspace.html",
        "templates/profile.html",
    ):
        path = root / rel
        if path.is_file():
            found |= set(_TEMPLATE_I18N_KEY_RE.findall(path.read_text(encoding="utf-8")))
    return tuple(sorted(k for k in found if k in EN))


def _locale_raw_strings(code: str) -> dict[str, str]:
    """Locale file only — no English merge."""
    code = normalize_lang(code)
    if code == "en":
        return dict(EN)
    loaded = _load_json_catalog(code)
    return dict(loaded) if loaded else {}


def _translation_valid(code: str, key: str, value: str | None) -> bool:
    if not value or not str(value).strip() or value == key:
        return False
    if code == "en":
        return key in EN
    en_val = EN.get(key)
    if en_val is None:
        return False
    if key in ALLOW_IDENTICAL:
        return True
    return value != en_val


def locale_ui_complete(code: str) -> bool:
    code = normalize_lang(code)
    if code == "en":
        return True
    for key in public_surface_keys():
        if _effective_translation(code, key) is None:
            return False
    return True


def _locale_json_codes() -> tuple[str, ...]:
    """Locale codes with an on-disk catalog (locales/<code>.json)."""
    root = _locales_dir()
    codes: list[str] = []
    for path in sorted(root.glob("*.json")):
        code = path.stem
        if code in LOCALES:
            codes.append(code)
    if "en" not in codes and "en" in LOCALES:
        codes.insert(0, "en")

    def _sort_key(c: str) -> tuple[int, str]:
        if c == "en":
            return (0, "")
        return (1, str(LOCALES.get(c, {}).get("native") or c))

    return tuple(sorted(set(codes), key=_sort_key))


def list_locales() -> list[dict[str, str]]:
    """Locales exposed in the header switcher (every locales/*.json catalog)."""
    return [dict(LOCALES[code]) for code in _locale_json_codes() if code in LOCALES]


def locale_catalog_available(code: str) -> bool:
    code = normalize_lang(code)
    if code not in LOCALES:
        return False
    if code == "en":
        return True
    return (_locales_dir() / f"{code}.json").is_file()


# ---------------------------------------------------------------------------
# English source catalog (all UI keys)
# ---------------------------------------------------------------------------
EN: dict[str, str] = {
    # Brand / meta
    "brand": "BLACKDARK",
    "meta.description": "BLACKDARK — one Act/Wait Oracle decision with a public verifiable accuracy ledger. Prove it, not trust me.",
    "meta.title.home": "BLACKDARK — AI Crypto Intelligence Platform",
    "meta.title.dashboard": "BLACKDARK — Intelligence Dashboard",
    "meta.title.login": "BLACKDARK — Login",
    "meta.title.accuracy": "BLACKDARK — Public Accuracy Ledger",
    "meta.title.about": "BLACKDARK — About",
    # About page
    "about.title": "About BlackDark",
    "about.lead": (
        "Institutional-grade market intelligence built for clarity, not noise — "
        "one clear Act or Wait decision backed by transparent evidence."
    ),
    "about.p1": (
        "BlackDark is an institutional-grade market intelligence platform built for clarity, not noise. "
        "It delivers one clear Act or Wait decision on major crypto assets, backed by transparent evidence "
        "and a public accuracy ledger that publishes both hits and misses."
    ),
    "about.p2": (
        "Unlike traditional dashboards that overwhelm users with endless charts, BlackDark focuses on a single, "
        "actionable signal supported by three key factors, a sealed decision certificate, and verifiable outcomes "
        "after 24 hours. Every decision is logged, resolved, and made public so users can verify performance themselves."
    ),
    "about.capabilities.title": "Core Capabilities",
    "about.capability.1": "Single-sentence Oracle decisions with live freshness and factor breakdown",
    "about.capability.2": "Public Accuracy Ledger with hash-chained proof of hits and misses",
    "about.capability.3": "Trust Pulse for real-time Act/Wait signals under five seconds",
    "about.capability.4": "Sealed Prediction Markets with timed certificates and public resolution",
    "about.capability.5": "Verified Miss Bounty for reported model errors with subscription credit",
    "about.capability.6": "Arb Opportunities for cross-venue price discrepancies (paid users)",
    "about.capability.7": "Discipline Mirror for private follow-vs-override tracking",
    "about.capability.8": "Decision Certificates with shareable proof",
    "about.capability.9": "Glass Box Challenge for public verification",
    "about.capability.10": "Multi-language support across 25 languages",
    "about.capability.11": "Institutional-grade data provenance and audit trail",
    "about.disclaimer": (
        "BlackDark is an analytical research tool. It is not financial advice. All outcomes, including misses, "
        "are published on the Public Accuracy Ledger for independent verification."
    ),
    "about.follow": "Follow us",
    "about.explore": "Explore",
    # Nav
    "nav.home": "Home",
    "nav.oracle": "Oracle",
    "nav.features": "Features",
    "nav.pricing": "Pricing",
    "nav.about": "About",
    "nav.accuracy": "Accuracy",
    "nav.login": "Login",
    "nav.signup": "Sign up",
    "nav.profile": "Profile",
    "nav.account_menu": "Account menu",
    "nav.logout": "Sign out",
    "nav.logout_failed": "Could not sign out. Try again.",
    "nav.dashboard": "Dashboard",
    "nav.platform": "Platform",
    "nav.capabilities": "Capabilities",
    "nav.funds": "Funds",
    "nav.compliance": "Compliance",
    "nav.portfolio": "Portfolio",
    "nav.stealth": "Stealth",
    "nav.try_oracle": STR_TRY_ORACLE_FREE,
    "nav.verify_accuracy": "Verify Accuracy",
    "nav.search.label": "Search site",
    "nav.search.placeholder": "Search",
    "lang.label": "Language",
    "lang.choose": "Choose language",
    # Launch / hero
    "launch.banner": "Launch Offer: 7-Day Pro Trial FREE on signup — code LAUNCHPRO for 14 days ·",
    "launch.register": "Register Now",
    "hero.badge": "Launch Live — 7-Day Pro Trial FREE",
    "hero.tagline": "One clear decision",
    "hero.sub": "Single-sentence Oracle with public verifiable accuracy — for beginners, pros, and whales.",
    "hero.stat.verdict": "Oracle verdict",
    "hero.stat.sources": "Live data sources",
    "hero.stat.free": "10 queries/day",
    "hero.cta.oracle": STR_TRY_ORACLE_FREE,
    "hero.cta.telegram": "Telegram — 3 Free Alerts/Day",
    "hero.cta.accuracy": "Live Accuracy",
    "stats.visitors": "Visitors",
    "stats.users": "Users",
    "stats.subscribers": "Subscribers",
    "stats.telegram": "Telegram",
    "stats.waitlist": "Waitlist",
    "waitlist.title": "Get early access to Trust OS",
    "waitlist.sub": "Join the waitlist for launch updates. No fake seat counters — just a clear path to Prove.",
    "waitlist.email_aria": "Enter your email",
    "waitlist.email_placeholder": "Enter your email",
    "waitlist.submit": "Join Waitlist",
    "waitlist.stats_aria": "Platform activity",
    "waitlist.page.title": "Join waitlist",
    "waitlist.page.h1": "Join the waitlist",
    "waitlist.page.body": "Launch updates for Trust OS — no fake seat counters. Counts on the homepage load from live /api/analytics/stats.",
    "waitlist.page.back": "← Back to homepage",
    "waitlist.page.submit": "Join",
    "waitlist.msg.submitting": "Submitting…",
    "waitlist.msg.error": "Could not join — try again.",
    "waitlist.msg.network": "Network error — try again.",
    "waitlist.msg.generic": "Something went wrong.",
    "waitlist.msg.welcome": "Welcome! You are #{position} on the waitlist.",
    # Telegram block
    "tg.title": "Telegram Free Alerts",
    "tg.badge": "3/day free",
    "tg.body": "Subscribe in Telegram — get top arbitrage + Oracle signals. No credit card.",
    "tg.open": "Open Telegram Bot",
    "tg.accuracy": "See AI Accuracy",
    "tg.commands": "Commands: /start · /status · /accuracy · /stop",
    "tg.start_free_suffix": "Start Free",
    # Oracle demo
    "oracle.title": "BLACKDARK Oracle",
    "oracle.field.audience": "Audience",
    "oracle.field.experience": "Experience",
    "oracle.field.symbol": "Symbol",
    "oracle.mode.decision_pro": "Decision Pro",
    "oracle.freshness.title": "Data freshness",
    "oracle.live": "Live",
    "oracle.audience.retail": "Retail",
    "oracle.audience.pro": "Pro",
    "oracle.audience.whale": "Whale",
    "oracle.audience.fund": "Fund",
    "oracle.mode.beginner": "Beginner",
    "oracle.mode.pro": "Pro",
    "oracle.get_decision": "Get Decision",
    "oracle.cta.retail": "Get one clear Act / Wait decision — no dashboard tourism.",
    "oracle.placeholder": "One clear decision — act or wait",
    "oracle.loading": "Getting your decision…",
    "oracle.error": "Could not get a decision right now. Try again.",
    "oracle.analyzing": "Analyzing…",
    "oracle.share.title": "Share Your Signal",
    "oracle.share.sub": "Spread the oracle verdict — viral growth fuels the dark side",
    "oracle.share.copy": "Copy Link",
    "oracle.share.facebook": "Facebook",
    "oracle.share.instagram": "Instagram",
    "oracle.share.whatsapp": "WhatsApp",
    "oracle.share.telegram": "Telegram",
    "oracle.share.reddit": "Reddit",
    "oracle.share.copied": "Copied!",
    "oracle.factor.spot_reference_price": "Spot reference price",
    "oracle.factor.change_24h": "24h price change",
    "oracle.factor.quote_volume_24h": "24h quote volume",
    "oracle.source.binance_ws": "Binance WebSocket top-of-book",
    "oracle.source.binance_rest": "Binance spot REST",
    "oracle.source.binance_spot": "Binance spot",
    "oracle.source.coinbase": "Coinbase Exchange (public)",
    "oracle.source.kraken": "Kraken spot (public)",
    "oracle.source.live_market": "live market",
    "oracle.source.model": "model",
    "oracle.source.oracle": "oracle",
    "oracle.source.context": "context",
    "trust.factor.opportunity_score": "Opportunity score {score}",
    "trust.factor.score_pending": "Score pending",
    "trust.factor.detail.composite": "Composite Trust OS score from live market context",
    "trust.factor.move_24h": "24h move {change}",
    "trust.factor.detail.move": "Short-horizon price change on the watched pair",
    "trust.factor.regime": "Regime {regime}",
    "trust.factor.detail.regime": "Regime label from unified context",
    "trust.grasp.top_reasons": "Top reasons — under five seconds",
    "action.ACT": "ACT",
    "action.WAIT": "WAIT",
    "action.CONDITIONS_MET": "CONDITIONS MET",
    "action.ABSTAIN": "ABSTAIN",
    "action.CAUTION": "CAUTION",
    # Features
    "features.title": "Built around the Oracle",
    "features.sub": "Everything supports one job: a clear crypto decision in under 30 seconds.",
    "features.oracle.title": "AI Oracle",
    "features.oracle.body": "Buy · Wait · Stay out — 0–100 score, narrative, support/resistance, and forecast context.",
    "features.whale.title": "Whale & CVVD",
    "features.whale.body": "Cross-venue volume signals folded into the Oracle verdict — not a separate product.",
    "features.radar.title": "Market Radar",
    "features.radar.body": "Top movers by volume — pick a symbol, send it to Oracle in one click.",
    "features.tg.title": "Telegram Alerts",
    "features.tg.body": "In-app inbox has no TradingView-style hard cap. Free: 3 Oracle alerts/day on Telegram. Pro adds unlimited Oracle + chat.",
    "features.pro_note": "Pro also includes AI Chat, Portfolio AI, and advanced tools.",
    "features.b2b": "Institutional feed →",
    # Pricing
    "pricing.title": "Choose Your Edge",
    "pricing.sub": "Start free. Upgrade when you're ready to dominate.",
    "pricing.free": "Free",
    "pricing.pro": "Pro",
    "pricing.whale": "Whale",
    "pricing.month": "/month",
    "pricing.cta.free": "Start Free",
    "pricing.cta.pro": "Go Pro",
    "pricing.cta.whale": "Go Whale",
    "pricing.free.f1": "Oracle 10×/day",
    "pricing.free.f2": STR_PUBLIC_ACCURACY_LEDGER,
    "pricing.free.f3": "Decision Certificate",
    "pricing.pro.f1": "Unlimited Oracle",
    "pricing.pro.f2": "Arbitrage scanner",
    "pricing.pro.f3": "AI Chat + alerts",
    "pricing.whale.f1": "Everything in Pro",
    "pricing.whale.f2": "B2B feed + Evidence Pack",
    "pricing.whale.f3": "Stealth Execution Advisor",
    # Dashboard
    "dash.hero.sub": "One clear decision — act or wait · public verifiable accuracy",
    "dash.stealth": "Stealth Advisor",
    "dash.portfolio": "Portfolio AI",
    "dash.chart": "Live Chart",
    "dash.refresh": "Refresh",
    "dash.radar": "Market Radar",
    "dash.arb": "Arbitrage",
    "dash.whales": "Whale Radar",
    "dash.guest": "Guest · Free",
    "dash.upgrade": "Beginner · $9.99/mo",
    "dash.symbol": "Symbol",
    "dash.stealth.sub": "Whale audience · advisory slice sizing — not a stealth-routing guarantee",
    "dash.portfolio.sub": "Risk in plain language — private holdings stay in-browser",
    "dash.intent.question": "What do you need?",
    "dash.intent.hint": "Four doors — Decide · Verify · My book · Alerts. Analytical tool, not advice.",
    # Login
    "login.trial": "7-Day Pro Trial on signup — code LAUNCHPRO = 14 days",
    "login.tab.login": "Login",
    "login.tab.register": "Register",
    "login.email": "Email",
    "login.pass_label": "Passcode",
    "login.password": "Passcode",
    "login.remember": "Remember me",
    "login.confirm_password": "Confirm password",
    "auth.signup_submit": "Sign up",
    "auth.divider_email": "or continue with email",
    "login.name": "Name",
    "login.pass_hint": "Passcode (8+ chars)",
    "login.submit": "Login",
    "login.create": "Create Account",
    "login.home": "← Home",
    # Accuracy / prove-it
    "accuracy.title": STR_PUBLIC_ACCURACY_LEDGER,
    "accuracy.sub": "Don't trust us. Verify us. — labeled predictions with public outcomes.",
    "accuracy.prove": "Prove it",
    # Common
    "common.loading": "Loading…",
    "common.retry": "Try again",
    "common.not_advice": "Not financial advice. Verify claims on the Public Accuracy Ledger.",
    "common.anti_hype": "Anti-Hype",
    "common.legal": "Legal",
    "common.contact": "Contact",
    "common.docs": "Docs",
    "footer.rights": "© 2026 BLACKDARK",
    # Decision sentence templates ({asset} {score})
    KEY_DECISION_ACT: "ACT on {asset} — score {score}.",
    KEY_DECISION_WAIT: "WAIT on {asset} — score {score}.",
    "decision.clear_act": "Clear opportunity on {asset}: score {score}/100.",
    "decision.clear_wait": "WAIT on {asset} — score {score}/100. Estimated net after costs ~{net}.",
    "decision.rejected": "Rejected: not executable after real costs.",
    "decision.veto": "Sources contradict — stay flat.",
    "decision.net": "Estimated net after costs ~${net}.",
    # DTS cross-cutting presentation keys (DTS-055)
    "dts.state.available": "Available",
    "dts.state.degraded": "Degraded",
    "dts.state.abstained": "Abstained",
    "dts.state.rejected": "Rejected",
    "dts.state.unavailable": "Unavailable",
    "dts.action.no_decision": "NO DECISION",
    "dts.why.admitted": "Opportunity admitted — all mandatory gates passed.",
    "dts.why.generic_blocked": "This opportunity did not pass ({state}).",
    "dts.why.net_edge": "Expected net edge: {bps} bps after costs.",
    "dts.why.execution": "Execution feasibility score: {score}.",
    "dts.why.freshness": "Input freshness is insufficient for a confident decision.",
    "dts.why.conflict": "Sources conflict — abstaining rather than forcing a decision.",
    "dts.why.blocking": "Blocking reasons: {reasons}.",
    "dts.why.invalidation": "Invalidation condition: {condition}.",
    "dts.no_decision.abstained": "NO DECISION — insufficient evidence to admit this opportunity.",
    "dts.no_decision.rejected": "NO DECISION — rejected ({reasons}).",
    "dts.no_decision.degraded": "NO DECISION — degraded confidence; mandatory safety conditions not fully met.",
    "dts.rejection.summary": "Opportunity rejected after economic, execution, and evidence evaluation.",
    "dts.abstention.summary": "Opportunity abstained — evidence or freshness insufficient.",
    "dts.risk.pre_impact": "Portfolio pre-impact warning",
    "dts.risk.main": "Main risk",
    "dts.evidence.grade": "Evidence grade",
    "dts.evidence.class": "Evidence class",
    "dts.calibration.insufficient": "Calibration insufficient data",
    "dts.calibration.weak": "Calibration weak",
    "dts.simulation.disclosure": "Historical/simulated — no future guarantee. Methodology version: {version}.",
    "dts.safety_floor.message": "Safety floor evaluation",
    "dts.cost_autopsy.label": "Cost autopsy",
    "dts.execution.feasibility": "Execution feasibility",
    "dts.daily.what_changed": "What changed",
    "dts.daily.why_matters": "Why it matters",
    "dts.daily.risks": "Risks / invalidation",
    "dts.trail.view": "View evidence trail",
    "dts.thirty_second.grasp": "30-second decision grasp",
    "dts.command_view.title": "Command view",
    "dts.hero.my_capital": "My capital",
    "dts.hero.market_state": "Market state",
    "dts.hero.best_opportunity": "Best verified opportunity",
    "dts.hero.main_risk": "Main risk",
    "dts.hero.smart_money": "Smart money / evidence",
    "dts.hero.daily_brief": "Today's decision brief",
    "dts.reason.freshness_gate_failed": "Freshness gate failed",
    "dts.reason.net_edge_truth_reject": "Net edge below threshold after costs",
    "dts.reason.execution_feasibility_low": "Execution feasibility too low",
    "dts.reason.portfolio_risk_reject": "Portfolio risk limits exceeded",
    "dts.reason.portfolio_risk_abstain": "Portfolio risk context requires abstention",
    "dts.reason.uncertainty_too_high": "Uncertainty too high for admission",
    "dts.reason.data_quality_below_floor": "Data quality below required floor",
    "dts.reason.evidence_class_insufficient": "Evidence class insufficient",
    "dts.reason.calibration_weak": "Calibration too weak for confident decision",
    "dts.reason.generic": "Mandatory gate failure: {code}",
    "dts.surface.unknown": "NO DECISION — insufficient evidence",
    "dts.surface.stale": "STALE INPUT",
    "dts.surface.conflict": "SOURCE CONFLICT",
    "dts.surface.insufficient": "INSUFFICIENT EVIDENCE",
    "dts.a11y.state_available": "Decision state: available",
    "dts.a11y.state_rejected": "Decision state: rejected",
    "dts.a11y.state_abstained": "Decision state: abstained",
    "dts.a11y.state_degraded": "Decision state: degraded",
    "dts.a11y.state_unavailable": "Decision state: unavailable",
    "dts.a11y.no_decision": "No decision issued",
    "dts.a11y.chart_alt": "Chart data summary: {summary}",
    "upgrade.pro_hint": "Switch to Pro to unlock Net-Edge Truth Score and Opportunity Half-Life.",
    "compliance.lead": "Engineering posture and overclaim denylist — not a license or SOC2 certificate.",
    "docs.title": "Public Developer Docs",
    "docs.lead": "Evidence and read APIs only. Analytical tool — not financial advice. Secrets and live execution writes are not exposed here.",
    "docs.btn.ledger": "Public Accuracy Ledger",
    "docs.btn.misses": "Public misses",
    "docs.btn.capabilities": "Capabilities",
    "docs.btn.status": "System status",
    "docs.integrators": "Machine-readable OpenAPI/JSON exports are available to signed-in integrators — request access via contact.",
    "docs.h2.primary": "Primary prove-it surfaces",
    "docs.h2.prefixes": "Allowed public prefixes",
    "docs.prefixes.lead": "Prefix allowlist for anonymous visitors (read/evidence). POST-only hero APIs are listed separately below.",
    "docs.h2.post_only": "POST-only (not in read list)",
    "docs.post_only.line": "— not a GET endpoint",
    "docs.h2.policy": "Policy",
    "docs.architecture": "Architecture index: ARCHITECTURE.md · Canon: four value layers · six heroes · no FalconAI 16-platform valuation.",
    "docs.anti_hype": "Anti-Hype · Not financial advice · Verify claims on the Public Accuracy Ledger.",
    "discipline.title": "Discipline Mirror",
    "discipline.sub": "Private habit surface — not the public ledger.",
    "discipline.nav.oracle": "Oracle",
    "discipline.h2.current_decision": "Current Oracle decision",
    "discipline.loading_decision": "Loading today’s decision…",
    "discipline.follow_question": "Did you follow this model state?",
    "discipline.btn.yes_followed": "Yes — I followed",
    "discipline.btn.no_overrode": "No — I overrode",
    "discipline.oracle_unavailable": "Oracle decision unavailable — try again from Dashboard.",
    "discipline.oracle_unavailable_short": "Oracle decision unavailable.",
    "discipline.system_state": "{symbol} · system state: {action}",
    "discipline.model_state_fallback": "Model state: {action} on {symbol}.",
    "discipline.answer_recorded": "Answer recorded for this Oracle decision.",
    "discipline.loading_mirror": "Loading private mirror…",
    "discipline.mirror_signin": "Mirror unavailable — sign in required.",
    "discipline.mirror_unavailable": "Mirror unavailable",
    "discipline.metric.answers": "Answers",
    "discipline.metric.followed": "followed",
    "discipline.metric.overridden": "overridden",
    "discipline.metric.follow_rate": "Follow rate",
    "discipline.msg.summary": "Answers: {total} · followed {followed} · overridden {overridden}",
    "discipline.no_answers": "No answers yet.",
    "discipline.row.system": "system",
    "discipline.row.followed": "followed",
    "discipline.row.overrode": "overrode",
    "discipline.saving": "Saving…",
    "discipline.save_failed": "Could not save answer.",
    "discipline.saved_private": "Saved privately — only you can see your Discipline Mirror.",
    "discipline.compliance": "Anti-Hype · Private coaching metrics · Not financial advice · Not shown on the public ledger.",
    "discipline.open_dashboard": "Open Dashboard",
    "utility.skip_content": "Skip to content",
    "utility.nav.dashboard": "Dashboard",
    "utility.nav.faq": "FAQ",
    "utility.nav.accuracy": "Accuracy",
    "utility.nav.contact": "Contact",
    # Sealed Trust OS landing (binding 2026-08-08)
    "nav.prove": "Prove",
    "nav.operate": "Operate",
    "nav.desk": "Desk",
    "nav.room": "Room",
    "nav.verify": "Verify",
    "nav.open_proof": "Open Proof",
    "hero.headline": "We publish the miss.",
    "hero.support": "Sealed forecasts before the event. Public proof after.",
    "hero.cta.try": STR_TRY_ORACLE_FREE,
    "hero.cta.seal": "See the Seal",
    "pulse.label": "TRUST PULSE",
    "pulse.live": "Live",
    "pulse.loading": "Loading today’s decision…",
    "pulse.sentence": "One clear Act / Wait — reviewable, not a mystery score.",
    "pulse.open_full": "Open full proof",
    "pulse.share": "Share Proof",
    "pulse.refreshing": "Refreshing…",
    "pulse.updated": "Updated",
    "pulse.foot": "Decide. Prove it. Share it. · Four-layer legal shield · Not financial advice · Hits and misses published",
    "seal.title": "The Seal",
    "seal.body": "Before the move, the forecast is sealed. After the event, hits and misses go public on the Ledger. No mystery score. No fake scarcity.",
    "seal.s1.title": "01 · Seal",
    "seal.s1.body": "A decision is committed with a certificate hash you can share — sealed before the outcome.",
    "seal.s2.title": "02 · Prove",
    "seal.s2.body": "Trust Pulse shows one live Act / Wait with Why under five seconds — research only, not advice.",
    "seal.s3.title": "03 · Publish the miss",
    "seal.s3.body": "The Public Accuracy Ledger posts outcomes, including misses. Don't trust us. Verify us.",
    "seal.cta.ledger": "Verify Ledger",
    "seal.cta.proof": "Open live proof",
    "lenses.title": "Feature division — four lenses, one Trust OS",
    "lenses.sub": "Not separate platforms. One product remembered as Prove → Operate → Desk → Room.",
    "lenses.prove.title": "Prove",
    "lenses.prove.body": "DISCOVER / FREE ($0): public Prove surface + daily decision limit.",
    "lenses.operate.title": "Operate",
    "lenses.operate.body": "Beginner ($9.99/mo): Watchlist, alerts, decision log, compare, offline.",
    "lenses.desk.title": "Desk",
    "lenses.desk.body": "Pro ($29/mo) and Desk ($79/mo): charts, share, API & export.",
    "lenses.room.title": "Room",
    "lenses.room.body": "SCALE THE EDGE / INSTITUTIONAL (from $999/mo): Data Room, SSO/MFA, SLA — Talk to us.",
    "workspace.watchlist.title": "Watchlist",
    "workspace.watchlist.sub": "Track symbols locally — latest Oracle quick decision per row (stored on this device).",
    "workspace.watchlist.add_symbol_aria": "Add symbol to watchlist",
    "workspace.watchlist.placeholder": "e.g. BTC",
    "workspace.watchlist.add": "Add",
    "workspace.watchlist.compare": "Compare",
    "workspace.watchlist.remove": "Remove {symbol}",
    "workspace.decisions.title": "My Decisions",
    "workspace.decisions.sub": "Last 50 Oracle decisions on this device (symbol, action, score, time, cert hash).",
    "workspace.compare.title": "Compare assets",
    "workspace.compare.sub": "Pick 2–3 symbols — same Oracle quick data.",
    "workspace.compare.close": "Close",
    "workspace.share.title": "Share decision",
    "workspace.share.copy": "Copy",
    "workspace.share.close": "Close",
    "workspace.share.text_aria": "Decision text to copy",
    "workspace.toast.offline": "Offline",
    "workspace.toast.unavailable": "Unavailable",
    "workspace.toast.last_known": "Offline · last known · {action}",
    "workspace.toast.score": "score",
    "dash.tp.sentence_fallback": "One clear decision — research only.",
    "dash.tp.why_title": "Why (under 5 seconds)",
    "dash.tp.factors_loading": "Why factors loading…",
    "dash.tp.unavailable": "Unavailable",
    "dash.tp.oracle_unavailable": "Oracle quick unavailable for this symbol.",
    "dash.tp.command_home_unavailable": "Launch-57 command home unavailable.",
    "dash.tp.offline_last_known": "Offline · last known",
    "dash.live": "Live",
    "dash.offline_last_known": "Offline · last known",
    "dash.lens.promise": "Prove → Operate → Desk → Room — Decide… and prove it.",
    "dash.tp.connecting": "Connecting…",
    "dash.tp.loading_decision": "Loading decision…",
    "dash.tp.sentence_placeholder": "One clear Act / Wait with a reviewable why.",
    "dash.tp.chart_note": "TradingView Lightweight Charts · loading…",
    "dash.tp.open_full_proof": "Open full proof",
    "dash.tp.share_proof": "Share Proof",
    "dash.tp.share_decision": "Share Decision",
    "dash.tp.anti_hype_on": "Anti-Hype ON",
    "dash.tp.anti_hype_banner": "Market price and 24h change hidden. Sentence, factors, and ledger proof stay visible.",
    "dash.tp.foot": "Anti-Hype · Not financial advice · AI cannot guarantee returns",
    "dash.tp.trust_pulse_aria": "Trust Pulse",
    "dash.tp.symbol_aria": "Trust Pulse symbol",
    "dash.tp.price_chart_aria": "Trust Pulse price chart",
    "dash.intent.decide": "Decide",
    "dash.intent.decide_hint": "Launch-57 command home — Act/Wait + Why + Proof.",
    "dash.intent.verify": "Verify",
    "dash.intent.verify_hint": "Public Accuracy Ledger — hits and misses.",
    "dash.intent.my_book": "My book",
    "dash.intent.my_book_hint": "Portfolio risk — Operate+ lens.",
    "dash.intent.alerts": "Alerts",
    "dash.intent.alerts_hint": "Inbox after Launch-57 gates.",
    "dash.ux.beginner": "Beginner",
    "dash.ux.pro": "Pro",
    "dash.nav.since_you_left": "Since You Left",
    "dash.nav.miss_feed": "Miss Feed",
    "dash.nav.coverage_honesty": "Coverage Honesty",
    "dash.nav.my_book": "My book",
    "dash.nav.desk_tools": "Desk tools",
    "dash.nav.desk_tools_aria": "Desk tools",
    "dash.nav.corpus_passport": "Corpus Passport",
    "dash.desk.stealth_title": "Stealth Execution Advisor",
    "dash.desk.stealth_sub": "Size-aware execution slices",
    "dash.desk.whales_title": "Signal vs Noise",
    "dash.desk.whales_sub": "Whale flow labels",
    "dash.desk.half_life_title": "Half-Life Clock",
    "dash.desk.half_life_sub": "Desk timing grounded",
    "dash.desk.mev_title": "MEV Protection",
    "dash.desk.mev_sub": "Execution risk report",
    "dash.desk.open_lens": "Open Desk lens",
    "dash.since.title": "Since You Left — Top 3",
    "dash.since.sub": "What changed since your last visit",
    "dash.since.loading": "Loading continuity…",
    "dash.since.open_full": "Open full page",
    "dash.data_spine.title": "Data Spine",
    "dash.data_spine.sub": "Launch-57 prices, freshness, provenance, and connector — claims hidden when unavailable.",
    "dash.data_spine.loading": "Loading data spine…",
    "dash.chart.interval_aria": "Chart interval",
    "dash.chart.note": "Launch-57 OHLCV (#23) — chart hidden if bars unavailable.",
    "dash.oi.title": "Open Interest",
    "dash.arb.title": "Arbitrage Engine",
    "dash.arb.scanning": "Scanning…",
    "dash.arb.live_scan": "Live Scan",
    "dash.whales.title": "Whale Intelligence · Signal vs Noise",
    "dash.whales.sub": "Transfers ≠ Trades — classifier labels SIGNAL / NOISE / HEDGED in one sentence",
    "dash.operate.title": "Operate digest",
    "dash.operate.sub": "Daily research brief + subscriber value — DECIDE / PRO and above",
    "dash.operate.refresh_report": "Refresh daily report",
    "dash.operate.refresh_value": "Refresh value",
    "dash.operate.markdown": "Markdown",
    "dash.operate.load_report": "Pro/Whale — load daily report",
    "dash.operate.load_value": "Pro/Whale — subscriber value",
    "dash.portfolio.title": "Portfolio AI",
    "dash.portfolio.hero_sub": "Risk in plain language — Hero #4 · private holdings stay in-browser",
    "dash.portfolio.amount": "Amount",
    "dash.portfolio.add": "Add",
    "dash.portfolio.analyze": "Analyze",
    "dash.portfolio.empty": "Add holdings, then analyze",
    "dash.half_life.title": "Half-Life Heat Clock",
    "dash.half_life.sub": "SEE THE EDGE / ELITE · seconds = money · urgency bands from Opportunity Half-Life",
    "dash.half_life.refresh": "Refresh clock",
    "dash.half_life.kill_rate": "Kill-Rate Board",
    "dash.half_life.committee": "Committee One-Pager",
    "dash.half_life.open_desk": "Open Desk lens and refresh.",
    "dash.stealth.title": "Stealth Execution Advisor",
    "dash.stealth.desk_sub": "Whale audience · advisory slice labels (SLICE_* / LIMIT_CLIP_ADVISORY) — not live TWAP/VWAP/SOR",
    "dash.stealth.side": "Side",
    "dash.stealth.buy": "Buy",
    "dash.stealth.sell": "Sell",
    "dash.stealth.advise": "Advise",
    "dash.stealth.empty": "Enter size and run advisor",
    "dash.mev.title": "MEV / Sandwich Report",
    "dash.mev.sub": "Shareable risk posture — prove the drag, don’t hype private mempool alpha",
    "dash.mev.build": "Build report",
    "dash.mev.copy": "Copy share text",
    "dash.mev.empty": "Generate a shareable MEV report",
    "dash.news.title": "Market headlines",
    "dash.news.sub": "U.S. Fed, SEC & CFTC press RSS — titles link to the publisher (not investment advice).",
    "dash.news.loading": "Loading headlines…",
    "dash.alerts.title": "Alerts",
    "dash.alerts.sub": "In-app inbox: no TradingView-style 15-alerts / 3-min hard cap · only Truth + Half-Life survivors fire",
    "dash.alerts.price_title": "Simple price alerts",
    "dash.alerts.price_sub": "Above/below spot (Binance public feed). Stored on this device ID — non-custodial, no auto-trading.",
    "dash.alerts.direction": "Direction",
    "dash.alerts.above": "Price above",
    "dash.alerts.below": "Price below",
    "dash.alerts.target": "Target USD",
    "dash.alerts.add": "Add alert",
    "dash.alerts.check": "Check prices",
    "dash.alerts.none": "No price alerts yet.",
    "dash.alerts.refresh_inbox": "Refresh Inbox",
    "dash.alerts.test_tg": "Test Telegram",
    "dash.chat.title": "AI Chat",
    "dash.chat.sub": "Operate+ · explains the current decision context — does not replace the Oracle or guarantee outcomes",
    "dash.chat.gate": "AI Chat is on DECIDE / PRO and paid tiers above.",
    "dash.chat.start_pro": "Start DECIDE / PRO",
    "dash.chat.placeholder": "Ask about BTC, ETH, or the latest Oracle context…",
    "dash.chat.input_placeholder": "What should I do with BTC?",
    "dash.chat.send": "Send",
    "dash.gate.operate_title": "Requires Operate subscription",
    "dash.gate.view_pricing": "View pricing",
    "dash.gate.close": "Close",
    "dash.js.route_unavailable": "Route unavailable",
    "dash.js.spine_unavailable": "Data spine unavailable — no live claims shown.",
    "dash.js.no_market_rows": "No market rows",
    "dash.js.daily_pro_required": "Decision Pro required for daily report Markdown",
    "dash.js.evidence": "Evidence: {ev}",
    "dash.js.net_edge": "Net-Edge: {score}",
    "dash.js.verify_ledger": "Verify Ledger",
    "dash.js.ledger_public_honesty": "Public accuracy ledger — verify hits and misses.",
    "dash.js.ledger_grounded_label": "Launch-57 grounded",
    "dash.js.stale_never_live_honesty": "Stale or unknown data is never presented as live.",
    "dash.js.factor_freshness_gate": "Freshness gate",
    "dash.js.factor_abstain": "Abstain",
    "dash.js.factor_oracle": "Oracle",
    "dash.js.cert_prefix": "cert",
    "dash.js.id_prefix": "id",
    "dash.js.veto_chip": "Veto",
    "dash.js.new_factors": " · New factors: {factors}",
    "dash.js.decision_pro": "Decision Pro",
    "dash.js.chart_unavailable": "Chart unavailable — no OHLCV from Binance or fallback.",
    "dash.js.daily_pro_report": "Decision Pro required for daily report",
    "dash.js.daily_brief_title": "Daily research brief",
    "dash.js.brief_ready": "Brief ready — open Markdown for full detail.",
    "dash.js.daily_foot": "Research brief, not advice · Verify Ledger",
    "dash.js.subscriber_value": "Subscriber value · {tier}",
    "dash.js.calls_30d": "Calls 30d: {calls} · Risk warnings: {warnings}",
    "dash.js.subscriber_foot": "Illustrative usage math · Not guaranteed ROI",
    "dash.js.pro_whale_value": "Pro/Whale required for subscriber value",
    "dash.js.oi_asset": "Asset",
    "dash.js.oi_col": "OI",
    "dash.js.oi_funding": "Funding",
    "dash.js.no_oi": "No OI data",
    "dash.js.arb_live_stats": "Live · Cross {cross} · Executable {exec} · Profitable {prof}",
    "dash.js.arb_cross_stats": "Cross {cross} · Executable {exec} · Profitable {prof}",
    "dash.js.rejected": "REJECTED",
    "dash.js.truth_hl": "Truth {truth} · HL {hl}s",
    "dash.js.live_scan_progress": "Live scan in progress…",
    "dash.js.pro_required_arb": "Pro required",
    "dash.js.upgrade_arb": "Upgrade required for arbitrage",
    "dash.js.no_opportunities": "No opportunities now",
    "dash.js.scan_failed": "Scan failed",
    "dash.js.refreshing_inbox": "Refreshing inbox…",
    "dash.js.inbox_status": "Inbox {unread} unread · {note} · works without Telegram",
    "dash.js.inbox_empty": "No alerts yet — inbox has no TradingView-style 15/3min hard cap",
    "dash.js.inbox_unavailable": "Inbox unavailable",
    "dash.js.alert_default": "Alert",
    "dash.js.read": "read",
    "dash.js.tap_mark_read": "new · tap to mark read",
    "dash.js.inbox_card_foot": "Truth + Half-Life gated · Not financial advice",
    "dash.js.triggered": "triggered",
    "dash.js.condition_met": "condition met",
    "dash.js.remove": "Remove",
    "dash.js.no_headlines": "No headlines available right now.",
    "dash.js.headlines_unavailable": "Headlines unavailable.",
    "dash.js.price_alerts_unavailable": "Price alerts unavailable.",
    "dash.js.whale_scanning": "Scanning…",
    "dash.js.whale_one_sentence": "One sentence · Signal vs Noise",
    "dash.js.no_whale": "No whale narratives",
    "dash.js.whale_foot": "Whale labels are classified, not guaranteed alpha · Not financial advice · Verify on Public Accuracy Ledger",
    "dash.js.no_deltas": "No deltas yet",
    "dash.js.continuity_unavailable": "Continuity unavailable",
    "dash.js.opened_share": "Opened share",
    "dash.js.copy_blocked": "Copy blocked",
    "dash.js.entry_rail_aria": "Primary entries",
    "dash.js.oracle_accuracy": "Oracle accuracy {pct}%",
    "dash.js.moat": "Moat {score}/100",
    "dash.js.whale_alerts_24h": "Whale alerts {n}",
    "dash.js.arb_alerts_24h": "Arb alerts {n}",
    "dash.js.decision_certificate": "Decision Certificate",
    "dash.js.now_price": " · now ${price}",
    "dash.js.below": "below",
    "dash.js.above": "above",
    "dash.js.live_word": "Live",
    "dash.js.inbox_note_default": "no TV-style 15/3min hard cap",
    "dash.js.sandwich_drag": "Est. sandwich drag ~{bps} bps (~${usd})",
    "dash.js.portfolio_analyze_empty": "Add holdings first",
    "dash.js.portfolio_result_unavailable": "Portfolio analysis unavailable",
    "dash.js.stealth_unavailable": "Stealth advisor unavailable",
    "dash.js.mev_copied": "MEV share text copied",
    "dash.js.half_life_unavailable": "Half-life clock unavailable",
    "dash.js.chat_thinking": "Thinking…",
    "dash.js.upgrade_pro_short": "Upgrade Pro",
    "dash.js.view_pricing": "View pricing",
    "dash.js.anti_hype_on_btn": "Anti-Hype ON",
    "dash.js.open_link": "Open",
    "dash.js.refreshing_clock": "Refreshing clock…",
    "dash.js.building": "Building…",
    "dash.js.report_unavailable": "Report unavailable",
    "dash.js.advising": "Advising…",
    "dash.js.advisor_unavailable": "Advisor unavailable",
    "dash.js.covers_plan": " · covers plan: {yes}",
    "dash.js.covers_yes": "yes",
    "dash.js.covers_not_yet": "not yet",
    "dash.js.intent_fallback": "Launch-57 only — Decide · Verify · My book · Alerts.",
    "dash.js.refreshing_chart": "Refreshing chart…",
    "dash.js.chart_lib_loading": "Chart library still loading — try Refresh again.",
    "dash.js.portfolio_add_holding": "Add at least one holding",
    "dash.js.portfolio_enter_amount": "Enter a positive amount, then Add.",
    "dash.js.portfolio_sign_in_required": "Sign in with an Operate+ plan to run Portfolio AI analysis.",
    "dash.js.portfolio_upgrade_required": "Portfolio AI requires Beginner (Operate) or above — upgrade in Profile & Billing.",
    "dash.js.portfolio_analysis_unavailable": "Portfolio analysis unavailable",
    "dash.js.portfolio_ai_unavailable": "Portfolio AI unavailable",
    "dash.js.portfolio_risk": "{level} risk ({score}/10)",
    "dash.js.marked_value": "Marked value {value} · BTC corr {corr}",
    "dash.js.alert_status_unavailable": "Alert status unavailable",
    "dash.js.telegram_configured": "Telegram bot configured — connect via /login",
    "dash.js.telegram_token_missing": "Set TELEGRAM_BOT_TOKEN to enable alerts",
    "dash.js.telegram_sent": "Sent!",
    "dash.js.telegram_failed": "Failed",
    "dash.js.telegram_test_failed": "Test failed — configure bot first",
    "dash.js.alert_generosity_title": "Alert generosity",
    "dash.js.operate_unlock": "Operate to unlock",
    "dash.js.stealth_th_index": "#",
    "dash.js.stealth_th_usd": "USD",
    "dash.js.stealth_th_delay": "Delay",
    "dash.js.stealth_th_offset": "Offset",
    "dash.js.stealth_th_algo": "Algo",
    "dash.js.stealth_plan": "Plan · {algo} · window {window}s · interval {interval}s · offset {offset} bps",
    "dash.js.stealth_slices": "{n} slices × ${slice} · urgency {urgency}",
    "dash.js.mev_report_title": "MEV Report",
    "dash.js.whale_funding": "Funding {rate}",
    "dash.js.whale_oi": " · OI {oi}",
    "dash.js.cert_pending": "pending",
    "dash.js.half_life_desk": "Launch-57 command home · {freshness} · {action} — desk timing grounded (no legacy oracle fetch).",
    "dash.js.entry_decide_hint": "Act/Wait + Proof",
    "lenses.cta": "Open the lenses",
    "prove.title": "Prove · Decide",
    "prove.sub": "One clear Act/Wait + Why + shareable Proof Card. Four lenses: Prove → Operate → Desk → Room.",
    "feat.pulse.title": "Trust Pulse",
    "feat.pulse.body": "One live Act / Wait with Why under five seconds — the first thing you see, every time.",
    "feat.cert.title": "Decision Certificate",
    "feat.cert.body": "Shareable Proof Card with verify link. Dual-coded: text + visual state — not a mystery score.",
    "feat.ledger.title": STR_PUBLIC_ACCURACY_LEDGER,
    "feat.ledger.body": "Hits and misses published. Don't trust us — verify us.",
    "feat.operate.title": "Operate depth",
    "feat.operate.body": "DECIDE / PRO unlocks daily habit, Portfolio AI, alerts, and AI Chat — without Free watermark.",
    "feat.note": "Five depths on one ladder — DISCOVER free, then PRO, ELITE, QUANT, INSTITUTIONAL Talk to us.",
    "pricing.title_os": "One Trust OS. Five depths.",
    "pricing.sub_os": "DISCOVER → DECIDE → SEE THE EDGE → EXECUTE THE EDGE → SCALE THE EDGE. Reviewable decisions + shareable proof — not charts or mystery scores.",
    "pricing.discover_free": "DISCOVER / FREE",
    "pricing.decide_pro": "Beginner",
    "pricing.see_edge_elite": "Pro",
    "pricing.execute_quant": "EXECUTE THE EDGE / QUANT",
    "pricing.scale_institutional": "SCALE THE EDGE / INSTITUTIONAL",
    "pricing.proof_pass": "DISCOVER / FREE",
    "pricing.decision_pro": "Beginner",
    "pricing.decision_desk": "Desk",
    "pricing.institutional": "SCALE THE EDGE / INSTITUTIONAL",
    "pricing.mo": "/month",
    "pricing.mo_usd": "/month USD",
    "pricing.or_year": "or",
    "pricing.year_suffix": "/year",
    "pricing.from_open": "From $999/mo",
    "pricing.proof_promise": "Public Prove surface + daily decision limit — honest $0 entry.",
    "pricing.pro_promise": "Daily verified habit after trial — unlimited certified decisions.",
    "pricing.elite_promise": "Edge tools + evidence packaging for serious desks.",
    "pricing.quant_promise": "Quant depth — backtesting, API scale, systematic workflows.",
    "pricing.desk_promise": "Edge + packaging to convince someone else.",
    "pricing.inst_promise": "Talk to us · not self-serve checkout · sales-led Room lens.",
    "pricing.trial_note": "7-day trial · cancel anytime before charge",
    "pricing.popular": "MOST POPULAR",
    "pricing.cta.free_signup": "Start free — Sign up",
    "pricing.cta.trial": "Start 7-day trial",
    "pricing.cta.elite": "Start ELITE trial",
    "pricing.cta.quant": "Start QUANT trial",
    "pricing.cta.desk": "Get ELITE",
    "pricing.cta.talk": "Talk to us",
    "pricing.cta.b2b": "B2B Data Feed",
    "pricing.pay_note": "",
    "pricing.manage": "Manage plan anytime from Profile & Billing.",
    "login.lead": "Login or create an account. Email + passcode. 7-day paid trial on signup.",
    "login.tab.signup": "Sign up",
    "auth.forgot_pass": "Forgot passcode?",
    "auth.forgot_username": "Forgot username?",
    "auth.google": "Continue with Google",
    "auth.google_slow": "Google sign-in is taking longer than usual. Use email below or try again.",
    "auth.google_redirecting": "Opening Google…",
    "auth.github": "Continue with GitHub",
    "auth.or_email": "or email",
    "auth.create": "Create account",
    "auth.accept_terms": "I accept the Terms, Privacy, and Risk Disclaimer. Not financial advice.",
    "profile.meta_title": "BLACKDARK — Profile",
    "profile.title": "Your profile",
    "profile.loading": "Loading…",
    "profile.gate_prefix": "Please",
    "profile.gate_login": "log in",
    "profile.gate_or": "or",
    "profile.gate_register": "create an account",
    "profile.gate_suffix": "to manage profile and billing.",
    "profile.avatar_alt": "Avatar",
    "profile.upload_label": "Upload avatar (JPEG/PNG/WebP ≤ 2MB)",
    "profile.upload_btn": "Upload",
    "profile.initials_btn": "Use initials",
    "profile.section.profile": "Profile",
    "profile.section.security": "Security",
    "profile.section.plan": "Plan",
    "profile.display_name": "Display name",
    "profile.username": "Public username (@handle for Proof Cards)",
    "profile.ui_lang": "UI language",
    "profile.ux_mode": "UX mode",
    "profile.ux_mode.beginner": "Beginner",
    "profile.ux_mode.pro": "Advanced",
    "profile.timezone": "Timezone",
    "profile.telegram": "Telegram chat ID (alerts)",
    "profile.save": "Save profile",
    "profile.resend_verify": "Resend verification email",
    "profile.current_password": "Current password (blank if OAuth-only / setting first password)",
    "profile.new_password": "New password (10+)",
    "profile.update_password": "Update password",
    "profile.mfa_enable": "Enable MFA (TOTP)",
    "profile.mfa_confirm_label": "Confirm MFA code",
    "profile.mfa_confirm_placeholder": "Confirm MFA code to enable",
    "profile.mfa_confirm_btn": "Confirm MFA",
    "profile.mfa_disable_label": "Disable MFA code",
    "profile.mfa_disable_placeholder": "Code to disable MFA",
    "profile.mfa_disable_btn": "Disable MFA",
    "profile.logout_all": "Log out all sessions",
    "profile.plan.plus_cta": "Plus · $29/mo",
    "profile.plan.pro_cta": "Pro · $49/mo",
    "profile.plan.enterprise_cta": "Enterprise",
    "profile.manage_billing": "Manage billing",
    "profile.compare_plans": "Compare all plans",
    "profile.plan.free": "Free",
    "profile.plan.plus": "Plus",
    "profile.plan.pro": "Pro",
    "profile.plan.enterprise": "Enterprise",
    "profile.email_verified": "verified",
    "profile.email_pending": "verification pending",
    "profile.verify_ok": "Email verified.",
    "profile.verify_pending": "Verify your email to harden account recovery.",
    "profile.mfa_on_pill": "MFA on",
    "profile.mfa_off_pill": "MFA off",
    "profile.mfa_on_hint": "Authenticator MFA is enabled.",
    "profile.mfa_off_hint": "Optional TOTP MFA — recommended for paid accounts.",
    "profile.current_plan": "Current plan: {plan}.",
    "profile.current_plan_status": "Current plan: {plan} · {status}",
    "profile.msg.email_verified": "Email verified.",
    "profile.msg.welcome_plus": "Welcome — your Plus trial is active.",
    "profile.msg.welcome_free": "Welcome — your Free plan is ready.",
    "profile.msg.welcome_default": "Welcome — complete your profile.",
    "profile.msg.saved": "Saved.",
    "profile.msg.save_failed": "Save failed",
    "profile.msg.choose_file": "Choose a file first",
    "profile.msg.avatar_updated": "Avatar updated",
    "profile.msg.upload_failed": "Upload failed",
    "profile.msg.initials_avatar": "Using initials avatar",
    "profile.msg.failed": "Failed",
    "profile.msg.password_updated": "Password updated — other sessions revoked.",
    "profile.msg.sent": "Sent",
    "profile.msg.mfa_enabled": "MFA enabled",
    "profile.msg.mfa_disabled": "MFA disabled",
    "profile.msg.enroll_failed": "Enroll failed",
    "profile.msg.mfa_scan_prefix": "Scan/provision secret:",
    "profile.msg.portal_unavailable": "Billing portal unavailable right now.",
    "auth.gate.title": "Account required",
    "auth.gate.body": "This surface needs a signed-in session. {hint}",
    "auth.gate.profile_hint": "Sign in to manage identity, security, and your plan.",
    "auth.gate.login": "Login",
    "auth.gate.signup": "Sign up",
    "auth.gate.home": "← Back to homepage",
    "auth.gate.prove_link": "Open public Prove demo",
    "auth.gate.prove_note": "on the homepage — no account needed.",
    "auth.gate.lens_suffix": "lens",
    "pricing.public.title": "Pricing — BLACKDARK",
    "pricing.public.headline": "One Trust OS. Four depths.",
    "pricing.public.subhead": "Reviewable decisions and shareable proof — not mystery scores. Not financial advice.",
    "pricing.public.compare": "Compare plans",
    "pricing.public.capability": "Capability",
    "pricing.public.enterprise_title": "For companies and funds",
    "pricing.public.enterprise_lead": "Enterprise is sales-led — Data Room, compliance pack, SSO/MFA, and SLA. Not financial advice.",
    "pricing.public.work_email": "Work email",
    "pricing.public.name": "Name",
    "pricing.public.firm": "Firm",
    "pricing.public.use_case": "Use case",
    "pricing.public.talk_to_us": "Talk to us",
    "pricing.public.profile_billing": "Profile & Billing",
    "pricing.public.refund_policy": "Refund Policy",
    "pricing.public.custom": "Custom",
    "pricing.public.col.free": "Free",
    "pricing.public.col.plus": "Plus",
    "pricing.public.col.pro": "Pro",
    "pricing.public.col.enterprise": "Enterprise",
    "pricing.public.tier.free.name": "Free",
    "pricing.public.tier.free.f1": "Trust Pulse + Act/Wait with Why",
    "pricing.public.tier.free.f2": "Public Accuracy Ledger (hits and misses)",
    "pricing.public.tier.free.f3": "Shareable Decision Certificate",
    "pricing.public.tier.free.f4": "Limited daily Oracle decisions",
    "pricing.public.tier.free.f5": "Free Proof watermark",
    "pricing.public.tier.free.cta": "Start free",
    "pricing.public.tier.plus.name": "Plus",
    "pricing.public.tier.plus.f1": "Everything in Free",
    "pricing.public.tier.plus.f2": "Higher daily decision ceiling",
    "pricing.public.tier.plus.f3": "Since-you-left continuity",
    "pricing.public.tier.plus.f4": "Portfolio AI + alerts",
    "pricing.public.tier.plus.f5": "AI Chat without Free watermark",
    "pricing.public.tier.plus.cta": "Start 7-day trial",
    "pricing.public.tier.pro.name": "Pro",
    "pricing.public.tier.pro.f1": "Everything in Plus",
    "pricing.public.tier.pro.f2": "Whale Signal vs Noise",
    "pricing.public.tier.pro.f3": "Stealth advisory views",
    "pricing.public.tier.pro.f4": "Evidence Pack + API priority",
    "pricing.public.tier.pro.f5": "Arbitrage scanner depth",
    "pricing.public.tier.pro.cta": "Upgrade to Pro",
    "pricing.public.tier.enterprise.name": "Enterprise",
    "pricing.public.tier.enterprise.f1": "Data Room + compliance pack",
    "pricing.public.tier.enterprise.f2": "SSO / enforced MFA",
    "pricing.public.tier.enterprise.f3": "SLA + integration addendum",
    "pricing.public.tier.enterprise.f4": "Dedicated onboarding",
    "pricing.public.tier.enterprise.cta": "Talk to us",
    "pricing.public.compare.r1": "Trust Pulse + Verify on Ledger",
    "pricing.public.compare.r2": "Decision Certificate / Free Proof",
    "pricing.public.compare.r3": "Public Accuracy Ledger",
    "pricing.public.compare.r4": "Unlimited certified Oracle",
    "pricing.public.compare.r5": "Portfolio AI + alerts",
    "pricing.public.compare.r6": "Stealth + Evidence Pack",
    "pricing.public.compare.r7": "Data Room + SSO / SLA",
    "pricing.public.inquiry.received": "Received",
    "pricing.public.inquiry.failed": "Failed",
    "pricing.public.inquiry.unavailable": "Inquiry unavailable right now.",
    # Dashboard / landing runtime UI (client-side via BD_I18N)
    "meta.title.dashboard_room": "BLACKDARK — Trust OS Decision Room",
    "ui.score": "Score",
    "ui.confidence": "Confidence",
    "ui.mode": "Mode",
    "ui.lang_label": "Lang",
    "ui.analyzing": "Analyzing…",
    "ui.could_not_analyze": "Could not analyze {symbol}",
    "ui.scenarios": "Scenarios (sketch)",
    "ui.why_top3": "Why (Top 3) — under five seconds",
    "ui.why_unavailable": "Factor breakdown unavailable on this response — score still shown.",
    "ui.pending": "pending",
    "ui.copied": "Copied!",
    "ui.copy_certificate": "Copy certificate",
    "ui.copy_certificate_text": "Copy certificate text",
    "ui.download_txt": "Download TXT",
    "ui.download_json": "Download JSON",
    "ui.certificate_label": "Certificate",
    "ui.prediction_id": "prediction_id",
    "ui.scenarios_title": "Scenarios",
    "ui.copy_cert_id_title": "Copy certificate ID",
    "ui.veto": "Contradiction Veto",
    "ui.do_not_touch": "WAIT / Do Not Touch",
    "ui.abstain": "Abstain",
    "ui.decision_certificate": "Decision Certificate",
    "ui.switch_pro": "Switch to Pro",
    "ui.proof": "Proof",
    "ui.public_accuracy": "Public accuracy",
    "ui.discipline_mirror": "Open private Discipline Mirror",
    "ui.upgrade_pro": "Upgrade to Pro",
    "ui.trust_pulse_live": "Trust Pulse · one live decision you can verify",
    "ui.truth": "Truth",
    "ui.half_life": "Half-Life",
    "ui.regime": "Regime",
    "ui.signal": "Signal",
    "ui.evidence_drawer": "Evidence drawer · Certificate + scenarios",
    "ui.copy": "Copy",
    "ui.share_x": "Share X",
    "ui.share_tg": "Share TG",
    "ui.teaser": "Teaser",
    "ui.unavailable": "Unavailable",
    "ui.loading_daily": "Loading daily report…",
    "ui.daily_unavailable": "Daily report unavailable",
    "ui.loading_value": "Loading value…",
    "ui.value_unavailable": "Value digest unavailable",
    "ui.logout": "Logout",
    "ui.upgrade": "Upgrade",
    "ui.start_trial": "Start 7-Day Trial",
    "ui.you": "You",
    "ui.ai": "AI",
    "ui.chat_unavailable": "Chat unavailable right now — try again or use Get Decision.",
    "ui.no_reply": "No reply",
    "ui.operate_required": "Operate+ required",
    "ui.stale": "Stale — not live",
    "ui.live": "Live",
    "ui.freshness_unknown": "Freshness unknown",
    "ui.freshness_unknown_not_live": "Freshness unknown — not live",
    "ui.not_presented_as_live": "Not presented as live",
    "ui.oracle_quick_unavailable": "Oracle quick unavailable",
    "ui.chat_upgrade_pro": "Upgrade to Decision Pro for AI Chat.",
    "ui.nothing_to_share": "Nothing to share",
    "ui.shared": "Shared!",
    "ui.updating_live_decision": "Updating live decision…",
    "ui.updating_label": "Updating…",
    "ui.launch57_blocked": "Launch-57 blocked — not live-eligible.",
    "ui.near_live": "NEAR LIVE",
    "ui.reconnecting": "Reconnecting…",
    "ui.live_stream": "Live stream on",
    "ui.trust_pulse_unavailable": "Trust Pulse unavailable — use Get Decision below.",
    "ui.one_clear_decision": "One clear decision — research only.",
    "ui.why_under5": "Why (under 5 seconds)",
    "ui.verified_ledger": "Verified on Ledger",
    "ui.proof_copied": "Proof text copied",
    "ui.no_factors": "No factor breakdown on this response",
    "ui.oracle_unavailable": "Oracle unavailable — try BTC or ETH.",
    "ui.discipline_saved": "Saved privately — only you can see your Discipline Mirror.",
    "ui.discipline_fail": "Could not save answer.",
    "ui.quota_exceeded": "Daily quota exceeded — upgrade",
    "ui.asset": "Asset",
    "ui.verdict": "Verdict",
    "ui.id": "ID",
    "ui.oi": "OI",
    "ui.funding": "Funding",
    "a11y.skip_trust_pulse": "Skip to Trust Pulse",
    "a11y.trust_pulse": "Trust Pulse",
    "pulse.stale": "Stale — not live",
    "pulse.verify_ledger": "Verify on Ledger",
    "pulse.free_proof": "Free Proof",
    "pulse.no_cert": "No certificate yet.",
    "pulse.cert_prefix": "cert",
    "pulse.fallback_sentence": "One clear Act / Wait — reviewable.",
    "pulse.share_default": "BLACKDARK Trust Pulse — one Act/Wait decision you can verify",
    "pulse.conditions_met_review": (
        "Analytical state only - the model's stated conditions are currently met. "
        "No transaction or investment action is recommended."
    ),
    "pulse.model_state": "MODEL STATE: {action} — {symbol}.",
    "pulse.model_state_conditions": "MODEL STATE: CONDITIONS MET — {symbol}. {review}",
    "pulse.drawer.title": "Decision Certificate · Trust Pulse",
    "pulse.drawer.open_ledger": "Open proof on ledger",
    "pulse.drawer.close": "Close",
    "pulse.msg.cert_text_copied": "Certificate text copied.",
    "pulse.msg.cert_id_copied": "Certificate ID copied.",
    "pulse.msg.cert_hash_copied": "Certificate hash copied.",
    "pulse.msg.copy_cert_id_failed": "Could not copy certificate ID.",
    "pulse.msg.copy_unsupported": "Copy not supported in this browser.",
    "pulse.msg.no_cert_hash": "No certificate hash yet — use Get Decision below.",
    "pulse.msg.no_cert_pulse": "No Decision Certificate for this pulse yet. Use Get Decision below to generate signed proof.",
    "pulse.chip.copy_hash_title": "Copy certificate hash",
    "pulse.chip.free_pending": "Free Proof — certificate pending",
    "seal.stamp_prefix": "Seal ·",
    "footer.col.product": "Product",
    "footer.col.trust": "Trust",
    "footer.col.company": "Company",
    "footer.col.legal": "Legal",
    "footer.follow": "Follow us",
    "footer.tagline": "Trust OS — Decide. Prove it. Share it.",
    "footer.story": "Prove → Operate → Desk → Room",
    "footer.ledger": "Ledger",
    "footer.status": "Status",
    "footer.disclaimer": (
        "Four-layer legal shield active. Not financial advice. AI cannot guarantee returns. "
        "Verify on the Public Accuracy Ledger."
    ),
    "footer.link.trust_pulse": "Trust Pulse",
    "footer.link.decide": "Decide",
    "footer.link.verify": "Verify",
    "footer.link.dashboard": "Dashboard",
    "footer.link.pricing": "Pricing",
    "footer.link.profile": "Profile & Billing",
    "footer.link.chat": "AI Chat",
    "footer.link.about": "About",
    "footer.link.contact": "Contact",
    "social.link.x": "X",
    "social.link.reddit": "Reddit",
    "social.link.facebook": "Facebook",
    "social.link.telegram": "Telegram",
    "social.link.linkedin": "LinkedIn",
    "social.join_telegram_alerts": "Join Telegram Alerts",
    "ledger.hero.badge": "LIVE · PUBLIC AUDIT",
    "ledger.hero.title": "BLACKDARK — Public Oracle Accuracy",
    "ledger.hero.engine_rules": "rules engine",
    "ledger.hero.engine_checking": "Checking…",
    "ledger.hero.lead": (
        "Every decision is logged, resolved after 24 hours, and feeds the learning model. "
        "Live engine:"
    ),
    "ledger.hero.alias": "We publish hits and misses. Alias:",
    "ledger.cta.verify_chain": "Verify Audit Chain",
    "ledger.cta.misses": "Public misses / errors",
    "ledger.cta.glass": "Transparency challenge",
    "ledger.cta.mirror": "Discipline Mirror",
    "ledger.cta.docs": "Developer docs",
    "ledger.proof_chain.title": "Proof Chain",
    "ledger.proof_chain.loading": "Loading chain…",
    "ledger.footer": "BLACKDARK — market-data and analytical technology · public outcome ledger (not exhaustive coverage)",
    "ledger.cta.dashboard": "Open Dashboard",
    "ledger.cta.json_api": "JSON API",
    "ledger.cta.evidence": "Evidence Pack",
    "ledger.cta.bounty_log": "Miss Bounty Log",
    "ledger.cta.sealed_markets": "Sealed Markets",
    "ledger.cta.audit_challenge": "Audit Challenge",
    "ledger.cta.mev_report": "MEV Report",
    "ledger.cta.locked_predictions": "Locked Predictions",
    "ledger.panel.sealed_title": "Sealed Prediction Markets",
    "ledger.panel.sealed_lead": (
        "Oracle Act/Wait decisions sealed before the 24h outcome — stake on correctness "
        "(max 50 USDT, 5% fee on losing pool)."
    ),
    "ledger.panel.sealed_all": "All sealed markets",
    "ledger.panel.arb_title": "Arb Opportunities",
    "ledger.panel.arb_lead": "Cross-exchange spreads from the latest scan — display only, not execution.",
    "ledger.panel.arb_empty": "No arb opportunities right now.",
    "ledger.panel.arb_loading": "Loading arb opportunities…",
    "ledger.panel.arb_unavailable": "Arb scan unavailable — try again shortly.",
    "ledger.panel.arb_status": "{count} opportunities shown (display only)",
    "ledger.panel.defi_title": "DeFi market context (DefiLlama)",
    "ledger.panel.defi_lead": (
        "Public TVL, 24h protocol fees, and yield pools — no API key. "
        "Macro context only; not a trade signal."
    ),
    "ledger.panel.defi_loading": "Loading DeFi context…",
    "ledger.panel.defi_unavailable": "DeFi context unavailable — try again shortly.",
    "ledger.panel.defi_empty": "No DeFi highlights for this asset right now.",
    "ledger.panel.defi_status": "{symbol} · total DeFi TVL {total}",
    "ledger.panel.defi_chain_tvl": "{chain} chain TVL {tvl}",
    "ledger.panel.defi_chain_row": "Chain {name}: {tvl} TVL",
    "ledger.panel.defi_fee_row": "Fees 24h · {name}: {fees}",
    "ledger.panel.defi_yield_row": "Yield · {project} ({symbol}): {apy}% APY",
    "ledger.panel.btc_fees_title": "Bitcoin network fees (mempool.space)",
    "ledger.panel.btc_fees_lead": "Public recommended sat/vB fees and block tip — no API key. Context for on-chain cost, not a fee quote.",
    "ledger.panel.btc_fees_loading": "Loading Bitcoin fee data…",
    "ledger.panel.btc_fees_unavailable": "Bitcoin fee data unavailable — try again shortly.",
    "ledger.panel.btc_fees_status": "Block height {height} · fastest {fast} sat/vB",
    "ledger.panel.btc_fees_row": "{label}: {value} sat/vB",
    "ledger.panel.fred_title": "U.S. macro context (FRED)",
    "ledger.panel.fred_lead": "Inflation, policy rate, GDP, and 10Y yield from the Federal Reserve — requires server FRED_API_KEY.",
    "ledger.panel.fred_loading": "Loading macro indicators…",
    "ledger.panel.fred_unavailable": "Macro data unavailable — FRED key not configured or quota exceeded.",
    "ledger.panel.fred_row": "{title}: {value} ({date})",
    "ledger.panel.fred_cpi_row": "CPI YoY: {yoy}% (index {value}, {date})",
    "nav.how_it_works": "How it works",
    "nav.swap": "Swap",
    "nav.wallet_balance": "Balance",
    "swap.page_title": "Non-custodial swap",
    "swap.lead": (
        "Swap via ChangeNOW partner API (revenue share — no subscription). "
        "You deposit directly to ChangeNOW; BLACKDARK never holds your funds."
    ),
    "swap.non_custodial": "Non-custodial",
    "swap.fee_note": "Partner commission on completed swaps. Not financial advice.",
    "swap.from": "From",
    "swap.to": "To",
    "swap.amount": "Amount to send",
    "swap.payout_address": "Your payout wallet address",
    "swap.estimate": "Get estimate",
    "swap.create": "Create swap (get deposit address)",
    "ledger.panel.locked_title": "Locked Predictions · Glass Box",
    "ledger.panel.mev_title": "Shareable MEV / Sandwich Report",
    "ledger.panel.misses_title": "Public Misses · Errors",
    "ledger.panel.misses_banner": "We publish misses publicly — verify on the ledger. Hits and incorrect model states are logged after resolution.",
    "ledger.panel.misses_summary_aria": "Verified miss statistics",
    "ledger.panel.misses_verified_label": "Verified errors (live count)",
    "ledger.panel.misses_partial_label": "Partial outcomes",
    "ledger.panel.misses_rate_label": "Miss + partial rate (resolved)",
    "ledger.panel.misses_recent_title": "Latest public misses",
    "ledger.panel.misses_col_asset": "Asset",
    "ledger.panel.misses_col_verdict": "Verdict",
    "ledger.panel.misses_col_outcome": "Outcome",
    "ledger.panel.misses_col_time": "Time (UTC)",
    "ledger.panel.misses_col_action": "Bounty",
    "ledger.panel.misses_lead": "Same Public Accuracy Ledger as the table below. Alias route:",
    "ledger.panel.verified_errors": "Verified errors we own",
    "ledger.panel.partial_outcomes": "Partial outcomes",
    "ledger.panel.audit_title": "Audit Challenge — Prove us wrong",
    "ledger.panel.audit_lead": "Find a real break in the hash chain. We publish the full ledger — including misses.",
    "ledger.panel.transparency_link": "Read transparency challenge",
    "ledger.panel.anti_hype_misses": (
        "Anti-Hype · Not financial advice. Past misses do not predict future results."
    ),
    "ledger.panel.anti_hype_audit": (
        "Anti-Hype · Not financial advice. Verify the chain yourself — trust is optional."
    ),
    "bounty.rules_banner": (
        "Verified Miss Bounty: paid subscribers may claim 20% off one month when a verified miss "
        "meets the rules (manual review, max 3 approvals/day site-wide)."
    ),
    "bounty.claim_btn": "Claim Miss Bounty",
    "bounty.claim_tooltip": "Claim 20% off one month",
    "bounty.modal.title": "Claim Miss Bounty",
    "bounty.modal.sub": "20% off one subscription month · not cash/USDT · manual review within 48h",
    "bounty.modal.decision_link": "Decision link",
    "bounty.modal.source_a_url": "Source A URL (close price)",
    "bounty.modal.source_a_close": "Source A closing price",
    "bounty.modal.source_b_url": "Source B URL (different domain)",
    "bounty.modal.source_b_close": "Source B closing price",
    "bounty.modal.cancel": "Cancel",
    "bounty.modal.submit": "Submit claim",
    "bounty.modal.submitting": "Submitting…",
    "bounty.modal.failed": "Claim failed",
    "bounty.modal.network_error": "Network error",
    "bounty.log.title": "Verified Miss Bounty Log",
    "bounty.log.lead": (
        "Public record of accepted and rejected bounty claims. Reward:"
    ),
    "bounty.log.reward": "20% off one subscription month",
    "bounty.log.reward_note": "(not cash or USDT). No personal data is published.",
    "bounty.log.back": "← Public Accuracy Ledger",
    "bounty.log.loading": "Loading…",
    "bounty.log.status_count": "{count} published outcomes",
    "bounty.log.no_claims": "No published claims yet.",
    "bounty.log.table_empty": "No claims yet.",
    "bounty.log.load_error": "Could not load log.",
    "bounty.log.table_error": "Error loading log.",
    "bounty.log.col.ref": "Ref",
    "bounty.log.col.asset": "Asset",
    "bounty.log.col.decision_id": "Decision ID",
    "bounty.log.col.status": "Status",
    "bounty.log.col.decided": "Decided",
    "bounty.log.col.note": "Note",
    "meta.title.bounty_log": "BLACKDARK — Miss Bounty Log",
    "sealed.title": "Sealed Prediction Markets",
    "sealed.lead": (
        "Every Oracle Act/Wait decision is sealed with a certificate hash before the 24h outcome. "
        "Stake up to 50 USDT (internal ledger credits). Winners share the losing pool after a 5% platform fee."
    ),
    "sealed.back_ledger": "Public Accuracy Ledger",
    "sealed.active_heading": "Active (betting open)",
    "sealed.settled_heading": "Settled / closed",
    "sealed.loading": "Loading…",
    "sealed.none_active": "No active markets.",
    "sealed.none_settled": "No settled markets yet.",
    "sealed.load_fail": "Failed to load markets.",
    "sealed.card.pool": "Pool {pool} USDT · {bettors} bettors",
    "sealed.card.open": "Open decision market →",
    "sealed.decision.title": "Sealed Oracle Market",
    "meta.title.sealed_markets": "BLACKDARK — Sealed Markets",
    "sealed.panel.status": "{active} active · {settled} recent settled",
    "sealed.panel.empty": "No sealed markets yet — created with each new Oracle decision.",
    "sealed.panel.unavailable": "Sealed markets unavailable",
    "sealed.panel.view": "view",
    "arb.btn": "View Arb Opportunities",
    "arb.panel.lead": "Cross-exchange spreads (display only · max 5)",
    "arb.loading": "Loading…",
    "arb.none": "No arb opportunities for this symbol right now.",
    "arb.auth_required": "Sign in with a paid plan to view spreads.",
    "arb.spread_line": "{buy} → {sell}: {spread}%",
    "ledger.js.missing": "missing",
    "ledger.js.no_scored": "No verified scored rows in the live ledger yet.",
    "ledger.js.no_misses": "No verified errors or partial outcomes in the live ledger yet.",
    "ledger.js.partial_tag": "partial outcome",
    "ledger.js.verified_error": "verified error",
    "ledger.js.no_verified_sample": "No verified errors in the latest live miss sample.",
    "ledger.js.no_partial_sample": "No partial outcomes in the latest live miss sample.",
    "ledger.js.losing_status": (
        "Live ledger · {source} · {verified} verified errors · {partial} partial outcomes · "
        "showing {errors} verified + {partials} partial from latest miss sample"
    ),
    "ledger.js.locked_status": (
        "Sealed forecasts · locked={locked} · revealed={unlocked} · Glass Box cadence"
    ),
    "ledger.js.locked_empty": "No locked predictions yet — seal before the next major macro event.",
    "ledger.js.copy_share": "Copy share text",
    "arb.none_symbol": "No spreads for {symbol} right now.",
    "arb.panel.lead_dashboard": "Cross-exchange spreads — display only (max 5). Not execution.",
    "arb.load_fail": "Could not load arb opportunities.",
}



# Per-locale overlays. Every locale should cover EN keys; missing → EN fallback.
_TRANSLATIONS: dict[str, dict[str, str]] = {
    "zh-CN": {
        "meta.description": "BLACKDARK — 一句 Act/Wait 神谕决策，附可验证公开准确率账本。别相信我们，来验证我们。",
        "meta.title.home": "BLACKDARK — AI 加密情报平台",
        "meta.title.dashboard": "BLACKDARK — 情报仪表盘",
        "meta.title.login": "BLACKDARK — 登录",
        "meta.title.accuracy": "BLACKDARK — 公开准确率账本",
        "nav.home": "首页", "nav.oracle": "神谕", "nav.features": "功能", "nav.pricing": "定价",
        "nav.accuracy": "准确率", "nav.login": "登录", "nav.logout": "退出", "nav.dashboard": "仪表盘",
        "nav.platform": "平台", "nav.capabilities": "能力", "nav.funds": "基金", "nav.compliance": "合规",
        "nav.portfolio": "组合", "nav.stealth": "隐身执行", "nav.try_oracle": "免费试用神谕",
        "nav.verify_accuracy": "验证准确率", "lang.label": "语言", "lang.choose": "选择语言",
        "launch.banner": "上线优惠：注册即送 7 天 Pro 试用 — 使用 LAUNCHPRO 可获 14 天 ·",
        "launch.register": "立即注册", "hero.badge": "已上线 — 7 天 Pro 免费试用",
        "hero.tagline": "一个清晰决策", "hero.sub": "单句神谕 + 可验证公开准确率 — 适合新手、专业与巨鲸。",
        "hero.stat.verdict": "神谕结论", "hero.stat.sources": "实时数据源", "hero.stat.free": "每日 10 次查询",
        "hero.cta.oracle": "免费试用神谕", "hero.cta.telegram": "Telegram — 每日 3 条免费提醒",
        "hero.cta.accuracy": "实时准确率", "stats.visitors": "访客", "stats.users": "用户",
        "stats.subscribers": "订阅者", "stats.telegram": "Telegram", "stats.waitlist": "候补名单",
        "tg.title": "Telegram 免费提醒", "tg.badge": "每日 3 条免费", "tg.body": "在 Telegram 订阅 — 获取套利与神谕信号。无需信用卡。",
        "tg.open": "打开 Telegram 机器人", "tg.accuracy": "查看 AI 准确率", "tg.commands": "命令：/start · /status · /accuracy · /stop",
        "oracle.title": "BLACKDARK 神谕", "oracle.live": "实时", "oracle.audience.retail": "零售",
        "oracle.audience.pro": "专业", "oracle.audience.whale": "巨鲸", "oracle.audience.fund": "基金",
        "oracle.mode.beginner": "新手", "oracle.mode.pro": "专业", "oracle.get_decision": "获取决策",
        "oracle.cta.retail": "一个清晰的 Act / Wait 决策 — 不做仪表盘观光。",
        "oracle.placeholder": "一个清晰决策 — 行动或等待", "oracle.loading": "正在获取决策…",
        "oracle.error": "暂时无法获取决策，请重试。", "oracle.analyzing": "分析中…",
        "oracle.share.title": "分享你的信号", "oracle.share.sub": "传播神谕结论", "oracle.share.copy": "复制链接",
        "action.ACT": "行动", "action.WAIT": "等待",
        "features.title": "围绕神谕构建", "features.sub": "一切只为一件事：30 秒内给出清晰加密决策。",
        "features.oracle.title": "AI 神谕", "features.oracle.body": "买入 · 等待 · 观望 — 0–100 分数、叙事与支撑阻力。",
        "features.whale.title": "巨鲸与 CVVD", "features.whale.body": "跨所成交量信号并入神谕结论 — 不是单独产品。",
        "features.radar.title": "市场雷达", "features.radar.body": "按成交量的热门币 — 一键送入神谕。",
        "features.tg.title": "Telegram 提醒", "features.tg.body": "免费：每日 3 条神谕提醒。Pro 含无限神谕与聊天。",
        "features.pro_note": "Pro 还包含 AI 聊天、组合 AI 与高级工具。", "features.b2b": "机构数据源 →",
        "pricing.title": "选择你的优势", "pricing.sub": "免费开始。准备好后再升级。",
        "pricing.free": "免费", "pricing.pro": "Pro", "pricing.whale": "Whale", "pricing.month": "/月",
        "pricing.cta.free": "免费开始", "pricing.cta.pro": "升级 Pro", "pricing.cta.whale": "升级 Whale",
        "pricing.free.f1": "神谕每日 10 次", "pricing.free.f2": "公开准确率账本", "pricing.free.f3": "决策证书",
        "pricing.pro.f1": "无限神谕", "pricing.pro.f2": "套利扫描", "pricing.pro.f3": "AI 聊天 + 提醒",
        "pricing.whale.f1": "包含全部 Pro", "pricing.whale.f2": "B2B 源 + 证据包", "pricing.whale.f3": "隐身执行顾问",
        "dash.hero.sub": "一个清晰决策 — 行动或等待 · 可验证公开准确率",
        "dash.stealth": "隐身顾问", "dash.portfolio": "组合 AI", "dash.chart": "实时图表", "dash.refresh": "刷新",
        "dash.radar": "市场雷达", "dash.arb": "套利", "dash.whales": "巨鲸雷达", "dash.guest": "访客 · 免费",
        "dash.upgrade": "Pro $29/月", "dash.symbol": "交易对",
        "dash.stealth.sub": "巨鲸受众 · 切片建议 — 不是实盘隐身路由保证",
        "dash.portfolio.sub": "通俗风险说明 — 持仓仅保存在浏览器",
        "login.trial": "注册即送 7 天 Pro — 代码 LAUNCHPRO = 14 天",
        "login.tab.login": "登录", "login.tab.register": "注册", "login.email": "邮箱", "login.pass_label": "密码",
        "login.name": "姓名", "login.pass_hint": "密码（至少 8 位）", "login.submit": "登录",
        "login.create": "创建账户", "login.home": "← 首页",
        "accuracy.title": "公开准确率账本", "accuracy.sub": "别相信我们。来验证我们。 — 带公开结果的标注预测。",
        "accuracy.prove": "去验证", "common.loading": "加载中…", "common.retry": "重试",
        "common.not_advice": "非投资建议。请在公开准确率账本上验证主张。",
        "common.anti_hype": "反炒作", "common.legal": "法律", "common.contact": "联系", "common.docs": "文档",
        "footer.rights": "© 2026 BLACKDARK",
        KEY_DECISION_ACT: "对 {asset} 采取行动 — 分数 {score}。",
        KEY_DECISION_WAIT: "对 {asset} 等待 — 分数 {score}。",
        "decision.clear_act": "{asset} 机会明确：分数 {score}/100。",
        "decision.clear_wait": "对 {asset} 等待：分数 {score}/100。",
        "decision.rejected": "已拒绝：扣除真实成本后不可执行。",
        "decision.veto": "信源冲突 — 保持观望。",
        "decision.net": "估计净收益约 ${net}。",
        "upgrade.pro_hint": "切换到 Pro 以解锁净优势真相分与机会半衰期。",
        "compliance.lead": "工程合规姿态与过度声明黑名单 — 不是牌照或 SOC2 证书。",
    },
}


def _fill_from_map(mapping: dict[str, str]) -> dict[str, str]:
    """Build full locale dict from partial mapping over EN keys."""
    out = dict(EN)
    out.update(mapping)
    return out


def _locales_dir() -> Path:
    return Path(__file__).resolve().parent / "locales"


def _overrides_dir() -> Path:
    return _locales_dir() / "overrides"


_LOCALE_OVERRIDES: dict[str, dict[str, str]] | None = None


def _locale_override_strings(code: str) -> dict[str, str]:
    global _LOCALE_OVERRIDES
    if _LOCALE_OVERRIDES is None:
        merged: dict[str, dict[str, str]] = {}
        odir = _overrides_dir()
        if odir.is_dir():
            for path in odir.glob("*.json"):
                try:
                    data = json.loads(path.read_text(encoding="utf-8"))
                    if isinstance(data, dict):
                        merged[path.stem] = {str(k): str(v) for k, v in data.items()}
                except Exception:
                    continue
        _LOCALE_OVERRIDES = merged
    return _LOCALE_OVERRIDES.get(normalize_lang(code), {})


def _load_json_catalog(code: str) -> dict[str, str] | None:
    path = _locales_dir() / f"{code}.json"
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return {str(k): str(v) for k, v in data.items()}
    except Exception:
        return None
    return None


def _hydrate_en_from_json_file() -> None:
    """Server t() reads EN; locales/en.json is shipped in Docker — keep them aligned."""
    overlay = _load_json_catalog("en")
    if overlay:
        EN.update(overlay)


_hydrate_en_from_json_file()


def _build_all() -> dict[str, dict[str, str]]:
    """Assemble locale catalogs from locales/*.json with EN fallback for missing keys."""
    catalogs: dict[str, dict[str, str]] = {"en": dict(EN)}
    for code in LOCALES:
        if code == "en":
            continue
        loaded = _load_json_catalog(code)
        if loaded:
            cat = dict(EN)
            cat.update(loaded)
            catalogs[code] = cat
            continue
        # Dev fallback before locale JSON is generated
        try:
            from i18n_locales import LOCALE_OVERLAYS  # type: ignore
        except Exception:
            LOCALE_OVERLAYS = {}
        base = dict(EN)
        base.update(_TRANSLATIONS.get(code, {}))
        base.update(LOCALE_OVERLAYS.get(code, {}))
        catalogs[code] = base
    return catalogs


_CATALOGS: dict[str, dict[str, str]] | None = None


def catalogs() -> dict[str, dict[str, str]]:
    global _CATALOGS
    if _CATALOGS is None:
        _CATALOGS = _build_all()
    return _CATALOGS


def _effective_translation(code: str, key: str) -> str | None:
    code = normalize_lang(code)
    if code == "en":
        return EN.get(key) or key
    override_val = _locale_override_strings(code).get(key)
    if _translation_valid(code, key, override_val):
        return str(override_val)
    raw_val = _locale_raw_strings(code).get(key)
    if _translation_valid(code, key, raw_val):
        return str(raw_val)
    return None


def _locale_file_value(code: str, key: str) -> str | None:
    """Value stored in locales/<code>.json (may match English)."""
    if normalize_lang(code) == "en":
        return None
    raw = _locale_raw_strings(code).get(key)
    if raw is None:
        return None
    text = str(raw).strip()
    return text if text else None


def _resolve_string(key: str, code: str) -> str:
    code = normalize_lang(code)
    if code == "en":
        return EN.get(key) or key
    filed = _locale_file_value(code, key)
    if filed is not None:
        if _translation_valid(code, key, filed):
            return filed
    val = _effective_translation(code, key)
    if val is not None:
        return val
    return EN.get(key) or key


def element_lang_for_key(key: str, page_lang: str | None) -> str:
    """BCP 47 lang for a rendered string (en when JSON value is empty or English)."""
    code = normalize_lang(page_lang)
    if code == "en":
        return "en"
    filed = _locale_file_value(code, key)
    if filed is None:
        return "en"
    en_val = (EN.get(key) or "").strip()
    if filed == key or (en_val and filed == en_val):
        return "en"
    return code


def t(key: str, lang: str | None = None, **kwargs: Any) -> str:
    code = normalize_lang(lang)
    text = _resolve_string(key, code)
    if kwargs:
        try:
            return text.format(**kwargs)
        except Exception:
            return text
    return text


def translator(lang: str | None) -> Callable[..., str]:
    code = normalize_lang(lang)

    def _t(key: str, **kwargs: Any) -> str:
        return t(key, code, **kwargs)

    return _t


def catalog_for(lang: str | None) -> dict[str, str]:
    """Client-visible catalog — translated strings with English fallback per key."""
    code = normalize_lang(lang)
    return {key: _resolve_string(key, code) for key in EN}


_CLIENT_CATALOG_EXTRA: frozenset[str] = frozenset(
    {
        "pulse.share_default",
        "pulse.conditions_met_review",
        "pulse.model_state",
        "pulse.model_state_conditions",
        "waitlist.msg.welcome",
        "waitlist.msg.generic",
        "waitlist.msg.submitting",
        "waitlist.msg.error",
        "waitlist.msg.network",
    }
)


_CLIENT_CATALOG_PREFIXES: tuple[str, ...] = (
    "action.",
    "dash.",
    "ui.",
    "oracle.factor.",
    "oracle.source.",
    "oracle.share.",
    "trust.",
    "pulse.drawer.",
    "pulse.msg.",
    "pulse.chip.",
    "bounty.",
    "sealed.",
    "arb.",
    "ledger.js.",
    "ledger.panel.",
    "ledger.cta.",
    "workspace.",
)


def catalog_for_client(lang: str | None) -> dict[str, str]:
    """JSON boot catalog for client JS — same resolved strings as server t() (with EN fallback)."""
    code = normalize_lang(lang)
    keys = set(public_surface_keys()) | _CLIENT_CATALOG_EXTRA
    keys |= {k for k in EN if any(k.startswith(p) for p in _CLIENT_CATALOG_PREFIXES)}
    return {k: _resolve_string(k, code) for k in keys if k in EN}


def resolved_api_lang(request: Any, lang: str | None = None) -> str:
    """Query lang param, else cookie / profile / Accept-Language (same as HTML pages)."""
    if lang is not None and str(lang).strip():
        return normalize_lang(str(lang).strip())
    return resolve_request_lang(request)


def _resolve_request_lang_raw(request: Any) -> str:
    try:
        q = request.query_params.get("lang")
        if q:
            return normalize_lang(q)
    except Exception:
        pass
    try:
        cookie = request.cookies.get("bd_lang")
        if cookie:
            return normalize_lang(cookie)
    except Exception:
        pass
    try:
        st = getattr(request, "state", None)
        if st is not None:
            ui_lang = getattr(st, "ui_lang", None)
            if ui_lang:
                return normalize_lang(str(ui_lang))
    except Exception:
        pass
    try:
        header = request.headers.get("accept-language") or ""
        if header:
            first = header.split(",")[0].strip().split(";")[0]
            cand = normalize_lang(first)
            if cand in LOCALES:
                return cand
    except Exception:
        pass
    return DEFAULT_LANG


def resolve_request_lang(request: Any) -> str:
    """lang query → cookie → Accept-Language → en (any locales/*.json catalog is allowed)."""
    code = _resolve_request_lang_raw(request)
    if not locale_catalog_available(code):
        return DEFAULT_LANG
    return code


def resolve_nav_active(request: Any) -> str | None:
    """Active product tab for global header (Prove / Operate / Desk / Room / Verify)."""
    try:
        path = getattr(getattr(request, "url", None), "path", "") or ""
        if path.startswith("/about"):
            return "about"
        if path.startswith("/oracle-accuracy"):
            return "verify"
        if path.startswith("/data-room"):
            return "room"
        if path.startswith("/dashboard"):
            lens = str(getattr(request, "query_params", {}).get("lens", "") or "").lower()
            if lens in {"prove", "operate", "desk", "room"}:
                return lens
            return "prove"
    except Exception:
        pass
    return None


_SOCIAL_LABEL_BY_ID: dict[str, str] = {
    "x": "social.link.x",
    "reddit": "social.link.reddit",
    "facebook": "social.link.facebook",
    "telegram": "social.link.telegram",
    "linkedin": "social.link.linkedin",
}


_FOOTER_LINK_BY_HREF: dict[str, str] = {
    "/about": "footer.link.about",
    "/contact": "footer.link.contact",
    "/#trust-pulse": "footer.link.trust_pulse",
    "/#oracle": "nav.oracle",
    "/login?next=/dashboard%3Flens%3Dprove": "footer.link.decide",
    "/oracle-accuracy": "accuracy.title",
    "/discipline-mirror": "discipline.title",
    "/login?next=/dashboard": "footer.link.dashboard",
    "/dashboard": "footer.link.dashboard",
    "/#pricing": "footer.link.pricing",
    "/pricing": "footer.link.pricing",
    "/login?next=/profile": "footer.link.profile",
    "/login?next=/dashboard%3Flens%3Doperate": "footer.link.chat",
    "/disclaimer": "footer.link.disclaimer",
    "/terms": "footer.link.terms",
    "/privacy": "footer.link.privacy",
}


def localize_footer_manifest(lang: str | None, raw: dict[str, Any]) -> dict[str, Any]:
    tr = translator(lang)
    out = dict(raw)
    for field, key in (
        ("tagline", "footer.tagline"),
        ("story", "footer.story"),
        ("disclaimer_line", "footer.disclaimer"),
    ):
        text = tr(key)
        if text:
            out[field] = text
    for section in ("product", "trust", "company", "legal"):
        items = []
        for item in out.get(section) or []:
            row = dict(item)
            href = str(row.get("href") or "")
            key = _FOOTER_LINK_BY_HREF.get(href)
            if key:
                label = tr(key)
                if label:
                    row["label"] = label
            items.append(row)
        out[section] = items
    follow_items = []
    for item in out.get("follow") or []:
        row = dict(item)
        sid = str(row.get("id") or "")
        key = _SOCIAL_LABEL_BY_ID.get(sid)
        if key:
            label = tr(key)
            if label:
                row["label"] = label
        follow_items.append(row)
    out["follow"] = follow_items
    alerts = str(out.get("telegram_alerts_url") or "").strip()
    if alerts:
        out["telegram_alerts_url"] = alerts
    return out


def template_context(request: Any, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    lang = resolve_request_lang(request)
    meta = locale_meta(lang)
    header_user = None
    try:
        st = getattr(request, "state", None)
        if st is not None:
            header_user = getattr(st, "header_user", None)
    except Exception:
        header_user = None
    code = normalize_lang(lang)
    ctx: dict[str, Any] = {
        "lang": lang,
        "dir": meta["dir"],
        "locale": meta,
        "locales": list_locales(),
        "t": translator(lang),
        "key_lang": lambda k, _lang=lang: element_lang_for_key(k, _lang),
        "i18n": catalog_for(lang),
        "en_i18n": catalog_for("en") if code != "en" else {},
        "i18n_json": json.dumps(catalog_for(lang), ensure_ascii=False),
        "locales_json": json.dumps(list_locales(), ensure_ascii=False),
        "header_user": header_user,
        "header_authenticated": bool(header_user),
        "nav_active": resolve_nav_active(request),
    }
    if extra:
        ctx.update(extra)
    if ctx.get("footer"):
        ctx["footer"] = localize_footer_manifest(lang, ctx["footer"])
    return ctx


def decision_sentence(lang: str | None, action: str, asset: str, score: Any) -> str:
    code = normalize_lang(lang)
    key = KEY_DECISION_ACT if str(action).upper() in {"ACT", "BUY", "BULLISH"} else KEY_DECISION_WAIT
    try:
        score_s = f"{float(score):.0f}"
    except Exception:
        score_s = str(score)
    return t(key, code, asset=str(asset).upper(), score=score_s)


def i18n_manifest() -> dict[str, Any]:
    return {
        "default": DEFAULT_LANG,
        "locales": list_locales(),
        "count": len(list_locales()),
        "rtl": [c for c, m in LOCALES.items() if m["dir"] == "rtl"],
        "note": f"{len(list_locales())} locales; catalogs in locales/*.json; RTL for ar, he, ur, fa.",
    }
