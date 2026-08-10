# دستور Zero-Tolerance — عيوب تدمّر الثقة (ملزم)

**الحالة:** Binding · أعلى معيار صدق للإطلاق  
**التاريخ:** 2026-08-10  
**API:** `GET /api/strategy/zero-tolerance` · `GET /api/public/zero-tolerance-closure`  
**صفحة:** `/zero-tolerance`  
**الحكم:** `all_done_for_agreed_scope: true` · `deferred_code_count: 0`

---

## العقيدة

هذه ليست Wow Features. هذه **عيوب Zero-Tolerance** — إن ظهرت كسلوك منتج، تُفقد الثقة.

| # | العيب | القاعدة |
|---|------|---------|
| 1 | AI Hallucinations | لا اختراع سعر/حدث/حوت/خبر/احتمال — إن جُهل → Unknown/WAIT |
| 2 | Stale Data | ممنوع LIVE مع بيانات متأخرة — Source + timestamp + freshness |
| 3 | Fake Precision | ممنوع «سيصل $X في Y ساعة» كحقيقة — سيناريوهات + ثقة + إبطال |
| 4 | Dashboard Hell | الشاشة الأولى: What matters right now؟ |
| 5 | Generic AI | لا ChatGPT بجلد كريبتو — سياق سوق/محفظة/أدوات |
| 6 | Alert Spam | كل تنبيه: لماذا يهمّني؟ |
| 7 | Black Box Scores | لا درجة بلا Why + ما يخفضها |

---

## التنفيذ

- `zero_tolerance.apply_zero_tolerance` على مسار Oracle  
- نفس البوابة على Trust Pulse  
- بوابة تقييم: LIVE / score / alert / fake precision  

```bash
pytest tests/test_zero_tolerance.py -q
curl -s localhost:8080/api/public/zero-tolerance-closure \
  | jq '.all_done_for_agreed_scope,.deferred_code_count,.strict_confirmation'
```

**جملة التأكيد:** Zero-Tolerance قانون منتج منفَّذ — نفضّل عدم المعرفة على المسرح.
