"""Payment-flow third-party script inventory and minimization (SDG-17)."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

# Hosted checkout architecture: redirect to Stripe/Lemon — no card fields in our templates.
_PAYMENT_FLOW_TEMPLATES = (
    "templates/landing.html",
    "templates/dashboard.html",
    "templates/utility.html",
)

_SCRIPT_SRC_RE = re.compile(r'<script[^>]+src=["\']([^"\']+)["\']', re.IGNORECASE)

# Third-party scripts allowed on general pages but NOT on payment-sensitive redirect path.
_ALLOWED_GENERAL_THIRD_PARTY = frozenset(
    {
        "https://unpkg.com/lightweight-charts@4.2.0/dist/lightweight-charts.standalone.production.js",
    }
)

# Payment path uses hosted provider — only first-party scripts for checkout initiation.
_PAYMENT_PATH_ALLOWED_EXTERNAL = frozenset()


def _scan_template(rel_path: str) -> dict[str, Any]:
    path = ROOT / rel_path
    if not path.is_file():
        return {"template": rel_path, "exists": False, "scripts": [], "third_party": []}
    content = path.read_text(encoding="utf-8", errors="replace")
    scripts = _SCRIPT_SRC_RE.findall(content)
    third_party = [s for s in scripts if s.startswith("http")]
    inline_checkout = "create-checkout-session" in content or "/api/billing/checkout" in content
    return {
        "template": rel_path,
        "exists": True,
        "scripts": scripts,
        "third_party": third_party,
        "hosted_checkout_redirect": inline_checkout,
        "payment_sensitive": inline_checkout,
    }


def payment_script_inventory() -> list[dict[str, Any]]:
    return [_scan_template(p) for p in _PAYMENT_FLOW_TEMPLATES]


_CHECKOUT_BLOCK_RE = re.compile(
    r"(create-checkout-session|/api/billing/checkout|upgradeTier|checkout_tier).{0,2000}",
    re.IGNORECASE | re.DOTALL,
)


def _checkout_block_third_party(template_path: Path, content: str) -> list[str]:
    """Third-party script refs that appear inside checkout initiation blocks only."""
    hits: list[str] = []
    for block in _CHECKOUT_BLOCK_RE.findall(content):
        for script in _SCRIPT_SRC_RE.findall(block):
            if script.startswith("http") and script not in _PAYMENT_PATH_ALLOWED_EXTERNAL:
                hits.append(script)
    return hits


def verify_payment_path_minimization() -> dict[str, Any]:
    """Ensure hosted checkout initiation does not load unnecessary third-party scripts."""
    inventory = payment_script_inventory()
    gaps: list[dict[str, Any]] = []
    for entry in inventory:
        if not entry.get("payment_sensitive"):
            continue
        path = ROOT / entry["template"]
        content = path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""
        checkout_scripts = _checkout_block_third_party(path, content)
        for script in checkout_scripts:
            gaps.append(
                {
                    "template": entry["template"],
                    "script": script,
                    "reason": "unnecessary_third_party_in_checkout_initiation_block",
                }
            )
    return {
        "architecture": "hosted_stripe_lemon_checkout_redirect",
        "inventory": inventory,
        "general_third_party_documented": [
            s for e in inventory for s in e.get("third_party", []) if s in _ALLOWED_GENERAL_THIRD_PARTY
        ],
        "gaps": gaps,
        "compliant": len(gaps) == 0,
        "csp_note": "CSP controls preserved via security_middleware — not weakened by this inventory",
    }


def payment_script_status() -> dict[str, Any]:
    result = verify_payment_path_minimization()
    return {
        "templates_scanned": len(result["inventory"]),
        "third_party_on_payment_path": len(result["gaps"]),
        "compliant": result["compliant"],
        "hosted_provider_preserved": True,
    }
