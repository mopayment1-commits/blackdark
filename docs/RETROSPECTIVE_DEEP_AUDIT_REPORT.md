# Retrospective Deep Audit — Batches 01 + 02

**Audited at:** 2026-08-30T14:53:00.430588+00:00

## Honest Count (200 capabilities)

| Classification | Count | % |
|---|---:|---:|
| **VERIFIED-DEEP** | **135** | 67.5% |
| WRAPPER-ONLY-UNVERIFIED | 18 | 9.0% |
| DEFERRED/DELEGATED | 47 | 23.5% |

### Per-batch breakdown

| Batch | VERIFIED-DEEP | WRAPPER-ONLY-UNVERIFIED | DEFERRED/DELEGATED |
|---|---:|---:|---:|
| Batch 01 (hero 100) | 70 | 18 | 12 |
| Batch 02 (101–200) | 65 | 0 | 35 |

**Honest closure rate:** 135 of 200 capabilities (67.5%) meet full deep-quad on the **underlying unit**, not merely the hero wrapper.

## WRAPPER-ONLY-UNVERIFIED (18 — Batch 01 only)

These wrappers execute live (`ok=true`) and call real code on `origin/main`, but the **underlying function has no independent pytest** outside `test_hero_batch_01_capabilities.py`:

| ID | Underlying binding |
|---:|---|
| 2 | `trade_simulator.simulate_spot_trade` |
| 10 | `instant_alert_engine.engine_stats` |
| 13, 27, 30, 37 | `bd_platform.pro_trader_layer.evaluate_flexible_alert_75` |
| 14 | `market_context.whale_alert_message` |
| 17 | `alert_service.subscribe_alerts` |
| 18, 21 | `bd_platform.alert_orchestration.alert_orchestration_status_18` |
| 49 | `bd_platform.flash_crash_protection.flash_crash_protection_status_49` |
| 55 | `due_diligence_bundle.build_full_due_diligence_bundle` |
| 56 | `bd_platform.market_analysis_layer.attach_market_health_bundle_106_112_114` |
| 299 | `bd_platform.news_classifier.classify_headlines` |
| 330 | `trade_simulator.simulate_spot_trade` |
| 437 | `bd_platform.correlation_mindshare.compute_mindshare_correlation_288` |
| 584 | `bd_platform.news_classifier.coindesk_feed` |
| 629 | `regulatory_compliance_guard.compliant_oracle_sentence` |

**Action:** Downgraded in `capabilities_checklist.xlsx`, both JSONL evidence files, and both gap reports to `مبني جزئيًا — يحتاج تحقق إضافي`.

## Acceptance

- **Batch 3 blocked** until all 18 WRAPPER-ONLY-UNVERIFIED items receive independent underlying tests + live proof, or are explicitly deferred.
- VERIFIED-DEEP requires: real underlying code + independent range/module test PASS + live exec OK + source traced.
- Hero wrapper tests (`test_hero_batch_01/02_capabilities.py`) **do not** count toward deep verification.

## Method

1. Resolve underlying module/function (heroes wrappers traced via AST + live `binding` field).
2. Reject stubs/deferred markers in underlying source.
3. Require independent `test_*batch*` or module-specific test (NOT hero_batch wrapper tests).
4. Run matching pytest nodeids; live `execute_capability`.
5. Trace git `origin/main` vs `capabilities-826-import`.

Full JSON: `docs/RETROSPECTIVE_DEEP_AUDIT_BATCHES_01_02.json`
