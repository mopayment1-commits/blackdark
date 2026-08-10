# تشغيل بشري مجاني — Soft Launch (بدون دفع/شراء)

**الهدف:** تنفيذ كل خطوات المشغّل التي **لا تحتاج بطاقة/اشتراك مدفوع** الآن.  
**الفرع/الكود:** جاهز على `main`.  
**ملف الأسرار المحلي (لا يُرفع):** `.env.softlaunch.local`

---

## ما يُنفَّذ مجانًا الآن (بالترتيب)

| # | الخطوة | من؟ | حالة |
|---|--------|-----|------|
| F1 | فتح ملف الأسرار في Notepad (أسهل طريقة) | أنت | انقر مرتين `scripts/open_softlaunch_env.bat` أو الأمر بالأسفل |
| F2 | توليد حزمة إطلاق عامة (اختياري) | سكربت | `python scripts/generate_launch_secrets.py --write --admin-email YOU@email` |
| F3 | تشغيل `security_max_audit` محليًا | سكربت | يجب `engineering_complete` في بيئة غير strict |
| F4 | إضافة Admin TOTP لتطبيق Authenticator | أنت | امسح URI من تعليق الملف المحلي |
| F5 | تشغيل التطبيق محليًا بـ Soft Launch | أنت/وكيل | `SOFT_LAUNCH=true` + ملف env |
| F6 | فحص 60 ثانية كمؤسس | أنت | افتح `/` و`/dashboard#trust-pulse` و`/oracle-accuracy` |
| F7 | `GET /api/acceptance/60s` على BASE المحلي | سكربت | آلة تساعد؛ الإحساس بشري |
| F8 | تحميل إضافة المتصفح unpacked | أنت | Chrome → `browser_extension/` |
| F9 | قراءة مسودات Glass Box (بدون نشر مدفوع) | أنت | `/api/glass-box/announce-drafts` — النشر لاحقًا مجانًا على حساباتك |
| F10 | UptimeRobot مجاني على `/health/live` | أنت | حساب مجاني — بعد وجود URL عام |
| F11 | Cloudflare Free (إن كان النطاق عندك مسبقًا) | أنت | بدون شراء WAF مدفوع؛ الخطة المجانية تكفي للبداية |
| F12 | Google/GitHub OAuth (مجاني) | أنت | Developer Console — اختياري Soft Launch |

---

## ما يُؤجَّل لأنه يدفع أو يحتاج شراء/PSP

- Lemon/Stripe + شراء تجريبي (H1)
- WhatsApp Cloud مدفوع/Meta Business مكتمل (H2) — wa.me click-to-send يعمل بدونه
- Postgres/Redis مدفوع على هوست إن لم تتوفر طبقة مجانية
- نطاق جديد مدفوع / شهادة مدفوعة / pentest مدفوع / SOC2

---

## الخطوة 1 — أسهل طريقة (ويندوز / Notepad)

**الطريقة الأسهل:** من مجلد المشروع انقر مرتين على:

`scripts/open_softlaunch_env.bat`

أو من Command Prompt / PowerShell داخل مجلد المشروع:

```bat
python scripts\open_softlaunch_env.py
```

أو مباشرة:

```bat
notepad .env.softlaunch.local
```

إذا قال إن الملف غير موجود:

```bat
python scripts\bootstrap_free_human_ops.py --admin-email mopayment1@gmail.com
notepad .env.softlaunch.local
```

---

## أوامر فورية

```bash
# 1) أسرار Soft Launch (لا تُطبع الأسرار)
python scripts/bootstrap_free_human_ops.py --admin-email mopayment1@gmail.com
# فتح الملف (ويندوز = Notepad)
python scripts/open_softlaunch_env.py

# 2) تدقيق هندسي
python scripts/security_max_audit.py

# 3) تشغيل محلي (مثال)
set -a; source .env.softlaunch.local; set +a
python -m uvicorn dashboard:app --host 127.0.0.1 --port 8080

# 4) فحوصات
curl -s http://127.0.0.1:8080/health/live
curl -s "http://127.0.0.1:8080/api/acceptance/60s?base_url=http://127.0.0.1:8080" | jq .
curl -s http://127.0.0.1:8080/api/public/zero-tolerance-closure | jq .all_done_for_agreed_scope
curl -s http://127.0.0.1:8080/api/strategy/priority-chain | jq .all_done_for_agreed_scope
```

---

## قائمة تحقق المؤسس (F6) — 10 دقائق

1. الصفحة الأولى تجيب: Act/Wait الآن؟  
2. Why ظاهر في أقل من 5 ثوانٍ  
3. Freshness/لا LIVE كاذب  
4. `/oracle-accuracy` يفتح ويظهر أخطاء إن وجدت  
5. `/zero-tolerance` و`/priority-chain` يفتحان  
6. لا تنفيذ حي (Soft Launch)  
7. سجّل ملاحظة ذهنية: هل تفهم القيمة بدون شرح؟

---

## بعد مجانية اليوم

انشر على أي هوست **مجاني/موجود** عندك → عيّن `APP_BASE_URL` → UptimeRobot مجاني → انشر مسودة Glass Box على حساب اجتماعي مجاني.

**قاعدة:** لا تدفع شيء حتى يثبت شخص واحد عادة Act/Wait.
