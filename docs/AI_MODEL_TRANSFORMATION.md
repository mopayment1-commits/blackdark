# BLACKDARK — خطة تحويل المشروع إلى نموذج ذكاء صناعي

> **تاريخ التسجيل:** 2026-07-25  
> **الهدف العام:** جذب عدد مهول من المستخدمين عند الإطلاق + بيع المنتج لشركة استحواذ (12–18 شهر)  
> **المنتج الأساسي:** نموذج AI متخصص في crypto market intelligence — الويب = واجهة التوزيع

---

## 1. التحول الاستراتيجي

### قبل
- منصة ويب + قواعد scoring (rules engine)
- Oracle = أوزان ثابتة + heuristics
- Retrain = تعديل أوزان يدوي (`oracle_retrainer.py`)

### بعد (الهدف)
- **BLACKDARK Oracle Model** — نموذج مدرب على بيانات حية
- Dataset proprietary: 100 منصة × 105 عملة × labels زمنية
- Flywheel: predict → wait → label → train → deploy → repeat
- الويب سايت = distribution + B2B API + proof of accuracy

### ما الذي يُباع للمستحوِذ؟
| Asset | الوصف |
|-------|--------|
| Proprietary dataset | millions of labeled predictions (parquet) |
| Trained models | direction + verdict classifiers (joblib) |
| Data moat | 100-exchange coverage لا يُنسخ بسرعة |
| Users + API revenue | distribution + MRR |
| Public accuracy track record | إثبات IP |

### Target Acquirers
Binance Labs, OKX, Kaiko, Amberdata, TradingView, Messari, Nansen, eToro, Revolut Crypto, Coin Metrics

### Valuation Range (realistic)
- 10K MAU + model >58% accuracy → **$3–5M**
- $500K ARR + B2B API → **$5–10M**
- 50K users + unique dataset → **$10–15M+**

---

## 2. مراحل التنفيذ التقني

### Phase 0 — Data Flywheel ✅ (منفّذ)
**الملفات:**
- `ml/labeling_pipeline.py` — تسجيل + resolve @ 1h/4h/24h
- `ml/feature_store.py` — feature vector per asset
- `ml/train_baseline.py` — GradientBoosting direction model
- `ml/inference.py` — predict API
- `ml_flywheel_scheduler.py` — cron كل ساعة
- `ml/experience_log.py` — سجل خبرات التدريب
- `ml/train_ensemble.py` — ensemble multi-model

**Database:**
- `oracle_predictions` — extended: price_after_1h/4h, label, direction_label, features_json
- `ml_model_runs` — training history
- Export: `data/training/labeled_oracle_dataset.parquet`

**Endpoints:**
- `GET /api/ml/status`
- `POST /api/ml/flywheel/run`
- `POST /api/ml/train`
- `GET /api/ml/predict/{asset}`
- `GET /api/oracle/accuracy/public`
- `GET /oracle-accuracy` — صفحة عامة
- `GET /api/ml/experience` — سجل التعلم
- `POST /api/ml/train/ensemble` — تدريب ensemble

### Phase 1 — Baseline ML (شهر 2–4)
- LightGBM / GradientBoosting على 50+ labeled samples
- Target: direction accuracy >58%
- Replace `forecast_engine.py` EMA with model inference

### Phase 2 — Multi-Modal Fusion (شهر 4–7)
- Inputs: technical, on-chain, sentiment, macro, whale, market microstructure
- Neural net / ensemble replaces `weight_aggregator.py` static weights

### Phase 3 — Oracle Fine-Tuned (شهر 7–10)
- Classification: Buy Now / Do Not Touch
- Training from resolved oracle audits
- Optional LLM layer for explanations only

### Phase 4 — Model-as-Product (شهر 10–12)
- `POST /v1/predict` public API
- Stripe tiers: Free / Pro / B2B / Enterprise

---

## 3. مراحل التسويق والاستحواذ

### Phase A — Proof of AI (شهر 1–3)
- صفحة Oracle Accuracy Live (public)
- Product Hunt + crypto Twitter
- Telegram bot مجاني (3 alerts/day)
- KPI: 1,000 waitlist + 500 DAU

### Phase B — Viral Launch (شهر 3–6)
- "Track our AI — every prediction published"
- Referral program
- Arabic-first market (MENA underserved)
- KPI: 10,000 registered + 2,000 DAU

### Phase C — Monetize (شهر 6–12)
- Free: 5 queries/day | Pro: $29/mo | B2B: $500–5K/mo
- KPI: $30K MRR or 5 B2B clients

### Phase D — Acquisition Ready (شهر 12–18)
- Data room: dataset + models + metrics + revenue
- Outreach: Kaiko, Amberdata, TradingView, Binance Labs

---

## 4. بنية ML في المشروع

```
BLACKDARK/
├── ml/
│   ├── labeling_pipeline.py    # Flywheel: label + export
│   ├── feature_store.py        # Features from DB + signals
│   ├── train_baseline.py       # Direction classifier v1
│   ├── train_ensemble.py       # Multi-model ensemble
│   ├── inference.py            # Runtime predictions
│   ├── experience_log.py       # Training experience journal
│   └── public_accuracy.py      # Public transparency API
├── data/
│   ├── training/               # labeled_oracle_dataset.parquet
│   ├── models/                 # *.joblib artifacts
│   └── ml_experience_log.jsonl # Full learning history
├── ai_oracle.py                # Logs every evaluation → training sample
└── ml_flywheel_scheduler.py    # Background loop
```

---

## 5. Feature Vector (Current)

| Feature | Source |
|---------|--------|
| price, ret_1h, ret_4h, ret_24h, volatility | pricing_logs |
| sentiment_score, sentiment_momentum | sentiment_engine |
| obi_score, obi_imbalance | obi_predictor |
| macro_weight | macro_correlations |
| opportunity_score, confidence | oracle evaluation |

---

## 6. KPIs للنموذج

| Metric | Baseline | Target Phase 1 |
|--------|----------|----------------|
| Direction accuracy 24h | ~50% | **>58%** |
| MAPE price forecast | EMA 3–5% | **<2.5%** |
| Oracle verdict accuracy | rules ~55% | **>65%** |
| Labeled samples | 6+ (live) | **10,000+** |
| Model retrain frequency | hourly check | weekly full retrain |

---

## 7. Environment Variables

```env
ML_FLYWHEEL_ENABLED=true
ML_FLYWHEEL_INTERVAL_SEC=3600
ML_MIN_TRAIN_SAMPLES=50
ML_AUTO_TRAIN=true
```

---

## 8. Timeline Master

```
شهر 1–2:   Flywheel + first model + Oracle Accuracy page
شهر 3:     Launch + Product Hunt → 1K users
شهر 4–6:   Viral → 10K users
شهر 6–9:   B2B → $10K MRR
شهر 9–12:  Model v2 + acquisition talks
شهر 12–18: Exit ($3–10M)
```

---

## 9. Commits Reference

| Commit | Content |
|--------|---------|
| `0b73d22` | 100-exchange universe (B2+C+D) |
| (pending) | AI flywheel + Oracle Accuracy Live |

---

## 10. مرجع التصميم التقني

التفاصيل المعمارية للنموذج المالي (ميزات، مسار القرار، الحراس، مراحل التنفيذ الهندسي):

→ [`docs/AI_FINANCIAL_MODEL_DESIGN.md`](./AI_FINANCIAL_MODEL_DESIGN.md)

---

*هذا الملف هو المرجع الرسمي لتحويل BLACKDARK من منصة ويب إلى نموذج ذكاء صناعي.*
