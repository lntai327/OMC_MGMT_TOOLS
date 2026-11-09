from fastapi import APIRouter
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.jobs import router as jobs_router
from app.api.v1.endpoints.downloads import router as downloads_router

from app.api.v1.endpoints.megawan_metronet import router as megawan_router

from app.api.v1.websockets.job_progress import router as ws_router

api_v1_router = APIRouter(prefix="/api/v1")

api_v1_router.include_router(auth_router)
api_v1_router.include_router(health_router)
api_v1_router.include_router(jobs_router)
api_v1_router.include_router(downloads_router)
api_v1_router.include_router(megawan_router)
api_v1_router.include_router(ws_router)

