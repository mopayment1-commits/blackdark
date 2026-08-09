# إغلاق جذري — ضعف العلامة + ضعف التغطية النسبية

**التاريخ:** 2026-08-09  
**الحكم:** **مغلق 100% كمنتج** وفق أعلى معيار جودة (صدق > تفاخر بالتغطية).  
**API الحالة:** `GET /api/public/brand-coverage-closure` → `product_complete: true` · `all_done: true`

---

## المشكلة → الحل المنفَّذ

| المشكلة | الحل الجذري | الأسطح الحية |
|---------|-------------|----------------|
| علامة أحدث | علامة الإثبات: نبدأ بالغلط + نفاخر بالرفض + ضريبة العاطفة + جدول Glass Box | `/miss-feed` · `/kill-rate` · `/emotion-tax` · announce-schedule |
| تغطية أضيق نسبيًا | صدق التغطية: LIVE ≠ PLANNED + Provenance Score على كل قرار | `/coverage-honesty` · `/api/oracle/provenance-score` |

---

## مذهب الجودة (ملزم)

1. **لا ندّعي 100 منصة حية** إن لم تكن `ingestion_ready`.  
2. **كل قرار** يحمل `data_provenance` (عبر `attach_oracle_freshness`).  
3. **الأخطاء تُنشر أولًا** (Miss Feed) — هذا هو بناء العلامة.  
4. التوسيع لاحقًا فقط حين يرفع Net-Edge / Fund Terminal — ليس للزينة.

---

## تحقق

```bash
pytest tests/test_brand_coverage_radical_closure.py -q
curl -s localhost:8080/api/public/brand-coverage-closure | jq .all_done,.product_complete
```

---

**جملة التأكيد:** أثر ضعف العلامة والتغطية النسبية **أُغلق منتجيًا** بتحويلهما إلى أصول ثقة علنية قابلة للمشاركة والتحقق.
