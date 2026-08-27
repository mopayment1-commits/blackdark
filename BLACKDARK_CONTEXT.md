# BLACKDARK — Institutional Master Baseline
# حقن السياق المؤسسي — Context Injection File

> **الاستخدام:** في Cursor، اكتب `@` واختار اسم الملف ده (أو اسحبه للشات) قبل أي سؤال.
> **الهدف:** يخلي AI يشتغل بناءً على 42 تحكم مؤسسي + خارطة عيوب + خارطة تنفيذ، مش بناءً على تخمين.

---

## 1. Executive Verdict — الحكم التنفيذي

- **المشروع:** BLACKDARK — AI Crypto Intelligence Platform
- **الوثيقة:** Institutional Engineering Baseline
- **الحالة:** PASS WITH RISK — العيوب الحرجة الستة (D-01, D-02, D-06, D-09, D-13, D-15) **مغلقة في الكود والاختبارات**؛ الأدلة الخارجية (HSM، pentest مستقل، SOC2) = EXTERNAL EVIDENCE
- **العيوب الحرجة (Critical):** 6 مغلقة | **عالية (High):** 8 مفتوحة | **متوسطة (Medium):** 1
- **عدد الضوابط:** 42 control
- **المصادر المحتفظ بها:** 40 source

---

## 2. Normative Standards — المعايير المطبقة

| ID | المعيار | الدور |
|----|---------|-------|
| STD-REQ | ISO/IEC/IEEE 29148:2018 | متطلبات الجودة والتتبع |
| STD-ARCH | ISO/IEC/IEEE 42010:2022 | وصف الهندسة المعمارية |
| STD-Q | ISO/IEC 25010:2023 | نموذج جودة المنتج |
| STD-QU | ISO/IEC 25019:2023 | الجودة في الاستخدام |
| STD-DQ | ISO/IEC 25012:2008 | جودة البيانات |
| STD-ISMS | ISO/IEC 27001:2022 | أمن المعلومات |
| STD-PRIV | ISO/IEC 27701:2025 | خصوصية البيانات |
| STD-CSF | NIST CSF 2.0 | حوكمة الأمن السيبراني |
| STD-SSDF | NIST SP 800-218 SSDF 1.1 | تطوير البرمجيات الآمن |
| STD-AI | NIST AI RMF 1.0 | حوكمة الذكاء الاصطناعي |
| STD-ASVS | OWASP ASVS 5.0.0 | التحقق من أمن التطبيقات |
| STD-HCD | ISO 9241-210:2019 | التصميم المتمحور حول الإنسان |
| STD-WCAG | W3C WCAG 2.2 | إمكانية الوصول للويب |

---

## 3. The 42 Institutional Controls — الضوابط الـ 42

### GOVERNANCE — الحوكمة

**GOV-001** — كل متطلب لازم يكون واضح، قابل للقياس، مع صاحب، مع acceptance criteria، ومرتبط بـ trace link.
- **الأدلة المطلوبة:** Requirements register، owner، acceptance criteria، trace link، review record.
- **المعايير:** ISO/IEC/IEEE 29148:2018، ISO/IEC 25010:2023

**GOV-002** — ممنوع تكرار المهام. كل مسؤولية ليها صاحب واحد بس.
- **الأدلة:** Canonical registry، duplicate scan، owner mapping.

**GOV-003** — ممنوع الادعاء بـ "جاهزية" أو "AI" من غير دليل. Demo/Mock/Fake مش دليل.
- **الأدلة:** Evidence pack، claim-to-evidence matrix، independent review.

---

### ARCHITECTURE — الهندسة المعمارية

**ARC-001** — لازم يكون فيه وصف معماري رسمي: boundaries، data flows، components، interfaces.
- **الأدلة:** Architecture description، DFD، component views، interface inventory، review sign-off.

**ARC-002** — Single Source of Truth. كل قرار ليه مصدر واحد مع lineage قابل للتدقيق.
- **الأدلة:** Canonical authority map، lineage trace، sample decision replay.

---

### QUALITY — الجودة

**QUA-001** — نموذج جودة رسمي مع acceptance criteria قابلة للقياس قبل إعلان الجاهزية.
- **الأدلة:** Quality model، measurable objectives، acceptance criteria، evaluation report.

---

### SECURITY — الأمن (9 controls)

**SEC-001** — Secrets: ممنوع API keys في الكود أو الـ logs أو الـ frontend. لازم secret store مع rotation.
- **الأدلة:** Secret inventory، scan results، secret-store config، rotation evidence.

**SEC-002** — Encryption at rest: البيانات الحساسة لازم تتشفر بـ AES-256-GCM (أو ما يعادله) مع key management.

**SEC-003** — Identity: MFA إجباري لـ admin accounts. SSO لو مؤسسي.

**SEC-004** — Authorization: RBAC/ABAC مع tenant isolation. التحقق من الصلاحيات لازم يكون server-side، مش UI hiding بس.

**SEC-005** — Vulnerability management: SCA/SAST على dependencies. Vulnerability register.

**SEC-006** — Pentest: ممنوع إعلان "جاهز أمنياً" من غير اختبار اختراق مستقل.

**SEC-007** — Audit logging: سجلات تشغيلية وأمنية tamper-evident.

**SEC-008** — Infrastructure protection: WAF + rate limiting + DDoS protection على مستوى الـ edge. Rate limiting داخل التطبيق وحده مش كافي.

**SEC-009** — Incident response: خطة استجابة للحوادث مكتوبة، مع تدريبات، مع escalation procedures.

---

### DATA — البيانات (4 controls)

**DAT-001** — Data provenance: كل بيانات مستخدمة في قرار لازم تكون قابلة للتتبع من المصدر للمخرج النهائي.

**DAT-002** — Data quality model: قياس صريح لـ freshness، accuracy، completeness، latency، anomaly rate — مع thresholds.

**DAT-003** — Stale data rejection: ممنوع استخدام بيانات قديمة أو غير موثوقة في قرارات التنفيذ. لازم downgrade أو rejection صريح.

**DAT-004** — Cross-source reconciliation: لو مصادر مختلفة بتختلف، لازم يكون فيه quarantine path مش اختيار عشوائي للقيمة.

---

### RELIABILITY — الاعتمادية (5 controls)

**REL-001** — Performance evidence: load/stress tests قبل إعلان الجاهزية. Latency/throughput/resource results.

**REL-002** — SPOF mitigation: تحديد ومعالجة نقاط الفشل الواحدة. Failover tests.

**REL-003** — Backup & DR: policy مكتوبة + restore drills + RTO/RPO.

**REL-004** — Circuit breaker: Stop rather than proceed silently. لما الشروط الآمنة تتviolated، النظام يوقف.

**REL-005** — Observability: metrics + logs + traces + alerts linked to root cause.

---

### QA — ضمان الجودة (4 controls)

**QA-001** — Automated quality gates: CI/CD blocks merge/release لو الجودة فشلت.

**QA-002** — Critical path testing: unit + integration tests للمسارات الحرجة، بما فيها مسارات الفشل (failure paths).

**QA-003** — Risk-based coverage: coverage thresholds مبررة (مش أرقام عشوائية عالية).

**QA-004** — No mock-only evidence: Mocks/Demos مش مقبولة كدليل وحيد على جاهزية الإنتاج.

---

### AI GOVERNANCE — حوكمة الذكاء الاصطناعي (5 controls)

**AI-001** — Confidence measurement: AI outputs لازم يظهروا confidence score معاها (calibrated)، مش certainty ثنائية.

**AI-002** — Model registry: كل model في الإنتاج مسجل بـ version + source + trustworthiness metadata.

**AI-003** — Drift monitoring: مراقبة model drift و data drift مع thresholds وإجراءات استجابة.

**AI-004** — Look-ahead prevention: ممنوع استخدام معلومات من المستقبل في training/testing. Temporal separation إجباري.

**AI-005** — Explainability: AI outputs قابلة للتفسير (model version، data factors، reasoning path).

---

### FINANCIAL — المالية (4 controls)

**FIN-001** — Net economic truth: أي ربح/فرصة لازم تحسب بعد كل التكاليف: fees، slippage، funding. Gross price difference مش كافي.

**FIN-002** — Numerical precision: استخدام BigDecimal / uint256 (حسب السياق) مع rounding policy واضحة. ممنوع الاعتماد على defaults.

**FIN-003** — Liquidity truth: ممنوع وصف فرصة بـ "executable" من غير مراجعة liquidity، slippage، order age.

**FIN-004** — Fail-safe under unsafe slippage: المسارات اللي ممكن تؤثر على التنفيذ لازم تتوقف لما slippage يتجاوز threshold.

---

### PRIVACY — الخصوصية (2 controls)

**PRV-001** — Privacy policy aligned: Privacy policy و Terms لازم تعكس المعالجة الفعلية. ممنوع boilerplate من غير review.

**PRV-002** — Privacy governance: لو فيه personal data processing، لازم PIMS مع roles و lifecycle controls و rights workflow.

---

### UX — تجربة المستخدم (3 controls)

**UX-001** — Human-centred design: قرارات المنتج مبنية على فهم المستخدمين والمهام، مش افتراضات.

**UX-002** — Accessibility: WCAG 2.2 AA كحد أدنى للواجهات العامة. Tested + documented.

**UX-003** — Quality-in-use: قياس task success، efficiency، error prevention، satisfaction قبل الجاهزية المؤسسية.

---

## 4. Critical Defects — العيوب الحرجة (D-01 → D-15)

| ID | الخطورة | المشكلة | الحل المطلوب |
|----|---------|---------|--------------|
| **D-01** | CRITICAL | Null data بيتعامل على إنه صفر. API outage بيسبب cascade | Explicit states: UNKNOWN≠0, MISSING≠0, STALE≠LIVE. Fault injection testing |
| **D-02** | CRITICAL | API keys مكشوفة في .env. مفيش HSM أو rotation | Zero-Trust Vault. AES-256-GCM. ممنوع plaintext secrets في DB/logs/frontend/CI |
| **D-03** | HIGH | Server downtime spikes. Data ingestion bottlenecks. Python wrappers في hot paths | Profile → Benchmark → Optimize → Rust/Go لو مبرر. Circuit breakers + health probes |
| **D-04** | HIGH | No throughput measured. No backpressure. Event loss ممكن تحت load | Measure events/sec, queue lag. Async I/O, batching, partitioning, buffering. Load + soak tests |
| **D-05** | HIGH | Stubs/mocks/wrappers بتتظاهر بأنها proprietary engines | Proprietary Core Audit: Input → Proprietary Processing → Output → Tests → Evidence |
| **D-06** | CRITICAL | API endpoint مش مؤسسي | TLS/HTTPS, Auth/AuthZ, Tenant isolation, Rate limiting, Quotas, Idempotency, OpenAPI spec, Audit logging |
| **D-07** | HIGH | ادعاء 50ms latency من غير دليل | Latency budget decomposition: Source→Ingestion→Normalization→Engine→Risk→API. Measure max |
| **D-08** | HIGH | ادعاء 99.9% uptime من غير دليل | Availability monitoring, SLI/SLO, Error budget, DR, Dependency monitoring. Prove before claim |
| **D-09** | CRITICAL | Exchange Internal Flow Filter لازم يفرّق بين internal rebalancing و economic flow | Build with: Exchange labels, Hot/cold wallets, Deposit/withdrawal clusters, Graph history. Output: INTERNAL_CONFIRMED, INTERNAL_LIKELY, ECONOMIC_FLOW, UNKNOWN |
| **D-10** | HIGH | Micro Order Splitter لازم يعالج أوامر كبيرة بقيود السوق الحقيقية | Inputs: L2 depth, spread, fees, slippage, volatility, liquidity. Outputs: Slicing, pacing, venue allocation, price impact |
| **D-11** | HIGH | Funding Rate Arbitrage Engine لازم يحسب كل التكاليف والمخاطر | Inputs: spot/perp bid-ask, funding, basis, borrow cost, slippage, margin, liquidation distance. Outputs: Gross Carry, Total Costs, Net Carry, Risk-Adjusted Carry, Break-even |
| **D-12** | MEDIUM | 568 parameter بتسبب data-saturate friction | UI modes: Beginner/Professional/Institutional. Primary surface: System Threat Index, Opportunity Matrix, Decision Surface |
| **D-13** | CRITICAL | Security verification غير مكتملة قبل الإنتاج | NIST SSDF, Zero Trust, OWASP ASVS, API Security testing, Threat modeling, SAST, DAST, Auth abuse tests, Tenant isolation tests |
| **D-14** | HIGH | System مش متأكد من سلوكه تحت الفشل | Failure injection: API outage, DB unavailable, Cache unavailable, Worker death, Corrupted message, Network partition, Slow dependency. Requirement: Safe failure, not silent failure |
| **D-15** | CRITICAL | "Everything is complete" claims not accepted | For every requirement: Architecture diagram, Source code refs, Commit, Tests, Test result, Benchmark, Security result, Failure result, Runbook, Documentation, Current status, Known limitations |

---

## 5. Execution Roadmap — خارطة التنفيذ (T01–T18)

### Phase 1: Foundation — T01 + T02 + T03
- **المجال:** Architecture, Security, Data Platform & Connectors
- **القاعدة:** ابدأ بالاعتمادات المشتركة: Architecture → Security → Data

### Phase 2: Market Intelligence — T04 + T08 + T09 + T10
- **المجال:** Market Data, Risk, On-chain, DeFi
- **القاعدة:** ابنِ طبقات السوق والمخاطر والـ on-chain بعد التحقق من البيانات

### Phase 3: Quant & AI — T05 + T11 + T12 + T07
- **المجال:** Derivatives, Quant Analytics, AI, Portfolio
- **القاعدة:** Derivatives, quant, AI, portfolio فوق البيانات المتحققة

### Phase 4: UX & Workflows — T13 + T14
- **المجال:** Alerts, Workflows, UX, Dashboards
- **القاعدة:** الواجهات بعد ما المنطق الأساسي يتاختبر

### Phase 5: Institutional & Operations — T15 + T16 + T17 + T18
- **المجال:** B2B, Billing, Reporting, Macro
- **القاعدة:** الطبقات المؤسسية والفوترة بعد استقرار المنصة الأساسية

**مبدأ التنفيذ:**
Market Regime Engine → Entity-Adjusted Metrics → Cost Basis/Profitability Intelligence → Futures/Options/Order Book → Point-in-Time Data → Data Provenance → Cross-Domain Decision Intelligence

---

## 6. Certification Rules — قواعد الشهادة

| الحالة | المعنى |
|--------|--------|
| **PASS** | متطلب منفذ + دليل حديث + عيوب حرجة مغلقة |
| **PASS WITH RISK** | منفذ لكن مع risk مقبول، صاحب معروف، خطة mitigation |
| **NOT VERIFIED** | مفيش دليل كافي. ممنوع اعتباره PASS |
| **FAIL** | الاختبار/التفتيش أثبت عدم الالتزام |
| **EXTERNAL EVIDENCE** | يحتاج دليل مستقل خارج فريق المشروع (legal, audit, test) |

### Final Zero-Defect Gate — باب الإغلاق النهائي

- كل Requirement = VERIFIED_COMPLETE
- صفر critical vulnerabilities
- صفر high vulnerabilities (غير mitigated)
- صفر مسارات corruption للبيانات
- صفر secrets مكشوفة
- صفر سلوك unknown→zero
- صفر failover غير مختبر
- صفر ادعاء latency من غير دليل
- صفر ادعاء SLA من غير دليل
- صفر stubs/mocks في الإنتاج
- صفر modules proprietary غير متحققة
- صفر P0/P1 defects مفتوحة

**لو فيه critical path واحد مفتوح: الحكم = NOT READY.**

---

## 7. Retained Source Evidence Register — سجل الأدلة (40 مصدر)

| المصدر | الأدلة |
|--------|--------|
| SRC-00003 | No Duplication principle |
| SRC-00009 | Quality before quantity |
| SRC-00010 | No duplicate capabilities |
| SRC-00011 | Single ownership |
| SRC-00020 | SSOT + Confidence + Explainability |
| SRC-00024 | Audit logging |
| SRC-00460 | Net profit after all costs |
| SRC-00782 | BigDecimal / uint256 precision |
| SRC-00784 | CI/CD Quality Gates |
| SRC-00785 | Test coverage ≥93%, mutation, security scan |
| SRC-00795 | Net profit formula |
| SRC-00880 | High slippage prevention |
| SRC-00900 | Vulnerable dependency scanning |
| SRC-00904 | Prevent look-ahead bias |
| SRC-00929 | Institutional Quality Gate |
| SRC-01107 | Secrets exposure risk |
| SRC-01116 | Missing architecture docs |
| SRC-01124 | Test infrastructure |
| SRC-01179 | Add ARCHITECTURE.md with DFD |
| SRC-01189 | GDPR privacy policy update |
| SRC-01269 | No load tests for 1000 concurrent users |
| SRC-01763 | Missing at-rest encryption |
| SRC-01890 | Single point of failure |
| SRC-01892 | No backup/DR plan |
| SRC-01895 | No DDoS protection |
| SRC-01899 | Security verification incomplete |
| SRC-01915 | Incomplete ToS/Privacy Policy |
| SRC-01929 | Full legal documentation required |
| SRC-01972 | Institutional SSO/MFA/multi-tenant |
| SRC-01973 | RBAC, Incident Response, Observability, Secrets manager |
| SRC-02017 | ARCHITECTURE.md with Data Flow Diagram |
| SRC-02082 | Data provenance tracking |
| SRC-02107 | Circuit breaker requirement |
| SRC-02125 | Model confidence measurement |
| SRC-02126 | Model registry |
| SRC-02128 | Drift monitoring |
| SRC-02423 | Explainable AI / TruLens |
| SRC-03183 | No fake demo / mock intelligence |
| SRC-03369 | Data quality dimensions |
| SRC-03376 | Source reconciliation and quarantine rules |

---

## 8. Official Standards References — المراجع الرسمية

- ISO/IEC/IEEE 29148:2018 — Requirements Engineering
- ISO/IEC/IEEE 42010:2022 — Architecture Description
- ISO/IEC 25010:2023 — Product Quality Model
- ISO/IEC 25019:2023 — Quality-in-Use
- ISO/IEC 25012:2008 — Data Quality
- ISO/IEC 27001:2022 — ISMS
- ISO/IEC 27701:2025 — Privacy Information Management
- NIST Cybersecurity Framework (CSF) 2.0
- NIST SP 800-218 SSDF 1.1 — Secure Software Development
- NIST AI RMF 1.0 — AI Risk Management
- OWASP ASVS 5.0.0 — Application Security Verification
- ISO 9241-210:2019 — Human-Centred Design
- W3C WCAG 2.2 — Web Accessibility

---

*Document Version: FINAL — Context Injection Edition*
*Review Date: 21 August 2026*
*Classification: Institutional Engineering Baseline*
