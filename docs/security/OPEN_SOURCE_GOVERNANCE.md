# Open Source Software Governance

**Alignment:** ISO/IEC 5230 (OpenChain) core practices

## Intake

- Dependencies added via `requirements.txt` / lockfile with hash pinning
- License scan via `NOTICE` and `THIRD_PARTY_NOTICES.md`

## Risk assessment

- `pip-audit` (CI weekly + PR)
- Bandit static analysis
- CycloneDX SBOM per release

## Update & patch

- Follow `docs/security/SECURITY_UPDATE_POLICY.md`
- Critical CVEs: emergency release branch from Launch-57 line

## Upstream contribution

- Security fixes developed internally are contributed upstream when license permits and fix is general
- Track contributions in PR descriptions referencing CVE/GHSA

## Roles

| Role | Responsibility |
|------|----------------|
| Engineering lead | Lockfile approval |
| Security lead | Exception approval for audit failures |
| Legal | License conflict resolution |

## OSPO equivalent

This document serves as the BLACKDARK OSS governance program until a formal OSPO charter is published.
