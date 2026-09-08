# BLACKDARK Subscription Legal Basis

**Status:** Governing legal compliance layer (BILL-047)  
**Scope:** Product controls and jurisdictional applicability — not universal legal advice.

## Purpose

This document separates jurisdictional applicability for subscription, billing, and entitlement product controls. No single jurisdiction's rules are presented as universal law.

## United States

Applicable frameworks referenced for product design (not legal certification):

- **ROSCA** (Restore Online Shoppers' Confidence Act): renewal disclosure and cancellation clarity
- **FTC Act**: unfair/deceptive practices — no dark patterns in checkout/cancel flows
- **State Automatic Renewal Laws (ARL)**: vary by state; product must support jurisdiction-specific disclosure where enabled
- **Card network rules**: chargeback/dispute handling architecture

**Product controls implemented locally:** renewal disclosure versioning, consent evidence, cancellation UX (cancel now / cancel at period end), pre-purchase price/tax/total display.

## European Economic Area (EEA)

- **PSD2 / SCA**: Strong Customer Authentication for applicable payments — no entitlement on unverified SCA failure
- **GDPR**: data minimization, lawful basis documentation structure, retention separation
- **Consumer protection**: jurisdiction-specific; not assumed uniform across EEA member states

**Product controls implemented locally:** SCA flow architecture, consent records, tax profile fields, data retention policy structure.

## Other Markets

Local legal review required before market activation. Architecture supports:

- Tax profile by merchant/customer jurisdiction
- B2B vs B2C distinction fields
- Consent and renewal disclosure versioning
- Contract reference for institutional accounts

## Explicit Non-Claims

BLACKDARK does **not** claim without independent external evidence:

- PCI Level 1 certification
- SOC 2 / ISO 27001 certification
- Tax registration or merchant eligibility in any jurisdiction
- Legal registration as payment institution
- Universal subscription law compliance

## Data Retention Separation (BILL-050)

| Category | Policy |
|----------|--------|
| Product personal data | Deletion subject to user request and lawful basis |
| Payment method tokens | Removed via Stripe/PSP — not stored in BLACKDARK |
| Subscription cancellation | Entitlement revoked per policy; billing projection retained for audit |
| Invoice/tax/accounting records | Legally required retention — not subject to immediate full deletion |

## Consent and Renewal (BILL-048, BILL-051)

Initial purchase requires documented consent: terms version, renewal disclosure version, tier, billing frequency, consent source, timestamp.

Recurring charges within an established subscription do not require re-consent per charge, but renewal terms must remain accessible and cancellation must remain clear.

## Institutional / B2B (BILL-043, BILL-045)

Enterprise payment terms (NET_15, NET_30, invoice billing, PO reference) require owner business decisions for activation. Local architecture supports contract reference, custom entitlement profile, and manual settlement evidence without fabricating legal eligibility.

## Live Activation

Legal and tax registration gates remain **EXTERNAL_GATED** until owner-verified evidence exists. See BILL-002 and BILL-061.
