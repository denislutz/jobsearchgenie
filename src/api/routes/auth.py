from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup")
async def signup() -> dict:
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.post("/login")
async def login() -> dict:
    raise HTTPException(status_code=501, detail="Not implemented yet")
