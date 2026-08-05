# BLACKDARK — تصميم نموذج الذكاء الاصطناعي المالي

> **الغرض:** مرجع تقني لتصميم وتشغيل نموذج AI مالي متخصص في crypto market intelligence  
> **المنتج:** Oracle يقيّم فرص المراجحة والاتجاه، مع مسار تعلم مستمر (flywheel)  
> **الوضع الحالي:** Rules engine + ML baseline/ensemble + RL policy خفيف + حماية drift/OOD  
> **التفرد الشغّال:** انظر `docs/UNIQUE_DIFFERENTIATORS_AR.md` (Net-Edge Truth · Half-Life · Signal Registry · Evidence Pack · Persona Clarity)

---

## 1. الهدف من النموذج

النموذج لا يتنبأ بسعر عشوائي فقط — بل يُنتج **قراراً قابلاً للتدقيق**:

| المخرج | المعنى | الاستخدام |
|--------|--------|-----------|
| `opportunity_score` (0–100) | جودة فرصة المراجحة | فلترة / ترتيب الفرص |
| `oracle_verdict` | Buy Now / Wait / Do Not Touch | واجهة المستخدم + API |
| `direction` (up / down / flat) | اتجاه السعر على أفق 1h/4h/24h | نموذج ML المدرب |
| `confidence` | ثقة معايرة | gating قبل العرض أو التنفيذ |
| `explanation` | أسباب + مخاطر | شفافية للمستثمر / المشتري |

**مبدأ التصميم:** القرار النهائي = قواعد مؤسسية + إشارات متعددة الوسائط + ML عند توفره، مع **fail-closed** عند OOD أو drift.

---

## 2. المعمارية العامة

```
┌─────────────────────────────────────────────────────────────────┐
│                     مصادر البيانات (Ingestion)                   │
│  CEX REST/WS · Order books · Funding · Sentiment · Macro · Whale │
│  On-chain · Options · Data lake (Parquet)                        │
└──────────────────────────────┬──────────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Feature Store (`ml/feature_store.py`)          │
│  price · returns · volatility · sentiment · OBI · macro_weight    │
└──────────────────────────────┬──────────────────────────────────┘
                               ▼
        ┌──────────────────────┼──────────────────────┐
        ▼                      ▼                      ▼
┌───────────────┐    ┌─────────────────┐    ┌──────────────────┐
│ Rules Oracle  │    │ ML Direction    │    │ RL Policy (PPO)  │
│ ai_oracle.py  │    │ inference.py    │    │ rl_policy.py     │
│ oracle_unified│    │ ensemble/joblib │    │ size / bias hint │
└───────┬───────┘    └────────┬────────┘    └────────┬─────────┘
        └──────────────────────┼──────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│              Decision Fusion + Guards                            │
│  conflict guard · sentiment panic · risk_manager · OOD/drift     │
│  regulatory verdict mapping                                      │
└──────────────────────────────┬──────────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│  Persist → evaluated_opportunities / oracle_predictions          │
│  Label @ 1h/4h/24h → train → deploy artifact → repeat            │
└─────────────────────────────────────────────────────────────────┘
```

### طبقات القرار (من الأسفل للأعلى)

1. **Microstructure** — OBI، عمق السوق، slippage، funding basis  
2. **Institutional context** — Whale CVVD/SII، on-chain flows، macro regime  
3. **NLP sentiment** — مركب أخبار/سوشيال مع عقوبة panic  
4. **ML direction** — classifier مدرب زمنياً (لا shuffle عشوائي)  
5. **Guards** — تعارض الأبعاد، سموم السعر، OOD reject، freeze المخاطر  

---

## 3. متجه الميزات (Feature Vector)

الميزات المستخدمة في التدريب والاستدلال (`ml/training_utils.FEATURE_COLUMNS`):

| الميزة | المصدر | الدور |
|--------|--------|-------|
| `price` | pricing_logs | مستوى السعر |
| `ret_1h` / `ret_4h` / `ret_24h` | closes محلية | زخم قصير/متوسط |
| `volatility` | متوسط \|Δreturns\| | مخاطر التذبذب |
| `sentiment_score` | sentiment_engine | مشاعر مركّبة (−1…+1) |
| `sentiment_momentum` | rolling compound | اتجاه المشاعر |
| `obi_score` / `obi_imbalance` | obi_predictor | اختلال دفتر الأوامر |
| `macro_weight` | macro_correlations | Risk-On / Off / Neutral |

### حارس تسريب البيانات (Leakage Guard)

**يُستبعد من التدريب:** `opportunity_score` و `confidence` (مخرجات الـ rules engine).  
التدريب يستخدم فقط تنبؤات حية (`live`) ويستبعد الصفوف الاصطناعية `historical_seed`.

---

## 4. التسميات والتعلم (Labeling Flywheel)

```
predict → انتظر الأفق → قارن السعر → label → تصدير Parquet → train → deploy
```

| الأفق | عتبة الاتجاه التقريبية | الملفات |
|-------|------------------------|---------|
| 1h | ±0.35% | `ml/labeling_pipeline.py` |
| 4h | نفس المنطق على نافذة أطول | + `ml_flywheel_scheduler.py` |
| 24h | الهدف الرئيسي للدقة العامة | + `oracle_track_record.py` |

**Outputs المخزّنة:**
- `oracle_predictions` — features_json + price_after_* + direction_label  
- `ml_model_runs` — سجل كل تدريب  
- `data/training/labeled_oracle_dataset.parquet` — dataset قابل للبيع/التدقيق  
- `data/models/*.joblib` — أوزان النموذج  

---

## 5. نماذج التعلم الآلي

### 5.1 Baseline — Direction Classifier
- **الخوارزمية:** GradientBoosting (scikit-learn)  
- **التحقق:** chronological hold-out (ماضي → مستقبل)  
- **الملف:** `ml/train_baseline.py`  
- **عتبة عينات:** `ML_MIN_TRAIN_SAMPLES` (افتراضي 50)

### 5.2 Ensemble
- GradientBoosting + RandomForest → soft VotingClassifier  
- **الملف:** `ml/train_ensemble.py`

### 5.3 Inference + حماية
- تحميل أحدث artifact → بناء features → OOD score  
- إذا OOD أو لا يوجد نموذج → **رجوع آمن للقواعد** (`engine: rules`)  
- معايرة الثقة عبر `ml/drift_monitor.py`  
- **الملف:** `ml/inference.py`

### 5.4 RL Policy (اختياري / مساعد)
- سياسة خطية PPO-like على `(ret_24h, volatility, obi_score, sentiment_score)`  
- لا تستبدل Oracle؛ تُستخدم كتوجيه حجم/انحياز  
- **الملف:** `ml/rl_policy.py`

---

## 6. مسار Oracle الموحّد (قرار واحد)

`oracle_unified.py` يفرض مساراً واحداً للداشبورد والمراجحة:

```
base technical score
  → أبعاد متعددة الوسائط (regime-weighted)
  → حل تعارض الأبعاد (dimension_conflict_guard)
  → عقوبات sentiment panic / greed
  → تعديل hub / ML اختياري
  → verdict عام متوافق تنظيمياً
```

### أوزان الفرصة في `ai_oracle.py` (قواعد)

| البُعد | الوزن |
|--------|-------|
| الربح الصافي | 40% |
| السيولة | 35% |
| الاستقرار / الانزلاق | 25% |

**تعديلات سياقية:** Whale، OBI، on-chain، sentiment (±4 أو −25 عند panic)، macro ×1.08 / ×0.92.

---

## 7. المخاطر والحوكمة داخل النموذج

| الحارس | الملف | السلوك |
|--------|-------|--------|
| OOD reject | `ml/drift_monitor.py` | رفض استدلال ML عند توزيع غير مألوف |
| Drift / PSI | نفس الملف | تجميد مؤقت عند انحراف الميزات |
| Sentiment panic | `sentiment_gate.py` / engine | حجب أو خصم كبير من الدرجة |
| Risk freeze | `risk_manager.py` | وقف عند سموم سعر / تجاوز slippage |
| Wash trade / spoof | `wash_trade_guard.py`, whale CVVD | تقليل الثقة المؤسسية |
| Regulatory mapping | `regulatory_compliance_guard.py` | verdict عام آمن (ليس نصيحة استثمارية) |

**Fail-closed:** عند الشك → لا تعتمد ML؛ ارجع للقواعد أو `WAIT` / `Do Not Touch`.

---

## 8. واجهات المنتج المرتبطة بالنموذج

| Endpoint / صفحة | الدور |
|-----------------|-------|
| `GET /api/ml/status` | حالة flywheel والنموذج |
| `POST /api/ml/train` / `.../ensemble` | تدريب يدوي |
| `GET /api/ml/predict/{asset}` | استدلال اتجاه |
| `GET /api/oracle/accuracy/public` | شفافية الدقة |
| `GET /oracle-accuracy` | صفحة عامة للمستثمرين |
| `GET /api/oracle/track-record` | سلسلة تدقيق غير قابلة للتلاعب |
| B2B institutional feed | تصدير إشارات مؤسسية |

---

## 9. ما الذي يميّز النموذج مالياً (Data Moat)

1. **Dataset مملوك:** تنبؤات مُسمّاة على أفق زمني حقيقي من تشغيل حي  
2. **تغطية منصات:** مسار توسع 50–100 منصة عبر operational manifest  
3. **Multi-modal:** سعر + دفتر أوامر + مشاعر + ماكرو + حيتان + on-chain  
4. **Track record عام:** إثبات دقة قابل للتدقيق قبل الاستحواذ  
5. **حوكمة ML:** anti-leakage + temporal split + OOD — مطلوبة في due diligence  

---

## 10. خارطة التطوير التقني (مراحل، بدون تقويم زمني)

### مكتمل / موجود
- [x] Feature store + labeling flywheel  
- [x] Baseline + ensemble trainers  
- [x] Inference مع OOD/drift  
- [x] Unified oracle path  
- [x] Public accuracy + audit chain  

### المرحلة التالية المقترحة (تنفيذ هندسي)

| الأولوية | المهمة | المخرج المتوقع |
|----------|--------|----------------|
| P0 | توسيع الميزات: funding spread، basis، whale SII، on-chain netflow | feature vector أغنى بدون leakage |
| P0 | هدف تدريب ثانٍ: `verdict_label` (Buy/Wait/Avoid) بجانب direction | classifier قرار مباشر |
| P1 | استبدال EMA في `forecast_engine` بـ ML عند `available=true` | توقع سعري موحّد |
| P1 | LightGBM/XGBoost كمرشح ثالث في الـ ensemble | دقة أعلى على بيانات جدولية |
| P2 | فصل `model serving` microservice عن لوحة التحكم | قابلية توسع API |
| P2 | بطاقة نموذج (Model Card): ميزات، حدود، مقاييس، تاريخ إعادة التدريب | جاهزية غرفة بيانات المشتري |

---

## 11. متغيرات البيئة الأساسية

```env
ML_FLYWHEEL_ENABLED=true
ML_FLYWHEEL_INTERVAL_SEC=3600
ML_MIN_TRAIN_SAMPLES=50
ML_AUTO_TRAIN=true
ML_DRIFT_PSI_THRESHOLD=0.25
ML_OOD_REJECT_THRESHOLD=0.65
ML_OOD_FAIL_CLOSED=true
ML_DRIFT_FREEZE_SEC=300
AI_ORACLE_PROVIDER=rules
ORACLE_DATA_HUB_ENABLED=true
```

---

## 12. تعريف النجاح للنموذج

| المقياس | حد أدنى مقبول | هدف قوي |
|---------|---------------|---------|
| Direction accuracy @ 24h | >55% | >58–62% |
| Oracle verdict hit-rate | >60% | >65% |
| عينات مُسمّاة حية | ≥50 للتدريب | آلاف+ للتوسع |
| OOD false-accept | منخفض (fail-closed) | مراقبة مستمرة |
| Latency استدلال | مناسب لـ API (ليس HFT) | مستقر تحت الحمل |

---

## 13. علاقة الوثائق

| وثيقة | المحتوى |
|-------|---------|
| `docs/AI_FINANCIAL_MODEL_DESIGN.md` | **هذا الملف — التصميم التقني للنموذج** |
| `docs/AI_MODEL_TRANSFORMATION.md` | التحول الاستراتيجي والمنتج/الاستحواذ |
| `docs/FULL_ARCHITECTURE_AUDIT.md` | مراجعة هندسية شاملة + الحاصرات المتبقية |
| `project_context.md` | خريطة المنصة الكاملة |
| `ml/*` | التنفيذ الفعلي |

---

*مرجع التصميم الرسمي لنموذج BLACKDARK المالي. أي تغيير جوهري في الميزات أو مسار القرار يجب أن يُحدّث هنا وفي `FEATURE_COLUMNS` معاً.*
