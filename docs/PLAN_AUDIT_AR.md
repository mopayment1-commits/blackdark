# خطة التحقيق — Excel vs BLACKDARK

> **المصدر:** `خطوات التحقيق - Copy.xlsx`  
> **آخر مراجعة:** 2026-07-25

---

## التقدم الإجمالي

| المؤشر | القيمة |
|--------|--------|
| **نسبة الإنجاز** | ~**82%** (weighted) |
| **مكتمل** | 35+ نقطة |
| **جزئي** | 8 نقاط |
| **مخطط** | 2 (Mobile native + SEC filings) |

```bash
python scripts/run_plan_audit.py
# أو افتح: http://127.0.0.1:8080/plan
```

---

## ما تم من Excel — مكتمل ✅

| الفئة | أمثلة |
|-------|--------|
| **مراجحة** | cross-exchange, triangular, funding, spot/futures, 77-type catalog |
| **لوحة التحكم** | Live dashboard, heatmap, arbitrage scan, net profit after fees |
| **AI** | Oracle, Market Radar narrative, Opportunity Score, Whale Intelligence |
| **Features** | Journal, Weekly reports, Profit analytics, Trade simulator, AI chat |
| **تنفيذ** | Panic button, dry-run + auto-exec, execution speed metric |
| **B2B** | WebSocket feed, Research Lab, on-chain overview |
| **اشتراكات** | free / pro / whale + Stripe |

---

## جزئي — يحتاج تعزيز ⚠️

| النقطة | الحالة | الخطوة التالية |
|--------|--------|----------------|
| 100 منصة | 103 مصادر، live على Tier-1 | توسيع CCXT fetchers |
| تحديث sub-second | WS 100–800ms | Kraken + más venues |
| تنفيذ live تلقائي | dry-run افتراضي | مفاتيح المستخدم + LIVE mode |
| CEX↔DEX | scan موجود | تنفيذ on-chain |
| WhatsApp alerts | wa.me links | Twilio/WhatsApp Business API |
| DeFi arb (Aave flash) | catalog planned | smart contract integration |

---

## مخطط — لاحقاً 📋

- تطبيقات Desktop / Android / iPhone (PWA web متاح الآن)
- SEC filings AI (خارج نطاق crypto core)

---

## أوامر الاستكمال

```bash
start_blackdark.bat          # تشغيل كامل
python scripts/run_plan_audit.py
python -m pytest tests/test_plan_audit.py -q
```

---

## Endpoints جديدة (هذه الجولة)

| Path | الغرض |
|------|-------|
| `/plan` | صفحة خطة التحقيق بالعربي |
| `/api/plan/audit` | JSON audit vs Excel |
| `/api/market/radar-narrative` | Market Radar بصيغة Excel |
| `/api/execution/speed` | Execution Speed panel |
