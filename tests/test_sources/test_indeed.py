from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from domain.errors import SourceUnavailableError
from domain.job import Job
from sources.indeed import IndeedAdapter, _normalize


# --- Normalization unit tests (no I/O) ---

RAW_JOB = {
    "jobkey": "abc123",
    "jobtitle": "Senior Python Developer",
    "company": "Acme GmbH",
    "formattedLocation": "Berlin, DE",
    "snippet": "We are looking for a senior developer.",
    "date": "Mon, 10 Mar 2026 00:00:00 GMT",
    "url": "https://de.indeed.com/viewjob?jk=abc123",
}


def test_normalize_job_fields() -> None:
    job = _normalize(RAW_JOB)
    assert isinstance(job, Job)
    assert job.title == "Senior Python Developer"
    assert job.company == "Acme GmbH"
    assert job.location == "Berlin, DE"
    assert job.description == "We are looking for a senior developer."
    assert job.url == "https://de.indeed.com/viewjob?jk=abc123"
    assert job.source == "indeed"


def test_id_prefixed_with_indeed() -> None:
    job = _normalize(RAW_JOB)
    assert job.id.startswith("indeed-")
    assert job.id == "indeed-abc123"


def test_posted_at_parsed() -> None:
    job = _normalize(RAW_JOB)
    assert isinstance(job.posted_at, datetime)


def test_normalize_missing_date() -> None:
    raw = {**RAW_JOB, "date": None}
    job = _normalize(raw)
    assert job.posted_at is None


# --- Adapter integration tests (mocked httpx) ---

@pytest.fixture
def mock_indeed_response() -> dict:
    return {
        "results": [RAW_JOB],
        "totalResults": 1,
    }


@pytest.fixture
def http_client() -> httpx.AsyncClient:
    return httpx.AsyncClient()


@pytest.mark.asyncio
async def test_search_returns_jobs(mock_indeed_response: dict) -> None:
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_indeed_response
    mock_response.raise_for_status = MagicMock()

    client = httpx.AsyncClient()
    adapter = IndeedAdapter(client)

    with patch("sources.indeed.get_settings") as mock_settings:
        mock_settings.return_value.indeed_publisher_id = "test_publisher"
        with patch.object(client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            jobs = await adapter.search("python", "Berlin")

    assert len(jobs) == 1
    assert jobs[0].id == "indeed-abc123"


@pytest.mark.asyncio
async def test_retry_on_timeout() -> None:
    client = httpx.AsyncClient()
    adapter = IndeedAdapter(client)

    successful_response = MagicMock()
    successful_response.status_code = 200
    successful_response.json.return_value = {"results": [RAW_JOB]}
    successful_response.raise_for_status = MagicMock()

    with patch("sources.indeed.get_settings") as mock_settings:
        mock_settings.return_value.indeed_publisher_id = "test_publisher"
        with patch.object(client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = [
                httpx.TimeoutException("timeout"),
                httpx.TimeoutException("timeout"),
                successful_response,
            ]
            jobs = await adapter.search("python", "Berlin")

    assert len(jobs) == 1
    assert mock_get.call_count == 3


@pytest.mark.asyncio
async def test_raises_source_unavailable_after_retries() -> None:
    client = httpx.AsyncClient()
    adapter = IndeedAdapter(client)

    with patch("sources.indeed.get_settings") as mock_settings:
        mock_settings.return_value.indeed_publisher_id = "test_publisher"
        with patch.object(client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = httpx.TimeoutException("timeout")
            with pytest.raises(SourceUnavailableError) as exc_info:
                await adapter.search("python", "Berlin")

    assert exc_info.value.source == "indeed"


@pytest.mark.asyncio
async def test_http_500_raises_source_unavailable() -> None:
    """HTTPStatusError is not retried — it propagates immediately as SourceUnavailableError."""
    client = httpx.AsyncClient()
    adapter = IndeedAdapter(client)

    bad_response = MagicMock()
    bad_response.status_code = 500
    bad_response.request = MagicMock()

    with patch("sources.indeed.get_settings") as mock_settings:
        mock_settings.return_value.indeed_publisher_id = "test_publisher"
        with patch.object(client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = bad_response
            with pytest.raises(SourceUnavailableError) as exc_info:
                await adapter.search("python", "Berlin")

    assert exc_info.value.source == "indeed"
    assert mock_get.call_count == 1  # no retries for 500
