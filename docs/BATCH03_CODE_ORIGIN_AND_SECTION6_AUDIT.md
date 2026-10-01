# Batch03 Code Origin & Section-6 Re-Audit

**Date:** 2026-09-03  
**Git commit:** see `docs/BATCH03_PRODUCTION_SLSA_SESSION.json`

## أ.1 — أصل الكود: batch03_prep → batch03

**نعم** — الـ44 قدرة المستقلة تستخدم **نفس handlers** في `cap646/batch03_dedicated.py` التي بُنيت أولاً تحت `batch03_prep` (اسم spine قديم: `production_spine=batch03_prep`).

**لكن:** الإغلاق الرسمي **لم يكن "ترقية حالة" فقط**. تم تنفيذ دورة فحص كاملة (القسم 6):

| بند القسم 6 | دليل إعادة الفحص |
|-------------|------------------|
| 1. هدف داخلي cap646/runtime | `scripts/audit_official_batch03_rtm.py` — 50/50 live execute |
| 2. نتيجة خارجية + surface | `EXPECTED_SURFACE` per ID — zero GENERIC_SURFACES |
| 3. واجهة E2E | `scripts/verify_official_batch03_production.py` — GET /api/cap646/{id} |
| 4. أمان/جودة | pytest + coverage gate `docs/BATCH03_SONAR_COVERAGE_GATE.json` |
| 5. مراجعة جماعية | orchestrator 10/10 `docs/BATCH_VERIFICATION_ORCHESTRATOR_RESULT.json` |
| REUSED-LINK Type-4 | `docs/BATCH03_TYPE4_CONTRACT_TABLE.json` |
| Gateway/canonical | `docs/BATCH03_GATEWAY_CANONICAL_ENTITLEMENT_PROOF.json` |

**تغييرات بنيوية عند الترقية:**
- `production_spine`: `batch03_prep` → `batch03`
- `catalog_link` hoisted to top-level in `dedicated_common.wrap()`
- `institutional_gateway` uses `canonical_id()` before entitlement

## أ.2 — الدومين الصحيح + SLSA

**الدومين المعتمد:** `https://blackdark-production.up.railway.app`

**حالة الجلسة الحالية:** الإنتاج يُرجع **HTTP 404 Application not found** (نفس فشل Postgres/Railway redeploy الموثَّق سابقًا).

| Probe | النتيجة |
|-------|---------|
| `GET /health/ready` | 404 |
| `GET /api/cap646/101..150` | محظور — التطبيق غير موجود |

**دليل SLSA (نفس commit + نفس جلسة):** `docs/BATCH03_PRODUCTION_SLSA_SESSION.json`

**Fallback same-commit:** orchestrator + TestClient proofs على commit المربوط — **ليست بديلاً عن إنتاج حي**؛ تُكمّل عند عودة الدومين.

**إجراء المالك المطلوب:** Redeploy web service على Railway بعد إرفاق Postgres، ثم إعادة تشغيل `scripts/run_batch03_comprehensive_gap_closure.py`.
