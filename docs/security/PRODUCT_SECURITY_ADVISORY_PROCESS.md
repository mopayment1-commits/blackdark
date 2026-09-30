# Product Security Advisory Process

**Launch-57** · Normative: CVE Program practices, MITRE CWE, NIST NVD CPE

## Product identification (CPE)

| Field | Value |
|-------|--------|
| Vendor | BLACKDARK |
| Product | blackdark-trust-os |
| CPE 2.3 (template) | `cpe:2.3:a:blackdark:blackdark_trust_os:*:*:*:*:launch57:*:*:*` |
| Version binding | Git tag `launch-57-*` or commit SHA in advisory |

## Workflow

1. **Intake** — VDP report or internal finding → ticket with severity (CVSS v3.1 base when applicable)
2. **CWE assignment** — Every product issue receives primary CWE (e.g. CWE-79 XSS)
3. **Fix** — Patch on Launch-57 remediation branch; regression test required
4. **CVE** — Request CVE ID via coordinated disclosure (CNA when available; else MITRE cveform or vendor broker)
5. **Publish** — `docs/security/advisories/YYYY-MM-DD-<slug>.md` + update index
6. **SBOM** — Regenerate CycloneDX for fixed release (`scripts/generate_sbom.py`)

## Advisory template

See `docs/security/PRODUCT_SECURITY_ADVISORY_TEMPLATE.md`.

## Dry-run

Advisory `docs/security/advisories/DRYRUN-2026-09-30-process-validation.md` validates pipeline without claiming a product CVE.
