# BLACKDARK — رفع مجاني على Render (بديل Railway)

> الهدف: لينك إنترنت مجاني بعد ما خلصت تجربة Railway  
> الكود يدعم `SOFT_LAUNCH=true` (SQLite بدون Postgres)

## حالة مسار «بدون بطاقة» (ملزم)

**Render طلب بطاقة ائتمان للتحقق من الهوية** (`Add credit card to verify your identity` — تفويض مؤقت $1).

تحت سياسة **FREE human ops = بدون دفع/شراء/بطاقة**:

| الحالة | القرار |
|--------|--------|
| Render يطلب بطاقة للتحقق | **مؤجّل / خارج المسار المجاني الصارم** |
| هل نضيف بطاقة «عشان مجاني»؟ | **لا** — يخرج من FREE playbook |
| Soft Launch المحلي | **مكتمل بدون Render** |
| متى نعود لـ Render؟ | فقط إذا قبل المؤسس إضافة بطاقة تحقق عن وعي |

مرجع المسار المجاني المكتمل محليًا: [`FREE_HUMAN_OPS_PLAYBOOK_AR.md`](./FREE_HUMAN_OPS_PLAYBOOK_AR.md)

---

## خطوات (إن قبلت لاحقًا تحقق البطاقة)

### 1) ادخل Render
افتح: https://dashboard.render.com  
سجّل بحساب GitHub (نفس حساب المستودع).

### 2) New → Blueprint
1. **New +**
2. اختار **Blueprint**
3. اربط مستودع: `mopayment1-commits/blackdark`
4. Branch: **main**
5. Render هيقرأ ملف `render.yaml` تلقائياً
6. اضغط **Apply**

### 3) عبّي 3 قيم فقط (الباقي يتولد لوحده)
في Environment للخدمة `blackdark-web`:

| الاسم | القيمة |
|------|--------|
| `ADMIN_EMAILS` | إيميلك (مثال: `you@gmail.com`) |
| `APP_BASE_URL` | سيبه فاضي أول مرة → بعد أول Deploy انسخ اللينك اللي Render يدّيه وحطه هنا |
| `LEMON_SQUEEZY_CHECKOUT_PRO` | اختياري — لو عندك لينك Lemon؛ أو سيبه فاضي في soft launch |

**مهم:** `SOFT_LAUNCH=true` موجود في `render.yaml` — متشيلوش.

### 4) استنى الـ Deploy
Deploy → Logs → لما تشوف Success  
اللينك شكلّه: `https://blackdark-web.onrender.com`

### 5) حدّث APP_BASE_URL
Environment → `APP_BASE_URL=https://YOUR-SERVICE.onrender.com` → Save → Redeploy مرة.

### 6) جرّب القرار
افتح اللينك → Oracle → BTC  
المفروض تشوف **ACT** أو **WAIT** + جملة واضحة.

---

## ملاحظات مجانية صادقة
- حتى مع خطة Free، Render قد يطلب **بطاقة تحقق** — وهذا ليس «مجاني بلا بطاقة».
- الخدمة المجانية على Render **تنام** بعد سكون (~15 دقيقة) — أول فتح بعد النوم ياخد 30–60 ثانية.
- مش HA / مش 10k مستخدم — للتجربة والإطلاق الناعم فقط.
- لما تحب إنتاج جاد: Postgres + Billing webhooks + `SOFT_LAUNCH=false`.

## لو Blueprint فشل
**New → Web Service** يدوياً:
- Runtime: Python 3
- Build: `pip install -r requirements-prod.txt`
- Start: `python run_service.py web --port $PORT`
- Health: `/health/live`
- نفس متغيرات البيئة فوق + `SOFT_LAUNCH=true`
