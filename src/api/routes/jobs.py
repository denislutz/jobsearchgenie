from fastapi import APIRouter, HTTPException, Query, Request

from domain.errors import InvalidSearchParamsError, SourceUnavailableError
from domain.job import SearchRequest, SearchResponse

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/search", response_model=SearchResponse)
async def search_jobs(
    request: Request,
    keywords: str = Query(...),
    location: str = Query(...),
    salary_min: int | None = Query(None),
    salary_max: int | None = Query(None),
    job_type: str | None = Query(None),
    contract_type: str | None = Query(None),
    limit: int = Query(20, ge=1, le=25),
    offset: int = Query(0, ge=0),
    sort_by: str = Query("relevance"),
) -> SearchResponse:
    if sort_by not in ("relevance", "date"):
        raise HTTPException(status_code=400, detail={
            "error": {"code": "BAD_REQUEST", "message": "sort_by must be 'relevance' or 'date'", "details": {}}
        })

    search_req = SearchRequest(
        keywords=keywords,
        location=location,
        salary_min=salary_min,
        salary_max=salary_max,
        job_type=job_type,
        contract_type=contract_type,
        limit=limit,
        offset=offset,
        sort_by=sort_by,
    )

    try:
        return await request.app.state.job_service.search(search_req)
    except SourceUnavailableError as exc:
        raise HTTPException(
            status_code=503,
            detail={"error": {"code": "SERVICE_UNAVAILABLE", "message": str(exc), "details": {}}},
        ) from exc
    except InvalidSearchParamsError as exc:
        raise HTTPException(
            status_code=400,
            detail={"error": {"code": "BAD_REQUEST", "message": exc.detail, "details": {}}},
        ) from exc


@router.get("/filters")
async def get_filters() -> dict:
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.get("/{job_id}")
async def get_job(job_id: str) -> dict:
    raise HTTPException(status_code=501, detail="Not implemented yet")
