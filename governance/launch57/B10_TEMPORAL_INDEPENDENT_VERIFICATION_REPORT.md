# B10 Temporal Independent Verification Report

**Verified implementation SHA:** `597120506c03d4a7ecf93c93fcf7ee9be4a527da`  
**HEAD at IV:** `1e009c8c` (docs only; B10 code unchanged since `59712050`)  
**Verdict:** `B10_INDEPENDENT_VERDICT = PASS_ENGINEERING`  
**IV at:** 2026-09-17T18:46:00+00:00

## Tests

```bash
python3 -m pytest tests/launch57/test_temporal_batch10.py tests/launch57/test_temporal_batch9.py tests/launch57/test_temporal_batch8.py tests/launch57/test_temporal_batch7.py tests/launch57/test_temporal_batch6.py tests/launch57/test_temporal_batch5.py tests/launch57/test_temporal_batch4.py -q
```

66 passed, 0 failed. **B4–B9 regression = false**

## SPEC §19 / control matrix

| Control | Verdict | Evidence |
|---------|---------|----------|
| Publication time (canonical) | PASS_ENGINEERING | `build_shareable_public_timing_context`; `test_shareable_public_timing_preserves_spec_fields` |
| Content snapshot time | PASS_ENGINEERING | payload/spine resolution; IV `content_snapshot_time` probe |
| Public validity window | PASS_ENGINEERING | start/end/duration; `test_public_validity_expired_not_presented_as_current` |
| Stale / expiry threshold | PASS_ENGINEERING | `DEFAULT_STALE_THRESHOLD_MS=600000`; `test_stale_share_not_presented_as_current` |
| No expired share as current | PASS_ENGINEERING | `finalize_b10_shareable_surface` fail-closed; IV `fail_closed_45` |
| TZ display ≠ canonical rewrite | PASS_ENGINEERING | `test_display_timezone_does_not_mutate_canonical_publication_time`; IV `tz_canonical` |
| Launch B10 path coverage | PASS_ENGINEERING | IV finalize + integration probes for #44/#45/#46 |

## Per-launch verdicts

| Launch | Surface | Verdict | Evidence |
|--------|---------|---------|----------|
| `B10:#44` | `shareable_decision_card` | PASS_ENGINEERING | `test_shareable_decision_card_includes_b10_timing`; IV `launch_44_b10_path` + integration |
| `B10:#45` | `shareable_accuracy_page` | PASS_ENGINEERING | `test_shareable_accuracy_page_includes_b10_timing`; IV `launch_45_b10_path` |
| `B10:#46` | `guest_trust_surface` | PASS_ENGINEERING | `test_guest_trust_surface_includes_b10_timing`; IV `launch_46_b10_path` |

## Adversarial probes

| Probe | Result |
|-------|--------|
| (a) Expired/stale share | PASS — `presented_as_current=false`; `#45` surface `success=false` |
| (b) Display TZ change | PASS — canonical `publication_time` unchanged |
| (c) Isolation | PASS — `b10_isolation_leakage=0`; B10 owner zero cap646 |
| (d) `utc_now` fallback | ACCEPTABLE_DOCUMENTED — fresh publication when fields absent; expiry via `content_age_ms` or explicit window end |
| (e) `#44` decision_certificate | OUT_OF_B10_TIMING_SCOPE — pre-existing cert build; B10 timing does not break §19 |
| (f) `#47`/`#48` scope boundary | PASS — no B10 attachment on `#47`; integration confirms `#47` unchanged |

## Overall

| Field | Verdict |
|-------|---------|
| `B10:#44` | PASS_ENGINEERING |
| `B10:#45` | PASS_ENGINEERING |
| `B10:#46` | PASS_ENGINEERING |
| `B10_INDEPENDENT_VERDICT` | PASS_ENGINEERING |

## Flags

- `PASS_LIVE_NOT_CLAIMED = true`
- `B11_NOT_STARTED = true`
- `B4_B5_B6_B7_B8_B9_REGRESSION = false`
- `LAUNCH57_TEMPORAL_CONSISTENCY_PASS_ENGINEERING = false`
