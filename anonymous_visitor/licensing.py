"""Public data licensing gate — AV §21 LICENSE_PUBLIC_DISPLAY_PASS."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any


@dataclass(frozen=True, slots=True)
class PublicSourceLicense:
    source_id: str
    provider_name: str
    license_public_display_allowed: bool
    commercial_use_allowed: bool
    attribution_required: bool
    attribution_text: str
    attribution_url: str
    derived_data_allowed: bool
    redistribution_allowed: bool
    api_reexposure_allowed: bool
    cache_allowed: bool
    retention_allowed: bool
    screenshot_social_card_allowed: bool
    license_expiry: str | None
    review_date: str
    evidence_source: str
    status: str
    upstream_raw_providers: tuple[str, ...] = ()
    upstream_raw_providers_proven: bool = False
    public_display_mode: str = "VERIFIED_SOURCE_ONLY"

    @property
    def production_public_display_pass(self) -> bool:
        return (
            self.license_public_display_allowed
            and self.upstream_raw_providers_proven
            and self.status == "VERIFIED_LOCALLY"
        )

    @property
    def license_public_display_pass(self) -> bool:
        if self.public_display_mode == "BLOCK":
            return False
        if self.public_display_mode == "VERIFIED_SOURCE_ONLY":
            return self.license_public_display_allowed and self.status == "VERIFIED_LOCALLY"
        return self.production_public_display_pass


def _today() -> str:
    return datetime.now(UTC).date().isoformat()


PUBLIC_SOURCE_LICENSES: dict[str, PublicSourceLicense] = {
    "oracle_unified": PublicSourceLicense(
        source_id="oracle_unified",
        provider_name="BLACKDARK Oracle (derived)",
        license_public_display_allowed=True,
        commercial_use_allowed=False,
        attribution_required=True,
        attribution_text="Decision evidence from BLACKDARK Oracle — methodology at /methodology",
        attribution_url="/methodology",
        derived_data_allowed=True,
        redistribution_allowed=False,
        api_reexposure_allowed=False,
        cache_allowed=True,
        retention_allowed=True,
        screenshot_social_card_allowed=True,
        license_expiry=None,
        review_date=_today(),
        evidence_source="internal_methodology+oracle_audit_chain",
        status="VERIFIED_LOCALLY",
        upstream_raw_providers=("binance", "internal_oracle_pipeline"),
        upstream_raw_providers_proven=False,
        public_display_mode="VERIFIED_SOURCE_ONLY",
    ),
    "oracle_audit_chain": PublicSourceLicense(
        source_id="oracle_audit_chain",
        provider_name="BLACKDARK Public Accuracy Ledger",
        license_public_display_allowed=True,
        commercial_use_allowed=False,
        attribution_required=True,
        attribution_text="Historical outcomes from BLACKDARK Public Accuracy Ledger",
        attribution_url="/oracle-accuracy",
        derived_data_allowed=True,
        redistribution_allowed=False,
        api_reexposure_allowed=False,
        cache_allowed=True,
        retention_allowed=True,
        screenshot_social_card_allowed=True,
        license_expiry=None,
        review_date=_today(),
        evidence_source="oracle_audit_chain.jsonl",
        status="VERIFIED_LOCALLY",
        upstream_raw_providers=("internal_ledger",),
        upstream_raw_providers_proven=False,
        public_display_mode="VERIFIED_SOURCE_ONLY",
    ),
    "data_governance_registry": PublicSourceLicense(
        source_id="data_governance_registry",
        provider_name="BLACKDARK Data Governance (summary)",
        license_public_display_allowed=True,
        commercial_use_allowed=False,
        attribution_required=True,
        attribution_text="Source coverage summary — full registry requires account",
        attribution_url="/methodology",
        derived_data_allowed=True,
        redistribution_allowed=False,
        api_reexposure_allowed=False,
        cache_allowed=True,
        retention_allowed=True,
        screenshot_social_card_allowed=True,
        license_expiry=None,
        review_date=_today(),
        evidence_source="data_governance/registry.py",
        status="VERIFIED_LOCALLY",
        upstream_raw_providers=("multiple_upstream_feeds",),
        upstream_raw_providers_proven=False,
        public_display_mode="VERIFIED_SOURCE_ONLY",
    ),
    "market_context": PublicSourceLicense(
        source_id="market_context",
        provider_name="Aggregated market context (derived)",
        license_public_display_allowed=True,
        commercial_use_allowed=False,
        attribution_required=True,
        attribution_text="Market data shown as derived summaries — see /status for freshness",
        attribution_url="/status",
        derived_data_allowed=True,
        redistribution_allowed=False,
        api_reexposure_allowed=False,
        cache_allowed=True,
        retention_allowed=True,
        screenshot_social_card_allowed=True,
        license_expiry=None,
        review_date=_today(),
        evidence_source="market_context module",
        status="VERIFIED_LOCALLY",
        upstream_raw_providers=("binance",),
        upstream_raw_providers_proven=False,
        public_display_mode="VERIFIED_SOURCE_ONLY",
    ),
}


def get_source_license(source_id: str | None) -> PublicSourceLicense | None:
    if not source_id:
        return None
    return PUBLIC_SOURCE_LICENSES.get(source_id)


def assert_license_public_display(source_id: str | None) -> dict[str, Any]:
    lic = get_source_license(source_id)
    if lic is None:
        return {
            "ok": False,
            "source_id": source_id,
            "license_public_display_pass": False,
            "reason": "unknown_source",
        }
    if lic.public_display_mode == "BLOCK":
        return {
            "ok": False,
            "source_id": lic.source_id,
            "license_public_display_pass": False,
            "reason": "blocked_pending_license",
        }
    passed = lic.license_public_display_pass
    return {
        "ok": passed,
        "source_id": lic.source_id,
        "license_public_display_pass": passed,
        "production_public_display_pass": lic.production_public_display_pass,
        "public_display_mode": lic.public_display_mode,
        "upstream_license_pending": not lic.upstream_raw_providers_proven,
        "upstream_raw_providers": list(lic.upstream_raw_providers),
        "attribution_required": lic.attribution_required,
        "attribution_text": lic.attribution_text if lic.attribution_required else None,
        "attribution_url": lic.attribution_url if lic.attribution_required else None,
        "status": lic.status,
    }


def licensing_register_export() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for lic in PUBLIC_SOURCE_LICENSES.values():
        out.append(
            {
                "source_id": lic.source_id,
                "provider_name": lic.provider_name,
                "LICENSE_PUBLIC_DISPLAY_ALLOWED": lic.license_public_display_allowed,
                "LICENSE_PUBLIC_DISPLAY_PASS": lic.license_public_display_pass,
                "PRODUCTION_PUBLIC_DISPLAY_PASS": lic.production_public_display_pass,
                "PUBLIC_DISPLAY_MODE": lic.public_display_mode,
                "UPSTREAM_RAW_PROVIDERS": list(lic.upstream_raw_providers),
                "UPSTREAM_RAW_PROVIDERS_PROVEN": lic.upstream_raw_providers_proven,
                "COMMERCIAL_USE_ALLOWED": lic.commercial_use_allowed,
                "ATTRIBUTION_REQUIRED": lic.attribution_required,
                "ATTRIBUTION_TEXT": lic.attribution_text,
                "ATTRIBUTION_URL": lic.attribution_url,
                "DERIVED_DATA_ALLOWED": lic.derived_data_allowed,
                "REDISTRIBUTION_ALLOWED": lic.redistribution_allowed,
                "API_REEXPOSURE_ALLOWED": lic.api_reexposure_allowed,
                "CACHE_ALLOWED": lic.cache_allowed,
                "RETENTION_ALLOWED": lic.retention_allowed,
                "SCREENSHOT_SOCIAL_CARD_ALLOWED": lic.screenshot_social_card_allowed,
                "LICENSE_EXPIRY": lic.license_expiry,
                "REVIEW_DATE": lic.review_date,
                "EVIDENCE_SOURCE": lic.evidence_source,
                "STATUS": lic.status,
            }
        )
    return out


def audit_unlicensed_public_sources(route_rows: list[dict[str, Any]]) -> list[str]:
    missing: list[str] = []
    for row in route_rows:
        sid = row.get("license_source_id")
        if not sid:
            continue
        lic = get_source_license(str(sid))
        if lic is None or not lic.license_public_display_pass:
            missing.append(f"{row.get('method')} {row.get('path')} source={sid}")
    return missing
