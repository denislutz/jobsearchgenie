from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient

from domain.errors import AppError


@pytest.mark.asyncio
async def test_search_returns_200(async_client: AsyncClient) -> None:
    response = await async_client.get("/jobs/search?keywords=python&location=Berlin")
    assert response.status_code == 200
    data = response.json()
    assert "jobs" in data
    assert "total" in data
    assert "limit" in data
    assert "offset" in data


@pytest.mark.asyncio
async def test_search_missing_keywords(async_client: AsyncClient) -> None:
    response = await async_client.get("/jobs/search?location=Berlin")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_search_missing_location(async_client: AsyncClient) -> None:
    response = await async_client.get("/jobs/search?keywords=python")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_search_default_pagination(async_client: AsyncClient) -> None:
    response = await async_client.get("/jobs/search?keywords=python&location=Berlin")
    data = response.json()
    assert data["limit"] == 20
    assert data["offset"] == 0


@pytest.mark.asyncio
async def test_search_custom_pagination(async_client: AsyncClient) -> None:
    response = await async_client.get("/jobs/search?keywords=python&location=Berlin&limit=5&offset=10")
    data = response.json()
    assert data["limit"] == 5
    assert data["offset"] == 10


@pytest.mark.asyncio
async def test_search_invalid_sort_by(async_client: AsyncClient) -> None:
    response = await async_client.get("/jobs/search?keywords=python&location=Berlin&sort_by=invalid")
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_search_indeed_unavailable(async_client: AsyncClient, mock_indeed_adapter: AsyncMock) -> None:
    mock_indeed_adapter.search.side_effect = AppError(503, "Indeed unavailable: connection timeout")
    response = await async_client.get("/jobs/search?keywords=python&location=Berlin")
    assert response.status_code == 503
    assert "Indeed unavailable" in response.json()["error"]


@pytest.mark.asyncio
async def test_stub_job_detail(async_client: AsyncClient) -> None:
    response = await async_client.get("/jobs/abc123")
    assert response.status_code == 501


@pytest.mark.asyncio
async def test_stub_filters(async_client: AsyncClient) -> None:
    response = await async_client.get("/jobs/filters")
    assert response.status_code == 501


@pytest.mark.asyncio
async def test_health(async_client: AsyncClient) -> None:
    response = await async_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
