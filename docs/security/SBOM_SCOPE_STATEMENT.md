# SBOM Scope Statement (NTIA minimum elements)

## In scope (automated)

| Artifact | Generator | Path |
|----------|-----------|------|
| Python application dependencies | `scripts/generate_sbom.py` | `docs/data-room/sbom/cyclonedx-python.json` |

Metadata includes: `blackdark:git_commit`, `blackdark:lockfile_sha256`, `blackdark:release`, optional `blackdark:image_digest`.

## Out of scope (documented gap)

| Component | Rationale | Mitigation |
|-----------|-----------|------------|
| Debian base image packages | Generated at image build | Operator runs `trivy image` / Syft in deploy pipeline |
| CDN-hosted JS (e.g. charts) | Third-party edge delivery | Subresource Integrity where embedded |
| Auth0 / Stripe SaaS | External processors | Vendor SOC reports in data room |

## Completeness claim

Launch-57 claims **complete Python lockfile SBOM** per release SHA, not full multi-ecosystem SBOM unless container SBOM artifact is attached to release notes.
