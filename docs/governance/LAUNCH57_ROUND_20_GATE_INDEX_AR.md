# الجولة 20 — فهرس بوابات الإصلاح + preflight الانتقالات

**السلطة:** `LAUNCH57_CISA_SECURE_BY_DEMAND_REMEDIATION_PROGRAM.md` — §3، §8، فهرس الأدلة

## فهرس البوابات

- التوليد: `python scripts/generate_launch57_gate_index.py`
- الملف: `governance/launch57/LAUNCH57_REMEDIATION_GATE_INDEX.json`
- التحقق: `python scripts/verify_launch57_gate_index.py`

## Preflight (بدون `--apply`)

`python scripts/preflight_launch57_open_finding_transitions.py` — يشغّل `transition_launch57_finding_status.py` تجريبيًا لكل finding مفتوح في الحزمة.

## API

`GET /api/security/launch57-closure-status` يتضمن مسارات `gate_index` و`open_ops_closure_package` ضمن `cisa_remediation_inventory.documents`.
