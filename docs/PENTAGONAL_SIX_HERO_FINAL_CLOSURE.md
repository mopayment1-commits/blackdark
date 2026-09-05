# Pentagonal Template + Six-Hero Binding — Final Institutional Closure

**Closed:** 2026-09-03  
**Authoritative production URL:** `https://blackdark-production.up.railway.app`  
**Authoritative live probe:** `docs/PRODUCTION_LIVE_VERIFICATION_2026-09-03.json`

---

## Executive summary

Institutional closure for capabilities 1–100 pentagonal template, six-hero binding, and all corrective tracks in this phase is **COMPLETE in code and documentation**, with **two runtime follow-ups** documented (not blockers for code closure):

1. **Postgres re-verify** — production domain returned HTTP 404 after owner “Deploy database”; web service redeploy required before `database_ready: true` can be confirmed.
2. **B2B live feed probe** — requires owner-set `BLACKDARK_B2B_API_KEY` on Railway (no paying customer needed).

---

## Final status table

| البند | الحالة النهائية | الدليل |
|-------|-----------------|--------|
| **القالب الخماسي (1–100)** | ✅ CLOSED | `docs/PENTAGONAL_TEMPLATE_1_100.json`, `scripts/generate_pentagonal_hero_binding_report.py`, `docs/PENTAGONAL_HERO_CLOSURE_REPORT.json` |
| **ربط الأبطال الستة (81 صف)** | ✅ CLOSED | `docs/HERO_SIX_BINDING_REPORT.json`, `docs/PENTAGONAL_HERO_BINDING_EVIDENCE.json`, `tests/test_pentagonal_hero_binding.py` (28 passed) |
| **إصلاح PSI (onchain_netflow 0.9104)** | ✅ CLOSED — MONITOR_ELEVATED | `docs/ADR_PSI_ONCHAIN_NETFLOW_MONITOR_ELEVATED.md`, threshold 0.75 documented as exceeded |
| **إصلاح Arbitrage (net-edge-truth pollution)** | ✅ CLOSED | `GET /api/arbitrage/scanner/status` (hero path), `decision_enrichment.py`, `net_edge_truth.py`, `docs/CAP_56_HERO_BINDING_CORRECTION.md` |
| **إصلاح GET Entitlement Bypass (PR #358)** | ✅ CLOSED — PROTECTED | Merge `42044a4` @ 20:48:39Z; deploy live ~20:51:40Z; live cap47/103 `allowed:false` on correct URL |
| **تصحيح رابط الإنتاج** | ✅ CLOSED | `docs/PRODUCTION_URL_CORRECTION.md`; wrong host `blackdark-web-production` never canonical |
| **إصلاح Telegram** | ✅ CLOSED (env) | `bot_token_set` + `default_chat_set` true @ 08:17–08:35Z 03-09; test message `message_id:15032` |
| **إصلاح gaierror (كود)** | ✅ CLOSED | `database_url_resolver.py`, graceful `/api/telegram/free/status` + `/api/gtm/status`, `docs/RAILWAY_POSTGRES_DNS_FIX.md` |
| **Postgres runtime (بعد Deploy database)** | ⚠️ AWAITING_REVERIFY | Production 404 @ 08:51–08:55Z 03-09 — see `post_database_deploy_recheck` in live verification JSON |
| **Latency caps 2, 3, 16, 54** | ✅ CLOSED (ADR) | `docs/ADR_LATENCY_CAPS_2_3_54.md`, `docs/ADR_LATENCY_CAP_16.md` |
| **Cap #56 hero binding** | ✅ CLOSED | Oracle YES / Arbitrage NO — `docs/CAP_56_HERO_BINDING_CORRECTION.md` |
| **Cap #69 dual-path** | ✅ CLOSED | `9746f81` → `b6d11a9`, ~14h38m window, Oracle+Arb only |
| **B2B empty_state** | ✅ CLOSED (code) | `whale_tracker.py` `empty_state` block |
| **B2B live feed على الإنتاج** | ⏳ OWNER_KEY_SETUP | 403 مقصود بدون `BLACKDARK_B2B_API_KEY` — خطوات أدناه |
| **Supplemental closure 1–18** | ✅ CLOSED | `docs/SUPPLEMENTAL_CLOSURE_REPORT_1_18.json` |
| **GET entitlement doc correction** | ✅ CLOSED | `docs/GET_ENTITLEMENT_PRODUCTION_CLOSURE.json` (URL + protected_at corrected) |

---

## 1. Postgres / gaierror — نتيجة الفحص الفعلي (بعد Deploy database)

**النافذة:** 2026-09-03T08:51:53Z – 08:55:21Z UTC (12 محاولة + فحص نهائي)

| Endpoint | النتيجة |
|----------|---------|
| `GET /health/ready` | **HTTP 404** — `Application not found` |
| `GET /api/telegram/free/status` | **HTTP 404** |
| `GET /api/gtm/status` | **HTTP 404** |

**لا يمكن تأكيد `database_ready: true` في هذه الجلسة** — الدومين العام غير متاح بالكامل (ليس gaierror فقط).

**التفسير:** زر “Deploy database” يفعّل Postgres؛ خدمة **web** تحتاج **Redeploy** منفصل + تأكيد أن Networking → Public Domain ما زال يشير إلى `blackdark-production.up.railway.app`.

**بعد إصلاح الوصول، المتوقع:**

```json
// GET /health/ready
{"database_ready": true, "postgres_pool": {"active": true}}

// GET /api/telegram/free/status
{"bot_configured": true, "active_subscribers": <n>}  // بدون subscribers_error

// GET /api/gtm/status
{"telegram": {"bot_configured": true}, "metrics_errors": null}
```

---

## 2. تصحيح التوثيق — تم

| ملف | التغيير |
|-----|---------|
| `docs/GET_ENTITLEMENT_PRODUCTION_CLOSURE.json` | `production_url` → `blackdark-production`; `protected_at_utc` → `2026-09-02T20:51:40Z`; ملاحظة عدم موثوقية القيم السابقة |
| `docs/PRODUCTION_LIVE_VERIFICATION_2026-09-03.json` | المرجع الرسمي الوحيد للـ live probes + `post_database_deploy_recheck` |

---

## 3. توليد `BLACKDARK_B2B_API_KEY` للاختبار الكامل

**لا يوجد تحقق من شكل خاص في الكود** — أي سلسلة سرية تُقارَن بـ `hmac.compare_digest` مع المتغير على Railway.

### الخطوات (المالك)

**1) توليد مفتاح (محليًا — لا تلصقه في المحادثات):**

```bash
python3 -c "import secrets; print('bd_inst_' + secrets.token_urlsafe(32))"
```

**2) Railway → خدمة web → Variables:**

```
BLACKDARK_B2B_API_KEY=<المفتاح_المولَّد>
```

اترك `BLACKDARK_B2B_DEMO_KEY` غير مضبوط أو `disabled` (strict production posture).

**3) Redeploy خدمة web.**

**4) اختبار:**

```bash
curl -sS "https://blackdark-production.up.railway.app/api/b2b/feed" \
  -H "X-API-Key: <المفتاح_المولَّد>" | python3 -m json.tool
```

**المتوقع:** HTTP 200، JSON يحتوي `feed_version`, `record_count`, `signature`, وربما `empty_state` إذا لا صفوف.

**بديل metadata بدون مفتاح:** `GET /api/b2b/info` (دائمًا متاح).

---

## 4. مراجع الإغلاق (ترتيب السلطة)

1. **`docs/PRODUCTION_LIVE_VERIFICATION_2026-09-03.json`** — live HTTP (الوحيد الموثوق للـ probes)
2. **`docs/PENTAGONAL_SIX_HERO_FINAL_CLOSURE.md`** — هذا التقرير
3. **`docs/GET_ENTITLEMENT_PRODUCTION_CLOSURE.json`** — توقيت PR #358 فقط
4. **`docs/PENTAGONAL_HERO_CLOSURE_REPORT.json`** — تفاصيل القالب والأبطال
5. **`docs/SUPPLEMENTAL_CLOSURE_REPORT_1_18.json`** — البنود 1–18

---

## Verdict

**ملف القالب الخماسي وربط الأبطال الستة: CLOSED** من ناحية الكود، الاختبارات، والتوثيق المؤسسي.

**Follow-ups runtime (موثَّقة، ليست "قيد مراجعة" غامضة):**

| Follow-up | المسؤول | الإجراء |
|-----------|---------|---------|
| Postgres `database_ready` | Owner | Redeploy web بعد Postgres + تأكيد الدومين العام |
| B2B feed 200 على الإنتاج | Owner | ضبط `BLACKDARK_B2B_API_KEY` بالخطوات أعلاه |

---

*Generated as institutional final closure for pentagonal + six-hero phase.*
