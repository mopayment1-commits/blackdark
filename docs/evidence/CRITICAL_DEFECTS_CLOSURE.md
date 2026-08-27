# Critical Defects Closure — D-01 through D-15

**Generated:** Wave 01 institutional closure  
**Governing:** [BLACKDARK_CONTEXT.md](../BLACKDARK_CONTEXT.md)  
**Platform verdict:** `PASS WITH RISK`

## Summary

All six **critical** defects identified in BLACKDARK_CONTEXT §4 are closed in code with automated tests and production API surfaces. External evidence (HSM, independent pentest, SOC2/ISO certification) remains out of scope for in-repo claims per GOV-003.

| ID | Title | Status | Certification |
|----|-------|--------|---------------|
| D-01 | Null data ≠ zero; no cascade on outage | CLOSED | PASS |
| D-02 | Secrets vault — no plaintext in prod | CLOSED | PASS WITH RISK |
| D-06 | Institutional API surface | CLOSED | PASS WITH RISK |
| D-09 | Exchange Internal Flow Filter | CLOSED | PASS WITH RISK |
| D-13 | Security verification | CLOSED | PASS WITH RISK |
| D-15 | Evidence pack per requirement | CLOSED | PASS |

## Evidence surfaces

- `GET /api/v1/platform/critical-defects` — live closure registry
- `GET /api/v1/data/wave-01` — institutional audit with `critical_defects_closure`
- `GET /api/v1/onchain/flow-classification` — D-09 classifier
- `scripts/build_critical_defects_closure.sh` — local proof runner
- `tests/test_d01_data_state.py` … `tests/test_d15_evidence_closure.py`

## Limitations (honest)

- **D-02:** Fernet AES-128-CBC + AES-256-GCM upgrade path; HSM = EXTERNAL EVIDENCE
- **D-06:** Enterprise IdP / full multi-tenant SSO = EXTERNAL EVIDENCE
- **D-09:** Wallet label DB seed partial; live graph ingest expands coverage
- **D-13:** Human pentest + SOC2 = EXTERNAL EVIDENCE

## Reproduce

```bash
bash scripts/build_critical_defects_closure.sh
pytest tests/test_d01_data_state.py tests/test_d02_secrets_vault.py \
  tests/test_d06_institutional_api.py tests/test_d09_flow_filter.py \
  tests/test_d13_auth_abuse.py tests/test_d15_evidence_closure.py -q
```
