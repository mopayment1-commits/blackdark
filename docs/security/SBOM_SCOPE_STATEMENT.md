# SBOM Scope Statement (NTIA minimum elements)

**Program:** `docs/governance/LAUNCH57_CISA_SECURE_BY_DEMAND_REMEDIATION_PROGRAM.md` — FINDING-11 / L57-P4-WP3  
**NTIA gap analysis (E-ART):** `governance/launch57/LAUNCH57_NTIA_SBOM_GAP_ANALYSIS.json`  
**Verifier:** `python scripts/verify_launch57_sbom_ntia_scope.py`

## In scope (automated)

| Artifact | Generator | Path |
|----------|-----------|------|
| Python application dependencies | `scripts/generate_sbom.py` | `docs/data-room/sbom/cyclonedx-python.json` |
| Prod lockfile (Syft, CI) | `scripts/generate_syft_lockfile_sbom.sh` | CI artifact `launch57-syft-prod-lock-sbom` |

Metadata includes: `blackdark:git_commit`, `blackdark:lockfile_sha256`, `blackdark:release`, optional `blackdark:image_digest`.

## Out of scope (documented gap)

| Component | Rationale | Mitigation |
|-----------|-----------|------------|
| Debian base image packages | Generated at image build | Operator runs `trivy image` / Syft in deploy pipeline |
| CDN-hosted JS (e.g. charts) | Third-party edge delivery | Subresource Integrity where embedded |
| Auth0 / Stripe SaaS | External processors | Vendor SOC reports in data room |

## Completeness claim

Launch-57 claims **complete Python lockfile SBOM** per release SHA, not full multi-ecosystem SBOM unless container SBOM artifact is attached to release notes.

Sec Lead approval of the gap analysis is recorded via `LAUNCH57_SBOM_SEC_LEAD_APPROVAL_ID` when closing FINDING-11 through `transition_launch57_finding_status.py` (program §6).
