# BLACKDARK Service Level Agreement

**Legal status:** APPROVED FOR PUBLICATION  
**Version:** 1.0  
**Effective Date:** 1 January 2025

## Provider

This Service Level Agreement ("SLA") is issued by **شركة أم أو لتصميم البرامج (MO Software Design LLC)** ("Provider") for the BLACKDARK decision-intelligence platform.

## 1. Scope

This SLA applies to paid subscription tiers (Pro, Elite, Quant) and institutional contracts that reference it. Free / demo access is best-effort and excluded unless expressly agreed in writing.

## 2. Availability targets

| Tier | Monthly uptime target | Measurement |
|---|---|---|
| Pro | 99.5% | `/health` + observability probes |
| Elite / Quant | 99.7% | Dedicated probe set |
| Institutional | 99.9% | Contractual — requires signed HA load evidence (REL-002) |

Scheduled maintenance windows are announced in advance when practicable and excluded from downtime calculations.

## 3. Support response

| Severity | Pro | Elite / Quant | Institutional |
|---|---|---|---|
| P1 — Platform down | 4h | 2h | 1h |
| P2 — Degraded | 8h | 4h | 2h |
| P3 — General | 48h | 24h | 8h |

Published support operations: **MOPAYMENT1@GMAIL.COM**, **10:00 AM – 10:00 PM Cairo Time, daily**. Urgent escalation: same email with subject prefix **URGENT**.

## 4. Measurement and evidence

Uptime is measured via `data/uptime_probes.jsonl`, `/health`, and the observability stack. Institutional buyers may request signed capacity evidence per the Integration Addendum.

## 5. Exclusions

Force majeure, third-party exchange/API outages outside Provider control, customer misconfiguration, and abuse/rate-limit enforcement are excluded from availability credits unless otherwise agreed in a signed order form.

## 6. Governing law

This SLA is governed by the **Laws of the Arab Republic of Egypt**, without regard to conflict-of-law principles.

## 7. Dispute resolution

The parties shall attempt good-faith resolution through the published support channels within thirty (30) days. Unresolved disputes shall be subject to the **exclusive jurisdiction of the competent courts in Cairo, Egypt**.

## 8. Legal approval

External legal review is complete. **Status: APPROVED FOR PUBLICATION.** Effective **1 January 2025**.
