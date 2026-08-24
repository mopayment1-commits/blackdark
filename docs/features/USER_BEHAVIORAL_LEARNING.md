# Feature #105 — User Behavioral Learning (Opt-in)

**Wave 2 — rule-based personalization with privacy-first defaults.**

## Principles

1. **Opt-in only** — tracking disabled until user explicitly enables
2. **No complex ML** — visit-count rules only (e.g. 5 Solana pages → Solana first)
3. **Encrypted at rest** — event payloads use Fernet via `secrets_vault`

## Rule engine (v1)

| Visits | Effect |
|--------|--------|
| 1–4 | Topic tracked, no boost |
| ≥5 | Topic ranked first in personalized suggestions |

## APIs

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/platform/user/behavioral-learning/opt-in?user_id=` | Enable tracking |
| POST | `/api/platform/user/behavioral-learning/opt-out?user_id=` | Disable (+ optional purge) |
| GET | `/api/platform/user/behavioral-learning/status?user_id=` | Opt-in state |
| POST | `/api/platform/user/behavioral-learning/record?user_id=&topic=` | Record page visit |
| GET | `/api/platform/user/behavioral-learning/ranked-topics?user_id=` | Ranked topics |
| GET | `/api/platform/user/behavioral-learning/module-status` | Module health |

## Response SLA

Target ≤2 seconds for ranking endpoints (in-memory counts + encrypted JSONL).
