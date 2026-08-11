# إغلاق كارثة الأمن P0 — منصة مالية

**التاريخ:** 2026-08-10  
**API:** `GET /api/security/catastrophe-p0`  
**الهدف:** علاج مخاطر data leak / API compromise / account takeover / manipulated signals بأعلى معيار هندسي fail-closed.

---

## الحكم

| الطبقة | الحالة |
|--------|--------|
| **كود (engineering)** | مكتمل — MFA أدمن موصول · بوابة Soft Launch تمنع التنفيذ الحي · إخفاء demo key · poison/freeze · audit chain |
| **Strict production runtime** | fail-closed عبر `production_guard` عند `ENV=production` و`SOFT_LAUNCH` غير مفعّل |
| **Operator gates** | يجب إعلان WAF + backup + مراقبة على البيئة الحية — التطبيق لا يستبدل CDN |

`code_complete: true` ≠ SOC2. الشهادات تبقى ممنوعة حتى إيداع طرف ثالث.

---

## التهديدات → الضوابط

| تهديد | ضابط منفَّذ |
|-------|-------------|
| Data leak | `SECRETS_MASTER_KEY` إلزامي · vault · backup ops gate · docs عامة منفصلة |
| API compromise | إخفاء demo keys · rate limits · CSRF/CORS/Host · WAF معلن · أحداث أمن |
| Account takeover | جلسات مُملّحة · حد دخول · **Admin MFA على `require_admin`** (`X-Admin-TOTP`) |
| Manipulated signals | poison/freeze · audit-chain verify · Soft Launch يمنع live execution |

---

## متغيرات البيئة الإلزامية (Strict Production)

```bash
ENV=production
# SOFT_LAUNCH unset
SECRETS_MASTER_KEY=…          # openssl rand -hex 32
SESSION_TOKEN_PEPPER=…        # openssl rand -hex 16
ADMIN_API_KEY=…
ADMIN_MFA_REQUIRED=true
ADMIN_TOTP_SECRET=…           # base32
EXPOSE_B2B_DEMO_KEY=false
BLACKDARK_B2B_DEMO_KEY=disabled
DATABASE_URL=postgresql://…
REDIS_URL=redis://…           # recommended; required for VIRAL_MODE HA
CDN_WAF_ACTIVE=true           # بعد تفعيل Cloudflare
BACKUP_SCHEDULE_CONFIGURED=true
SENTRY_DSN=…                  # و/أو:
EXTERNAL_UPTIME_CONFIGURED=true
PRODUCTION_GUARD_FAIL_CLOSED=true
LIVE_EXECUTION_ALLOW_API=false
JUPITER_LIVE_EXECUTION=false
```

---

## تحقق

```bash
pytest tests/test_security_catastrophe_p0.py tests/test_security_max_closure.py -q
python scripts/security_max_audit.py
curl -s "$BASE/api/security/catastrophe-p0" | jq '.code_complete,.strict_production_ready,.operator_gates_pending'
curl -s "$BASE/api/security/status" | jq '.honesty,.catastrophe_p0'
```

---

## ما يبقى Operator-only (ليس فشل كود)

1. تفعيل DNS + Cloudflare WAF فعليًا ثم `CDN_WAF_ACTIVE=true`  
2. جدولة `scripts/backup_postgres.py` + تجربة restore ثم `BACKUP_SCHEDULE_CONFIGURED=true`  
3. Sentry / UptimeRobot على `/health/live`  
4. وضع أسرار الإنتاج في Railway/host  
5. pentest / SOC2 عند الجاهزية المؤسسية

**جملة التأكيد:** كارثة المنصة المالية عولجت هندسيًا fail-closed؛ البوابات التشغيلية معلنة وإلزامية في strict production — بلا ادعاء شهادات مزيفة.
