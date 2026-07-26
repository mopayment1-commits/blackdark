# BLACKDARK — IP Cleanliness & Due Diligence Pack

**Purpose:** Answer acquirer questions on code ownership, license safety, and
integration risk.

**Verdict (2026-07-25):** ✅ **Commercial-safe** — proprietary application code,
permissive OSS dependencies only, no GPL/AGPL in direct stack.

---

## 1. Code Ownership

| Category | Status | Evidence |
|----------|--------|----------|
| Application Python source | ✅ 100% BLACKDARK | ~70+ modules, no fork headers, no GPL imports |
| Templates / static UI | ✅ Owned | `templates/`, `static/sw.js` |
| Algorithms (CVVD, SII, Oracle) | ✅ Proprietary | Documented in `research_lab.py` → `ip_assets` |
| Training datasets | ✅ Generated in-house | Parquet/SQLite from own ingestion |
| Third-party vendored code | ✅ None | No copied SDKs in repo |

**API endpoint for live moat/IP list:** `GET /api/research/moat`

---

## 2. License Stack

| Layer | License | Acquisition risk |
|-------|---------|------------------|
| BLACKDARK application | **Proprietary** (`LICENSE`) | Buyer acquires IP via asset purchase agreement |
| Python dependencies | MIT / Apache-2.0 / BSD | ✅ Commercial + resale OK |
| Copyleft (GPL/AGPL) | **None detected** | ✅ No viral license contamination |
| Fonts (CDN) | SIL OFL 1.1 | ✅ Web use OK |

Full dependency table: [`THIRD_PARTY_NOTICES.md`](../THIRD_PARTY_NOTICES.md)

---

## 3. What the Buyer Sees (checklist)

- [x] `LICENSE` — proprietary ownership statement
- [x] `THIRD_PARTY_NOTICES.md` — OSS attribution + license types
- [x] `legal_content.py` — Terms / Privacy / Disclaimer (feed redistribution)
- [x] `docs/IP_CLEANLINESS.md` — this due-diligence pack
- [x] No GPL/AGPL dependencies in `requirements.txt`
- [x] Public transparency API (`/api/oracle/accuracy/public`) — honest engine labeling

---

## 4. Gaps to Close Before Acquisition Close

| Gap | Priority | Action |
|-----|----------|--------|
| Copyright headers in source files | Low | Optional `Copyright (c) BLACKDARK` in key modules |
| Contributor assignment agreement | Medium | Single-founder: signed IP assignment to holding entity |
| `extracted_chat*.txt`, `blackdark.zip` | Medium | Exclude from data room / add to `.gitignore` |
| SBOM automation in CI | Low | `pip-licenses` on each release |
| Trademark "BLACKDARK" | Medium | Register or document unregistered use |

---

## 5. Data vs Code IP

| Asset | Type | Notes |
|-------|------|-------|
| Source code | **Transferable IP** | Core acquisition value |
| Market tick data | **Licensed usage** | Exchange API ToS; buyer inherits operational compliance |
| User/subscriber data | **GDPR/privacy** | See `/privacy` |
| ML model weights (`.joblib`) | **Derivative of proprietary pipeline** | Trained on own labels |

---

## 6. Integration Safety Statement

> BLACKDARK can be merged into a buyer's stack as a **Python microservice**
> (FastAPI) without open-source license conflicts. Dependencies are standard
> permissive licenses. No requirement to open-source buyer's proprietary code.

---

## 7. Quick Audit Commands

```bash
# License scan
pip install pip-licenses
pip-licenses --from=requirements.txt --format=csv | findstr /I "GPL AGPL LGPL"

# Should return empty (no matches)

# Count proprietary modules
Get-ChildItem -Recurse -Filter *.py | Measure-Object

# Live IP assets
curl http://localhost:8080/api/research/moat
```

---

*Maintained for acquisition due diligence. Update when `requirements.txt` changes.*
