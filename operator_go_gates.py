"""Operator GO gates — what the engineer cannot close in-repo.

Each remaining launch-critical FAIL maps to an owner/external action.
This module never marks a gate PASS. It only describes how a later SHA can.
"""

from __future__ import annotations

import os
from datetime import UTC, datetime
from typing import Any


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _compact_hosts(probe: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in probe.get("hosts") or []:
        out.append(
            {
                "host": row.get("host"),
                "ok": row.get("ok"),
                "http_status": row.get("http_status"),
                "geo_blocked": bool(row.get("geo_blocked")),
            }
        )
    return out


def run_live_probes(*, drills: dict[str, Any] | None = None) -> dict[str, Any]:
    """Re-verify remaining owner/external gates with live calls. Never logs secrets."""
    import asyncio

    from launch_drills import (
        drill_counsel_artifacts,
        drill_independent_pentest_artifact,
        drill_oauth_google_idp,
        drill_stripe_sandbox,
    )
    from ops_recovery import prove_cloud_multi_az_ha
    from telegram_monitor import oncall_live_proved

    by_id = (drills or {}).get("by_id") or {}
    stripe = by_id.get("stripe_sandbox") or drill_stripe_sandbox()
    oauth = by_id.get("oauth_google_idp") or drill_oauth_google_idp()
    counsel = by_id.get("counsel_signoff") or drill_counsel_artifacts()
    pentest = by_id.get("independent_pentest_artifact") or drill_independent_pentest_artifact()
    cloud = prove_cloud_multi_az_ha()
    live_row = by_id.get("telegram_oncall_live") or {}
    if not live_row:
        from launch_drills import drill_telegram_oncall_live

        live_row = drill_telegram_oncall_live()
    tg = live_row.get("verdict") == "PASS" or oncall_live_proved()

    async def _net() -> dict[str, Any]:
        import aiohttp
        from execution_engine import probe_binance_order_host_connectivity

        prev = os.environ.get("BINANCE_TESTNET")
        os.environ["BINANCE_TESTNET"] = "true"
        try:
            testnet = await probe_binance_order_host_connectivity()
        finally:
            if prev is None:
                os.environ.pop("BINANCE_TESTNET", None)
            else:
                os.environ["BINANCE_TESTNET"] = prev
        os.environ["BINANCE_TESTNET"] = "false"
        try:
            mainnet = await probe_binance_order_host_connectivity()
        finally:
            if prev is None:
                os.environ.pop("BINANCE_TESTNET", None)
            else:
                os.environ["BINANCE_TESTNET"] = prev

        lemon = os.getenv("LEMON_SQUEEZY_CHECKOUT_PRO", "").strip()
        lemon_status = 0
        if lemon.startswith("https://"):
            timeout = aiohttp.ClientTimeout(total=12)
            try:
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.get(lemon, allow_redirects=False) as resp:
                        lemon_status = int(resp.status)
            except Exception as exc:
                lemon_status = 0
                lemon_err = type(exc).__name__
            else:
                lemon_err = None
        else:
            lemon_err = "unset_or_not_https"

        wallet = "BgaNfyoeqRtSF5ACHdz7sP1DqFa81Hj9XZ9dNLtB5Yf"
        lamports = None
        rpc_err = None
        try:
            timeout = aiohttp.ClientTimeout(total=12)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    "https://api.mainnet-beta.solana.com",
                    json={"jsonrpc": "2.0", "id": 1, "method": "getBalance", "params": [wallet]},
                ) as resp:
                    body = await resp.json()
                    lamports = ((body.get("result") or {}).get("value"))
        except Exception as exc:
            rpc_err = type(exc).__name__

        return {
            "binance_testnet": {
                "ok": testnet.get("ok"),
                "geo_blocked": testnet.get("geo_blocked"),
                "external_block": testnet.get("external_block"),
                "hosts": _compact_hosts(testnet),
            },
            "binance_mainnet": {
                "ok": mainnet.get("ok"),
                "geo_blocked": mainnet.get("geo_blocked"),
                "external_block": mainnet.get("external_block"),
                "hosts": _compact_hosts(mainnet),
            },
            "lemon_checkout_http_status": lemon_status,
            "lemon_error": lemon_err,
            "jupiter_wallet": wallet,
            "sol_lamports": lamports,
            "rpc_error": rpc_err,
            "wallet_funded": bool(isinstance(lamports, int) and lamports > 0),
        }

    net = asyncio.run(_net())
    return {
        "proved_at": _utcnow(),
        "telegram_oncall_configured": tg,
        "telegram_oncall_live": {
            "verdict": live_row.get("verdict"),
            "reason": live_row.get("reason"),
            "message_id": live_row.get("message_id"),
            "bot_username": live_row.get("bot_username"),
            "chat_type": live_row.get("chat_type"),
            "http_status": live_row.get("http_status"),
            "bot_token_present": live_row.get("bot_token_present"),
            "chat_id_present": live_row.get("chat_id_present"),
        },
        "stripe_sandbox": {
            "verdict": stripe.get("verdict"),
            "error": stripe.get("error") or stripe.get("error_type"),
            "reason": stripe.get("reason"),
            "checkout_session_prefix": stripe.get("checkout_session_prefix"),
            "subscription_prefix": stripe.get("subscription_prefix"),
            "subscription_status": stripe.get("subscription_status"),
            "livemode": stripe.get("livemode"),
        },
        "oauth_google_idp": {
            "verdict": oauth.get("verdict"),
            "reason": oauth.get("reason"),
            "start_ok": oauth.get("start_ok"),
            "authorize_accepted": oauth.get("authorize_accepted"),
            "token_client_accepted": oauth.get("token_client_accepted"),
            "google_error": oauth.get("google_error"),
            "token_error": oauth.get("token_error"),
            "redirect_uri": (
                "{APP_BASE_URL}/api/auth/oauth/google/callback" if oauth.get("redirect_uri") else ""
            ),
            "human_callback_completed": False,
        },
        "counsel": {"verdict": counsel.get("verdict")},
        "pentest": {"verdict": pentest.get("verdict")},
        "cloud_multi_az": bool(cloud.get("cloud_multi_az")),
        "app_base_url_set": bool(os.getenv("APP_BASE_URL") or os.getenv("PUBLIC_BASE_URL")),
        **net,
        "engineer_cannot_close": True,
    }

# id → owner action. Keep in sync with production_launch_certification domains.
GATES: dict[str, dict[str, Any]] = {
    "D07": {
        "owner": "you + venue region",
        "paid": True,
        "kind": "external_geo",
        "action_ar": "تشغيل عملية FILL حية على Binance من منطقة غير محظورة جغرافياً (HTTP 451 حالياً). لا تستخدم بروكسي لتزييف الموقع.",
        "action": "Prove a live Binance FILL from a non-451 region. Do not use a geo proxy to fake unblocking.",
        "artifact": "docs/dd/BLACKDARK_FOUR_BLOCKERS_EVIDENCE.json blocker_1 live_fill=true",
        "flips": ["D07", "EXT_LIVE_FILL", "LIVE-MONEY-READY"],
    },
    "EXT_LIVE_FILL": {
        "owner": "you + venue region",
        "paid": True,
        "kind": "external_geo",
        "action_ar": "نفس D07: FILL حي مثبت بعد زوال حظر 451.",
        "action": "Same as D07 — live_fill must be true on the four-blockers evidence for this SHA.",
        "artifact": "docs/dd/BLACKDARK_FOUR_BLOCKERS_EVIDENCE.json",
        "flips": ["EXT_LIVE_FILL"],
    },
    "D10": {
        "owner": "independent pentest firm",
        "paid": True,
        "kind": "external_firm",
        "action_ar": "تعاقد مع شركة pentest مستقلة وإيداع التقرير في المستودع.",
        "action": "Commission an independent pentest. Deposit the signed report in-repo.",
        "artifact": "docs/dd/INDEPENDENT_PENTEST_REPORT.pdf (or .md)",
        "flips": ["D10"],
    },
    "D20": {
        "owner": "you + cloud vendor",
        "paid": True,
        "kind": "paid_cloud",
        "action_ar": "نشر Postgres والتطبيق على سحابة مدفوعة multi-AZ وإعادة إثبات HA.",
        "action": "Deploy app+Postgres on paid cloud multi-AZ. Local streaming HA is not this gate.",
        "artifact": "cloud HA proof with cloud_multi_az=true",
        "flips": ["D20", "EXT_CLOUD_HA", "LIVE-PRODUCTION-READY"],
    },
    "EXT_CLOUD_HA": {
        "owner": "you + cloud vendor",
        "paid": True,
        "kind": "paid_cloud",
        "action_ar": "نفس D20: cloud_multi_az=true بدليل من حساب سحابي مدفوع.",
        "action": "Same as D20 — four-blockers cloud_multi_az must be true.",
        "artifact": "docs/dd/BLACKDARK_FOUR_BLOCKERS_EVIDENCE.json blocker_4",
        "flips": ["EXT_CLOUD_HA"],
    },
    "D13": {
        "owner": "you",
        "paid": False,
        "kind": "secrets",
        "action_ar": "وضع مفتاح Stripe TEST صالح (sk_test_ حقيقي) و STRIPE_PRICE_PRO ثم إثبات دورة TEST: Account.retrieve + checkout BLACKDARK + اشتراك tok_visa ثم إلغاء.",
        "action": "Set a real Stripe TEST secret (sk_test_) and STRIPE_PRICE_PRO. Prove the TEST cycle: Account.retrieve, BLACKDARK checkout, tok_visa subscription, then cancel. Live keys are refused.",
        "artifact": "STRIPE_SECRET_KEY + STRIPE_PRICE_PRO + stripe_sandbox PASS (cs_ + sub_ prefixes)",
        "flips": ["D13"],
    },
    "D16": {
        "owner": "you",
        "paid": True,
        "kind": "prod_dns_tls",
        "action_ar": "ربط نطاق إنتاج مع TLS بنسخة منشورة من هذا الـSHA وإثبات https://<prod>/health/live.",
        "action": "Attach production DNS+TLS to a deployed replica of this SHA. Probe https://<prod>/health/live.",
        "artifact": "HTTPS health probe log for the production hostname",
        "flips": ["D16", "LIVE-PRODUCTION-READY"],
    },
    "D18": {
        "owner": "you",
        "paid": True,
        "kind": "prod_slo",
        "action_ar": "قياس p50/p95/p99 على عمال إنتاج (WEB_CONCURRENCY≥2، replicas≥2، Postgres+Redis) وليس TestClient.",
        "action": "Measure p50/p95/p99 against production-like workers (not local TestClient/ASGI).",
        "artifact": "docs/dd production SLO pack on prod topology",
        "flips": ["D18"],
    },
    "D19": {
        "owner": "you",
        "paid": True,
        "kind": "prod_load",
        "action_ar": "قياس نقطة الانهيار وهامش الأمان على طوبولوجيا إنتاج.",
        "action": "Measure breaking point and safety margin on production-like topology.",
        "artifact": "load/stress/soak report against prod workers",
        "flips": ["D19"],
    },
    "D24": {
        "owner": "you",
        "paid": False,
        "kind": "secrets",
        "action_ar": "ضبط TELEGRAM_BOT_TOKEN و TELEGRAM_CHAT_ID ثم إثبات صفحة on-call (رسالة اختبار تصل).",
        "action": "Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID. Prove a test page reaches a human. LAUNCH_SKIP_TELEGRAM is not done.",
        "artifact": "TELEGRAM_BOT_TOKEN + successful /api/alerts/telegram/test as authenticated owner",
        "flips": ["D24", "D37", "D40"],
    },
    "D25": {
        "owner": "you",
        "paid": True,
        "kind": "prod_deploy",
        "action_ar": "نشر موقّع لهذا الـSHA على حساب الإنتاج (Railway/Docker) مع سجل نشر.",
        "action": "Perform a signed production deploy of this SHA to the operator account. Record the deploy.",
        "artifact": "production deploy log / release for this SHA",
        "flips": ["D25"],
    },
    "D28": {
        "owner": "you + vendors",
        "paid": True,
        "kind": "third_parties",
        "action_ar": "إنجاح الاعتمادات الحية: Binance غير 451، Jupiter ممول، OAuth IdP، PSP صالح، تيليغرام.",
        "action": "Make live third parties work: Binance not 451, funded Jupiter, OAuth client ids, valid PSP, Telegram.",
        "artifact": "four-blockers + billing + oauth + telegram proofs",
        "flips": ["D28"],
    },
    "D30": {
        "owner": "independent counsel",
        "paid": True,
        "kind": "external_firm",
        "action_ar": "رأي قانوني مستقل (خصوصية/امتثال/ترخيص بيانات) يُودَع كملف. المهندس لا يوقّع عن المحامي.",
        "action": "Independent counsel sign-off (privacy/compliance/data licensing). An engineer file is not counsel.",
        "artifact": "docs/legal/COUNSEL_SIGNOFF.pdf (or docs/dd/INDEPENDENT_COUNSEL_SIGNOFF.md)",
        "flips": ["D30"],
    },
    "D37": {
        "owner": "you",
        "paid": False,
        "kind": "ops",
        "action_ar": "تسليح غرفة تحكم الإطلاق: on-call بشري عبر تيليغرام/SMTP وفق runbook.",
        "action": "Staff launch operations: armed human on-call (Telegram/SMTP) per runbook.",
        "artifact": "same as D24 plus named on-call",
        "flips": ["D37"],
    },
    "D39": {
        "owner": "you",
        "paid": True,
        "kind": "prod_capacity",
        "action_ar": "قياس المستخدمين المتزامنين على طوبولوجيا إنتاج، لا نموذج viral_capacity وحده.",
        "action": "Measure concurrent-user capacity on production-like workers.",
        "artifact": "signed capacity pack / load evidence on prod topology",
        "flips": ["D39"],
    },
    "D40": {
        "owner": "you",
        "paid": False,
        "kind": "ops",
        "action_ar": "تجميد الطوارئ موجود داخل العملية؛ صفحة 3 صباحاً تتطلب on-call مسلّح (D24).",
        "action": "In-app panic freeze exists. Unattended 3 AM page requires armed on-call (D24).",
        "artifact": "same as D24",
        "flips": ["D40"],
    },
    "EXT_JUPITER_VC": {
        "owner": "you",
        "paid": True,
        "kind": "wallet_funding",
        "action_ar": "تمويل المحفظة BgaNfyoeqRtSF5ACHdz7sP1DqFa81Hj9XZ9dNLtB5Yf بـ SOL/USDC وإثبات توقيع Jupiter على السلسلة (VC).",
        "action": "Fund wallet BgaNfyoeqRtSF5ACHdz7sP1DqFa81Hj9XZ9dNLtB5Yf with SOL/USDC and prove Jupiter on-chain VC.",
        "artifact": "docs/dd/BLACKDARK_FOUR_BLOCKERS_EVIDENCE.json blocker_2 verified_complete=true",
        "flips": ["EXT_JUPITER_VC", "LIVE-MONEY-READY"],
    },
}


def gates_for_open_domains(domains: list[dict[str, Any]]) -> list[dict[str, Any]]:
    from billing_service import stripe_test_cycle_proved
    from telegram_monitor import oncall_live_proved

    tg_ok = oncall_live_proved()
    stripe_ok = stripe_test_cycle_proved()
    out: list[dict[str, Any]] = []
    for d in domains:
        if not d.get("launch_critical"):
            continue
        if d.get("verdict") == "PASS":
            continue
        gid = str(d.get("id") or "")
        meta = dict(
            GATES.get(gid)
            or {
                "owner": "you",
                "paid": False,
                "kind": "unknown",
                "action": "Close this FAIL with a re-verifiable artifact on a later SHA.",
                "action_ar": "أغلق هذا البند بملف/دليل قابل لإعادة التحقق على SHA لاحق.",
                "artifact": d.get("evidence"),
                "flips": [gid],
            }
        )
        if gid == "D28":
            from oauth_service import oauth_google_live_proved

            oauth_ok = oauth_google_live_proved()
            remain_ar = []
            remain_en = []
            remain_ar.append("Binance غير 451")
            remain_en.append("Binance not 451")
            remain_ar.append("Jupiter ممول")
            remain_en.append("funded Jupiter")
            closed = []
            if oauth_ok:
                closed.append("OAuth Google IdP")
            else:
                remain_ar.append("OAuth IdP")
                remain_en.append("OAuth")
            if tg_ok:
                closed.append("تيليغرام")
            else:
                remain_ar.append("تيليغرام")
                remain_en.append("Telegram")
            if stripe_ok:
                closed.append("Stripe TEST PSP")
            else:
                remain_ar.append("PSP صالح")
                remain_en.append("valid PSP")
            closed_ar = (
                (" شرائح أُغلقت: " + "، ".join(closed) + ".") if closed else ""
            )
            meta["action_ar"] = "إنجاح الاعتمادات الحية المتبقية: " + "، ".join(remain_ar) + "." + closed_ar
            meta["action"] = "Remaining live vendors: " + ", ".join(remain_en) + "."
            arts = ["four-blockers"]
            if oauth_ok:
                arts.append("oauth_google_idp PASS")
            else:
                arts.append("oauth proofs")
            if tg_ok:
                arts.append("telegram_oncall_live PASS")
            if stripe_ok:
                arts.append("stripe_sandbox PASS")
            meta["artifact"] = "; ".join(arts)
        out.append(
            {
                "id": gid,
                "title": d.get("title"),
                "verdict": d.get("verdict"),
                "severity": d.get("severity_if_open"),
                **meta,
                "closable_in_repo": False,
            }
        )
    return out


def render_markdown(cert: dict[str, Any]) -> str:
    v = cert.get("final_production_verdict") or {}
    tracks = cert.get("tracks") or v.get("tracks") or {}
    rows = gates_for_open_domains(cert.get("domains") or [])
    lines = [
        "# Operator GO gates — cannot be closed by the engineer alone",
        "",
        f"**SHA:** `{cert.get('sha')}`  ",
        f"**Decision:** **{v.get('decision')}**  ",
        f"**PUBLIC-DEMO-READY:** `{tracks.get('PUBLIC-DEMO-READY')}`  ",
        f"**LIVE-PRODUCTION-READY:** `{tracks.get('LIVE-PRODUCTION-READY')}`  ",
        f"**LIVE-MONEY-READY:** `{tracks.get('LIVE-MONEY-READY')}`  ",
        "",
        "Unconditional GO stays NO-GO until every row below is closed with re-verifiable evidence. "
        "Do not deposit fake counsel/pentest files. Do not geo-proxy Binance. Do not invent AMM L2.",
        "",
        "| ID | Severity | Owner | Paid? | What you must do | Artifact |",
        "|---|---|---|---|---|---|",
    ]
    for r in rows:
        lines.append(
            f"| {r['id']} | {r.get('severity')} | {r.get('owner')} | {r.get('paid')} | {r.get('action_ar') or r.get('action')} | `{r.get('artifact')}` |"
        )
    live = cert.get("operator_live_probes") or {}
    if live:
        lines += [
            "",
            "## Live re-probe on this SHA",
            "",
            f"- Telegram on-call configured: `{live.get('telegram_oncall_configured')}`",
            f"- Telegram on-call live: `{(live.get('telegram_oncall_live') or {}).get('verdict')}` "
            f"reason=`{(live.get('telegram_oncall_live') or {}).get('reason')}` "
            f"message_id=`{(live.get('telegram_oncall_live') or {}).get('message_id')}` "
            f"bot=`{(live.get('telegram_oncall_live') or {}).get('bot_username')}`",
            f"- Stripe TEST API: `{((live.get('stripe_sandbox') or {}).get('verdict'))}` ({(live.get('stripe_sandbox') or {}).get('error')})",
            f"- Google OAuth live IdP: `{((live.get('oauth_google_idp') or {}).get('verdict'))}` "
            f"reason=`{((live.get('oauth_google_idp') or {}).get('reason'))}` "
            f"authorize_accepted=`{((live.get('oauth_google_idp') or {}).get('authorize_accepted'))}` "
            f"token_client_accepted=`{((live.get('oauth_google_idp') or {}).get('token_client_accepted'))}`",
            f"- Counsel artifact: `{(live.get('counsel') or {}).get('verdict')}`",
            f"- Pentest artifact: `{(live.get('pentest') or {}).get('verdict')}`",
            f"- Binance testnet order host ok: `{(live.get('binance_testnet') or {}).get('ok')}` geo_blocked=`{(live.get('binance_testnet') or {}).get('geo_blocked')}`",
            f"- Binance mainnet order host ok: `{(live.get('binance_mainnet') or {}).get('ok')}` geo_blocked=`{(live.get('binance_mainnet') or {}).get('geo_blocked')}`",
            f"- Jupiter wallet funded: `{live.get('wallet_funded')}` lamports=`{live.get('sol_lamports')}`",
            f"- cloud_multi_az: `{live.get('cloud_multi_az')}`",
            f"- APP_BASE_URL set: `{live.get('app_base_url_set')}`",
            f"- Lemon checkout HTTP: `{live.get('lemon_checkout_http_status')}`",
            "",
        ]
    lines += [
        "## After you close a gate",
        "",
        "1. Put the artifact or secrets in the environment.",
        "2. Run `python scripts/prove_four_blockers.py` if FILL / Jupiter / cloud HA changed.",
        "3. Run `python scripts/prove_production_launch_cert.py` on the new SHA.",
        "4. GO only if Critical=0, High=0, untested LC=0, LIVE-PRODUCTION-READY and LIVE-MONEY-READY are true.",
        "",
    ]
    return "\n".join(lines) + "\n"
