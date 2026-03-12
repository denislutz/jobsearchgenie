from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from api.router import router
from domain.errors import InvalidSearchParamsError, SourceUnavailableError
from services.job_service import JobService
from sources.indeed import IndeedAdapter


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    http_client = httpx.AsyncClient()
    indeed_adapter = IndeedAdapter(http_client)
    app.state.job_service = JobService(indeed_adapter)
    app.state.http_client = http_client
    yield
    await http_client.aclose()


app = FastAPI(
    title="JobSearchGenie",
    version="0.1.0",
    description="Unified job search API for the DACH market",
    lifespan=lifespan,
)

app.include_router(router)


@app.get("/health", tags=["monitoring"])
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.exception_handler(SourceUnavailableError)
async def source_unavailable_handler(request: Request, exc: SourceUnavailableError) -> JSONResponse:
    return JSONResponse(
        status_code=503,
        content={"error": {"code": "SERVICE_UNAVAILABLE", "message": str(exc), "details": {}}},
    )


@app.exception_handler(InvalidSearchParamsError)
async def invalid_params_handler(request: Request, exc: InvalidSearchParamsError) -> JSONResponse:
    return JSONResponse(
        status_code=400,
        content={"error": {"code": "BAD_REQUEST", "message": exc.detail, "details": {}}},
    )
