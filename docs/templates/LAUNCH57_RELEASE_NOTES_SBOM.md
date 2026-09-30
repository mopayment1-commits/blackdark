# Launch-57 release — security supply-chain evidence

**Release:** `{{BLACKDARK_RELEASE}}`  
**Git commit:** `{{GIT_COMMIT}}`  
**Remediation SHA (CISA program):** `{{REMEDIATION_SHA}}`

## SBOM artifacts

| Artifact | Path / CI |
|----------|-----------|
| Python CycloneDX | `docs/data-room/sbom/cyclonedx-python.json` |
| Release manifest | `docs/data-room/sbom/LAUNCH57_RELEASE_MANIFEST.json` |
| Syft prod lockfile (optional) | CI artifact `launch57-syft-prod-lock-sbom` |

Regenerate manifest locally:

```bash
python scripts/publish_launch57_release_evidence.py
```

## Honesty

This section documents engineering SBOM bindings. It does **not** claim CISA certification or independent pentest completion.
