from datetime import datetime

from pydantic import BaseModel, Field


class Salary(BaseModel):
    min: int | None = None
    max: int | None = None
    currency: str = "EUR"


class Job(BaseModel):
    id: str
    title: str
    company: str
    location: str
    job_type: str | None = None
    contract_type: str | None = None
    salary: Salary | None = None
    description: str
    posted_at: datetime | None = None
    url: str
    source: str
    extracted_skills: list[str] = Field(default_factory=list)
    normalized_level: str | None = None
    confidence_score: float | None = None


class SearchRequest(BaseModel):
    keywords: str
    location: str
    salary_min: int | None = None
    salary_max: int | None = None
    job_type: str | None = None
    contract_type: str | None = None
    sources: list[str] = Field(default_factory=lambda: ["indeed"])
    limit: int = Field(default=20, ge=1, le=25)
    offset: int = Field(default=0, ge=0)
    sort_by: str = "relevance"


class SearchResponse(BaseModel):
    total: int
    limit: int
    offset: int
    jobs: list[Job]
