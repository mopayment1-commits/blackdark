# BLACKDARK — Data Trust Law (ملزم)

> **Status:** Binding · quiet engine under the six heroes — not a seventh product  
> **Adopted:** 2026-08-13  
> **Parent:** [`PRODUCT_CONSTITUTION_AR.md`](./PRODUCT_CONSTITUTION_AR.md) · [`CANONICAL_BINDING.md`](./CANONICAL_BINDING.md) · [`STRATEGIC_CORRECTION_BINDING.md`](./STRATEGIC_CORRECTION_BINDING.md)  
> **API:** `GET /api/strategy/data-trust-law` · `GET /api/public/canonical-market-state`  
> **Code:** `data_trust_engine.py` · `data_source_trust.py` · `canonical_market_state.py`

---

## حكم التنفيذ (ما يُبنى الآن / ما لا يُبنى)

| يُنفَّذ الآن | لا يُنفَّذ الآن |
|---------------|------------------|
| قانون الطبقات + تصنيف المصادر الموجودة | إدخال 100 مصدر جديد |
| Observation envelope + إجماع/ حجر / عقوبة مصدر واحد | Kaiko / Coin Metrics / Amberdata / CoinAPI كتكامل مدفوع |
| Canonical Market State للأصول الأساسية من venue-direct فقط | Bloomberg / LSEG / Reuters / FT / WSJ |
| Honesty gate: ممنوع L2 وهمي من CoinGecko/مجمّع | محرك جيوسياسي يصدر حكمًا سعريًا |
| Fail-closed: بيانات تجميعية/مصنَّعة لا تُعامل كدفتر قابل للتنفيذ | بحيرة vintage كاملة لكل سلاسل FRED |
| وسم CoinGecko/CMC كاكتشاف/احتياطي غير قراري | سطح منتج «100 API» أو Financial Truth Layer مستقل |

**المعيار:** هل الرقم الذي يظهر للمستخدم/الصندوق يحمل مصدرًا مباشرًا، زمنًا، جودة، رخصة، واتفاقًا؟ إن لم يحملها، النظام يرفض أن يقرر.

---

## القانون

1. **لا مسار CoinGecko → BLACKDARK → User كحقيقة سوقية.** ولا «100 API → Dashboard».
2. **Tier A — Primary Truth:** دفتر/صفقات venue عبر REST/WS مباشر. لا تصنيع L2 لبورصة لا توفر L2.
3. **Tier B — Independent verification:** مجمّع/مرجع مؤسسي = مقارنة لاحقة، ليس رقم القرار.
4. **Tier C — On-chain:** سلسلة مستقلة عن البورصة. RPC عام واحد ليس إنتاجًا.
5. **Tier D — Macro:** FRED/Fed سياق نظام. الأرقام الاقتصادية تُحفظ بـvintage عند توفرها — ليس «آخر رقم» وحده كحقيقة تاريخية.
6. **Tier E — News:** أصل حكومي > سلك > تحليل. ممنوع أن يقرر LLM صدق الخبر من 50 موقعًا.
7. **Tier F — Geopolitics:** سلسلة سببية بثقة — ممنوع «حدث = BTC ينخفض».
8. **لا مصدر معصوم.** فشل → بديل. خلاف → حجر. متقادم → رفض. شاذ → تحقيق. مصدر واحد → عقوبة ثقة.
9. **الخندق:** تحويل مصادر متعارضة إلى حالة سوقية قابلة للتدقيق ثم Intelligence — **تحت** Oracle/الأبطال، لا كمنتج يُباع بعدد الـAPI.

---

## Phase I المسموح تشغيله كقراري

venues حية ذات دفتر مباشر (native/CCXT) + سلاسل قائمة أصلًا + FRED/SEC/CFTC إن وُجدت في السجل + CoinGecko/CMC **بوسم fallback/discovery فقط**.

أي مصدر لا يغيّر Act/Wait أو لا يرفع إثباته = ليس Phase I.
