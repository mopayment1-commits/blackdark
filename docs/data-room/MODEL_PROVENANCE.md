# Model Provenance Inventory

**Finding:** `F-SC-03` / DEC-0014

| Artifact | In repo? | Notes |
|----------|----------|-------|
| Online / rules oracle | Yes | `oracle_unified.py`, regime helpers |
| Stored model weights | Partial | Fernet-protected paths when present; HMAC claims in architecture |
| Offline training corpora | **External** | Not shipped; DEC-0014 |
| Feature schemas | Yes | Feature builders in repo |
| Evaluation / accuracy ledger | Yes | `/oracle-accuracy` surfaces |

**Executable financial decisions** must not depend on unverifiable external training claims. Truth gates and fee/gas fail-closed paths remain code authorities.
