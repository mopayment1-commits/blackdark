# PHASE 01 — Immutable Audit Log & Decision Registry

**Status:** IMPLEMENTED (runtime verified locally; production deploy pending merge)  
**Principle:** DON'T DELETE KNOWLEDGE — COMPOUND IT  
**Branch:** `cursor/phase-01-audit-registry-e85e`

---

## Goal

Every API call, decision, prediction, and outcome is logged permanently with provenance — structured, versioned, searchable, attributable, and HMAC-signed.

---

## Deliverables

| Item | Status | Location |
|------|--------|----------|
| `audit_logs` table | ✅ | `database.py` (SCHEMA + migrations) |
| `decisions` table | ✅ | `database.py` (SCHEMA + migrations) |
| `POST /api/audit/log` | ✅ | `api/routers/audit.py` |
| `GET /api/decisions/{id}` | ✅ | `api/routers/audit.py` |
| `GET /api/decisions/search` | ✅ | `api/routers/audit.py` |
| `GET /api/audit/export` (JSON/CSV) | ✅ | `api/routers/audit.py` |
| `POST /api/decisions` | ✅ | Create + version via `PATCH` |
| Middleware: all `/api/*` → audit log | ✅ | `dashboard.py` `institutional_audit_middleware` |
| Core module | ✅ | `audit_registry.py` |
| Automated tests | ✅ | `tests/test_phase01_audit_registry.py` (5/5 pass) |

---

## Schema

### `audit_logs`

| Column | Type | Description |
|--------|------|-------------|
| `timestamp` | TEXT | ISO-8601 UTC |
| `actor` | TEXT | Bearer hash / API key hash / session / IP |
| `action` | TEXT | e.g. `api.get`, `decision.create` |
| `payload_hash` | TEXT | SHA-256 fingerprint of request |
| `outcome` | TEXT | e.g. `http_200`, `created:pending` |
| `signature` | TEXT | HMAC-SHA256 tamper evidence |
| `request_method` | TEXT | HTTP verb |
| `request_path` | TEXT | API path |
| `metadata_json` | TEXT | Structured context |

### `decisions`

| Column | Type | Description |
|--------|------|-------------|
| `decision_id` | TEXT | Stable ID (`dec_*`) |
| `context` | TEXT | JSON context |
| `prediction` | TEXT | JSON prediction |
| `confidence` | REAL | 0–1 |
| `timestamp` | TEXT | ISO-8601 UTC |
| `outcome` | TEXT | `pending` / `verified` / `rejected` / `expired` |
| `version` | INTEGER | Immutable version chain |
| `signature` | TEXT | HMAC-SHA256 |

**Versioning:** Updates create a new row (`version` increments). Prior versions are never mutated.

**Signing key:** `AUDIT_SIGNING_KEY` (falls back to `SECRETS_MASTER_KEY`, then dev default).

---

## Acceptance Criteria (Runtime Verified)

| # | Criterion | Result |
|---|-----------|--------|
| 1 | Call any existing API → audit log has entry | ✅ `GET /api/trust-os` → `api.get` row with `http_200` |
| 2 | Create decision → retrieve by ID → versioned | ✅ v1 pending → PATCH → v2 verified |
| 3 | Search decisions by date range | ✅ Returns latest version per `decision_id` |
| 4 | Export returns valid JSON/CSV file | ✅ Both formats with `signature_valid` |

---

## Automated Test Output

```text
tests/test_phase01_audit_registry.py::test_audit_log_signature_and_persistence PASSED
tests/test_phase01_audit_registry.py::test_decision_versioning PASSED
tests/test_phase01_audit_registry.py::test_decision_search_by_date_range PASSED
tests/test_phase01_audit_registry.py::test_api_middleware_writes_audit_on_existing_api PASSED
tests/test_phase01_audit_registry.py::test_decision_api_create_get_search_export PASSED
========================= 5 passed =========================
```

---

## curl Runtime Proof (local `uvicorn` on `127.0.0.1:8765`)

Full output captured in `/opt/cursor/artifacts/phase01_curl_output.txt`.

### 1. Existing API → audit log

```bash
curl -sS -o /dev/null -w "HTTP %{http_code}\n" http://127.0.0.1:8765/api/trust-os
# HTTP 200
```

### 2. Create + retrieve versioned decision

```bash
curl -sS -X POST http://127.0.0.1:8765/api/decisions \
  -H 'Content-Type: application/json' \
  -d '{"context":{"symbol":"BTC","phase":"1"},"prediction":{"action":"long","horizon":"24h"},"confidence":0.81}'
```

```json
{
  "ok": true,
  "decision": {
    "decision_id": "dec_dcde709770734dbe",
    "version": 1,
    "outcome": "pending",
    "signature_valid": true
  }
}
```

```bash
curl -sS http://127.0.0.1:8765/api/decisions/dec_dcde709770734dbe
# versions: [1], version_count: 1
```

### 3. Version bump (immutable history)

```bash
curl -sS -X PATCH http://127.0.0.1:8765/api/decisions/dec_dcde709770734dbe \
  -H 'Content-Type: application/json' \
  -d '{"outcome":"verified"}'
# version: 2, outcome: verified, signature_valid: true
```

### 4. Search by date range

```bash
curl -sS "http://127.0.0.1:8765/api/decisions/search?start=...&end=...&symbol=BTC"
# count: 2, latest version per decision_id
```

### 5. Export

```bash
curl -sS "http://127.0.0.1:8765/api/audit/export?format=json&limit=5"
curl -sS "http://127.0.0.1:8765/api/audit/export?format=csv&limit=3"
```

Sample audit row:

```json
{
  "actor": "ip:127.0.0.1",
  "action": "api.get",
  "outcome": "http_200",
  "request_path": "/api/trust-os",
  "signature_valid": true
}
```

---

## Production (Railway)

**URL:** `https://blackdark-production.up.railway.app`

Phase 1 endpoints deploy after merging PR to `main`. Post-merge verification:

```bash
PROD=https://blackdark-production.up.railway.app
curl -sS "$PROD/api/trust-os" | head -c 200
curl -sS -X POST "$PROD/api/decisions" -H 'Content-Type: application/json' \
  -d '{"context":{"symbol":"BTC"},"prediction":{"action":"long"},"confidence":0.7}'
curl -sS "$PROD/api/audit/export?format=json&limit=3"
```

Set `AUDIT_SIGNING_KEY` in Railway environment for production-grade signatures.

---

## Architecture Notes

- **Middleware** (`institutional_audit_middleware`): captures every `/api/` request after response; fingerprints method + path + query + body SHA-256; excludes `/api/audit/export` polling noise.
- **Immutability:** append-only tables; decision updates = new version row.
- **Attribution:** actor resolved from Bearer token, `X-API-Key`, session cookie, or client IP.
- **Postgres + SQLite:** same schema via `database.py` SCHEMA + `_apply_migrations`.

---

## Out of Scope (Phase 1)

- Phase 2+ (Knowledge Graph, Signals, Learning, Trust enhancements, etc.)
- Legal IP registration / revenue metrics (EXTERNAL DEPENDENCY per corporate compounding brief)

---

## Next Step

Confirm Phase 1 acceptance → proceed to **Phase 2: Knowledge Graph Schema** only after explicit approval.
