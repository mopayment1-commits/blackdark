# Revocation: Invalid INSTITUTIONAL_CLOSED Claim (PR #349)

**Date:** 2026-09-01  
**Governance:** CLOSURE-REJECT-02 / CLOSURE-REJECT-03  
**Target commit on main:** `9798ab86c6a94287fbee88fdb147f5988ce6cfbe`

## Revocation statement

The merge commit message and prior agent declaration:

> `Official Batch 01+02 institutional closure (IDs 1–100) INSTITUTIONAL_CLOSED`

is **revoked and void**. Git history is immutable; this document is the corrective record on `main` after merge of PR #350.

## Legal effect

- `closure_status` in all manifests = **`PENDING_CLOSURE`**
- Merge ≠ institutional closure
- Owner written approval required before any future `INSTITUTIONAL_CLOSED` declaration

## Required follow-up on main

1. Merge PR #350 (CLOSURE-REJECT-02/03 remediation)
2. Move tag `batch01-02-pending-closure-v1` to first post-revocation commit on `main`
3. Achieve gate-full + Sonar Grade A + >=80% spine coverage
