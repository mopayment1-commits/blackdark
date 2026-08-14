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
    tracks = cert.get("tracks") or v.get("tracks") or {}
    drills = (cert.get("drills") or {}).get("items") or []
    cc = cert.get("capability_counts") or {}

    one = f"""# FINAL PRODUCTION VERDICT

**SHA:** `{sha}`  
**الحكم:** **{v['decision']}**  
**product_complete:** `{cert['product_complete']}`  
**unconditional_go_criteria_met:** `{v['unconditional_go_criteria_met']}`

## Three tracks (explicit — never «Production Ready ورقيًا»)

| Track | Result |
|---|---|
| PUBLIC-DEMO-READY | **{tracks.get('PUBLIC-DEMO-READY')}** |
| LIVE-PRODUCTION-READY | **{tracks.get('LIVE-PRODUCTION-READY')}** |
| LIVE-MONEY-READY | **{tracks.get('LIVE-MONEY-READY')}** |

PUBLIC-DEMO-READY is not LIVE-PRODUCTION-READY. LIVE-PRODUCTION-READY is not LIVE-MONEY-READY. Unconditional GO requires both live tracks plus the counts below at zero.

| عنصر الإدارة | القيمة |
|---|---|
| Critical open | **{v['critical_open']}** |
| High open | **{v['high_open']}** |
| Medium open | **{v['medium_open']}** |
| Low open | **{v.get('low_open', 0)}** |
| Untested launch-critical requirements | **{v['untested_launch_critical_requirements']}** |
| Unverified launch-critical assumptions | {len(v.get('unverified_launch_critical_assumptions') or [])} |
| Unverified assumptions | {len(v.get('unverified_assumptions') or [])} |
| External blockers | {', '.join(v['external_blockers']) or 'none'} |
| Known accepted risks | {len(v['known_accepted_risks'])} |
| Unknown launch blockers | {len(v['unknown_launch_blockers'])} |

## لماذا ليس Unconditional GO

{v.get('why_not_go') or 'n/a'}

## افتراضات غير مُثبتة (إطلاق-حرج)

{(chr(10).join(f'- {x}' for x in (v.get('unverified_launch_critical_assumptions') or [])) or '- none (converted to FAIL/PASS with drills)')}

## مخاطر مقبولة (لا تُخفى)

{chr(10).join(f'- {x}' for x in v['known_accepted_risks'])}

## ما الذي نجح دون أن يُحوَّل إلى GO

- نزاهة القرار المالية (11 حالة): **{integ['verdict']}** ({integ['pass_count']}/{integ['case_count']})
- جمهور HTTP مباشر: **{pub.get('public_direct_use_percent')}%** (مقام معلن ≠ مال حي)
- محرك المخاطر / تجميد التنفيذ: انظر D08
- سلامة المستخدم (لا يقين مضلل): انظر D35
- Drills PASS/FAIL: {cert.get('drills', {}).get('pass_count')}/{cert.get('drills', {}).get('fail_count')} (not_tested={cert.get('drills', {}).get('not_tested_count')})

معيار GO غير المشروط: 0 Critical + 0 High + 0 untested launch-critical + 0 unknown blockers + 0 unverified launch-critical assumptions + LIVE-PRODUCTION-READY + LIVE-MONEY-READY + أدلة قابلة لإعادة التحقق. **غير متحقق ما لم يظهر الجدول أعلاه كلها صفرًا والمساران الحيّان true.**
"""
    (DD / "BLACKDARK_FINAL_PRODUCTION_VERDICT.md").write_text(one, encoding="utf-8")

    domain_rows = [
        (d["id"], d["title"], d["verdict"], str(d["launch_critical"]), d["severity_if_open"])
        for d in domains
    ]
    drill_rows = [(d.get("id"), d.get("verdict"), str(d.get("evidence") or "")[:80]) for d in drills]
    audit = f"""# Production Readiness Audit Report

**SHA:** `{sha}`  
**Verdicts allowed:** PASS / FAIL / NOT_TESTED / NOT_APPLICABLE only.  
**Feature tracks allowed:** PUBLIC-DEMO-READY / LIVE-PRODUCTION-READY / LIVE-MONEY-READY / NOT-READY.  
**Final:** **{v['decision']}**

{_md_table(domain_rows, ("ID", "Domain", "Verdict", "Launch-critical", "Severity if open"))}

## Evidence rule

Each launch-critical domain is FAIL unless a re-verifiable drill on this SHA supports PASS. NOT_TESTED is forbidden for launch-critical controls after this cert (converted to FAIL when the required control is absent). Public HTTP 100% is D03/D32 support only — it is not live-money certification.

## Drills executed on this SHA

{_md_table(drill_rows, ("Drill", "Verdict", "Evidence"))}

## Capability track counts

- Total: {cc.get('total')}
- PUBLIC-DEMO-READY: {cc.get('PUBLIC-DEMO-READY')}
- LIVE-PRODUCTION-READY: {cc.get('LIVE-PRODUCTION-READY')}
- LIVE-MONEY-READY: {cc.get('LIVE-MONEY-READY')}
- NOT-READY: {cc.get('NOT-READY')}

Binding JSON: `docs/dd/BLACKDARK_PRODUCTION_LAUNCH_CERT_EVIDENCE.json`
"""
    (DD / "BLACKDARK_PRODUCTION_READINESS_AUDIT.md").write_text(audit, encoding="utf-8")

    d10 = next((d for d in domains if d["id"] == "D10"), {})
    d11 = next((d for d in domains if d["id"] == "D11"), {})
    sec = f"""# Security Assessment + Penetration Test

**SHA:** `{sha}`  
**Independent pentest artifact:** **{d10.get('verdict')}** (D10)  
**In-repo adversarial API pack:** **{d11.get('verdict')}** (D11)

D10 FAIL means no independent firm pentest report is on disk for this SHA. The in-repo pack (`tests/test_adversarial_launch_redteam.py`) is D11, not a pentest firm.

Unit evidence that exists:

- `tests/test_security_hardening.py`
- `tests/test_p0_authz_hardening.py`
- Fail-closed HTTP 503 on unconfigured OAuth / Telegram / PSP
- Session cookie + PBKDF2 + TOTP enrollment path

**Closure condition (pentest + zero unaccepted Critical/High):** remains open while D10 is FAIL.
"""
    (DD / "BLACKDARK_SECURITY_ASSESSMENT.md").write_text(sec, encoding="utf-8")

    icases = [(c["id"], c["intent"], c["verdict"]) for c in integ["cases"]]
    fin = f"""# Financial & Decision Integrity Audit

**SHA:** `{sha}`  
**Pipeline:** Raw source → ingestion → canonical → signal/rules → risk → decision → displayed output → audit record  
**Verdict:** **{integ['verdict']}** ({integ['pass_count']}/{integ['case_count']})

{_md_table(icases, ("Case", "Intent", "Verdict"))}

Rule: correct data may pass; stale / missing / contradictory / duplicated / delayed / outlier / disconnected / wrong timestamp / source disagreement / partial coverage must reject or abstain — never convert uncertainty into a live BUY.

Independent venue FILL vs P&amp;L reference: **FAIL** (live_fill=false, geo 451) — evaluated, not untested.
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

    sc_rows = [
        (s["id"], s["verdict"], str(s.get("blocks_bad_decision")), str(s.get("fails_safe")))
        for s in three["scenarios"]
    ]
    rel = f"""# Reliability / HA / DR / Failure Injection Report

**SHA:** `{sha}`  
**3 AM definition:** production-bad conditions with no developer catching the process.

{_md_table(sc_rows, ("Scenario", "Verdict", "Blocks bad decision", "Fails safe"))}

On-call Telegram configured: **{three.get('telegram_oncall_configured')}**  
On-call live drill: see `drills.telegram_oncall_live` (PASS requires telegram ok + message_id; secrets never recorded).

Cloud multi-AZ: **FAIL** (unpaid external). Local Postgres streaming HA is a different control and is not this report's cloud HA claim.

DR region/AZ loss: **FAIL** (D20 / EXT_CLOUD_HA). Local probe-DB DROP + pg_restore: see drill `postgres_dump_restore` (D22). Backup restore: `sqlite_restore` / `postgres_dump_restore`.
"""
    (DD / "BLACKDARK_RELIABILITY_HA_DR_FAILURE_INJECTION.md").write_text(rel, encoding="utf-8")

    d18 = next((d for d in domains if d["id"] == "D18"), {})
    d19 = next((d for d in domains if d["id"] == "D19"), {})
    d39 = next((d for d in domains if d["id"] == "D39"), {})
    asgi = next((d for d in drills if d.get("id") == "asgi_latency"), {})
    http_load = next((d for d in drills if d.get("id") == "http_load_local"), {})
    chrome = next((d for d in drills if d.get("id") == "chrome_public_pages"), {})
    perf = f"""# Performance / Load / Stress / Soak Report

**SHA:** `{sha}`  
**D18 Performance:** {d18.get('verdict')}  
**D19 Load/Stress/Spike:** {d19.get('verdict')}  
**D39 Launch capacity:** {d39.get('verdict')}

Local ASGI pack (`asgi_latency`): verdict={asgi.get('verdict')} p50_ms={asgi.get('p50_ms')} p95_ms={asgi.get('p95_ms')} n={asgi.get('n')}.  
Local 2-worker HTTP pack (`http_load_local`): verdict={http_load.get('verdict')} p50_ms={http_load.get('p50_ms')} p95_ms={http_load.get('p95_ms')} n={http_load.get('n')}.  
Chrome public pages (`chrome_public_pages`): verdict={chrome.get('verdict')}.

These local packs are **not** a production multi-AZ SLO, soak, or breaking-point measurement. D18/D19/D39 remain FAIL for live production even if the local packs PASS.
"""
    (DD / "BLACKDARK_PERFORMANCE_LOAD_STRESS_SOAK.md").write_text(perf, encoding="utf-8")

    d30 = next((d for d in domains if d["id"] == "D30"), {})
    d31 = next((d for d in domains if d["id"] == "D31"), {})
    legal = f"""# Legal, Privacy & Data-Licensing Gap Report

**SHA:** `{sha}`  
**Author role:** software engineering cert on this SHA — **not independent legal counsel.**

| Topic | Engineering fact | Specialist verdict |
|---|---|---|
| Terms / Privacy / Disclaimer / Refund / Cookies pages | PASS render (public HTTP catalog) | counsel artifact {d30.get('verdict')} |
| GDPR DSR export/erase | PASS code path | counsel artifact {d30.get('verdict')} |
| Financial positioning | Research tool; anti-hype; ledger of misses | counsel artifact {d30.get('verdict')} |
| Venue API / derived-data commercial use | Public market adapters; license inventory {d31.get('verdict')} | counsel artifact {d30.get('verdict')} |
| Jurisdictions | Not mapped in this cert | FAIL unless counsel artifact present |

**D30:** {d30.get('verdict')} (launch-critical). Missing independent counsel file is FAIL, not NOT_TESTED. This file is a **gap report**, not a legal opinion.
"""
    (DD / "BLACKDARK_LEGAL_PRIVACY_LICENSING_GAP.md").write_text(legal, encoding="utf-8")

    cap_rows = [(c["id"], c["certification"], c["inventory_status"], c["scope"]) for c in caps]
    red_rows = [(r["axis"], r["verdict"], (r.get("notes") or "")[:120]) for r in red]
    reg = f"""# Final Launch Certification & Evidence Register

**SHA:** `{sha}`  
**Decision:** **{v['decision']}**  
**Tracks:** PUBLIC-DEMO-READY={tracks.get('PUBLIC-DEMO-READY')} · LIVE-PRODUCTION-READY={tracks.get('LIVE-PRODUCTION-READY')} · LIVE-MONEY-READY={tracks.get('LIVE-MONEY-READY')}  
**JSON:** `docs/dd/BLACKDARK_PRODUCTION_LAUNCH_CERT_EVIDENCE.json`

This register is bound to SHA `{sha}` only. A later SHA requires a new prove run.

## Red team (7 axes)

{_md_table(red_rows, ("Axis", "Verdict", "Notes"))}

## Feature-by-feature certification

Tokens allowed: PUBLIC-DEMO-READY / LIVE-PRODUCTION-READY / LIVE-MONEY-READY / NOT-READY.  
PUBLIC-DEMO-READY is visitor/paper. It is not live production and not live money.

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
    from operator_go_gates import render_markdown as render_operator_gates

    (DD / "BLACKDARK_OPERATOR_GO_GATES.md").write_text(render_operator_gates(cert), encoding="utf-8")


def main() -> int:
    sys.path.insert(0, str(ROOT))
    from production_launch_certification import EVIDENCE_PATH, build_certification

    cert = build_certification()
    EVIDENCE_PATH.parent.mkdir(parents=True, exist_ok=True)
    EVIDENCE_PATH.write_text(json.dumps(cert, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    render_reports(cert)
    v = cert["final_production_verdict"]
    tracks = cert.get("tracks") or {}
    summary = {
        "sha": cert["sha"],
        "decision": v["decision"],
        "PUBLIC-DEMO-READY": tracks.get("PUBLIC-DEMO-READY"),
        "LIVE-PRODUCTION-READY": tracks.get("LIVE-PRODUCTION-READY"),
        "LIVE-MONEY-READY": tracks.get("LIVE-MONEY-READY"),
        "critical_open": v["critical_open"],
        "high_open": v["high_open"],
        "medium_open": v["medium_open"],
        "untested_launch_critical": v["untested_launch_critical_requirements"],
        "unverified_launch_critical_assumptions": len(v.get("unverified_launch_critical_assumptions") or []),
        "unknown_launch_blockers": v.get("unknown_launch_blockers"),
        "integrity": cert["financial_decision_integrity"]["verdict"],
        "integrity_pass": f"{cert['financial_decision_integrity']['pass_count']}/{cert['financial_decision_integrity']['case_count']}",
        "drills_pass": cert.get("drills", {}).get("pass_count"),
        "drills_fail": cert.get("drills", {}).get("fail_count"),
        "product_complete": False,
        "live_money_ready": bool(tracks.get("LIVE-MONEY-READY")),
        "evidence": str(EVIDENCE_PATH),
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0 if v["decision"] in {"GO", "CONDITIONAL GO", "NO-GO"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
