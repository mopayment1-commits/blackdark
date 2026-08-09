# مراجعة تشغيل k6 + هدف أقل من 200ms (2026-08-09)

## تشخيص الـ521ms

تشغيلك السابق:

```text
✓ status is 200
http_req_duration avg ≈ 521ms
1 VU · 1 iteration
```

**الحكم السابق:** Smoke ناجح وظيفيًا، لكن **الوقت سيئ** ولا يمرّ شريط المنتج (<200ms بكثير).

### الأسباب التي أصلحناها في الكود

| السبب | الأثر | الإصلاح |
|--------|--------|---------|
| صورة Hero PNG ≈ **1.8MB** | بطء التحميل البصري بشدة | WebP ≈ **43–60KB** + JPEG fallback |
| `REDIS_URL` ميت (localhost بدون Redis) | مهلة socket على كل طلب — غالبًا **+80–700ms** على Windows | Negative-cache + timeout قصير (80ms) |
| كاش HTML للـlanding = 15s فقط | إعادة تصيير Jinja بلا داع | `max-age=120` + كاش in-process لكل لغة |
| سكربت k6 يخلط Oracle الثقيل مع المسارات السريعة | متوسط مضلّل | `MODE=fast` بعتبة `p(95)<200` |

على السيرفر نفسه بعد الإصلاح: `GET /` (دافئ) ≈ **5ms**؛ Hero WebP ≈ **43KB**.

## التشغيل المطلوب عندك (بعد `git pull` وإعادة تشغيل السيرفر)

```bat
cd C:\Users\o\Desktop\BLACKDARK
git fetch origin cursor/morning-final-recs-literal-eef3
git checkout cursor/morning-final-recs-literal-eef3
git pull origin cursor/morning-final-recs-literal-eef3

REM أعد تشغيل السيرفر ثم:
k6 run -e MODE=fast scripts\k6_trust_os_smoke.js
```

المتوقع:

- `fast_http_duration` → **p(95) < 200ms** و **avg < 150ms**
- المسارات: `/health/live`, `/`, `/?lang=ar`, `/login`, `/api/pricing`, WebP hero

Smoke أشمل (يشمل Oracle — قد يتجاوز 200ms وهذا متوقع):

```bat
k6 run scripts\k6_trust_os_smoke.js
```

## ما الذي *لا* يثبته هذا التشغيل؟

| الادعاء | هل أثبته؟ |
|---------|-----------|
| الموقع يفتح محليًا بسرعة | نعم (مع `MODE=fast`) |
| تحمل إطلاق فيروسي | **لا** (يحتاج VUs أعلى + Postgres/Redis) |
| إثبات HA موقّع | **لا** — صف في `LOAD_TEST_RUN_LOG.md` |

## معيار إثبات HA الصادق

1. `DATABASE_URL=postgresql://…` + `REDIS_URL=redis://…` (Redis حي)
2. `WEB_CONCURRENCY` ≥ 2 وبدون Soft Launch للوضع الفيروسي
3. تعبئة صف حقيقي في [`LOAD_TEST_RUN_LOG.md`](./LOAD_TEST_RUN_LOG.md)

هذا يبقى **HUMAN_OPS** — ليس سهو كود.
