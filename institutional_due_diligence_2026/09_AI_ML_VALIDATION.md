# 09 — AI/ML Validation (Wave 6)

**Generated:** 2026-09-10T23:50:00Z

## AI Systems Inventory
| System | Type | Provider | Confidence Output |
|---|---|---|---|
| ai_oracle.py | Hybrid rules+LLM | OpenAI/Ollama/free chain | confidence_percent 0-100 |
| sentiment_engine.py | NLP | VADER + optional LLM | NOT VERIFIED |
| chat_service.py | LLM | OpenAI | NOT VERIFIED |
| ml/regime_router.py | ML routing | joblib models | NOT VERIFIED |

## AI Financial Safety (§48)
- LLM prompts request one-sentence verdict — hallucination risk NOT VERIFIED at runtime
- Rules engine fallback when LLM fails — NOT VERIFIED dominant path

**Wave 6 CLOSED:** Inventory complete; grounding/calibration NOT VERIFIED.
