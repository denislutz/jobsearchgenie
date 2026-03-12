from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/saved-searches", tags=["saved-searches"])


@router.post("")
async def create_saved_search() -> dict:
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.get("")
async def list_saved_searches() -> dict:
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.delete("/{search_id}")
async def delete_saved_search(search_id: str) -> dict:
    raise HTTPException(status_code=501, detail="Not implemented yet")
