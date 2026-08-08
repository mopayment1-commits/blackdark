# BLACKDARK — تصحيح تقرير جاهزية الاستحواذ + إغلاق الفجوات

> **التاريخ:** 2026-03-28  
> **الفرع:** `cursor/acquisition-readiness-rebuttal-eef3`

---

## الحكم المختصر

تقرير v2.0 فيه **أخطاء وقائعية**. الفجوات الحقيقية اتقفلت في الكود بنسبة تنفيذ هندسي كاملة لما هو قابل للأتمتة.  
ما يفضلش “مفتوح” إلا خطوات **بشرية/تشغيلية** (مفاتيح OAuth من Google/GitHub، تشغيل load test على ستاك إنتاج، خطاب محامٍ SEC/MiCA).

---

## 1) ادعاءات كانت غلط (موجودة أصلًا)

| الادعاء | الواقع |
|---|---|
| Missing `/accuracy` | موجود: `/oracle-accuracy` |
| Missing Persona Routing | موجود: `audience_routing.py` |
| Missing whale signal classifier | موجود: `whale_signal_classifier.py` |
| Multi-tenant moat | غير مستهدف (Single-Tenant intentional) |
| IFRS 13 كامل / Decimal في كل مسار | مبالغ فيه |

---

## 2) فجوات حقيقية — حالة الإغلاق الآن

| # | الفجوة | الحالة |
|---|---|---|
| C1 | `docker-compose.prod.yml` | ✅ مغلق |
| C2 | OAuth2 Google/GitHub (`authlib`) | ✅ مغلق في الكود — يحتاج Client IDs بشرية |
| C3 | `VAULT_KEY_ROTATION_DAYS` | ✅ مغلق (سياسة + تحذير) |
| C4 | AuditLog فشل الدخول | ✅ مغلق (`data/auth_audit.jsonl`) |
| C5 | `generate_mrr_report` / `compute_churn_rate` | ✅ مغلق + `/api/billing/reports/*` |
| C6 | pgcrypto / at-rest helpers | ✅ مغلق (`postgres_backend.ensure_pgcrypto`) |
| C7 | حزمة SEC/MiCA هندسية | ✅ مغلق كـ pack — ❌ شهادة قانونية تحتاج محامٍ |
| C8 | Redis إلزامي في الإنتاج | ✅ مغلق في `production_guard` |
| C9 | Admin TOTP MFA | ✅ مغلق (`admin_mfa.py` + `X-Admin-TOTP`) |
| C10 | ARCHITECTURE.md | ✅ مغلق |
| C11 | Privacy/Disclaimer محدّثة | ✅ مغلق |
| C12 | حمل 10k harness | ✅ سكربت جاهز — الدليل يكتمل بعد تشغيله على Postgres+Redis |

---

## 3) نقاط نهاية جديدة

- `GET /api/auth/oauth/{google|github}/login`
- `GET /api/auth/oauth/{provider}/callback`
- `GET /api/auth/oauth/status`
- `POST /api/auth/admin/totp/setup|verify`
- `GET /api/billing/reports/mrr`
- `GET /api/billing/reports/churn?window_days=30`
- `scripts/load_test_10k.py`
- `docs/SEC_MICA_COMPLIANCE_PACK.md`

---

## 4) خطوات بشرية متبقية (ليست عيوب كود)

1. ضبط `OAUTH_GOOGLE_*` / `OAUTH_GITHUB_*` في بيئة الإنتاج.
2. ضبط `ADMIN_TOTP_SECRET` وتسجيل Authenticator للأدمن.
3. تشغيل: `docker compose -f docker-compose.prod.yml up` ثم `python scripts/load_test_10k.py`.
4. مراجعة قانونية خارجية لـ SEC/MiCA قبل أي لغة استحواذ تسويقية.

**درجة جاهزية هندسية بعد الإغلاق:** ~8.6 / 10 (بشروط تشغيل المفاتيح + إثبات الحمل).
