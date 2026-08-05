# BLACKDARK — حزمة الإعلان والإطلاق (Go-Live Pack)

> دستور المنتج: [`PRODUCT_CONSTITUTION_AR.md`](./PRODUCT_CONSTITUTION_AR.md)  
> Runbook: [`RUNBOOK.md`](./RUNBOOK.md)

## 1) قبل الضغط على Deploy
```bash
python scripts/finalize_launch.py
python scripts/verify_constitution_live.py
```
- الصق `.env.launch.local` في Railway Variables  
- أضف `DATABASE_URL` (Postgres)  
- تأكد `LEMON_SQUEEZY_CHECKOUT_PRO` موجود  
- اختياري الآن: Telegram / Redis / Sentry  

## 2) بعد Deploy
افتح وتحقق:
1. `/health/live`  
2. `/api/production/guard` → `required_pass: true`  
3. `/api/launch/readiness` → `code_launch_ready: true`  
4. `/oracle/BTC?ux_mode=beginner&lang=ar` → جملة قرار عربية  
5. `/oracle-accuracy`  
6. `/dashboard`  

UptimeRobot → `APP_BASE_URL/health/live` كل 5 دقائق.

## 3) نص الإعلان (انسخ/عدّل)
**عربي:**  
BLACKDARK انطلق — قرار سوقي واحد واضح: افعل أو انتظر.  
دقة عامة قابلة للتحقق · Net-Edge Truth · عمر الفرصة بالثواني · للمبتدئ والمحترف والحيتان.  
جرّب Oracle مجاناً: `APP_BASE_URL`

**English:**  
BLACKDARK is live — one clear market decision: act or wait.  
Public verifiable accuracy · Net-Edge Truth · Opportunity Half-Life.  
Try the Oracle free: `APP_BASE_URL`

## 4) تأكيد الإطلاق داخلياً
```bash
python scripts/mark_golive.py --url https://YOUR-DOMAIN
```
هذا يضع `data/golive_announced.json` ويميز بند GO LIVE في checklist كـ done.

## 5) أول 24 ساعة
- راقب `/health/ready` والـ billing webhook  
- راكم عينات Oracle حية (flywheel)  
- لا تَعِد بربح مضمون ولا HFT  
