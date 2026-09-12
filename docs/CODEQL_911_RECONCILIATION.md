# CodeQL Institutional Reconciliation

- Original analyzed SHA (reproduced): `f9e06f136f54fda777cc740a33e6b6b9fa14902f`
- Final SARIF findings: **924** (reference inventory claimed 911; original CSV/SARIF not in repo)
- Security in final SARIF: **33** + **5** remediated absent = **38** original security
- Quality in final SARIF: **891** (reference quality: 873)
- Final SARIF disposition complete: **924 / 924**
- Original security disposition complete: **38 / 38** (33 in SARIF + 5 remediated closed)

## Closure status

**CODEQL SOURCE-LEVEL REVIEW COMPLETE — FINAL CLOSURE BLOCKED BY EXTERNAL VERIFICATION**

Reason: original `blackdark-codeql-911.csv` unavailable; reproduced pre-fix inventory was 928 not 911. Cannot assert 911/911 byte-level reconciliation without reference artifact.

## Remediated findings absent from final SARIF

- address segment joined into URL path without validation; remediated _safe_address_segment.
- scale_readiness_report nested artifact_error exposed str(exc); remediated to type name.
- viral_readiness_report embeds scale_readiness_report; canonical scale_readiness.py.
- build_info returned str(exc); remediated to type(exc).__name__.
- vendor_rate_limit_status returned str(exc); remediated in ops/vendor_rate_limit_watchdog.py.


## Disposition totals (final SARIF)

| Bucket | Count |
|---|---:|
| TP | 8 |
| FP | 20 |
| TEST_ONLY | 5 |
| DUPLICATE | 1 |
| QUALITY_DEBT | 890 |
| RAV | 0 |
| **SUM** | **924** |

## Security reconciliation (38/38)

| Bucket | Count |
|---|---:|
| TP | 8 |
| FP | 20 |
| TEST_ONLY | 4 |
| DUPLICATE | 1 |
| RAV | 0 |
| remediated | 8 |

## Rule breakdown

| ruleId | original_total | TP | FP | TEST_ONLY | DUPLICATE | QUALITY_DEBT | RAV | remediated |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| py/catch-base-exception | 2 | 0 | 0 | 0 | 0 | 2 | 0 | 0 |
| py/clear-text-logging-sensitive-data | 17 | 1 | 15 | 1 | 0 | 0 | 0 | 1 |
| py/clear-text-storage-sensitive-data | 3 | 0 | 1 | 2 | 0 | 0 | 0 | 0 |
| py/constant-conditional-expression | 1 | 0 | 0 | 0 | 0 | 1 | 0 | 0 |
| py/cyclic-import | 302 | 0 | 0 | 0 | 0 | 302 | 0 | 0 |
| py/duplicate-key-dict-literal | 2 | 0 | 0 | 0 | 0 | 2 | 0 | 0 |
| py/empty-except | 191 | 0 | 0 | 0 | 0 | 191 | 0 | 0 |
| py/file-not-closed | 3 | 0 | 0 | 1 | 0 | 2 | 0 | 0 |
| py/import-and-import-from | 23 | 0 | 0 | 0 | 0 | 23 | 0 | 0 |
| py/incomplete-url-substring-sanitization | 3 | 0 | 2 | 1 | 0 | 0 | 0 | 0 |
| py/log-injection | 9 | 7 | 1 | 0 | 1 | 0 | 0 | 7 |
| py/loop-variable-capture | 1 | 0 | 0 | 0 | 0 | 1 | 0 | 0 |
| py/multiple-definition | 3 | 0 | 0 | 0 | 0 | 3 | 0 | 0 |
| py/redundant-comparison | 2 | 0 | 0 | 0 | 0 | 2 | 0 | 0 |
| py/repeated-import | 10 | 0 | 0 | 0 | 0 | 10 | 0 | 0 |
| py/undefined-export | 9 | 0 | 0 | 0 | 0 | 9 | 0 | 0 |
| py/uninitialized-local-variable | 3 | 0 | 0 | 0 | 0 | 3 | 0 | 0 |
| py/unnecessary-lambda | 2 | 0 | 0 | 0 | 0 | 2 | 0 | 0 |
| py/unreachable-statement | 6 | 0 | 0 | 0 | 0 | 6 | 0 | 0 |
| py/unsafe-cyclic-import | 1 | 0 | 0 | 0 | 0 | 1 | 0 | 0 |
| py/unused-global-variable | 72 | 0 | 0 | 0 | 0 | 72 | 0 | 0 |
| py/unused-import | 192 | 0 | 0 | 0 | 0 | 192 | 0 | 0 |
| py/unused-local-variable | 66 | 0 | 0 | 0 | 0 | 66 | 0 | 0 |
| py/weak-sensitive-data-hashing | 1 | 0 | 1 | 0 | 0 | 0 | 0 | 0 |

## Confirmed true positives remediated

- `billing/audit_ledger.py:73` — py/clear-text-logging-sensitive-data — PII email logged cleartext; remediated via sanitize_log_value at sink (CodeQL may still trace taint).
- `bd_platform/address_intelligence.py:67` — py/log-injection — Snapshot key logged; remediated via sanitize_log_value.
- `billing/audit_ledger.py:73` — py/log-injection — User email interpolated into log line; remediated via sanitize_log_value CRLF scrub.
- `audit_registry.py:295` — py/log-injection — decision_id in exception log; remediated via sanitize_log_value.
- `audit_registry.py:371` — py/log-injection — User-supplied decision_id in exception log; remediated via sanitize_log_value.
- `api/routers/didit_webhook.py:51` — py/log-injection — Webhook event_id attacker-controlled; remediated via sanitize_log_value.
- `ml/market_replay_bootstrap.py:188` — py/log-injection — asset interpolated in log; remediated via sanitize_asset.
- `signal_compounding.py:112` — py/log-injection — signal id logged; remediated via sanitize_log_value.

## RAV

- None

## Global suppressions

No global CodeQL rule suppression or query-suite exclusion introduced.
