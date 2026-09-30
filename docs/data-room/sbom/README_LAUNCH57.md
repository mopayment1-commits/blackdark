# Launch-57 SBOM data room

| File | Generator |
|------|-----------|
| `cyclonedx-python.json` | `scripts/generate_sbom.py` |
| `LAUNCH57_RELEASE_MANIFEST.json` | `scripts/publish_launch57_release_evidence.py` |

Syft CycloneDX from prod lockfile is produced in CI (`launch57-cisa-assurance` workflow) and uploaded as `launch57-syft-prod-lock-sbom`.

See `docs/security/SBOM_SCOPE_STATEMENT.md`.
