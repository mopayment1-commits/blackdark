# الجولة 29 — مسار إغلاق FINDING-11 (SBOM / NTIA) — هندسة فقط

**السلطة:** البرنامج **§6 FINDING-11**، **NTIA-MIN**، `LAUNCH57_NTIA_SBOM_GAP_ANALYSIS.json`

## بوابة المسار

```bash
python scripts/verify_launch57_finding11_sbom_closure_lane.py
python scripts/preflight_launch57_finding11_transition.py
```

## إغلاق حقيقي (أحد المسارين)

1. **موافقة Sec Lead:**  
   `python scripts/record_launch57_finding11_sec_lead_approval.py --approval-id <id> --recorded-by <role>`  
   ثم `LAUNCH57_SBOM_SEC_LEAD_APPROVAL_ID=<id>` و`transition_launch57_finding_status.py --finding FINDING-11 --apply`

2. **SBOM Syft/حاوية:** artifact `syft-prod-lock.cyclonedx.json` أو `LAUNCH57_CONTAINER_SBOM_PATH` ثم transition.

**لا** يُغيّر الجولة حالة الفهرس إلى `CLOSED` بدون أحد المسارين أعلاه.
