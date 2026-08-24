"""Canonical asset resolver — stable mapping from any vendor input."""

from __future__ import annotations

import re

from blackdark.canonical.registry import build_registry_index, get_canonical_asset
from blackdark.canonical.schema import CanonicalAsset, ResolveResult, make_canonical_id
from blackdark.canonical.vendor_maps import COINGECKO_REVERSE, KRAKEN_BASE_REVERSE

_PAIR_RE = re.compile(r"^([A-Z0-9]{2,12})(USDT|USD|USDC|BUSD)$")
_ADDR_RE = re.compile(r"^0x[a-fA-F0-9]{40}$")


def _strip_input(raw: str) -> str:
    return raw.strip()


def resolve_asset(raw: str, *, chain: str | None = None) -> ResolveResult:
    """
    Resolve symbol, alias, trading pair, CoinGecko id, or contract address
    to a stable canonical asset record.
    """
    original = _strip_input(raw)
    if not original:
        return ResolveResult(found=False, input=raw)

    idx = build_registry_index()
    upper = original.upper().replace("/", "").replace("-", "")

    # Canonical ID direct
    if upper.startswith("BD:") or original.lower().startswith("bd:"):
        cid = original if original.lower().startswith("bd:") else f"bd:{upper[3:]}"
        asset = idx["by_canonical"].get(cid)
        if asset:
            return ResolveResult(
                found=True,
                input=raw,
                canonical_id=asset.canonical_id,
                symbol=asset.symbol,
                asset=asset,
                matched_via="canonical_id",
            )

    # Contract address
    if _ADDR_RE.match(original):
        asset = idx["by_contract"].get(original.lower())
        if asset:
            return ResolveResult(
                found=True,
                input=raw,
                canonical_id=asset.canonical_id,
                symbol=asset.symbol,
                asset=asset,
                matched_via="contract_address",
            )

    # CoinGecko slug
    cg_asset = idx["by_coingecko"].get(original.lower())
    if cg_asset:
        return ResolveResult(
            found=True,
            input=raw,
            canonical_id=cg_asset.canonical_id,
            symbol=cg_asset.symbol,
            asset=cg_asset,
            matched_via="coingecko_id",
        )

    # Trading pair (BTCUSDT, ETHUSD)
    pair_asset = idx["by_pair"].get(upper)
    if pair_asset:
        return ResolveResult(
            found=True,
            input=raw,
            canonical_id=pair_asset.canonical_id,
            symbol=pair_asset.symbol,
            asset=pair_asset,
            matched_via="trading_pair",
        )
    m = _PAIR_RE.match(upper)
    if m:
        base = m.group(1)
        base = KRAKEN_BASE_REVERSE.get(base, base)
        asset = idx["by_symbol"].get(base) or idx["by_alias"].get(base)
        if asset:
            return ResolveResult(
                found=True,
                input=raw,
                canonical_id=asset.canonical_id,
                symbol=asset.symbol,
                asset=asset,
                matched_via="pair_base",
            )

    # Symbol / alias
    asset = idx["by_symbol"].get(upper) or idx["by_alias"].get(upper)
    if asset:
        return ResolveResult(
            found=True,
            input=raw,
            canonical_id=asset.canonical_id,
            symbol=asset.symbol,
            asset=asset,
            matched_via="symbol" if idx["by_symbol"].get(upper) else "alias",
        )

    # CoinGecko reverse table fallback
    cg_sym = COINGECKO_REVERSE.get(original.lower())
    if cg_sym:
        asset = idx["by_symbol"].get(cg_sym)
        if asset:
            return ResolveResult(
                found=True,
                input=raw,
                canonical_id=asset.canonical_id,
                symbol=asset.symbol,
                asset=asset,
                matched_via="coingecko_slug",
            )

    # Unknown — return stable synthetic ID for passthrough (no silent remap)
    return ResolveResult(
        found=False,
        input=raw,
        canonical_id=make_canonical_id(upper[:12] if upper.isalnum() else "UNKNOWN"),
        symbol=upper if upper.isalnum() and len(upper) <= 12 else None,
        matched_via="unmapped",
    )


def resolve_symbol(raw: str) -> str:
    """Backward-compatible symbol normalizer used across the platform."""
    result = resolve_asset(raw)
    if result.found and result.symbol:
        return result.symbol
    cleaned = raw.upper().strip().replace("/", "").replace("-", "")
    if cleaned.endswith("USDT"):
        return cleaned[:-4]
    return cleaned


def contract_address(symbol: str, chain: str = "ethereum") -> str | None:
    """Lookup on-chain contract for a canonical symbol."""
    asset = get_canonical_asset(symbol)
    if not asset:
        return None
    chain_l = chain.lower()
    for key, meta in asset.contracts.items():
        if key.lower().startswith(chain_l):
            return str(meta.get("address") or "") or None
    return None
