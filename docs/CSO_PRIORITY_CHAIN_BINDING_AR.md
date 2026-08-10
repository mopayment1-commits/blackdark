# دستور سلسلة أولويات الـ CSO (ملزم)

**الحالة:** Binding · أعلى من إضافة ميزات جديدة  
**التاريخ:** 2026-08-10  
**API:** `GET /api/strategy/priority-chain` · `GET /api/public/cso-priority-closure`  
**صفحة:** `/priority-chain`  
**الحكم:** `all_done_for_agreed_scope: true` · `deferred_code_count: 0`

---

## السلسلة المعتمدة (بعد تصحيح الخبير)

```
Product Excellence
↓
Unique Intelligence
↓
Distribution Engine + Habit Loop
↓
Data Flywheel
↓
Early Revenue
↓
Institutional Proof
↓
Strategic Moat
↓
Acquisition Leverage
```

### مرفوض نهائيًا
`Features → Features → Features → Launch → Users → Acquisition`

---

## القاعدة الملزمة

**لا ميزة جديدة ما لم ترفع:** عادة القرار · أو التوزيع · أو الإيراد · أو الموآت الحي (data flywheel)  
(يُسمح أيضًا بتعميق Unique Intelligence من نوع Prove-it / Kill-Rate / Net-Edge فقط)

تحقق الاقتراح:

```bash
curl -s "localhost:8080/api/strategy/priority-chain/evaluate?title=coverage+vanity&lever=acquisition_leverage" | jq .allowed
# expected: false
```

---

## ماذا يعني لكل مرحلة

| # | المرحلة | المعنى التشغيلي |
|---|---------|-----------------|
| 1 | Product Excellence | عادة Act/Wait واحدة + Trust Pulse |
| 2 | Unique Intelligence | صدق علني لا تغطية أوسع |
| 3 | Distribution + Habit | مشاركة إثبات + عودة يومية معًا |
| 4 | Data Flywheel | قرارات حية مُسمّاة فقط |
| 5 | Early Revenue | Proof→Pro قبل مسرح Institutional |
| 6 | Institutional Proof | Data Room بعد احتفاظ حقيقي |
| 7 | Strategic Moat | نتيجة تراكم لا مشروع منفصل |
| 8 | Acquisition Leverage | خيار لا هدف يومي للبناء |

---

## تأكيد التنفيذ

```bash
pytest tests/test_cso_priority_chain.py -q
curl -s localhost:8080/api/public/cso-priority-closure \
  | jq '.all_done_for_agreed_scope,.deferred_code_count,.strict_confirmation'
```

**جملة التأكيد:** سلسلة CSO صارت قانون منتج قابل للتحقق — أهم من إضافة عشرات الإمكانيات.
