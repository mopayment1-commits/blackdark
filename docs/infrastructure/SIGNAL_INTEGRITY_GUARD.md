# Signal Integrity Guard (#1053)

**Sprint 2 · Signal Engine + Data Engine · NOT standalone**

Pre-filter detecting manipulated/spoofed signals before they reach users.

## 5 Rule-Based Patterns

1. **Wash Trading** — same address buyer + seller
2. **Volume Spike** — volume up without price movement
3. **Social Burst** — mentions from new/duplicate accounts
4. **Order Book Spoofing** — cancel after signal
5. **Timestamp Manipulation** — future or mislabeled stale data

Plus: **Single Source** → "Spoof Risk" flag

## Output

> "إشارة مشبوهة — مصدر مُحتمل للتلاعب"

NOT: "تم اكتشاف جريمة"

## Sequence

```
Integrity Guard → Outlier (#1026) → Signal Engine filters → Scoring
```

## API

- `GET /api/platform/signal-integrity/{status,e2e}`
- Hooked into `signal_registry.register_signal()`

## Integrations

- #1026 Outlier · #960 Fraud · #945 Provenance · #1017 Incident (>10 flags/hour)
