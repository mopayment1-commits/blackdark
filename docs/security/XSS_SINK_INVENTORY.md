# XSS / DOM Sink Inventory (Launch-57)

| Surface | Mechanism | Status |
|---------|-----------|--------|
| `templates/dashboard.html` | `esc()` / `escapeHtml()` on user/oracle fields | Monitored — regression in CI |
| `templates/platform.html` | esc + safeUrl | Monitored |
| `static/js/dom_escape.js` | Shared helpers | PASS |
| `templates/b2b.html` | WebSocket URL — demo key in query | LOW — demo path only |

Residual risk: new template literals must pass `test_optional_dangerous_unescaped_innerhtml_pattern_scan`.
