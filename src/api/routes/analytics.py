from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/trending")
async def get_trending() -> dict:
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.get("/salary-ranges")
async def get_salary_ranges() -> dict:
    raise HTTPException(status_code=501, detail="Not implemented yet")
