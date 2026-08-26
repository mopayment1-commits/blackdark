# Derivatives Cross-Signal Synthesis Module — #315 (Sprint 2)

Renamed from **Cross-Derivatives Decision Intelligence** → **Derivatives Cross-Signal Synthesis Module**.

Layer **above #327** Derivatives Market State Module:
- **#327** = what is happening (market state)
- **#315** = do the signals agree (synthesis)

## Output (no Decision)

1. **Signal Agreement Matrix**
2. **Contradiction Flags**
3. **Confidence Score**

Forbidden: Decision, recommendation, buy, sell, relevance (undefined).

## Synthesis logic

| Step | Logic |
|------|-------|
| 1 | Normalization — z-score vs 30-day rolling |
| 2 | Agreement — 4+ = Convergent \| 2-3 = Mixed \| 0-1 = Divergent |
| 3 | Contradiction — >2σ opposing directions + root cause (5 categories) |
| 4 | Confidence — freshness×0.35 + source_quality×0.35 + historical_accuracy×0.30 |
| 5 | Output — matrix + flags + confidence |

## Enforcement

- **< 3 signals** → output = null (code-level, unit tested)
- Heatmap alone / CVD alone → no output
- Requires **#327** stable

## Integrations

- **#1003** — provenance audit trail per matrix cell
- **#316** — Fact = raw signal \| Inference = agreement/contradiction \| Hypothesis = regime implication

## Scope

Perpetuals only | 1h/4h/1d | No <1h realtime Phase 1 | Across signal types (not venues — #317)

## Acceptance criteria

- Agreement TP > 70%, FP < 20% (50 historical events)
- Contradiction latency < 15 min
- Root cause: 5+ categories
- Confidence calibrated monthly, Brier tracked
- No output without ≥3 signals

## APIs

| Endpoint | Description |
|----------|-------------|
| `GET /api/platform/intelligence-ledger/derivatives-cross-signal/status` | Status |
| `GET /api/platform/intelligence-ledger/derivatives-cross-signal` | Synthesis panel |
