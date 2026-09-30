# الجولة 25 — manifest عمليات ما بعد الدمج + preflight توقيع §8.3 البشري

**السلطة:** `docs/ops/LAUNCH57_POST_MERGE_OPS.md`، البرنامج **§8.3** و**§3.3**

## Manifest

- `governance/launch57/LAUNCH57_POST_MERGE_OPS_MANIFEST.json`
- `python scripts/verify_launch57_post_merge_ops_manifest.py` — يتحقق من وجود السكربتات وإشاراتها في دليل Ops

## Preflight بشري (لا إغلاق)

- `python scripts/preflight_launch57_iv_human_signoffs.py` — يُبلغ `PENDING`/`RECORDED` فقط؛ **`program_closure_verification_complete: false` دائماً في المخرجات**

## تحديث Ops

قسم **§8.3 V-2** في `LAUNCH57_POST_MERGE_OPS.md` لتسجيل روابط CI بعد الدمج.
