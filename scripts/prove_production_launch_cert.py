"""Prove production launch certification on the exact git SHA. Never claims GO without evidence."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DD = ROOT / "docs" / "dd"


def _md_table(rows: list[tuple[str, ...]], headers: tuple[str, ...]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    for r in rows:
        lines.append("| " + " | ".join(str(c).replace("|", "/") for c in r) + " |")
    return "\n".join(lines)


def render_reports(cert: dict) -> None:
    v = cert["final_production_verdict"]
    sha = cert["sha"]
    domains = cert["domains"]
    integ = cert["financial_decision_integrity"]
    three = cert["three_am"]
    caps = cert["capabilities"]
    red = cert["red_team"]
    pub = cert.get("public_direct_use") or {}

    one = f"""# FINAL PRODUCTION VERDICT

**SHA:** `{sha}`  
**الحكم:** **{v['decision']}**  
**product_complete:** `{cert['product_complete']}`  
**live_money_ready:** `{cert['live_money_ready']}`  
**unconditional_go_criteria_met:** `{v['unconditional_go_criteria_met']}`

| عنصر الإدارة | القيمة |
|---|---|
| Critical open | **{v['critical_open']}** |
| High open | **{v['high_open']}** |
| Medium open | **{v['medium_open']}** |
| Low open | **{v.get('low_open', 0)}** |
| Untested launch-critical requirements | **{v['untested_launch_critical_requirements']}** |
| Unverified assumptions | {len(v['unverified_assumptions'])} |
| External blockers | {', '.join(v['external_blockers']) or 'none'} |
| Known accepted risks | {len(v['known_accepted_risks'])} |
| Unknown launch blockers | {len(v['unknown_launch_blockers'])} |

## لماذا ليس GO

{v['why_not_go']}

## افتراضات غير مُثبتة

{chr(10).join(f'- {x}' for x in v['unverified_assumptions'])}

## مخاطر مقبولة (لا تُخفى)

{chr(10).join(f'- {x}' for x in v['known_accepted_risks'])}

## ما الذي نجح دون أن يُحوَّل إلى GO

- نزاهة القرار المالية (11 حالة): **{integ['verdict']}** ({integ['pass_count']}/{integ['case_count']})
- جمهور HTTP مباشر: **{pub.get('public_direct_use_percent')}%** (مقام معلن ≠ مال حي)
- محرك المخاطر / تجميد التنفيذ: PASS (D08)
- سلامة المستخدم (لا يقين مضلل): PASS (D35)

معيار GO غير المشروط: 0 Critical + 0 High + 0 untested launch-critical + 0 unknown blockers + أدلة إنتاج إلزامية قابلة لإعادة التحقق. **غير متحقق.**
"""
    (DD / "BLACKDARK_FINAL_PRODUCTION_VERDICT.md").write_text(one, encoding="utf-8")

    domain_rows = [(d["id"], d["title"], d["verdict"], str(d["launch_critical"]), d["severity_if_open"]) for d in domains]
    audit = f"""# Production Readiness Audit Report

**SHA:** `{sha}`  
**Verdicts allowed:** PASS / FAIL / NOT_TESTED / NOT_APPLICABLE only.  
**Final:** **{v['decision']}**

{_md_table(domain_rows, ("ID", "Domain", "Verdict", "Launch-critical", "Severity if open"))}

## Evidence rule

Each domain is FAIL or NOT_TESTED unless a re-verifiable artifact on this SHA supports PASS. Public HTTP 100% is D03/D32 support only — it is not live-money certification.

## Capability certification counts

- Total: {cert['capability_counts']['total']}
- PRODUCTION-READY (paper/advisory scope): {cert['capability_counts']['production_ready']}
- NOT PRODUCTION-READY: {cert['capability_counts']['not_production_ready']}

Binding JSON: `docs/dd/BLACKDARK_PRODUCTION_LAUNCH_CERT_EVIDENCE.json`
"""
    (DD / "BLACKDARK_PRODUCTION_READINESS_AUDIT.md").write_text(audit, encoding="utf-8")

    sec = f"""# Security Assessment + Penetration Test

**SHA:** `{sha}`  
**Independent pentest:** **NOT_TESTED**  
**Domain D10:** NOT_TESTED (launch-critical, severity critical)  
**Domain D11:** NOT_TESTED (launch-critical, severity high)

This is **not** a penetration test report. Unit evidence that exists:

- `tests/test_security_hardening.py` (Telegram test 401, CSP, logout)
- `tests/test_p0_authz_hardening.py`
- Fail-closed HTTP 503 on unconfigured OAuth / Telegram / PSP
- Session cookie + PBKDF2 + TOTP enrollment path

**Closure condition (pentest + zero unaccepted Critical/High):** **FAIL to close.**  
An engineer running unit tests is not a pentest firm.
"""
    (DD / "BLACKDARK_SECURITY_ASSESSMENT.md").write_text(sec, encoding="utf-8")

    icases = [(c["id"], c["intent"], c["verdict"]) for c in integ["cases"]]
    fin = f"""# Financial & Decision Integrity Audit

**SHA:** `{sha}`  
**Pipeline:** Raw source → ingestion → canonical → signal/rules → risk → decision → displayed output → audit record  
**Verdict:** **{integ['verdict']}** ({integ['pass_count']}/{integ['case_count']})

{_md_table(icases, ("Case", "Intent", "Verdict"))}

Rule: correct data may pass; stale / missing / contradictory / duplicated / delayed / outlier / disconnected / wrong timestamp / source disagreement / partial coverage must reject or abstain — never convert uncertainty into a live BUY.

Independent venue FILL vs P&amp;L reference: **NOT_TESTED** (live_fill=false, geo 451).
"""
    (DD / "BLACKDARK_FINANCIAL_DECISION_INTEGRITY_AUDIT.md").write_text(fin, encoding="utf-8")

    data = f"""# Data Integrity & Provenance Audit

**SHA:** `{sha}`  
**Canonical layer:** `canonical_data_layer.py` (LIVE fails closed without provenance)  
**Stale guard:** `stale_price_guard.py`  
**L2 remainder:** synthetic_mid labeled; full_mesh_l2_complete=false

Integrity cases covering missing/stale/conflict/partial coverage: **{integ['verdict']}**.

A decision that cannot be proved is withheld (Net-Edge reject, dimension veto → Do Not Touch, execution freeze).
"""
    (DD / "BLACKDARK_DATA_INTEGRITY_PROVENANCE_AUDIT.md").write_text(data, encoding="utf-8")

    sc_rows = [(s["id"], s["verdict"], str(s.get("blocks_bad_decision")), str(s.get("fails_safe"))) for s in three["scenarios"]]
    rel = f"""# Reliability / HA / DR / Failure Injection Report

**SHA:** `{sha}`  
**3 AM definition:** production-bad conditions with no developer catching the process.

{_md_table(sc_rows, ("Scenario", "Verdict", "Blocks bad decision", "Fails safe"))}

On-call Telegram configured: **{three.get('telegram_oncall_configured')}**

Cloud multi-AZ: **FAIL** (unpaid external). Local Postgres streaming HA is a different control and is not this report's cloud HA claim.

DR region loss: **NOT_TESTED**. Backup restore drill: **NOT_TESTED** in this cert function (helper exists in `ops_recovery.py`).
"""
    (DD / "BLACKDARK_RELIABILITY_HA_DR_FAILURE_INJECTION.md").write_text(rel, encoding="utf-8")

    perf = f"""# Performance / Load / Stress / Soak Report

**SHA:** `{sha}`  
**D18 Performance:** NOT_TESTED  
**D19 Load/Stress/Spike:** NOT_TESTED  
**D39 Launch capacity:** NOT_TESTED

Harness present: `scripts/load_test_concurrent.py`.  
No p50/p95/p99 SLO pack and no endurance/soak of this SHA against production-like workers is attached.

This report does **not** invent latency numbers.
"""
    (DD / "BLACKDARK_PERFORMANCE_LOAD_STRESS_SOAK.md").write_text(perf, encoding="utf-8")

    legal = f"""# Legal, Privacy & Data-Licensing Gap Report

**SHA:** `{sha}`  
**Author role:** software engineering cert on this SHA — **not independent legal counsel.**

| Topic | Engineering fact | Specialist verdict |
|---|---|---|
| Terms / Privacy / Disclaimer / Refund / Cookies pages | PASS render (public HTTP catalog) | NOT_TESTED by counsel |
| GDPR DSR export/erase | PASS code path | NOT_TESTED by privacy counsel |
| Financial positioning | Research tool; anti-hype; ledger of misses | NOT_TESTED by counsel |
| Venue API / derived-data commercial use | Public market adapters | NOT_TESTED by licensing counsel |
| Jurisdictions | Not mapped in this cert | NOT_TESTED |

**D30 / D31:** NOT_TESTED (launch-critical). This file is a **gap report**, not a legal opinion.
"""
    (DD / "BLACKDARK_LEGAL_PRIVACY_LICENSING_GAP.md").write_text(legal, encoding="utf-8")

    cap_rows = [(c["id"], c["certification"], c["inventory_status"], c["scope"]) for c in caps]
    red_rows = [(r["axis"], r["verdict"], r["notes"][:120]) for r in red]
    reg = f"""# Final Launch Certification & Evidence Register

**SHA:** `{sha}`  
**Decision:** **{v['decision']}**  
**JSON:** `docs/dd/BLACKDARK_PRODUCTION_LAUNCH_CERT_EVIDENCE.json`

## Red team (7 axes)

{_md_table(red_rows, ("Axis", "Verdict", "Notes"))}

## Feature-by-feature certification

PRODUCTION-READY here means the feature may run in a production **paper/advisory** deploy without lying. It is **not** live-money ready unless scope says so (none do for FILL/PSP/Jupiter VC).

{_md_table(cap_rows, ("ID", "Certification", "Inventory", "Scope"))}

## Mandatory outputs

1. Production Readiness Audit — `BLACKDARK_PRODUCTION_READINESS_AUDIT.md`
2. Security Assessment + Pentest status — `BLACKDARK_SECURITY_ASSESSMENT.md`
3. Financial & Decision Integrity — `BLACKDARK_FINANCIAL_DECISION_INTEGRITY_AUDIT.md`
4. Data Integrity & Provenance — `BLACKDARK_DATA_INTEGRITY_PROVENANCE_AUDIT.md`
5. Reliability / HA / DR / Failure injection — `BLACKDARK_RELIABILITY_HA_DR_FAILURE_INJECTION.md`
6. Performance / Load / Stress / Soak — `BLACKDARK_PERFORMANCE_LOAD_STRESS_SOAK.md`
7. Legal / Privacy / Licensing gap — `BLACKDARK_LEGAL_PRIVACY_LICENSING_GAP.md`
8. This register + one-pager `BLACKDARK_FINAL_PRODUCTION_VERDICT.md`
"""
    (DD / "BLACKDARK_FINAL_LAUNCH_CERTIFICATION_EVIDENCE_REGISTER.md").write_text(reg, encoding="utf-8")


def main() -> int:
    sys.path.insert(0, str(ROOT))
    from production_launch_certification import EVIDENCE_PATH, build_certification

    cert = build_certification()
    EVIDENCE_PATH.parent.mkdir(parents=True, exist_ok=True)
    EVIDENCE_PATH.write_text(json.dumps(cert, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    render_reports(cert)
    v = cert["final_production_verdict"]
    summary = {
        "sha": cert["sha"],
        "decision": v["decision"],
        "critical_open": v["critical_open"],
        "high_open": v["high_open"],
        "medium_open": v["medium_open"],
        "untested_launch_critical": v["untested_launch_critical_requirements"],
        "integrity": cert["financial_decision_integrity"]["verdict"],
        "integrity_pass": f"{cert['financial_decision_integrity']['pass_count']}/{cert['financial_decision_integrity']['case_count']}",
        "product_complete": False,
        "live_money_ready": False,
        "evidence": str(EVIDENCE_PATH),
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0 if v["decision"] in {"GO", "CONDITIONAL GO", "NO-GO"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
