from domain.job import Job, SearchRequest, SearchResponse
from sources.indeed import IndeedAdapter


class JobService:
    def __init__(self, indeed: IndeedAdapter) -> None:
        self._indeed = indeed

    async def search(self, request: SearchRequest) -> SearchResponse:
        jobs: list[Job] = await self._indeed.search(
            keywords=request.keywords,
            location=request.location,
            limit=request.limit,
            offset=request.offset,
            sort_by=request.sort_by,
        )

        if request.salary_min is not None:
            jobs = [j for j in jobs if j.salary is not None and j.salary.min is not None and j.salary.min >= request.salary_min]
        if request.salary_max is not None:
            jobs = [j for j in jobs if j.salary is not None and j.salary.max is not None and j.salary.max <= request.salary_max]

        return SearchResponse(
            total=len(jobs),
            limit=request.limit,
            offset=request.offset,
            jobs=jobs,
        )
