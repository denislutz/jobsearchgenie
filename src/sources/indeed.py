from datetime import datetime
from email.utils import parsedate_to_datetime

import httpx
from tenacity import RetryError, retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from config import get_settings
from domain.errors import AppError
from domain.job import Job

_INDEED_API_URL = "https://api.indeed.com/ads/apisearch"


def _parse_date(date_str: str | None) -> datetime | None:
    if not date_str:
        return None
    try:
        return parsedate_to_datetime(date_str)
    except Exception:
        return None


def _normalize(raw: dict) -> Job:
    return Job(
        id=f"indeed-{raw.get('jobkey', '')}",
        title=raw.get("jobtitle", ""),
        company=raw.get("company", ""),
        location=raw.get("formattedLocation", ""),
        description=raw.get("snippet", ""),
        posted_at=_parse_date(raw.get("date")),
        url=raw.get("url", ""),
        source="indeed",
    )


class IndeedAdapter:
    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client

    @retry(
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError)),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        stop=stop_after_attempt(3),
        reraise=False,
    )
    async def _fetch_raw(self, params: dict) -> dict:
        response = await self._client.get(_INDEED_API_URL, params=params, timeout=10.0)
        if response.status_code >= 500:
            raise httpx.HTTPStatusError(
                f"Indeed returned {response.status_code}",
                request=response.request,
                response=response,
            )
        response.raise_for_status()
        return response.json()  # type: ignore[no-any-return]

    async def search(
        self,
        keywords: str,
        location: str,
        limit: int = 20,
        offset: int = 0,
        sort_by: str = "relevance",
    ) -> list[Job]:
        settings = get_settings()
        params: dict[str, str | int] = {
            "publisher": settings.indeed_publisher_id,
            "q": keywords,
            "l": location,
            "co": "de",
            "v": "2",
            "format": "json",
            "limit": limit,
            "start": offset,
        }
        if sort_by == "date":
            params["sort"] = "date"

        try:
            data = await self._fetch_raw(params)
        except RetryError as exc:
            raise AppError(503, f"Indeed unavailable: {exc.__cause__}") from exc
        except (httpx.TimeoutException, httpx.ConnectError, httpx.HTTPStatusError) as exc:
            raise AppError(503, f"Indeed unavailable: {exc}") from exc

        results: list[dict] = data.get("results", [])
        return [_normalize(r) for r in results]
