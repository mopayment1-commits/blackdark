"""Tests for GraphQL schema."""

import pytest


@pytest.mark.asyncio
async def test_graphql_health_query():
    from graphql_schema import schema

    result = await schema.execute("{ health { status probe } }")
    assert result.errors is None
    assert "ok" in str(result.data)


@pytest.mark.asyncio
async def test_graphql_data_sources():
    from graphql_schema import schema

    result = await schema.execute("{ dataSources { totalSources } }")
    assert result.errors is None
    assert result.data["dataSources"]["totalSources"] >= 100
