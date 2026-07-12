import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock
from main import app
from app.core.config import get_settings
from app.core.dependencies import get_audit

settings = get_settings()


@pytest.fixture
def override_audit():
    mock_audit = AsyncMock()
    app.dependency_overrides[get_audit] = lambda: mock_audit
    yield mock_audit
    app.dependency_overrides.pop(get_audit, None)


@pytest.mark.asyncio
async def test_insights_endpoint_returns_200(override_audit):
    override_audit.get_anomalies.return_value = {
        "high_failure_tools": ["weather_tool"],
        "slow_sessions": ["session_abc"],
        "slow_tools": [{"tool": "calc_tool", "avg_ms": 1200.0}],
    }

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(
            "/api/v1/insights",
            headers={"X-API-KEY": settings.API_KEY}
        )

    assert response.status_code == 200
    data = response.json()
    assert "high_failure_tools" in data
    assert "slow_sessions" in data
    assert "slow_tools" in data
    assert data["high_failure_tools"] == ["weather_tool"]
    assert data["slow_sessions"] == ["session_abc"]
    assert data["slow_tools"] == [{"tool": "calc_tool", "avg_ms": 1200.0}]


@pytest.mark.asyncio
async def test_insights_endpoint_auth_failure_invalid_key(override_audit):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(
            "/api/v1/insights",
            headers={"X-API-KEY": "wrong_key_123"}
        )

    assert response.status_code == 403
    assert "INVALID_API_KEY" in response.json()["detail"]


@pytest.mark.asyncio
async def test_insights_endpoint_auth_failure_missing_key(override_audit):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/insights")

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_insights_endpoint_returns_503_when_no_audit():
    app.dependency_overrides[get_audit] = lambda: None
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(
                "/api/v1/insights",
                headers={"X-API-KEY": settings.API_KEY}
            )

        assert response.status_code == 503
        assert "not available" in response.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_audit, None)
