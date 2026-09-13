# CodeQL Institutional Reconciliation

- Original analyzed SHA: `f038bc331a06ed52aeb85035c9c01ad1b4492f2b`
- Final analyzed SHA: `1181fd9cbacf368bc6569b924e0d85da70d8146c`
- Canonical original inventory: `docs/evidence/blackdark-codeql-original-911.csv` (911 findings)
- Original security / quality: **38** / **873**
- Original reconciliation complete: **911 / 911**
- Final SARIF findings (post-remediation scan): **924**
- Security disposition complete: **38 / 38**

## Closure status

**CODEQL INSTITUTIONAL RECONCILIATION CLOSED**

## Numerical reconciliation (original 911)

| Bucket | Count |
|---|---:|
| TP | 12 |
| FP | 19 |
| TEST_ONLY | 5 |
| DUPLICATE | 3 |
| QUALITY_DEBT | 872 |
| RAV | 0 |
| **SUM** | **911** |

## Security reconciliation (38/38)

| Bucket | Count |
|---|---:|
| TP | 12 |
| FP | 19 |
| TEST_ONLY | 4 |
| DUPLICATE | 3 |
| RAV | 0 |
| remediated | 12 |

## Remediated findings absent from final SARIF

- `dashboard.py:2123` — py/stack-trace-exposure — scale_readiness_report nested artifact_error exposed str(exc); remediated to type name.
- `dashboard.py:4564` — py/stack-trace-exposure — build_info returned str(exc); remediated to type(exc).__name__.
- `api/routers/monitoring.py:32` — py/stack-trace-exposure — vendor_rate_limit_status returned str(exc); remediated in ops/vendor_rate_limit_watchdog.py.
- `blackdark/ingestion/arkham_connector.py:73` — py/partial-ssrf — address segment joined into URL path without validation; remediated _safe_address_segment.

## Remediated findings still flagged in final SARIF (CodeQL taint limitation)

- `billing/audit_ledger.py:71` — py/clear-text-logging-sensitive-data — PII email logged cleartext; remediated via sanitize_log_value at sink (CodeQL may still trace taint). (still_present_near_line_73)
- `bd_platform/address_intelligence.py:65` — py/log-injection — Snapshot key logged; remediated via sanitize_log_value. (still_present_near_line_67)
- `billing/audit_ledger.py:71` — py/log-injection — User email interpolated into log line; remediated via sanitize_log_value CRLF scrub. (still_present_near_line_73)
- `audit_registry.py:302` — py/log-injection — decision_id in exception log; remediated via sanitize_log_value. (still_present_near_line_295)
- `audit_registry.py:376` — py/log-injection — User-supplied decision_id in exception log; remediated via sanitize_log_value. (still_present_near_line_371)
- `api/routers/didit_webhook.py:47` — py/log-injection — Webhook event_id attacker-controlled; remediated via sanitize_log_value. (still_present_near_line_51)
- `ml/market_replay_bootstrap.py:186` — py/log-injection — asset interpolated in log; remediated via sanitize_asset. (still_present_near_line_188)
- `signal_compounding.py:110` — py/log-injection — signal id logged; remediated via sanitize_log_value. (still_present_near_line_112)

## Rule breakdown (original 911)

| ruleId | original_total | TP | FP | TEST_ONLY | DUPLICATE | QUALITY_DEBT | RAV |
|---|---:|---:|---:|---:|---:|---:|---:|
| py/clear-text-logging-sensitive-data | 17 | 1 | 15 | 1 | 0 | 0 | 0 |
| py/clear-text-storage-sensitive-data | 3 | 0 | 1 | 2 | 0 | 0 | 0 |
| py/constant-conditional-expression | 1 | 0 | 0 | 0 | 0 | 1 | 0 |
| py/cyclic-import | 302 | 0 | 0 | 0 | 0 | 302 | 0 |
| py/duplicate-key-dict-literal | 2 | 0 | 0 | 0 | 0 | 2 | 0 |
| py/empty-except | 191 | 0 | 0 | 0 | 0 | 191 | 0 |
| py/file-not-closed | 3 | 0 | 0 | 1 | 0 | 2 | 0 |
| py/import-and-import-from | 22 | 0 | 0 | 0 | 0 | 22 | 0 |
| py/incomplete-url-substring-sanitization | 3 | 0 | 1 | 1 | 1 | 0 | 0 |
| py/log-injection | 9 | 7 | 1 | 0 | 1 | 0 | 0 |
| py/loop-variable-capture | 1 | 0 | 0 | 0 | 0 | 1 | 0 |
| py/multiple-definition | 3 | 0 | 0 | 0 | 0 | 3 | 0 |
| py/partial-ssrf | 1 | 1 | 0 | 0 | 0 | 0 | 0 |
| py/redundant-comparison | 2 | 0 | 0 | 0 | 0 | 2 | 0 |
| py/repeated-import | 10 | 0 | 0 | 0 | 0 | 10 | 0 |
| py/stack-trace-exposure | 4 | 3 | 0 | 0 | 1 | 0 | 0 |
| py/undefined-export | 9 | 0 | 0 | 0 | 0 | 9 | 0 |
| py/uninitialized-local-variable | 1 | 0 | 0 | 0 | 0 | 1 | 0 |
| py/unnecessary-lambda | 2 | 0 | 0 | 0 | 0 | 2 | 0 |
| py/unreachable-statement | 5 | 0 | 0 | 0 | 0 | 5 | 0 |
| py/unsafe-cyclic-import | 1 | 0 | 0 | 0 | 0 | 1 | 0 |
| py/unused-global-variable | 64 | 0 | 0 | 0 | 0 | 64 | 0 |
| py/unused-import | 189 | 0 | 0 | 0 | 0 | 189 | 0 |
| py/unused-local-variable | 65 | 0 | 0 | 0 | 0 | 65 | 0 |
| py/weak-sensitive-data-hashing | 1 | 0 | 1 | 0 | 0 | 0 | 0 |

## Confirmed true positives (original inventory)

- `dashboard.py:2123` — py/stack-trace-exposure — scale_readiness_report nested artifact_error exposed str(exc); remediated to type name. [remediated_absent; absent_from_final_sarif]
- `dashboard.py:4564` — py/stack-trace-exposure — build_info returned str(exc); remediated to type(exc).__name__. [remediated_absent; absent_from_final_sarif]
- `api/routers/monitoring.py:32` — py/stack-trace-exposure — vendor_rate_limit_status returned str(exc); remediated in ops/vendor_rate_limit_watchdog.py. [remediated_absent; absent_from_final_sarif]
- `billing/audit_ledger.py:71` — py/clear-text-logging-sensitive-data — PII email logged cleartext; remediated via sanitize_log_value at sink (CodeQL may still trace taint). [remediated_still_flagged; still_present_near_line_73]
- `bd_platform/address_intelligence.py:65` — py/log-injection — Snapshot key logged; remediated via sanitize_log_value. [remediated_still_flagged; still_present_near_line_67]
- `billing/audit_ledger.py:71` — py/log-injection — User email interpolated into log line; remediated via sanitize_log_value CRLF scrub. [remediated_still_flagged; still_present_near_line_73]
- `audit_registry.py:302` — py/log-injection — decision_id in exception log; remediated via sanitize_log_value. [remediated_still_flagged; still_present_near_line_295]
- `audit_registry.py:376` — py/log-injection — User-supplied decision_id in exception log; remediated via sanitize_log_value. [remediated_still_flagged; still_present_near_line_371]
- `api/routers/didit_webhook.py:47` — py/log-injection — Webhook event_id attacker-controlled; remediated via sanitize_log_value. [remediated_still_flagged; still_present_near_line_51]
- `ml/market_replay_bootstrap.py:186` — py/log-injection — asset interpolated in log; remediated via sanitize_asset. [remediated_still_flagged; still_present_near_line_188]
- `signal_compounding.py:110` — py/log-injection — signal id logged; remediated via sanitize_log_value. [remediated_still_flagged; still_present_near_line_112]
- `blackdark/ingestion/arkham_connector.py:73` — py/partial-ssrf — address segment joined into URL path without validation; remediated _safe_address_segment. [remediated_absent; absent_from_final_sarif]

## RAV

- None (0)

## Global suppressions

No global CodeQL rule suppression or query-suite exclusion introduced.
