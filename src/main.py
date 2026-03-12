from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from api.router import router
from domain.errors import AppError
from services.job_service import JobService
from sources.indeed import IndeedAdapter


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    http_client = httpx.AsyncClient()
    app.state.job_service = JobService(IndeedAdapter(http_client))
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


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(status_code=exc.status, content={"error": exc.message})
