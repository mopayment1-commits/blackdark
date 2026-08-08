"""
BLACKDARK — GraphQL API with authentication context.
"""

from __future__ import annotations

from dataclasses import dataclass

import strawberry
from strawberry.fastapi import GraphQLRouter
from strawberry.types import Info


@dataclass
class GraphContext:
    user: dict | None = None


@strawberry.type
class HealthStatus:
    status: str
    probe: str


@strawberry.type
class OracleAccuracy:
    total_predictions: int
    resolved_predictions: int
    recent_hit_rate_percent: float
    average_accuracy_percent: float


@strawberry.type
class ArbitrageOpportunity:
    kind: str
    asset: str
    net_profit_usdt: float
    execution_feasibility: str


@strawberry.type
class RiskStatus:
    trading_frozen: bool
    freeze_reason: str
    max_slippage_bps: float
    active_stop_losses: int


@strawberry.type
class DataSourceSummary:
    total_sources: int
    categories_json: str


def _require_user(info: Info) -> dict:
    ctx = info.context
    user = getattr(ctx, "user", None) if ctx else None
    if not user:
        raise PermissionError("Authentication required — send Authorization: Bearer <token>")
    return user


def _require_pro(info: Info) -> dict:
    user = _require_user(info)
    tier = str(user.get("tier") or "free")
    if tier not in {"pro", "whale"}:
        raise PermissionError("Pro tier or above required")
    return user


@strawberry.type
class Query:
    @strawberry.field
    async def health(self) -> HealthStatus:
        return HealthStatus(status="ok", probe="graphql")

    @strawberry.field
    async def oracle_accuracy(self) -> OracleAccuracy:
        from ml.public_accuracy import build_public_accuracy_payload

        payload = await build_public_accuracy_payload(recent_limit=10)
        oracle = payload.get("oracle") or {}
        return OracleAccuracy(
            total_predictions=int(oracle.get("total_predictions") or 0),
            resolved_predictions=int(oracle.get("resolved_predictions") or 0),
            recent_hit_rate_percent=float(oracle.get("recent_hit_rate_percent") or 0),
            average_accuracy_percent=float(oracle.get("average_accuracy_percent") or 0),
        )

    @strawberry.field
    async def top_arbitrage(self, info: Info, limit: int = 5) -> list[ArbitrageOpportunity]:
        _require_pro(info)
        from scan_coordinator import get_shared_scan

        scan = await get_shared_scan(profitable_only=True)
        opps = (scan.get("opportunities") or [])[:limit]
        return [
            ArbitrageOpportunity(
                kind=str(o.get("kind") or ""),
                asset=str(o.get("asset") or ""),
                net_profit_usdt=float(o.get("net_profit_usdt") or 0),
                execution_feasibility=str(o.get("execution_feasibility") or ""),
            )
            for o in opps
        ]

    @strawberry.field
    def risk_status(self, info: Info) -> RiskStatus:
        _require_pro(info)
        from risk_manager import risk_status as _rs

        s = _rs()
        return RiskStatus(
            trading_frozen=bool(s.get("trading_frozen")),
            freeze_reason=str(s.get("freeze_reason") or ""),
            max_slippage_bps=float(s.get("max_slippage_bps") or 0),
            active_stop_losses=int(s.get("active_stop_losses") or 0),
        )

    @strawberry.field
    def data_sources(self) -> DataSourceSummary:
        import json

        from data_sources_registry import registry_summary

        summary = registry_summary()
        return DataSourceSummary(
            total_sources=int(summary.get("total_sources") or 0),
            categories_json=json.dumps(summary.get("by_category") or {}),
        )


schema = strawberry.Schema(query=Query)


async def graphql_context(request) -> GraphContext:
    from auth_service import get_user_from_token

    auth = request.headers.get("Authorization") or ""
    token = auth.removeprefix("Bearer ")
    user = await get_user_from_token(token.strip()) if token.strip() else None
    ctx = GraphContext()
    ctx.user = user
    return ctx


def create_graphql_router() -> GraphQLRouter:
    return GraphQLRouter(schema, path="/graphql", context_getter=graphql_context)
