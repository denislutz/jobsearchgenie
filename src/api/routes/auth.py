from typing import Any

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup")
async def signup() -> dict[str, Any]:
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.post("/login")
async def login() -> dict[str, Any]:
    raise HTTPException(status_code=501, detail="Not implemented yet")
