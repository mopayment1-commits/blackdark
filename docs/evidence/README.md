# Security scan evidence

## Bandit 4703 reconciliation

| File | Purpose |
|---|---|
| `bandit-full-4703-compact.json` | Original 4703 findings (`filename`, `line_number`, `test_id` only — no issue text) |
| `bandit-disposition-inventory-4703.json` | Explicit per-location disposition for fail-closed rules |

Run reconciliation:

```bash
python3 scripts/bandit_disposition_audit.py
# or: --report docs/evidence/bandit-full-4703-compact.json --inventory docs/evidence/bandit-disposition-inventory-4703.json
```
