# Epistemic Output Framework — #316 (Sprint 2 Intelligence Ledger)

Renamed from **Cross-Domain Decision Intelligence** → **Epistemic Output Framework**.

This is a **design principle**, not a standalone product feature. Applied to ALL intelligence outputs.

> CoinGecko shows data (facts). BLACKDARK shows facts + inferences + hypotheses — separated and documented.

## Epistemic separation

| Type | Definition | Confidence |
|------|------------|------------|
| **Fact** | Verifiable data | 100% if verified |
| **Inference** | Logical deduction from facts | Confidence % + supporting facts count |
| **Hypothesis** | Testable prediction | Probability range + test conditions |

**Rules:**
- No mixing epistemic types in untagged statements
- AI/ML outputs = Inference or Hypothesis — **never Fact**
- #284 Evidence Confidence = input to inference confidence
- #1003 Provenance = evidence chain for every conclusion

## Output model

**Includes:** Analysis + Evidence + Confidence + Why  
**Excludes:** Decision, Buy, Sell, Recommendation  
**User decides.**

## Cross-domain synthesis

Confirm/contradict across domains (derivatives, DEX, risk, narratives, sentiment, market state) — analysis only, no decision output.

## API

| Endpoint | Purpose |
|----------|---------|
| `GET /api/platform/intelligence-ledger/epistemic-output/status` | Framework status |
| `GET /api/platform/intelligence-ledger/epistemic-output` | Cross-domain panel |
| `POST /api/platform/intelligence-ledger/epistemic-output/wrap` | Wrap any output in epistemic envelope |

## Acceptance criteria

- Fact/Inference/Hypothesis separated ✅
- Every conclusion traceable ✅
- Confidence taxonomy ✅
- No Decision in output ✅
- Applied to all intelligence outputs ✅
