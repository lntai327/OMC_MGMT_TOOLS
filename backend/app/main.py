import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.router import api_v1_router
from app.core.config import settings
from app.core.database import db_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ensure storage directories exist
    os.makedirs(settings.STORAGE_PATH, exist_ok=True)
    os.makedirs(settings.TEMPLATES_PATH, exist_ok=True)
    os.makedirs(settings.UPLOADS_PATH, exist_ok=True)
    os.makedirs(settings.EXPORTS_PATH, exist_ok=True)
    os.makedirs(settings.LOGS_PATH, exist_ok=True)
    yield
    # Shutdown: Close database connections
    await db_manager.close()


app = FastAPI(
    title="VNPT OMC Management Tools API",
    description="High-performance backend API with Celery asynchronous pipeline and WebSockets for VNPT OMC.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routers
app.include_router(api_v1_router)


@app.get("/", tags=["Root"])
async def root():
    return {
        "app": "VNPT OMC Management Tools API",
        "version": "1.0.0",
        "status": "online",
        "docs": "/docs",
    }

