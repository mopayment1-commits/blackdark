# قائمة نشر Staging على Railway — قبل Production

## المتطلبات المسبقة

- [ ] `PRE_LAUNCH_GATE_ASSESSMENT.json` → مراجعة البوابات
- [ ] `SECRETS_HYGIENE_REPORT.json` → `clean: true`
- [ ] `docs/security/SECURITY_WORKFLOW_REGISTER.json` → WF-015/016/017 = REMEDIATED
- [ ] PostgreSQL staging منفصل (BLK-002)
- [ ] `.env.staging.example` مُعبّأ في Railway dashboard

## خطوات النشر

1. إنشاء مشروع Railway **staging** (منفصل عن prod)
2. إضافة Postgres plugin → نسخ `DATABASE_URL`
3. إضافة Redis plugin → نسخ `REDIS_URL`
4. ربط الريبو + branch `cursor/pre-launch-institutional-completion-358c`
5. تعيين `SERVICE_MODE=web` + متغيرات من `.env.staging.example`
6. Deploy → انتظر `/health/live` = 200

## اختبار كمستخدم (إلزامي)

| # | الخطوة | الدليل |
|---|--------|--------|
| 1 | فتح URL staging | screenshot |
| 2 | تسجيل حساب جديد | session cookie |
| 3 | تسجيل دخول / MFA إن مفعّل | 200 OK |
| 4 | تشغيل قدرة أساسية (oracle/market) | API response JSON |
| 5 | صفحة billing (test mode) | checkout session |
| 6 | webhook test من Stripe dashboard | event logged |

## ممنوع قبل إكمال Staging

- ❌ فتح الإنتاج للعملاء
- ❌ `sk_live_` على staging
- ❌ مشاركة `DATABASE_URL` بين staging و prod

## بعد نجاح Staging

- تحديث `PRE_LAUNCH_GATE_ASSESSMENT.json` → G8 PARTIAL → PASS (staging)
- موافقة المالك للانتقال لـ production setup
