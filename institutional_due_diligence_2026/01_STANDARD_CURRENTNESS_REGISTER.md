# 01 — STANDARD CURRENTNESS REGISTER

**Audit ID:** IDA-2026-BLACKDARK-001  
**Created:** 2026-09-11T01:05:00Z  
**Purpose:** Mandatory currentness check before audit (Contract §5)

| Ref ID | Issuer | Title | Version | Pub Date | Status | Superseded | URL | Applicability | Domains |
|---|---|---|---|---|---|---|---|---|---|
| REF-F01 | Fed/OCC/FDIC | Model Risk Management (SR 26-2) | Apr 2026 | 2026-04-17 | FINAL | NO | https://www.federalreserve.gov/supervisionreg/srletters/SR2602.htm | INSTITUTIONAL_BENCHMARK | W3 Models |
| REF-F02 | BIS/BCBS | BCBS 239 Risk Data Aggregation | Jan 2013 | 2013-01 | FINAL | NO | https://www.bis.org/publications/201301-guidelines-principles-effective-risk-data-aggregation-and-risk-reporting | INSTITUTIONAL_BENCHMARK | W4 Data |
| REF-F02b | BIS/BCBS | Basel Operational Resilience | Current | — | FINAL | NO | https://www.bis.org/committees/bcbs/basel-consolidated-guidelines/module/orr/20 | INSTITUTIONAL_BENCHMARK | W15 Resilience |
| REF-F03 | NIST | Cybersecurity Framework | 2.0 | 2024 | FINAL | NO | https://www.nist.gov/cyberframework | TECHNICAL_BENCHMARK | W7 Security |
| REF-F03a | NIST | SP 800-53 Rev.5 | Rev.5 | 2020+ | FINAL | NO | https://csrc.nist.gov/pubs/sp/800/53/a/r5/final | TECHNICAL_BENCHMARK | W7 Security |
| REF-F03b | NIST | SP 800-218 SSDF | 1.1 | 2022 | FINAL | NO | https://csrc.nist.gov/pubs/sp/800/218/final | TECHNICAL_BENCHMARK | W13 CI/CD |
| REF-F03c | NIST | SP 800-61 Rev.3 | Rev.3 | 2024 | FINAL | NO | https://csrc.nist.gov/pubs/sp/800/61/r3/final | TECHNICAL_BENCHMARK | W16 IR |
| REF-F03d | NIST | AI RMF 1.0 | 1.0 | 2023 | FINAL | NO | https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-generative-artificial-intelligence | TECHNICAL_BENCHMARK | W6 AI/ML |
| REF-F04 | ISO/IEC | 25010 Product Quality | 2023 | 2023 | FINAL | NO | https://www.iso.org/ | TECHNICAL_BENCHMARK | W10 Frontend |
| REF-F04a | ISO/IEC | 27001 ISMS | 2022 | 2022 | FINAL | NO | https://www.iso.org/ | TECHNICAL_BENCHMARK | W7 Security |
| REF-F04b | ISO | 22301 BCMS | 2019 | 2019 | FINAL | NO | https://www.iso.org/ | INSTITUTIONAL_BENCHMARK | W15/W16 |
| REF-F04c | ISO/IEC | 42001 AI Management | 2023 | 2023 | FINAL | NO | https://www.iso.org/ | TECHNICAL_BENCHMARK | W6 AI/ML |
| REF-F05 | OWASP | ASVS | 5.0.0 | 2024 | FINAL | NO | https://owasp.org/www-project-application-security-verification-standard/ | TECHNICAL_BENCHMARK | W7 Security |
| REF-F05a | OWASP | API Security Top 10 | 2023 | 2023 | FINAL | NO | https://owasp.org/API-Security/ | TECHNICAL_BENCHMARK | W9 API |
| REF-F06 | CIS | Controls | v8.1 | 2024 | FINAL | NO | https://www.cisecurity.org/controls | TECHNICAL_BENCHMARK | W7/W13 |
| REF-F07 | AICPA | Trust Services Criteria | Current | — | FINAL | NO | — | INSTITUTIONAL_BENCHMARK | W13 (readiness only) |
| REF-F08 | EU | DORA 2022/2554 | 2022 | 2022 | FINAL | NO | https://eur-lex.europa.eu/eli/reg/2022/2554/oj | APPLICABILITY_NOT_VERIFIED | W15 |
| REF-F09 | FSB | Third-Party Risk Toolkit | Dec 2023 | 2023-12 | FINAL | NO | https://www.fsb.org/2023/12/final-report-on-enhancing-third-party-risk-management-and-oversight-a-toolkit-for-financial-institutions-and-financial-authorities/ | INSTITUTIONAL_BENCHMARK | W18 Vendor |
| REF-F10a | CFA | GIPS Standards | Current | — | FINAL | NO | https://rpc.cfainstitute.org/gips-standards | CONDITIONAL | W18 (gate) |
| REF-F10b | PCI SSC | PCI DSS | Current | — | FINAL | NO | https://www.pcisecuritystandards.org/document_library/ | CONDITIONAL | W18 (gate) |

**Notes:**
- SR 26-2 (Apr 2026) used as model-risk benchmark only — not supervised-bank compliance claim.
- SSDF 1.1 used as normative; any draft SSDF 1.2 recorded separately if encountered.
- GIPS/PCI applicability determined by execution gates (see W18-GIPS-001, W18-PCI-001).
