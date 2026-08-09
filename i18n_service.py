"""
BLACKDARK — Public UI i18n (15 locales).

English is the default and source of truth. Missing keys fall back to English.
Arabic uses RTL (dir=rtl).
"""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

# code -> metadata
LOCALES: dict[str, dict[str, str]] = {
    "en": {"code": "en", "name": "English", "native": "English", "dir": "ltr", "group": "core"},
    "zh-CN": {"code": "zh-CN", "name": "Chinese (Simplified)", "native": "简体中文", "dir": "ltr", "group": "core"},
    "hi": {"code": "hi", "name": "Hindi", "native": "हिन्दी", "dir": "ltr", "group": "core"},
    "ja": {"code": "ja", "name": "Japanese", "native": "日本語", "dir": "ltr", "group": "core"},
    "ko": {"code": "ko", "name": "Korean", "native": "한국어", "dir": "ltr", "group": "core"},
    "ru": {"code": "ru", "name": "Russian", "native": "Русский", "dir": "ltr", "group": "core"},
    "pt": {"code": "pt", "name": "Portuguese", "native": "Português", "dir": "ltr", "group": "core"},
    "es": {"code": "es", "name": "Spanish", "native": "Español", "dir": "ltr", "group": "core"},
    "fr": {"code": "fr", "name": "French", "native": "Français", "dir": "ltr", "group": "core"},
    "de": {"code": "de", "name": "German", "native": "Deutsch", "dir": "ltr", "group": "core"},
    "ar": {"code": "ar", "name": "Arabic", "native": "العربية", "dir": "rtl", "group": "edge"},
    "tr": {"code": "tr", "name": "Turkish", "native": "Türkçe", "dir": "ltr", "group": "edge"},
    "vi": {"code": "vi", "name": "Vietnamese", "native": "Tiếng Việt", "dir": "ltr", "group": "edge"},
    "id": {"code": "id", "name": "Indonesian", "native": "Bahasa Indonesia", "dir": "ltr", "group": "edge"},
    "th": {"code": "th", "name": "Thai", "native": "ไทย", "dir": "ltr", "group": "edge"},
}

DEFAULT_LANG = "en"
_ALIASES = {
    "zh": "zh-CN",
    "zh-cn": "zh-CN",
    "zh_cn": "zh-CN",
    "zh-hans": "zh-CN",
    "pt-br": "pt",
    "pt_br": "pt",
    "pt-pt": "pt",
    "en-us": "en",
    "en-gb": "en",
    "ara": "ar",
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


def list_locales() -> list[dict[str, str]]:
    return [dict(v) for v in LOCALES.values()]


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
    # Nav
    "nav.home": "Home",
    "nav.oracle": "Oracle",
    "nav.features": "Features",
    "nav.pricing": "Pricing",
    "nav.accuracy": "Accuracy",
    "nav.login": "Login",
    "nav.signup": "Sign up",
    "nav.logout": "Logout",
    "nav.dashboard": "Dashboard",
    "nav.platform": "Platform",
    "nav.capabilities": "Capabilities",
    "nav.funds": "Funds",
    "nav.compliance": "Compliance",
    "nav.portfolio": "Portfolio",
    "nav.stealth": "Stealth",
    "nav.try_oracle": "Try Oracle Free",
    "nav.verify_accuracy": "Verify Accuracy",
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
    "hero.cta.oracle": "Try Oracle Free",
    "hero.cta.telegram": "Telegram — 3 Free Alerts/Day",
    "hero.cta.accuracy": "Live Accuracy",
    "stats.visitors": "Visitors",
    "stats.users": "Users",
    "stats.subscribers": "Subscribers",
    "stats.telegram": "Telegram",
    "stats.waitlist": "Waitlist",
    # Telegram block
    "tg.title": "Telegram Free Alerts",
    "tg.badge": "3/day free",
    "tg.body": "Subscribe in Telegram — get top arbitrage + Oracle signals. No credit card.",
    "tg.open": "Open Telegram Bot",
    "tg.accuracy": "See AI Accuracy",
    "tg.commands": "Commands: /start · /status · /accuracy · /stop",
    # Oracle demo
    "oracle.title": "BLACKDARK Oracle",
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
    "action.ACT": "ACT",
    "action.WAIT": "WAIT",
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
    "pricing.free.f2": "Public Accuracy Ledger",
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
    "dash.upgrade": "Pro $29/mo",
    "dash.symbol": "Symbol",
    "dash.stealth.sub": "Whale audience · advisory slice sizing — not a stealth-routing guarantee",
    "dash.portfolio.sub": "Risk in plain language — private holdings stay in-browser",
    # Login
    "login.trial": "7-Day Pro Trial on signup — code LAUNCHPRO = 14 days",
    "login.tab.login": "Login",
    "login.tab.register": "Register",
    "login.email": "Email",
    "login.pass_label": "Passcode",
    "login.name": "Name",
    "login.pass_hint": "Passcode (8+ chars)",
    "login.submit": "Login",
    "login.create": "Create Account",
    "login.home": "← Home",
    # Accuracy / prove-it
    "accuracy.title": "Public Accuracy Ledger",
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
    "decision.act": "ACT on {asset} — score {score}.",
    "decision.wait": "WAIT on {asset} — score {score}.",
    "decision.clear_act": "Clear opportunity on {asset}: score {score}/100.",
    "decision.clear_wait": "Wait on {asset}: score {score}/100.",
    "decision.rejected": "Rejected: not executable after real costs.",
    "decision.veto": "Sources contradict — stay flat.",
    "decision.net": "Estimated net after costs ~${net}.",
    "upgrade.pro_hint": "Switch to Pro to unlock Net-Edge Truth Score and Opportunity Half-Life.",
    "compliance.lead": "Engineering posture and overclaim denylist — not a license or SOC2 certificate.",
    # Sealed Trust OS landing (binding 2026-08-08)
    "nav.prove": "Prove",
    "nav.operate": "Operate",
    "nav.desk": "Desk",
    "nav.room": "Room",
    "nav.verify": "Verify",
    "nav.open_proof": "Open Proof",
    "hero.headline": "We publish the miss.",
    "hero.support": "Sealed forecasts before the event. Public proof after.",
    "hero.cta.try": "Try Oracle Free",
    "hero.cta.seal": "Watch the Seal",
    "pulse.label": "TRUST PULSE",
    "pulse.live": "Live",
    "pulse.loading": "Loading today’s decision…",
    "pulse.sentence": "One clear Act / Wait — reviewable, not a mystery score.",
    "pulse.open_full": "Open full proof",
    "pulse.share": "Share Proof",
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
    "lenses.prove.body": "Free Proof Pass: one Act/Wait + Why + shareable certificate + public ledger.",
    "lenses.operate.title": "Operate",
    "lenses.operate.body": "Decision Pro $29: daily habit — unlimited Oracle, Portfolio AI, alerts, AI Chat.",
    "lenses.desk.title": "Desk",
    "lenses.desk.body": "Decision Desk $49: edge + packaging to convince someone else — Stealth, Evidence, API.",
    "lenses.room.title": "Room",
    "lenses.room.body": "Institutional from $3,000 → open: Data Room, SSO/MFA, SLA — Talk to us.",
    "lenses.cta": "Open the lenses",
    "prove.title": "Prove · Decide",
    "prove.sub": "One clear Act/Wait + Why + shareable Proof Card. Four lenses: Prove → Operate → Desk → Room.",
    "feat.pulse.title": "Trust Pulse",
    "feat.pulse.body": "One live Act / Wait with Why under five seconds — the first thing you see, every time.",
    "feat.cert.title": "Decision Certificate",
    "feat.cert.body": "Shareable Proof Card with verify link. Dual-coded: text + visual state — not a mystery score.",
    "feat.ledger.title": "Public Accuracy Ledger",
    "feat.ledger.body": "Hits and misses published. Don't trust us — verify us.",
    "feat.operate.title": "Operate depth",
    "feat.operate.body": "Decision Pro unlocks daily habit, Portfolio AI, alerts, and AI Chat — without Free watermark.",
    "feat.note": "Decision Pro unlocks the daily habit. Decision Desk / Institutional package proof for others.",
    "pricing.title_os": "One Trust OS. Four depths.",
    "pricing.sub_os": "Proof → daily habit → desk packaging → institutional trust room. We sell a reviewable decision + shareable proof — not charts or mystery scores.",
    "pricing.proof_pass": "Proof Pass",
    "pricing.decision_pro": "Decision Pro",
    "pricing.decision_desk": "Decision Desk",
    "pricing.institutional": "Trust OS Institutional",
    "pricing.mo": "/month",
    "pricing.mo_usd": "/month USD",
    "pricing.from_open": "From $3,000 → open",
    "pricing.proof_promise": "Take a clear decision… and prove it publicly.",
    "pricing.pro_promise": "From one-off proof → a daily decision habit.",
    "pricing.desk_promise": "Edge + packaging to convince someone else.",
    "pricing.inst_promise": "USD · Room lens · Talk to us · not self-serve checkout.",
    "pricing.trial_note": "7-day trial · cancel anytime before charge",
    "pricing.popular": "Most chosen depth",
    "pricing.cta.free_signup": "Start free — Sign up",
    "pricing.cta.trial": "Start 7-day trial",
    "pricing.cta.desk": "Get Decision Desk",
    "pricing.cta.talk": "Talk to us",
    "pricing.cta.b2b": "B2B Data Feed",
    "pricing.pay_note": "Prices in USD. Card data is processed by Lemon Squeezy / Stripe hosted checkout — never stored on BLACKDARK.",
    "pricing.manage": "Manage plan anytime from Profile & Billing.",
    "login.lead": "Login or create an account. Email + passcode (Google when configured). 7-day Decision Pro trial on signup. USD billing via hosted Lemon/Stripe — card data never touches us.",
    "login.tab.signup": "Sign up",
    "auth.forgot_pass": "Forgot passcode?",
    "auth.forgot_username": "Forgot username?",
    "auth.google": "Continue with Google",
    "auth.github": "Continue with GitHub",
    "auth.or_email": "or email",
    "auth.create": "Create account",
    "auth.accept_terms": "I accept the Terms, Privacy, and Risk Disclaimer. Not financial advice.",
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
        "decision.act": "对 {asset} 采取行动 — 分数 {score}。",
        "decision.wait": "对 {asset} 等待 — 分数 {score}。",
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


def _build_all() -> dict[str, dict[str, str]]:
    """Assemble all locale catalogs. Non-EN locales use curated overlays + EN fallback."""
    # Import heavy overlays lazily from sibling module if present; else embed compact set.
    try:
        from i18n_locales import LOCALE_OVERLAYS  # type: ignore
    except Exception:
        LOCALE_OVERLAYS = {}
    catalogs: dict[str, dict[str, str]] = {"en": dict(EN)}
    # Seed zh-CN from inline
    catalogs["zh-CN"] = _fill_from_map(_TRANSLATIONS["zh-CN"])
    for code, overlay in LOCALE_OVERLAYS.items():
        if code == "en":
            continue
        base = dict(catalogs.get(code, EN))
        base.update(overlay)
        # ensure all EN keys exist
        for k, v in EN.items():
            base.setdefault(k, v)
        catalogs[code] = base
    # Ensure every supported locale exists (fallback EN)
    for code in LOCALES:
        catalogs.setdefault(code, dict(EN))
    return catalogs


_CATALOGS: dict[str, dict[str, str]] | None = None


def catalogs() -> dict[str, dict[str, str]]:
    global _CATALOGS
    if _CATALOGS is None:
        _CATALOGS = _build_all()
    return _CATALOGS


def t(key: str, lang: str | None = None, **kwargs: Any) -> str:
    code = normalize_lang(lang)
    cat = catalogs().get(code) or EN
    text = cat.get(key) or EN.get(key) or key
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
    code = normalize_lang(lang)
    return dict(catalogs().get(code) or EN)


def resolve_request_lang(request: Any) -> str:
    """lang query → cookie bd_lang → Accept-Language → en."""
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
        header = request.headers.get("accept-language") or ""
        if header:
            first = header.split(",")[0].strip().split(";")[0]
            cand = normalize_lang(first)
            if cand in LOCALES:
                return cand
    except Exception:
        pass
    return DEFAULT_LANG


def template_context(request: Any, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    lang = resolve_request_lang(request)
    meta = locale_meta(lang)
    ctx: dict[str, Any] = {
        "lang": lang,
        "dir": meta["dir"],
        "locale": meta,
        "locales": list_locales(),
        "t": translator(lang),
        "i18n": catalog_for(lang),
        "i18n_json": json.dumps(catalog_for(lang), ensure_ascii=False),
        "locales_json": json.dumps(list_locales(), ensure_ascii=False),
    }
    if extra:
        ctx.update(extra)
    return ctx


def decision_sentence(lang: str | None, action: str, asset: str, score: Any) -> str:
    code = normalize_lang(lang)
    key = "decision.act" if str(action).upper() in {"ACT", "BUY", "BULLISH"} else "decision.wait"
    try:
        score_s = f"{float(score):.0f}"
    except Exception:
        score_s = str(score)
    return t(key, code, asset=str(asset).upper(), score=score_s)


def i18n_manifest() -> dict[str, Any]:
    return {
        "default": DEFAULT_LANG,
        "locales": list_locales(),
        "count": len(LOCALES),
        "rtl": [c for c, m in LOCALES.items() if m["dir"] == "rtl"],
        "note": "English is source of truth; missing keys fall back to English.",
    }
