# SPEC_02 Runtime Truth Table

| Req ID | Section | Status | Evidence |
|--------|---------|--------|----------|
| REQ-S02-001 | §2, §0 | **YES** | PRIVATE_BY_DEFAULT + no eligible/denied overlap |
| REQ-S02-002 | §3 | **YES** | §3 eligible vs §4 denied sets consistent |
| REQ-S02-003 | §4 | **YES** | allow/deny HTTP matrix matches spec §4/§22 |
| REQ-S02-004 | §5 | **YES** | guest-trust #46 reachable anonymously |
| REQ-S02-005 | §7 | **YES** | allow/deny HTTP matrix matches spec §4/§22 |
| REQ-S02-006 | §8 | **YES** | public proof index |
| REQ-S02-007 | §10 | **YES** | evidence class module bound to #6 |
| REQ-S02-008 | §11 | **YES** | freshness module bound to #41 |
| REQ-S02-009 | §20 | **YES** | persistence gated; public browse allowed |
| REQ-S02-010 | §22 | **YES** | 7 routes inventoried with server enforcement |
| REQ-S02-011 | §22 | **YES** | allow/deny HTTP matrix matches spec §4/§22 |
| REQ-S02-012 | §22, §23 | **YES** | {"public": true, "private_denied": true, "no_broad_prefix": true} |
| REQ-S02-013 | §4, §22 | **YES** | allow/deny HTTP matrix matches spec §4/§22 |
| REQ-S02-014 | §25 | **YES** | local licensing gate contract present; production NEEDS_EXTERNAL |
| REQ-S02-015 | §26 | **YES** | PII rejected on public boundary probe |
| REQ-S02-016 | §23 | **YES** | rate_limits flag true in governance status |
| REQ-S02-017 | §5, §6 | **YES** | landing anonymous fetch uses guest-trust |
| REQ-S02-018 | §0 | **YES** | legacy surfaces excluded; ANONYMOUS state explicit |
| REQ-S02-019 | §3 | **YES** | capability library #52 public discovery |
| REQ-S02-020 | AV-01 | **YES** | legacy surfaces excluded; ANONYMOUS state explicit |
| REQ-S02-021 | AV-03 | **YES** | {"public": true, "private_denied": true, "no_broad_prefix": true} |
| REQ-S02-022 | AV-09 | **YES** | allow/deny HTTP matrix matches spec §4/§22 |
| REQ-S02-023 | AV-10 | **YES** | persistence gated; public browse allowed |
| REQ-S02-024 | AV-24 | **YES** | PII rejected on public boundary probe |
| REQ-S02-025 | §35 | **YES** | IV performed in independent_verification() |
| REQ-S02-026 | §0 | **YES** | PASS_LIVE=false by policy; LIVE_VALIDATION_PENDING=true |
