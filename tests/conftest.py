from collections.abc import AsyncGenerator
from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from domain.job import Job, SearchResponse
from main import app
from services.job_service import JobService
from sources.indeed import IndeedAdapter


@pytest.fixture
def sample_jobs() -> list[Job]:
    return [
        Job(
            id="indeed-abc123",
            title="Senior Python Developer",
            company="Acme GmbH",
            location="Berlin, DE",
            description="We are looking for a senior Python developer.",
            posted_at=datetime(2026, 3, 10, tzinfo=timezone.utc),
            url="https://de.indeed.com/viewjob?jk=abc123",
            source="indeed",
        ),
        Job(
            id="indeed-def456",
            title="FastAPI Engineer",
            company="StartupX",
            location="Munich, DE",
            description="Join our growing team building APIs.",
            posted_at=datetime(2026, 3, 9, tzinfo=timezone.utc),
            url="https://de.indeed.com/viewjob?jk=def456",
            source="indeed",
        ),
    ]


@pytest.fixture
def mock_indeed_adapter(sample_jobs: list[Job]) -> AsyncMock:
    mock = AsyncMock(spec=IndeedAdapter)
    mock.search.return_value = sample_jobs
    return mock


@pytest_asyncio.fixture
async def async_client(mock_indeed_adapter: AsyncMock) -> AsyncGenerator[AsyncClient, None]:
    app.state.job_service = JobService(mock_indeed_adapter)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
