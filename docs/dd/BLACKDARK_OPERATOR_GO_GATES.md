# Operator GO gates — cannot be closed by the engineer alone

**SHA:** `c3da0ce7a851a0edf3689db24a13a95e98204ad2`  
**Decision:** **NO-GO**  
**PUBLIC-DEMO-READY:** `True`  
**LIVE-PRODUCTION-READY:** `False`  
**LIVE-MONEY-READY:** `False`  

Unconditional GO stays NO-GO until every row below is closed with re-verifiable evidence. Do not deposit fake counsel/pentest files. Do not geo-proxy Binance. Do not invent AMM L2.

| ID | Severity | Owner | Paid? | What you must do | Artifact |
|---|---|---|---|---|---|
| D07 | critical | you + venue region | True | تشغيل عملية FILL حية على Binance من منطقة غير محظورة جغرافياً (HTTP 451 حالياً). لا تستخدم بروكسي لتزييف الموقع. | `docs/dd/BLACKDARK_FOUR_BLOCKERS_EVIDENCE.json blocker_1 live_fill=true` |
| D10 | critical | independent pentest firm | True | تعاقد مع شركة pentest مستقلة وإيداع التقرير في المستودع. | `docs/dd/INDEPENDENT_PENTEST_REPORT.pdf (or .md)` |
| D13 | high | you | False | وضع مفتاح Stripe TEST صالح (sk_test_ حقيقي) ومعرّفات الأسعار. المفتاح الحالي مرفوض من Stripe API. | `STRIPE_SECRET_KEY + STRIPE_PRICE_PRO (valid TEST)` |
| D16 | high | you | True | ربط نطاق إنتاج مع TLS بنسخة منشورة من هذا الـSHA وإثبات https://<prod>/health/live. | `HTTPS health probe log for the production hostname` |
| D18 | high | you | True | قياس p50/p95/p99 على عمال إنتاج (WEB_CONCURRENCY≥2، replicas≥2، Postgres+Redis) وليس TestClient. | `docs/dd production SLO pack on prod topology` |
| D19 | high | you | True | قياس نقطة الانهيار وهامش الأمان على طوبولوجيا إنتاج. | `load/stress/soak report against prod workers` |
| D20 | critical | you + cloud vendor | True | نشر Postgres والتطبيق على سحابة مدفوعة multi-AZ وإعادة إثبات HA. | `cloud HA proof with cloud_multi_az=true` |
| D24 | high | you | False | ضبط TELEGRAM_BOT_TOKEN و TELEGRAM_CHAT_ID ثم إثبات صفحة on-call (رسالة اختبار تصل). | `TELEGRAM_BOT_TOKEN + successful /api/alerts/telegram/test as authenticated owner` |
| D25 | high | you | True | نشر موقّع لهذا الـSHA على حساب الإنتاج (Railway/Docker) مع سجل نشر. | `production deploy log / release for this SHA` |
| D28 | high | you + vendors | True | إنجاح الاعتمادات الحية: Binance غير 451، Jupiter ممول، OAuth IdP، PSP صالح، تيليغرام. | `four-blockers + billing + oauth + telegram proofs` |
| D30 | high | independent counsel | True | رأي قانوني مستقل (خصوصية/امتثال/ترخيص بيانات) يُودَع كملف. المهندس لا يوقّع عن المحامي. | `docs/legal/COUNSEL_SIGNOFF.pdf (or docs/dd/INDEPENDENT_COUNSEL_SIGNOFF.md)` |
| D37 | high | you | False | تسليح غرفة تحكم الإطلاق: on-call بشري عبر تيليغرام/SMTP وفق runbook. | `same as D24 plus named on-call` |
| D39 | high | you | True | قياس المستخدمين المتزامنين على طوبولوجيا إنتاج، لا نموذج viral_capacity وحده. | `signed capacity pack / load evidence on prod topology` |
| D40 | high | you | False | تجميد الطوارئ موجود داخل العملية؛ صفحة 3 صباحاً تتطلب on-call مسلّح (D24). | `same as D24` |
| EXT_LIVE_FILL | critical | you + venue region | True | نفس D07: FILL حي مثبت بعد زوال حظر 451. | `docs/dd/BLACKDARK_FOUR_BLOCKERS_EVIDENCE.json` |
| EXT_JUPITER_VC | high | you | True | تمويل المحفظة BgaNfyoeqRtSF5ACHdz7sP1DqFa81Hj9XZ9dNLtB5Yf بـ SOL/USDC وإثبات توقيع Jupiter على السلسلة (VC). | `docs/dd/BLACKDARK_FOUR_BLOCKERS_EVIDENCE.json blocker_2 verified_complete=true` |
| EXT_CLOUD_HA | critical | you + cloud vendor | True | نفس D20: cloud_multi_az=true بدليل من حساب سحابي مدفوع. | `docs/dd/BLACKDARK_FOUR_BLOCKERS_EVIDENCE.json blocker_4` |

## Live re-probe on this SHA

- Telegram on-call configured: `False`
- Stripe TEST API: `FAIL` (AuthenticationError)
- Counsel artifact: `FAIL`
- Pentest artifact: `FAIL`
- Binance testnet order host ok: `False` geo_blocked=`True`
- Binance mainnet order host ok: `False` geo_blocked=`True`
- Jupiter wallet funded: `False` lamports=`0`
- cloud_multi_az: `False`
- APP_BASE_URL set: `False`
- Lemon checkout HTTP: `302`

## After you close a gate

1. Put the artifact or secrets in the environment.
2. Run `python scripts/prove_four_blockers.py` if FILL / Jupiter / cloud HA changed.
3. Run `python scripts/prove_production_launch_cert.py` on the new SHA.
4. GO only if Critical=0, High=0, untested LC=0, LIVE-PRODUCTION-READY and LIVE-MONEY-READY are true.

