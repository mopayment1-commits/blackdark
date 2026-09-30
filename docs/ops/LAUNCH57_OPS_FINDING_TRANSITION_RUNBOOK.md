# Launch-57 — Ops finding transition runbook

Use when **real** ops/executive evidence exists. This tool **refuses** fake closure.

## Supported transitions → `CLOSED`

| Finding | Prerequisite |
|---------|----------------|
| FINDING-01 | `--pledge-url` (CISA portal) + update `SECURE_BY_DESIGN_PLEDGE_STATUS.md` manually |
| FINDING-14 | `LAUNCH57_PROD_URL` + `verify_well_known_security_txt.py --url` pass |
| FINDING-18 | `verify_pentest_attestation()` true (deposit via institutional API) |
| FINDING-19 | `CDN_WAF_ACTIVE=1` + `verify_edge_waf_cdn.py` exit 0 |
| FINDING-11 | Syft SBOM artifact present (CI or `LAUNCH57_CONTAINER_SBOM_PATH`) |

## Commands

```bash
# Dry-run (default)
python scripts/transition_launch57_finding_status.py --finding FINDING-14 --prod-url https://...

# Apply after success
python scripts/transition_launch57_finding_status.py --finding FINDING-14 --prod-url https://... --apply

python scripts/generate_launch57_completion_status.py
python scripts/generate_launch57_engineering_closure.py
```

## Prohibited

- `--apply` without passing verification (script exits 2)
- Marking FINDING-18 closed without vendor pentest deposit
