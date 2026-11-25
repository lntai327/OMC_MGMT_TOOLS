import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.api.v1.router import api_v1_router
from app.core.config import settings
from app.core.database import db_manager
from app.core.init_db import init_db
from app.core.logging import setup_app_logging, get_logger

# Initialize logging to intercept Uvicorn and FastAPI logs immediately
setup_app_logging()
logger = get_logger("app_logger")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ensure storage directories exist
    os.makedirs(settings.STORAGE_PATH, exist_ok=True)
    os.makedirs(settings.TEMPLATES_PATH, exist_ok=True)
    os.makedirs(settings.UPLOADS_PATH, exist_ok=True)
    os.makedirs(settings.EXPORTS_PATH, exist_ok=True)
    os.makedirs(settings.LOGS_PATH, exist_ok=True)

    # Attach file handler to uvicorn, uvicorn.access, uvicorn.error after server starts
    setup_app_logging()

    # Automatically verify/create missing database tables and seed default admin
    await init_db()

    yield
    # Shutdown: Close database connections
    await db_manager.close()


app = FastAPI(
    title="VNPT GLI OMC Management Tools API",
    description="High-performance backend API with Celery asynchronous pipeline and WebSockets for VNPT GLI OMC.",
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


@app.exception_handler(StarletteHTTPException)
async def http_exception_logging_handler(request: Request, exc: StarletteHTTPException):
    """Log all HTTPExceptions (4xx, 5xx) into app.log with Vietnam timezone."""
    client_host = request.client.host if request.client else "unknown"
    log_msg = (
        f"HTTPException [{exc.status_code}] on {request.method} {request.url.path} "
        f"from {client_host} | Detail: {exc.detail}"
    )

    if exc.status_code >= 500:
        logger.error(log_msg)
    elif exc.status_code >= 400:
        logger.warning(log_msg)
    else:
        logger.info(log_msg)

    headers = getattr(exc, "headers", None)
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=headers,
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_logging_handler(request: Request, exc: RequestValidationError):
    """Log 422 Request Validation Errors into app.log."""
    client_host = request.client.host if request.client else "unknown"
    logger.warning(
        f"Validation Error (422) on {request.method} {request.url.path} from {client_host} | "
        f"Errors: {exc.errors()}"
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()},
    )


@app.exception_handler(Exception)
async def unhandled_exception_logging_handler(request: Request, exc: Exception):
    """Log 500 Unhandled Exceptions with full traceback into app.log."""
    client_host = request.client.host if request.client else "unknown"
    logger.exception(
        f"Unhandled Server Error (500) on {request.method} {request.url.path} from {client_host}: {str(exc)}"
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )


# Mount API routers
app.include_router(api_v1_router)


@app.get("/", tags=["Root"])
async def root():
    return {
        "app": "VNPT GLI OMC Management Tools API",
        "version": "1.0.0",
        "status": "online",
        "docs": "/docs",
    }


