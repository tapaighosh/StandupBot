"""
StandupBot — Health Endpoint Tests

Tests for the health check and readiness probe endpoints.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Test that the health endpoint returns OK."""
    response = await client.get("/api/v1/health/")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "ok"
    assert data["version"] == "0.1.0"
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_health_response_format(client: AsyncClient):
    """Test that the health response has the correct structure."""
    response = await client.get("/api/v1/health/")
    data = response.json()

    assert "status" in data
    assert "version" in data
    assert "environment" in data
    assert "timestamp" in data
