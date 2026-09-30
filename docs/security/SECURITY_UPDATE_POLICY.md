# Security Update Policy

**Normative:** NIST SP 800-218 (SSDF) PW practices; CISA Secure by Demand

## SaaS delivery model

BLACKDARK SaaS deployments receive security fixes via **controlled application release** (no customer patch installation). This policy defines our commitments for vulnerability response and supported versions.

## Severity SLAs (engineering targets)

| Severity | Definition | Target fix deployment |
|----------|------------|------------------------|
| Critical | Active exploitation or CVSS ≥ 9.0 | 7 calendar days |
| High | CVSS 7.0–8.9 or KEV-listed dependency | 14 calendar days |
| Medium | CVSS 4.0–6.9 | 30 calendar days |
| Low | CVSS < 4.0 | Next maintenance release |

## CISA KEV

When a dependency or component appears on [CISA KEV](https://www.cisa.gov/known-exploited-vulnerabilities-catalog), remediation follows **High** SLA unless rated Critical.

## Supported versions

| Line | Support |
|------|---------|
| Launch-57 remediation branch | Active security support |
| Prior Launch tags | Best-effort for 90 days after successor tag |

## End of life

Unsupported lines receive no security patches. Customers on EOL lines must upgrade to a supported Launch line.

## Verification

- `pip-audit` on `requirements.hashes.txt` in CI (`.github/workflows/security.yml`)
- SBOM regenerated per release (`scripts/generate_sbom.py`)
