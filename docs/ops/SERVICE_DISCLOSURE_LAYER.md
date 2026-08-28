# Service Disclosure Layer (#57)

Cross-cutting legal disclosure — NOT standalone. Mandatory on every touchpoint.

## Fixed text (lawyer-reviewed)

- **EN:** BLACKDARK is an analytical tool providing insights only — not licensed investment advice and no financial guarantees.
- **AR:** BLACKDARK هي أداة تحليلية تقدم insights فقط — لا توصيات استثمارية مرخّصة ولا ضمانات مالية.

## Integration points

- Footer: `site_services.footer_manifest()` → `service_disclosure_57`
- API body: `attach_service_disclosure_57(payload)`
- Reports/certificates: `decision_certificate.compliance_footer_block()`

## API

```
GET  /api/platform/legal/disclosure/status
POST /api/platform/legal/disclosure/attach
GET  /api/platform/legal/commercial/status
```

Sprint 1 — must be live before any Stripe financial interaction.
