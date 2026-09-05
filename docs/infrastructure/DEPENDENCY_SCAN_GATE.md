# Dependency & SBOM Scanning Gate (#1044)

**Sprint 0 · CI/CD Infrastructure · NOT a standalone product module**

Third pillar of the security trilogy:

| Gate | Scope | Ref |
|------|-------|-----|
| SAST | Our source code | #1042 |
| DAST | Runtime / staging | #1043 |
| **Dependency Scan** | Third-party libraries | **#1044** |

## Purpose

Prevent exploitation of known CVEs in third-party dependencies. Continuous supply-chain scanning on every PR, merge, and deployment candidate.

## Tooling (open-source first)

| Tool | Role |
|------|------|
| `pip-audit` | CVE detection (Python) |
| `scripts/generate_sbom.py` | CycloneDX 1.5 SBOM |
| `scripts/generate_license_inventory.py` | License compliance |
| Dependabot / Snyk / OWASP Dependency-Check | Documented alternatives |

## Policy

| Severity | Action |
|----------|--------|
| Critical CVE | **Block merge / deployment** |
| High CVE | **Block merge / deployment** |
| Medium | Track — remediate within sprint |
| Low | Track only |

### Supply chain

- All dependencies pinned in `requirements.hashes.txt` with `sha256` hashes
- No unpinned versions, no hash mismatches
- SBOM generated per release (`docs/data-room/sbom/cyclonedx-python.json`)
- SBOM locked to `requirements.lock.txt` hash (#1029 immutable audit)

### License compliance

- Copyleft licenses (GPL, AGPL, SSPL, LGPL) → flag + legal review trigger
- Unknown licenses → tracked

### Suppressions

- **No developer self-suppress**
- Security lead approval required (`data/dependency_scan_suppressions.json`)
- Must include CVE ID + reason + `approved_by_security_lead`

## CI integration

```yaml
# .github/workflows/security.yml — job: dependency-scan-gate
python scripts/run_dependency_scan_gate.py
```

## API

| Endpoint | Auth | Description |
|----------|------|-------------|
| `GET /api/platform/dependency-scan/status` | Public | Policy + config |
| `GET /api/platform/dependency-scan/gate` | Public | Production gate checks |
| `GET /api/platform/dependency-scan/e2e` | Public | E2E self-test |
| `POST /api/platform/dependency-scan/run` | Admin | Trigger scan |

## Audit trail

- Append-only: `data/dependency_scan_audit.jsonl`
- Retention: 2 years (730 days)
- Fields: dependency, version, CVE ID, severity, CVSS, remediation, SBOM version

## Integrations

| Ref | Integration |
|-----|-------------|
| #1042 SAST | Security trilogy — unified CI gates |
| #1043 DAST | Runtime exploitability cross-reference |
| #1017 Incident Response | Critical CVE → emergency patch playbook |
| #1029 Immutable Audit | SBOM per release locked with hash |
| #1038 Activity Audit | Scan events in developer activity trail |

## Incident playbook (#1017)

When critical/high CVE detected in production dependency:

1. `trigger_dependency_cve_incident()` fires
2. Emergency patch assessment
3. Rollback evaluation
4. Forensics per incident response runbook

## Local usage

```bash
# Full gate (pip-audit + pinning + license + SBOM)
python scripts/run_dependency_scan_gate.py

# Fast scan (skip SBOM)
python scripts/run_dependency_scan_gate.py --skip-sbom

# JSON output
python scripts/run_dependency_scan_gate.py --json
```

## Files

| File | Purpose |
|------|---------|
| `dependency_scan_gate.py` | Gate engine |
| `data/dependency_scan_seed.json` | Policy seed |
| `data/dependency_scan_suppressions.json` | Approved suppressions |
| `scripts/run_dependency_scan_gate.py` | CI entry point |
| `scripts/generate_sbom.py` | CycloneDX SBOM |
| `scripts/generate_license_inventory.py` | License inventory |
