from fastapi import APIRouter

from api.routes import analytics, auth, jobs, saved_searches

router = APIRouter()

router.include_router(jobs.router)
router.include_router(analytics.router)
router.include_router(saved_searches.router)
router.include_router(auth.router)
