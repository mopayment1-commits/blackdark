# BLACKDARK — ميزات فريدة مبهرة (فوق النواة الحالية)

> **الدستور الملزم الأعلى:** [`docs/PRODUCT_CONSTITUTION_AR.md`](./PRODUCT_CONSTITUTION_AR.md) — هذا الملف يفصّل التنفيذ التقني لـ D1–D8 فقط.  
> الهدف: منافسة العملاقة **بالتفرد** لا بالميزانية — حلول لمشاكل حقيقية لكل شريحة، مع أصول تُسيل لعاب الصناديق ولجان الاستحواذ.

---

## المشكلة التي نحلها (لكل شريحة)

| الشريحة | ألم حقيقي عند العملاقة | حل BLACKDARK الفريد |
|---------|------------------------|---------------------|
| مستخدم عادي | غرق في 200 مؤشر بلا قرار | **Persona Clarity** → فعل/انتظر بجملة عربية واضحة |
| محترف | إشارات كثيرة غير قابلة للتنفيذ | **Net-Edge Truth Score** يرفض الوهم بعد التكاليف |
| حوت | الفرصة تموت أثناء التحجيم | **Opportunity Half-Life** بالثواني + احتمال الاختفاء |
| صندوق | لا يوجد رفض مسبب قابل للتدقيق | Contradiction Veto + Registry + Evidence Pack |
| لجنة استحواذ | داشبورد لا أصل بيانات | **Signal Registry + Proof Chain + Evidence Pack** |

---

## ما أُضيف فوق النموذج الحالي (Live)

| ID | الميزة | الملف / API | لماذا تبهر؟ |
|----|--------|-------------|-------------|
| D3 | Net-Edge Truth Score | `net_edge_truth.py` · `GET /api/oracle/net-edge-truth` | أقل إشارات، أعلى قابلية تنفيذ |
| D4 | Opportunity Half-Life | `opportunity_tracker.py` · `GET /api/oracle/half-life` | زمن = مال للحيتان |
| D6 | Acquirer Evidence Pack | `acquirer_evidence_pack.py` · `GET /api/due-diligence/evidence-pack` | زر واحد لغرفة بيانات المشتري |
| D7 | Persona Clarity AR/EN | `persona_clarity.py` · `GET /api/oracle/persona-clarity/demo` | وتد MENA + وضوح لكل شريحة |
| D8 | Sovereign Signal Registry | `signal_registry.py` · `GET /api/oracle/signals` | معجم إشارات مُسمّى = Data Moat |

موجود مسبقاً ويُعزَّز بالدمج: **D1 Proof-Native Oracle** · **D2 Contradiction Veto** · **D5 Regime Weights** · Flywheel.

---

## أين تُحقن في المحرك؟

```
scan → economic net profit
     → unified multimodal score (regime)
     → Net-Edge Truth gate          ← NEW hard reject
     → Half-Life annotation         ← NEW whale clock
     → Contradiction Veto
     → Persona Clarity messages     ← NEW
     → Signal Registry row          ← NEW
     → Proof / audit chain
     → execution (skips on Truth/Half-Life kill)
```

لا يوجد محرك قرار ثانٍ — كل التفرد يركب على `unified_multimodal_v1`.

---

## جملة البيع (Investment / M&A)

> لا نبيع مؤشرات. نبيع **قرارات سوقية موثّقة**، بـ **Truth Score قابل للتنفيذ**، و**عمر فرصة متوقع**، و**معجم إشارات مُسمّى**، وحزمة إثبات جاهزة للجنة.

---

## ما لن نفعله (حراسة مصداقية)

- لا وعد HFT دون ملي ثانية
- لا «نضمن ربح»
- لا تضخيم 100 مؤشر جديد — التفرد في البوابات والإثبات لا في الأسماء

---

*يُحدَّث مع كل قدرة تفرد تُشحن للإنتاج.*
