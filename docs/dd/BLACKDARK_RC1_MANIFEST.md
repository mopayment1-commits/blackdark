# BLACKDARK RC1_MANIFEST

**Freeze timestamp (UTC):** 2026-08-12T09:58:00Z  
**Audit mode:** READ-ONLY Technology Due Diligence (no production code changes)

| Field | Value |
|---|---|
| Repository | `mopayment1-commits/blackdark` |
| Canonical branch | `main` |
| **RC1 SHA** | `de6537fb29d6bc6203d58b572924db55b9c74d53` |
| Tree | `200e9bc3abb815d49e7620cdadd9aa1009eac813` |
| Merge parents | `abc9e2bb602d82274d6c7f60e1547306745490d2` + `8bd0f16231ad8f2cb9d88fe653c61f3d14ad5003` |
| Tip subject | Merge pull request #62 (final two-track certification docs) |
| Release tag | none (`git describe` → short SHA only) |
| Tracked files | 680 |
| Python files | 437 |
| Working tree at freeze | clean vs `origin/main` |
| Dependency locks | `requirements.hashes.txt`, `requirements.lock.txt`, `requirements-prod.hashes.txt` |
| requirements.txt SHA256 | `7285eb95d0713438c3fbaa6ceb7106a008069fe3b859381e407f02aa2f5da328` |
| requirements.hashes.txt SHA256 | `3df5bfd8d6d64568110682dce829bc952980bee440280cd0f442dd49be125bfb` |
| CI workflows | `.github/workflows/{ci,security,sonarcloud}.yml` |
| Environment assumptions | Soft Launch may use SQLite; strict production requires Postgres + sealed secrets; viral HA requires Redis + multi-instance + Soft Launch unset |
| Deployment assumptions | Docker/`SERVICE_MODE=web` primary; optional compose HA / Railway / Render Soft Launch / k8s manifests present |
| Live production / buyer cloud | **NOT IN SCOPE** for this DD (no access) |
| Code Scanning alerts API | **403** this principal |
| Branch protection API | **403 / not verifiable** this principal |
| Cursor historical chats | **NOT ACCESSIBLE** — not claimed reviewed |

**Invalidation rule:** Any new commit on `main` after this SHA invalidates RC1; open RC2.

**Independent test snapshot (E3):** `tests/ -m "not load and not network"` → **603 passed / 0 failed** on RC1 SHA (local clean env).  
**Bandit (E3):** HIGH=0 MEDIUM=0 LOW=112.  
**CI @ RC1:** Critical SUCCESS (`31584454435`); Security Scan SUCCESS (`31584454461`); Sonar Analysis FAILURE QG new_coverage 28.3% (`31584454484`); CodeQL Analyze SUCCESS (`31584454258`).
