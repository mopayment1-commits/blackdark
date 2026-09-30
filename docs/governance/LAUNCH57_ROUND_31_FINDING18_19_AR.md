# الجولة 31 — مسارات إغلاق FINDING-18 (pentest) و FINDING-19 (WAF/CDN)

**السلطة:** البرنامج **§6 FINDING-18/19**، `L57-P7-WP3` / `L57-P7-WP4`

## بوابات المسار (مستودع)

```bash
python scripts/verify_launch57_finding18_pentest_closure_lane.py
python scripts/verify_launch57_finding19_waf_closure_lane.py
python scripts/preflight_launch57_finding18_transition.py
python scripts/preflight_launch57_finding19_transition.py
```

## إغلاق حقيقي (E-OPS)

**18:** إيداع pentest موقّع → `record_launch57_finding18_assurance_run.py` (exit 0) → `transition_launch57_finding_status.py --finding FINDING-18 --apply`

**19:** `CDN_WAF_ACTIVE=1` + `verify_edge_waf_cdn.py` → `record_launch57_finding19_waf_run.py` → `transition ... FINDING-19 --apply`

لا يُغيّر الجولة الحالة إلى `CLOSED` بدون الأدلة أعلاه.
