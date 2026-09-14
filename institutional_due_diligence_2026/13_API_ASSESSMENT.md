# 12 — API Assessment (Wave 9)

**Generated:** 2026-09-10T23:50:00Z

## Endpoint Universe: 657 route decorators (657 API handlers)

### api/routers/ auth coverage
| Metric | Count |
|---|---:|
| Total handlers | 304 |
| Strict auth Depends | 83 |
| Optional auth | 25 |
| No auth decorator | 196 |

Largest unauthenticated surfaces: heroes.py (70/74), compounding.py (28/28), oracle.py (20/28).

**Wave 9 CLOSED:** Full endpoint inventory; per-endpoint authorization audit NOT VERIFIED.
