from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.database import init_db, close_db
from app.api import (
    auth_router,
    accounts_router,
    proxies_router,
    profiles_router,
    campaigns_router,
    jobs_router,
    stats_router
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup
    await init_db()
    yield
    # Shutdown
    await close_db()


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_credentials,
    allow_methods=settings.cors_methods,
    allow_headers=settings.cors_headers,
)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "app_name": settings.app_name,
        "debug": settings.debug
    }


# Mount API routers
app.include_router(auth_router, prefix=settings.api_prefix)
app.include_router(accounts_router, prefix=settings.api_prefix)
app.include_router(proxies_router, prefix=settings.api_prefix)
app.include_router(profiles_router, prefix=settings.api_prefix)
app.include_router(campaigns_router, prefix=settings.api_prefix)
app.include_router(jobs_router, prefix=settings.api_prefix)
app.include_router(stats_router, prefix=settings.api_prefix)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": f"Welcome to {settings.app_name} API",
        "docs": "/docs",
        "health": "/health"
    }
