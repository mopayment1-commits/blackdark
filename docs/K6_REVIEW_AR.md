# مراجعة تشغيل k6 (2026-08-09)

## ما الذي نجح عندك؟

```text
✓ status is 200
http_req_failed: 0.00%
http_req_duration avg ≈ 521ms
1 VU · 1 iteration
```

**الحكم:** Smoke ناجح — السيرفر على `:8080` يرد 200، والشبكة المحلية تعمل.

## ما الذي *لا* يثبته هذا التشغيل؟

| الادعاء | هل أثبته تشغيلك؟ |
|---------|------------------|
| الموقع يفتح محليًا | نعم |
| تحمل إطلاق فيروسي | **لا** (1 مستخدم وهمي فقط) |
| Postgres + Redis HA | **لا** |
| Oracle تحت ضغط | **لا** (غالبًا طلب واحد لمسار واحد في `test.js`) |
| جاهزية للاستحواذ كرقم capacity | **لا** — يحتاج صفًا في `LOAD_TEST_RUN_LOG.md` |

تشغيل `1 VU / 1 iter` = فحص حياة، ليس اختبار حمل.

## الخطوة التالية الموصى بها (محلي Soft Launch)

من مجلد المشروع (والسيرفر شغال):

```bat
k6 run scripts\k6_trust_os_smoke.js
k6 run -e BASE=http://127.0.0.1:8080 -e VUS=10 -e DURATION=30s scripts\k6_trust_os_smoke.js
```

أو هارنس المشروع:

```bat
python scripts\load_test.py --base http://127.0.0.1:8080 --requests 100
python scripts\load_test_concurrent.py --base http://127.0.0.1:8080 --workers 20 --requests 100
```

## معيار إثبات HA الصادق

لا تُكتب أرقام تحمل تسويقية إلا بعد:

1. `DATABASE_URL=postgresql://…` + `REDIS_URL=redis://…`
2. `WEB_CONCURRENCY` ≥ 2 وبدون Soft Launch للوضع الفيروسي
3. تعبئة صف حقيقي في [`LOAD_TEST_RUN_LOG.md`](./LOAD_TEST_RUN_LOG.md)

هذا يبقى **HUMAN_OPS** — ليس سهو كود.
