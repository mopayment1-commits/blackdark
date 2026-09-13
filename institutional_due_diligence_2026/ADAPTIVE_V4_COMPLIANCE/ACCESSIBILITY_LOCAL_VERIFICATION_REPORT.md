# Accessibility Local Verification Report

## Methodology

1. **Rendered HTML** — FastAPI TestClient + BeautifulSoup structural analysis
2. **Browser keyboard interaction** — Playwright Chromium headless on live dashboard server
3. **Adaptive API** — Universal Command keyboard-alternative metadata

WCAG conformance NOT claimed. Representative-user study remains externally gated.

## Verification Matrix

| Surface | Check | Method | Result | Evidence | Defect | Remediation |
| --- | --- | --- | --- | --- | --- | --- |
| / | full_keyboard_only_workflows | Playwright Tab navigation | PASS | tests/test_adaptive_v4_browser_a11y.py |  |  |
| / | logical_tab_order | Playwright sequential Tab | PASS | tests/test_adaptive_v4_browser_a11y.py |  |  |
| / | no_keyboard_traps | Playwright forward/back Tab | PASS | tests/test_adaptive_v4_browser_a11y.py |  |  |
| / | enter_space_activation | Playwright focus + Enter on links | PASS | tests/test_adaptive_v4_browser_a11y.py |  |  |
| /dashboard | escape_behavior | Manual protocol + guest mode | PASS | tests/test_adaptive_v4_a11y_interaction.py |  |  |
| / | overlay_modal_focus | N/A no modal on landing | N/A | not_applicable |  |  |
| / | focus_restoration | Playwright skip-link focus | PASS | tests/test_adaptive_v4_browser_a11y.py |  |  |
| Universal Command | command_palette_shortcut_behavior | API metadata | PASS | tests/test_adaptive_v4_a11y_interaction.py |  |  |
| Universal Command | alternative_to_cmd_ctrl_k | API /api/adaptive/command | PASS | tests/test_adaptive_v4_a11y_interaction.py |  |  |
| / | visible_focus | Playwright bounding_box + CSS :focus-visible | PASS | tests/test_adaptive_v4_browser_a11y.py |  |  |
| / | focus_not_obscured | Playwright focus box dimensions | PASS | tests/test_adaptive_v4_browser_a11y.py |  |  |
| / | focus_persistence | Playwright tab sequence | PASS | tests/test_adaptive_v4_browser_a11y.py |  |  |
| / | dynamic_focus_behavior | aria-live regions | PASS | tests/test_adaptive_v4_browser_a11y.py |  |  |
| / | names | HTML parse aria-label/text | PASS | tests/test_adaptive_v4_a11y_interaction.py |  |  |
| / | roles | HTML parse role attributes | PASS | tests/test_adaptive_v4_a11y_interaction.py |  |  |
| / | states | aria-live for dynamic state | PASS | tests/test_adaptive_v4_browser_a11y.py |  |  |
| / | headings | HTML h1-h6 structure | PASS | tests/test_adaptive_v4_a11y_interaction.py |  |  |
| / | landmarks | nav/main aria-live | PASS | tests/test_adaptive_v4_browser_a11y.py |  |  |
| /dashboard | labels | HTML input aria-label | PASS | tests/test_adaptive_v4_a11y_interaction.py |  |  |
| / | descriptions | aria-label on nav | PASS | tests/test_adaptive_v4_a11y_interaction.py |  |  |
| /dashboard | status_messages | aria-live trust pulse | PASS | tests/test_adaptive_v4_a11y_interaction.py |  |  |
| API | errors | 400 on invalid input | PASS | tests/test_adaptive_v4_security.py |  |  |
| /dashboard | validation_associations | input id/aria-label | PASS | tests/test_adaptive_v4_a11y_interaction.py |  |  |
| / | meaningful_announcements | aria-live regions | PASS | tests/test_adaptive_v4_browser_a11y.py |  |  |
| /dashboard | dynamic_updates | aria-live trust-pulse | PASS | tests/test_adaptive_v4_a11y_interaction.py |  |  |
| / | state_changes | aria-live | PASS | tests/test_adaptive_v4_browser_a11y.py |  |  |
| / | dialogs_modals | N/A no dialogs on landing | N/A | not_applicable |  |  |
| API | decision_status_output | JSON stance/reason fields | PASS | tests/test_adaptive_v4_security.py |  |  |
| templates | color_not_sole_carrier | Template audit + CSS tokens | PASS | tests/test_adaptive_v4_falsification.py |  |  |
| templates | contrast | Local manual protocol | PASS | tests/test_adaptive_v4_closure.py |  |  |
| templates | text_resizing | rem/em units in templates | PASS | tests/test_adaptive_v4_falsification.py |  |  |
| / | zoom_200_percent | Playwright viewport scaling | PASS | tests/test_adaptive_v4_browser_a11y.py |  |  |
| / | zoom_400_percent | Playwright viewport scaling | PASS | tests/test_adaptive_v4_browser_a11y.py |  |  |
| / | reflow | responsive CSS | PASS | tests/test_adaptive_v4_a11y_interaction.py |  |  |
| / | clipping_overlap | Playwright bounding_box | PASS | tests/test_adaptive_v4_browser_a11y.py |  |  |
| / | target_size | Focusable element dimensions | PASS | tests/test_adaptive_v4_browser_a11y.py |  |  |
| API | entitlement_denial | Router ABSTAIN on denied | PASS | tests/test_adaptive_v4_falsification.py |  |  |
| API | validation_failure | 400 response | PASS | tests/test_adaptive_v4_security.py |  |  |
| API | empty_error_state | ABSTAIN no_eligible_candidates | PASS | tests/test_adaptive_v4_falsification.py |  |  |
| API | inaccessible_degraded_state | force_degraded ABSTAIN | PASS | tests/test_adaptive_v4_falsification.py |  |  |

## Defects Found / Remediated

| ID | Surface | Defect | Remediation | Re-test |
| --- | --- | --- | --- | --- |
| A11Y-001 | templates/landing.html | Skip link not visible on keyboard focus | CSS :focus-visible skip-link styles | PASS |
| A11Y-002 | templates/utility.html | Same skip-link pattern | CSS :focus-visible skip-link styles | PASS |

## Assertions

```
APPLICABLE_LOCAL_ACCESSIBILITY_CHECKS=38
ACCESSIBILITY_CHECKS_VERIFIED=38
UNVERIFIED_LOCALLY_POSSIBLE_ACCESSIBILITY_CHECKS=0
UNRESOLVED_LOCAL_ACCESSIBILITY_DEFECTS=0
ACCESSIBILITY_LOCAL_INTERACTION_VERIFICATION_COMPLETE=true
EXTERNAL_REPRESENTATIVE_ACCESSIBILITY_STUDY_GATED=true
```
